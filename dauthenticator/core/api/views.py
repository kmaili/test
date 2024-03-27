from datetime import timedelta, datetime
import re
import json
import pytz
import requests
from typing import List
from django.core.exceptions import MultipleObjectsReturned, FieldDoesNotExist, ObjectDoesNotExist 
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import APIException
from dauthenticator.core.models import AccountAuthentification, AirflowDAGRUN, Driver
from dauthenticator.core.api.serializers import AccountAuthentificationSerializer, DriverSerializer
from ...utils.logging import Logger
from ...utils.utils import load_class, check_cookies, get_node_available
from ...utils import config
# 3. Améliorer le code ici, une fonction générale pour tous les drivers login
# 4. discuter avec Sun pour les commentaires twitter crawl

# I. obtenir les drivers en login
# II. créer un système pour que pendant 3 heures les drivers (sessions) soient vifs

def driver_login(accounts:List[dict], media_name:str):
    """Get all valid accounts and update info for all accounts

        Args:
            accounts List of dict: accounts that need login
            media_name str: name of the media
        Returns:
            cookies: list of login cookies for each account
    """

    cookies = []
    drivers = []

    for account in accounts:

        account_info = account["account"]
        driver_info = Driver.objects.get(driver_name=media_name)           

        driver = load_class(driver_info.import_package)(
            driver_language='en-EN',
            credentials_login=account_info["login"],
            credentials_password=account_info["password"],
            credentials_username=account_info["user_id"],
            remote_url=account_info["ip"],
            headless = False
        )
        cookies.append(driver.get_login_cookies()) if driver.login() else cookies.append("Login Failed")
        driver.close()
        drivers.append(driver)
    return cookies

class AccountAuthentificationViewSet(GenericViewSet):

    serializer_class = AccountAuthentificationSerializer
    querysetdriver = AccountAuthentification.objects.all()
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    logger = Logger(config).logger

    @action(detail=False, methods=['POST'])
    def get_available_accounts(self, request):
        """Get all valid accounts and update info for all accounts

        Args:
            data (_dict_): accounts for which media and number of accounts needed

        Returns:
            _Dict_: accounts or session available
        """

        media_name = request.data["media"] 
        client_name = request.data.get("client_name","crawlserver")
        nb_jobs = int(request.data["nb_jobs"])
        current_date = datetime.now().astimezone(pytz.timezone('Europe/Paris'))

        # find all accounts of this media
        all_accounts = AccountAuthentification.objects.filter(media=media_name, client_name=client_name, cookie_valid=True).order_by("cookie", "cookie_real_end")
        all_accounts_situations = []
        print(' all_accounts_situations ',len(all_accounts))
        # Get the driver strategy related to the media name
        driver_info = Driver.objects.get(driver_name = media_name)
        for account in all_accounts:
            available, should_login =  getattr(self, driver_info.strategy)(account, current_date, media_name)
            print('------------------------available ',available)
            # 
            # 1. sort all_accounts in order no cookie and with cookie
            # 2. If there is an account or session available, break

            all_accounts_situations.append(
                {"account": {
                    "user_id": account.user_id, 
                    "login": account.login, 
                    "password": account.password, 
                    "ip": account.ip, 
                    "media": media_name, 
                    "cookie": account.cookie or "", 
                    "cookie_start": account.cookie_start.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_start else "", 
                    "cookie_expected_end": account.cookie_expected_end.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_expected_end else "", 
                    "cookie_real_end": account.cookie_real_end.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_real_end else "1980-01-01 00:00:00.954774+00:00", 
                    "modified_at": account.modified_at}, 
                    "available": available, 
                    "should_login": should_login})  
                    
        accounts_available = list(filter(lambda account: account["available"], all_accounts_situations))
        # if there are no accounts available, just tell the Scheduler that there are no accounts
        self.logger.info(f'\n account available = {len(accounts_available)}')

        if not accounts_available:
            self.logger.info(f"There is no account available")
            return Response(status=status.HTTP_200_OK, data=[])

        # login and get cookies
        accounts_selected = self.get_cookies_by_login(accounts_available, nb_jobs, media_name)
        return Response(status=status.HTTP_200_OK, data=accounts_selected)

    def get_cookies_by_login(self, accounts_available, nb_jobs, media_name):
        """for all accounts selected, pass login get cookies for these accounts, if there are already cookies,
        just keep the cookie without login

        Args:
            accounts_available (_List[Dict]_): All accounts available
            nb_jobs (_int_): Number of accounts asked by Scheduler

        Returns:
            _List[Dict]_: Accounts to use by Scheduler
        """

        #self.logger.info(f"\n ----- inside the function get_cookies_by_login -----\n")
        accounts_to_login = list(filter(lambda account: account["should_login"], accounts_available))
        self.logger.info(f"accounts_to_login = {accounts_to_login} ")

        accounts_in_using_once = list(filter(lambda account: not account["should_login"], accounts_available))
        accounts_selected = []
        if accounts_to_login:
            # We prefer those who haven't login
            # select that used earliest
            accounts_to_login.sort(key=lambda account: account["account"]["cookie_real_end"])
            # Not login all accounts without use
            if len(accounts_to_login) >= nb_jobs:
                accounts_to_login = accounts_to_login[:nb_jobs]
            # login according to media
            self.logger.info(f"Number of accounts to log in = {len(accounts_to_login)} " )
            cookies = driver_login(accounts_to_login, media_name)
            assert len(cookies) == len(accounts_to_login)
            # filter login failed
            # keep cookies which have login success
            # update account without login success
            accounts_logined = []
            for i in range(len(accounts_to_login)):
                cookie = json.dumps(cookies[i])
                if "Login Failed" not in str(cookie):
                    accounts_to_login[i]["account"]["cookie"] = cookie
                    cookie_start = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                    cookie_expected_end = cookie_start + timedelta(hours=3)
                    # update state of this account available
                    accounts_to_login[i]["account"]["cookie"] = cookie
                    accounts_to_login[i]["account"]["cookie_start"] = cookie_start
                    accounts_to_login[i]["account"]["cookie_expected_end"] = cookie_expected_end
                    accounts_logined.append(accounts_to_login[i])
                    user_id = accounts_to_login[i]["account"]["user_id"]
                    try:
                        AccountAuthentification.objects.filter(user_id=user_id,media=media_name).update(
                            cookie=cookie, cookie_start=cookie_start,
                            cookie_expected_end=cookie_expected_end,
                            cookie_valid=True,
                            account_active=True,
                            account_valid=True
                        )
                    except FieldDoesNotExist as e :
                        self.logger.error(f"Field Does not exist {e}")
                        pass

                else:
                    user_id = accounts_to_login[i]["account"]["user_id"]
                    AccountAuthentification.objects.filter(user_id=user_id,media= media_name).update(
                        cookie="",
                        cookie_valid=False,
                        account_active=False,
                        account_valid=False
                    )
            accounts_selected.extend(accounts_logined)
        # if all the accounts have been login, select that used earliest
        if len(accounts_selected) < nb_jobs:
            accounts_in_using_once.sort(key=lambda account: account["account"]["modified_at"])
            accounts_selected.extend(accounts_in_using_once)
        # Json parser cookie for accounts:
        accounts_selected = accounts_selected[:nb_jobs]
        try:
            accounts_selected.sort(key=lambda account: len(AirflowDAGRUN.objects.filter(session=AccountAuthentification.objects.get(user_id=account["account"]["user_id"],media = media_name))))  # noqa E501
        except MultipleObjectsReturned  as e:
            self.logger.error(f"Multiple Object returned {e}")
        except ObjectDoesNotExist as e:
            self.logger.error(f"Object does not exist {e}")
            accounts_selected = []

        for i in range(len(accounts_selected)):
            accounts_selected[i]["account"]["cookie"] = json.loads(accounts_selected[i]["account"]["cookie"])
        return accounts_selected

    def update_account(self, user_id, cookie, session_real_end, media_name):
        try:
            AccountAuthentification.objects.filter(user_id=user_id,media=media_name).update(
                        cookie=cookie,
                        cookie_real_end=session_real_end,
                        cookie_valid=False,
                        account_active=False,
                        account_valid=False,
                    )

        except  AccountAuthentification.DoesNotExist:
            self.logger.info("Account not found")
        except FieldDoesNotExist as e :
            self.logger.error(f"Field Does not exist {e}")

    def update_account_state(self, user_id, cookie_start, cookie_expected_end, cookie, session_real_end, media_name, error="", cookie_valid=False, account_active=False, account_valid=False):
        try:
            AccountAuthentification.objects.filter(user_id=user_id,media=media_name).update(
                        cookie_start=cookie_start,
                        cookie_expected_end=cookie_expected_end,
                        cookie=cookie,
                        cookie_real_end=session_real_end,
                        cookie_valid=cookie_valid,
                        account_active=account_active,
                        account_valid=account_valid,
                        issue=error
                    )
        except  AccountAuthentification.DoesNotExist:
            self.logger.info("Account not found")
        except FieldDoesNotExist as e :
            self.logger.error(f"Field Does not exist {e}")

    def strategy1(self, account, current_date, media_name):
        """To verify if an account is now available following the first strategy

        Args:
            account (_AccountAuthentification_): the Object of AccountAuthentification
            current_date (_Datetime_): the date which Airflow Scanner Check Dauthenticator

        Returns:
            _Tuple(Boolean, Boolean)_: (Is this account available, Should have a login or not)
        """
        cookie = account.cookie
        cookie_start = account.cookie_start
        cookie_real_end = account.cookie_real_end
        cookie_expected_end = account.cookie_expected_end
        ip = account.ip

        # check if there is availabe nodes
        if get_node_available(self.logger, ip) == 0:
            self.logger.info(f"There is no node selenium available in cluster {ip}")
            return (False, False)
        
        last_use_date = cookie_real_end
        if not cookie :
            if not cookie_real_end:       # if cookie_real_end is empty this mean we are going to use this account for the first time
                self.logger.info(f"{account.user_id} has never been used or has stayed empty for three hours, so login if necessary")  
                return (True, True)
            # check if the account has completed 3 hours of rest
            next_use_date = last_use_date + timedelta(hours=3)
            return (current_date >= next_use_date, True)

        # check if there is a running session for this account    
        dag_runs = AirflowDAGRUN.objects.filter(session=account)  
        

        if cookie_expected_end >= current_date :  # The session is in 3 hours
            # check if there are already two DAG_Runs using this session
            # if no, we can use this session, otherwise no
            self.logger.info(f"{account.user_id} there are {len(dag_runs)} DAG_Runs using this session, ")
            return (len(dag_runs) < 2, False)

        else:  # The session has finished 3 hours
            if len(dag_runs) > 1 :
                # wait for crawl to be completed
                self.logger.info(f"{account.user_id} is in use, so don't stop it and never use it")
            else:

                try :
                    hours = (current_date - cookie_real_end).seconds // 60 // 60
                    # if the difference between current date and cookie real end is greater than 3 hours we can use the account
                    if hours >= 3 and len(dag_runs) == 0 :
                        self.logger.info(f"{account.user_id} session completed 3 hours of rest")
                        self.update_account_state(account.user_id,account.cookie_start, cookie_expected_end,"", cookie_real_end, media_name)
                        return (True, True)
                except: 
                    pass
                
                # The account should complete 3 hours of rest
                session_real_end = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                self.logger.info(f"{account.user_id} session has finished and it should stop for 3 hours")
                self.update_account_state(account.user_id,account.cookie_start, cookie_expected_end,"", cookie_real_end, media_name)
       
            return (False, False)

    def strategy2(self, account, current_date, media_name):
        """To verify is this account available now

        Args:
            account (_AccountAuthentification_): the Object of AccountAuthentification
            current_date (_Datetime_): the date which Airflow Scanner Check Dauthenticator

        Returns:
            _Tuple(Boolean, Boolean)_: (Is this account available, Should have a login or not)
        """
        cookie = account.cookie
        cookie_real_end = account.cookie_real_end
        cookie_expected_end = account.cookie_expected_end
        login = account.login  

        last_use_date = cookie_real_end

        # If cookie is None, you can't use it. You need to add cookies first!
        if not cookie: 
            self.logger.info(f"There is no cookies for this account {login}")
            return  (False, False)

        valid, error = check_cookies(cookie)
        if not valid : 
            # if the cookies are not valid we need to delete them from the database
            self.update_account_state(account.user_id,account.cookie_start, account.cookie_expected_end,account.cookie, None, media_name, error)
            self.logger.info(f"The cookies for this account {account.user_id} are not valid {error}")  
            return (False, False)

                           
        if not account.cookie_start :
            # if we don't have a cookie_start we need to check if the account never been used or if it was used and completed 3 hours of rest
            if not cookie_real_end  or (current_date >= cookie_real_end + timedelta(hours=3)):
                self.logger.info(f"{account.user_id} has never been used or has stayed empty for three hours")
                # set the new start and expected cookie end and update the state of the account to available
                cookie_start = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                cookie_expected_end = cookie_start + timedelta(hours=3)
                try:
                    AccountAuthentification.objects.filter(user_id=account.user_id, media=media_name).update(
                                cookie=cookie, cookie_start=cookie_start,
                                cookie_expected_end=cookie_expected_end,
                                cookie_valid=True,
                                account_active=True,
                                account_valid=True
                            )
                except FieldDoesNotExist as e :
                    self.logger.error(f"Field Does not exist {e}")
                    pass
                return (True, False)
            else: 
                self.logger.info(f"{account.user_id} in rest ")
                return (False,False)

        dag_runs = AirflowDAGRUN.objects.filter(session=account)

        if cookie_expected_end >= current_date:
            # The account doesn't exceeded 3 hours of use
            # check if there are already a DAG_Runs session using this account
            # if no, we can use this account, otherwise no
            self.logger.info(f"{account.user_id} there is {len(dag_runs)} DAG_Runs using this session, ")
            return (len(dag_runs) < 1, False)
        else:  # The session has finished 3 hours
            if len(dag_runs) > 0 :
                # wait for crawl to complete
                self.logger.info(f"{account.user_id} is in use, so don't stop it and never use it")
            else:
                try :
                    hours = (current_date - cookie_real_end).seconds // 60 // 60
                    # if the difference between current date and cookie real end is greater than 3 hours we can use the account
                    if hours >= 3 and len(dag_runs) == 0 :
                        self.logger.info(f"{account.user_id} session completed 3 hours of rest")
                        cookie_start = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                        cookie_expected_end = cookie_start + timedelta(hours=3)
                        AccountAuthentification.objects.filter(user_id=account.user_id,media=media_name).update(
                                    cookie_start=cookie_start,
                                    cookie_expected_end=cookie_expected_end,
                                    cookie=cookie,
                                    cookie_real_end=cookie_real_end,
                                    cookie_valid=True,
                                    account_active=True,
                                    account_valid=True,
                                )
                        return (True, False)
                except: 
                    pass
                # delete old cookie_start and cookie_expected_end but keep the cookie value and set the account as non available
                try:
                    AccountAuthentification.objects.filter(user_id=account.user_id,media=media_name).update(
                                cookie_start=None,
                                cookie_expected_end=None,
                                cookie=cookie,
                                cookie_real_end=cookie_real_end,
                                cookie_valid=False,
                                account_active=False,
                                account_valid=False,
                            )

                except  AccountAuthentification.DoesNotExist:
                    self.logger.info("Account not found")
                except FieldDoesNotExist as e :
                    self.logger.error(f"Field Does not exist {e}")


                self.logger.info(f"{account.user_id} session has finished and it should stop for 3 hours")
                    
            return (False, False)


    @action(detail=False, methods=['POST'])
    def _cookie(self, media_name):
        username = media_name.data["user_id"]
        accounts = AccountAuthentification.objects.filter(user_id=username)
        for account in accounts:
            cookie = media_name.data.get("cookie", account.cookie)
            cookie_valid = media_name.data.get("cookie_valid", account.cookie_valid)
            account_valid = media_name.data.get("account_valid", account.account_valid)
            account_active = media_name.data.get("account_active", account.account_active)
            cookie_start = media_name.data.get("cookie_start", account.cookie_start)
            cookie_expected_end = media_name.data.get("cookie_expected_end", account.cookie_expected_end)
            cookie_real_end = media_name.data.get("cookie_real_end", account.cookie_real_end)  # noqa F841
            modified_at = media_name.data.get("modified_at", account.modified_at)
            AccountAuthentification.objects.filter(user_id=username).update(
                cookie=cookie,
                cookie_valid=cookie_valid,
                account_active=account_active,
                account_valid=account_valid,
                cookie_start=cookie_start,
                cookie_expected_end=cookie_expected_end,
                modified_at=modified_at
            )
        return Response(status=status.HTTP_200_OK, data={"status": "ok"})

    def check_format_email(self, email):
        """check if the input is email

        Args:
            email (_str_): input string

        Returns:
            _boolean_: if the input is an email
        """
        return re.fullmatch(self.regex, email)

    @action(detail=False, methods=['POST'])
    def add_account(self, media_name):
        """Add accounts (email, username, password, media)

        Args:
            media_name (_Django QuerySet_): twitter, instagram

        Returns:
            Response: Status code
        """
        media_name = media_name.data
        media, login, password, user_id, ip, cookie = media_name["media"], media_name["login"], media_name["password"], media_name["user_id"], media_name["ip"],  media_name["cookie"]  # noqa E501
        client_name = media_name["client_name"]
        strategy = Driver.objects.get(driver_name = media).strategy
        try :

            if strategy == "strategy1":
                new_account = AccountAuthentification(login=login,
                                                password=password,
                                                user_id=user_id,
                                                media=media,
                                                client_name=client_name,
                                                ip=ip)
            else :
                new_account = AccountAuthentification(login=login,
                                                password=password,
                                                user_id=user_id,
                                                media=media,
                                                ip=ip,
                                                client_name=client_name,
                                                cookie=cookie,
                                                cookie_valid=True,
                                                account_active=True,
                                                account_valid=True)
            new_account.save()
        except IntegrityError as e :
            self.logger.error(f'This account already exists {e}')
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={})
        
        output_serializer = AccountAuthentificationSerializer(new_account)
        return Response(status=status.HTTP_200_OK, data=output_serializer.data)

    @action(detail=False, methods=['POST'])
    def update_cookies(self, request):
        login = request.data["login"]  # which social media
        media_name = request.data["media"]  # which social media
        client_name = request.data.get("client_name","crawlserver")
        cookies = request.data['cookies']
        print(cookies)
        try:
            table = AccountAuthentification.objects.filter(login=login,media=media_name, client_name=client_name).update(cookie=cookies, cookie_valid=True, issue="")
        except ObjectDoesNotExist as e:
            self.logger.error(f"Object does not exist {e}")
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={"status": "Failed"})         
        except FieldDoesNotExist as e :
            self.logger.error(f"Field Does not exist {e}")
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={"status": "Failed"})
        self.logger.info(f'cookies successfuly updated for the account {login}')
        return Response(status=status.HTTP_200_OK, data={"status": "success"})

    @action(detail=False, methods=['POST'])
    def update_dagrun_account_mappings(self, data):
        """create or update DAG RUN in dauth

        Args:
            data (_dict_): which dag_run has been started? Using which account (session)?

        Returns:
            Response: Status code
        """
        data = data.data
        dag_run_id = data["dag_run_id"]
        user_id = data["user_id"]
        start = data["start"]
        end = data.get("end", "")
        try :
            session = AccountAuthentification.objects.get(user_id=user_id,media=data["media"])
        except ObjectDoesNotExist as e:
            self.logger.error(f"Object does not exist {e}")
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={"status": "Failed"})
            
        dag_run = AirflowDAGRUN.objects.filter(dag_run_id=dag_run_id)
        # create or update DAG RUN
        if not dag_run:
            AirflowDAGRUN(session=session, dag_run_id=dag_run_id, start=start).save()
        else:
            dag_run.update(end=end)
        return Response(status=status.HTTP_200_OK, data={"status": "Ok"})

    @action(detail=False, methods=['POST'])
    def get_session_by_dag_run_id(self, data):
        data = data.data
        dag_run_id = data["dag_run_id"]
        dag_run = AirflowDAGRUN.objects.filter(dag_run_id=dag_run_id)
        if not dag_run:
            return Response(status=status.HTTP_200_OK, data={"status": "There is no account with this DAG"})
        dag_run = dag_run[0]
        start = dag_run.start
        end = dag_run.end
        session = dag_run.session
        response = {
            "media": session.media,
            "login": session.login,
            "password": session.password,
            "user_id": session.user_id,
            "active": session.account_active,
            "start": start,
            "end": end
        }
        return Response(status=status.HTTP_200_OK, data=response)

    @action(detail=False, methods=['POST'])
    def update_consume(self, media_name):
        media_name = media_name.data
        login, modified_at, active = media_name["login"], media_name["modified_at"], media_name["active"]
        table = AccountAuthentification.objects.filter(login=login)
        table.update(modified_at=modified_at, active=active)
        output_serializer = AccountAuthentificationSerializer(table[0])
        return Response(status=status.HTTP_200_OK, data=output_serializer.data)

    @action(detail=False, methods=['POST'])
    def get_invalid_accounts(self, media_name):
        media_name = media_name.data["media"]
        accounts = AccountAuthentification.objects.filter(media=media_name, account_valid=False)
        all_accounts = [AccountAuthentificationSerializer(account).data for account in accounts]
        return Response(status=status.HTTP_200_OK, data=all_accounts)

    @action(detail=False, methods=['POST'])
    def get_account_in_using(self, media_name):
        media_name = media_name.data["media"]
        accounts = AccountAuthentification.objects.filter(media=media_name, account_active=True)
        all_accounts = [AccountAuthentificationSerializer(account).data for account in accounts]
        return Response(status=status.HTTP_200_OK, data=all_accounts)

    @action(detail=False, methods=['POST'])
    def get_cookie_by_account(self, username):
        user_id = username.data["user_id"]
        media = username.data["media"]
        accounts = AccountAuthentification.objects.filter(user_id=user_id,media=media)
        if not accounts:
            return Response(status=status.HTTP_200_OK, data=[])

        cookie = accounts[0].cookie if accounts[0].cookie else ""
        self.logger.info(f"cookie : {cookie}")
        return Response(status=status.HTTP_200_OK, data=cookie)

    @action(detail=False, methods=['POST'])
    def get_cookie_end_time_by_account(self, username):
        user_id = username.data["user_id"]
        media = username.data["media"]
        accounts = AccountAuthentification.objects.filter(user_id=user_id,media=media)
        if not accounts :
            return Response(status=status.HTTP_200_OK, data=[])
        cookie = accounts[0].cookie if accounts[0].cookie else ""
        cookie_real_end = accounts[0].cookie_real_end if accounts[0].cookie_real_end else ""
        response = (cookie, cookie_real_end)
        return Response(status=status.HTTP_200_OK, data=response)

    @action(detail=False, methods=['POST'])
    def get_all_exist_accounts(self, media_name):
        req = media_name.data["media"]
        accounts = AccountAuthentification.objects.filter(media=req)
        all_accounts = [AccountAuthentificationSerializer(account).data for account in accounts]
        return Response(status=status.HTTP_200_OK, data=all_accounts)

    @action(detail=False, methods=["DELETE"])
    def delete_one(self, user_id):
        user_id = user_id.data["user_id"]
        self.logger.info(f"user_id :  {user_id}")
        try:
            AccountAuthentification.objects.filter(user_id=user_id).delete()
        except Exception as ex:
            raise APIException(f"[EXCEPTION] when trying to delete account {id}, Message: {ex}")
        return Response(status=status.HTTP_200_OK, data={"status": "ok"})

    @action(detail=False, methods=["DELETE"])
    def delete_all(self):
        try:
            account = AccountAuthentification.objects.all()
            account.delete()
        except Exception as ex:
            raise APIException(f"[EXCEPTION] when trying to delete all accounts, Message: {ex}")
        return Response(status=status.HTTP_200_OK, data={"status": "ok"})

    @action(detail=False, methods=["DELETE"])
    def delete_dag_run(self, data):
        dag_run_id = data.data["dag_run_id"]
        self.logger.info("{dag_run_id}")
        try:
            account = AirflowDAGRUN.objects.filter(dag_run_id=dag_run_id)
            account.delete()
        except Exception as ex:
            raise APIException(f"[EXCEPTION] when trying to delete all accounts, Message: {ex}")
        return Response(status=status.HTTP_200_OK, data={"status": "ok"})
    
    @action(detail=False, methods=["POST"])
    def update_real_end(self, data):
        user_id = data.data["user_id"]
        self.logger.info("{user_id}")
        media = data.data["media"]
        self.logger.info("{media}")
        cookie_real_end = data.data["cookie_real_end"]
        self.logger.info("{cookie_real_end}")
        try:
            account_auth = AccountAuthentification.objects.get(user_id=user_id, media=media)
            account_auth.cookie_real_end = cookie_real_end  
            account_auth.save()
        except AccountAuthentification.DoesNotExist:
            raise APIException("[EXCEPTION] account id does not exist")
        except Exception as e:
            raise APIException(f"[EXCEPTION] there has been an error, Message: {e}")

        return Response({"status": "success"})  
            
    
    @action(detail=False, methods=["POST"])
    def set_cookie_error_message(self, data):
        print("data -----------------------",data)
        user_id = data.data["user_id"]
        media = data.data["media"]
        error = data.data["error"]
        try:
            account_auth = AccountAuthentification.objects.get(user_id=user_id, media=media)
            account_auth.cookie_valid = False
            account_auth.issue = error
            account_auth.save()
        except AccountAuthentification.DoesNotExist:
            raise APIException("[EXCEPTION] account id does not exist")
        except Exception as e:
            raise APIException(f"[EXCEPTION] there has been an error, Message: {e}")

        return Response({"status": "success"}) 

class DriverViewSet(GenericViewSet):

    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    logger = Logger(config).logger


    @action(detail=False, methods=['POST'])
    def add_driver(self, driver_info):
        """Add driver (driver_id, driver_name, password, media)

        Args:
            media_name (_Django QuerySet_): twitter, instagram

        Returns:
            Response: Status code
        """
        driver_info = driver_info.data
        driver_id, driver_name, class_name, import_package = driver_info["driver_id"], driver_info["driver_name"], driver_info["class_name"], driver_info["import_package"]
        new_driver  = Driver(driver_id=driver_id,
                                              driver_name=driver_name,
                                              class_name=class_name,
                                              import_package=import_package)

        new_driver.save()
        output_serializer = DriverSerializer(new_driver)
        return Response(status=status.HTTP_200_OK, data=output_serializer.data)
