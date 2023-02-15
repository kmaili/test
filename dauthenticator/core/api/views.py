from datetime import timedelta, datetime
import re
import json
import pytz
import requests
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import APIException
from dauthenticator.core.models import AccountAuthentification, AirflowDAGRUN
from dauthenticator.core.api.serializers import AccountAuthentificationSerializer, AccountAuthSerializer
# from twitter_driver.drivers import TwitterDriver
# from instaDriver.drivers import InstaDriver
from importlib import import_module



# 3. Améliorer le code ici, une fonction générale pour tous les drivers login
# 4. discuter avec Sun pour les commentaires twitter crawl

# I. obtenir les drivers en login
# II. créer un système pour que pendant 3 heures les drivers (sessions) soient vifs


def load_class(dotpath: str):
    """load function in module.  function is right-most segment"""
    module_, func = dotpath.rsplit(".", maxsplit=1)
    print(module_)
    m = import_module(module_)
    return getattr(m, func)

def driver_login(accounts, media_name):

    cookies = []
    drivers = []
    driver_class = {
        "twitter": load_class("twitter_driver.drivers.TwitterDriver"),
        "instagram": load_class("instaDriver.drivers.InstaDriver"),
        "quora": load_class("quora_driver.drivers.QuoraDriver"),
        "adoasis": load_class("adoasis_driver.drivers.AdoasisDriver")
    }
    for account in accounts:
        account_info = account["account"]
        username = account_info["user_id"]
        login = account_info["login"]
        password = account_info["password"]
        remote_url = account_info["ip"]
        driver = driver_class[media_name](
            driver_language='en-EN',
            credentials_login=login,
            credentials_password=password,
            credentials_username=username,
            remote_url=remote_url,
            headless = False
        )
        if driver.login():
            cookies.append(driver.get_login_cookies())
            driver.close()
        else:
            cookies.append("Login Failed")
            driver.close()
        drivers.append(driver)
    return cookies, drivers

def check_cookies(cookies,media_name):
    expiry=0
    cookies = json.loads(cookies)

    dict_name = {
        "instagram": 'ds_user_id',
        "facebook": 'fr'
    }
    name = dict_name[media_name]
    for dic in cookies:
       
        if dic.get('name') == name:
            expiry = dic.get('expiry')
            print(expiry,"------")
            break
    check = datetime.fromtimestamp(expiry).strftime("%Y/%d/%m") > datetime.now().strftime("%Y/%d/%m")
    return check

class AccountAuthentificationViewSet(GenericViewSet):

    serializer_class = AccountAuthentificationSerializer
    queryset = AccountAuthentification.objects.all()
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # login_func = {
    #     "twitter": lambda accounts: twitter_login(accounts),
    #     "instagram": lambda accounts: ins_login(accounts)
    # }
    media_index = {
        "1": "twitter",
        "2": "instagram",
        "3": "facebook",
        "4": "quora",
        "5": "adoasis",
        1: "twitter",
        2: "instagram",
        3: "facebook",
        4: "quora",
        5: "adoasis",
        "twitter": "twitter",
        "instagram": "instagram",
        "facebook": "facebook",
        "quora": "quora",
        "adoasis": "adoasis"
    }

    @action(detail=False, methods=['POST'])
    def get_available_accounts(self, request):
        """Get all valid accounts and update info for all accounts

        Args:
            data (_dict_): accounts for which media and number of accounts needed

        Returns:
            _Dict_: accounts or session available
        """
        media_name = request.data["media"]  # which social media
        nb_jobs = int(request.data["nb_jobs"])
        current_date = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
        # find all accounts of this media
        all_accounts = AccountAuthentification.objects.filter(media=media_name).order_by("cookie", "cookie_real_end")
        #print("all account \n",len(all_accounts),'______')
        all_accounts_situations = []
        for account in all_accounts:
            # 1. sort all_accounts in order no cookie and with cookie
            # 2. If there is an account or session available, break
            available, should_login = self.is_account_available(account, current_date,media_name)
            all_accounts_situations.append({"account": {"user_id": account.user_id, "login": account.login, "password": account.password, "ip": account.ip, "media": self.media_index[account.media], "cookie": account.cookie or "", "cookie_start": account.cookie_start.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_start else "", "cookie_expected_end": account.cookie_expected_end.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_expected_end else "", "cookie_real_end": account.cookie_real_end.strftime("%Y-%m-%d %H:%M:%S") if account.cookie_real_end else "1980-01-01 00:00:00.954774+00:00", "modified_at": account.modified_at}, "available": available, "should_login": should_login})  # noqa E501
        accounts_available = list(filter(lambda account: account["available"], all_accounts_situations))
        # if there are no accounts available, just tell the Scheduler that there are no accounts
        print('\n account available = ',len(accounts_available))

        if not accounts_available:
            print("There is no account available")
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

        print("\n ----- inside the function get_cookies_by_login -----\n")
        accounts_to_login = list(filter(lambda account: account["should_login"], accounts_available))
        print("accounts_to_login = ", accounts_to_login)

        accounts_in_using_once = list(filter(lambda account: not account["should_login"], accounts_available))
#        print("accounts_in_using_once = ",accounts_in_using_once)
        accounts_selected = []
        if accounts_to_login:
            # We prefer those who haven't login
            # select that used earliest
            accounts_to_login.sort(key=lambda account: account["account"]["cookie_real_end"])
            # Not login all accounts without use
            if len(accounts_to_login) >= nb_jobs:
                accounts_to_login = accounts_to_login[:nb_jobs]
            # login according to media
            print("\n-------------- login according to media ------------\n")
            #print("accounts_to_login = ", accounts_to_login)
            cookies, drivers = driver_login(accounts_to_login, media_name)
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
                    AccountAuthentification.objects.filter(user_id=user_id).update(
                        cookie=cookie, cookie_start=cookie_start,
                        cookie_expected_end=cookie_expected_end,
                        cookie_valid=True,
                        account_active=True,
                        account_valid=True
                    )
                else:
                    user_id = accounts_to_login[i]["account"]["user_id"]
                    AccountAuthentification.objects.filter(user_id=user_id).update(
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
        # accounts_selected.sort(key=lambda account: len(AirflowDAGRUN.objects.filter(session=AccountAuthentification.objects.get(user_id=account["account"]["user_id"]))))  # noqa E501
        accounts_selected.sort(key=lambda account: len(AirflowDAGRUN.objects.filter(session=AccountAuthentification.objects.get(user_id=account["account"]["user_id"]))))  # noqa E501
        for i in range(len(accounts_selected)):
            #print('\n -----------------', accounts_selected[i]["account"]["cookie"],'------------\n')
            accounts_selected[i]["account"]["cookie"] = json.loads(accounts_selected[i]["account"]["cookie"])
        return accounts_selected

    def get_node_available(self, remote_url: str) -> int:
        """
            Get number of selenium grid node available
    
            Parameters:
                remote_url (str): Selenium grid remote url
    
            Returns:
                no_of_nodes_available (int): Number of nodes available in selenium grid  # noqa E501
    
        """
        try:
            res = self.get_selenium_status(remote_url)
            ready = res["value"]["ready"]
            if ready:
                nodes = res["value"]["nodes"]
                nodes_available = [
                    node for node in nodes if not node["slots"][0]["session"]
                ]
                no_of_nodes_available = len(nodes_available)
                # print("Number of nodes available, ", no_of_nodes_available)
                return no_of_nodes_available
            else:
                print("Selenium hub is not ready")
                return 0
        except Exception as e:
            print(f"['ERROR'] : selenium hub error => {e}")
            return 0

    def get_selenium_status(self, remote_url: str):
        url = f"{remote_url}/wd/hub/status"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.request("GET", url, headers=headers)
            return json.loads(response.text)
        except Exception as e:
            print(f"['ERROR'] : selenium hub error => {e}")
            return

    def is_account_available(self, account, current_date, media_name):
        """To verify is this account available now

        Args:
            account (_AccountAuthentification_): the Object of AccountAuthentification
            current_date (_Datetime_): the date which Airflow Scanner Check Dauthenticator

        Returns:
            _Tuple(Boolean, Boolean)_: (Is this account available, Should have a login or not)
        """
        # If cookie is None, this account has no session
        print("-------------------")
        cookie = account.cookie
        cookie_real_end = account.cookie_real_end
        cookie_start = account.cookie_start
        cookie_expected_end = account.cookie_expected_end
        user_id = account.ip  # noqa F841
        login = account.login  # noqa F841
        password = account.password  # noqa F841
        ip = account.ip
        # if selenium cluster is never available
        nb_nodes = self.get_node_available(ip)

        if nb_nodes == 0:
            print(f"There is no node selenium available in cluster {ip}")
            return (False, False)
        
        last_use_date = cookie_real_end
        if media_name in ["facebook","instagram"]:
            if not cookie: 
                print(f"There is no cookies for this account {login}")
                return  (False, False)

            #cookies expiré
            elif not check_cookies(cookie,media_name):
                AccountAuthentification.objects.filter(user_id=account.user_id).update(
                    cookie="",
                    cookie_real_end=None,
                    cookie_valid=False,
                    account_active=False,
                    account_valid=False,
                )
                print(f"The cookies for this account {account.user_id} are expired")  # noqa E501
                return (False, False)
                
            # If this account is never used
            if not last_use_date:
                # this account has never been used, so login
                print(f"{account.user_id} has never been used or has stayed empty for three hours, so login if necessary")  # noqa E501
                return (True, False)
            

            next_use_date = last_use_date + timedelta(hours=3)
            return (current_date >= next_use_date, False)

        # If the field cookie is empty in table
        if not cookie and media_name not in ["facebook","instagram"]:

            # If this account is never used
            if not last_use_date:
                # this account has never been used, so login
                print(f"{account.user_id} has never been used or has stayed empty for three hours, so login if necessary")  # noqa E501
                return (True, True)
            next_use_date = last_use_date + timedelta(hours=3)
            return (current_date >= next_use_date, True)
        

        # check if this session is runing
        cookie_end_date = cookie_expected_end
        dag_runs = AirflowDAGRUN.objects.filter(session=account)
        if cookie_end_date >= current_date:
            # The session is in 3 hours
            # check if there are already two DAG_Runs using this session
            # if no, we can use this session, otherwise no
            print(f"{account.user_id} there are {len(dag_runs)} DAG_Runs using this session, ")
            return (len(dag_runs) < 3, False)
        else:  # The session has finished 3 hours
            hours = (current_date - cookie_end_date).seconds // 60 // 60
            if len(dag_runs) > 1 and hours < 1.5:
                # wait for crawl terminated
                print(f"{account.user_id} is in using, so don't stop it and never use it")
            else:
            #     if cookie_real_end > cookie_start and  current_date >= cookie_real_end + timedelta(hours=3) :
            #         return (True, False)
                    
                session_real_end = datetime.now()
                # update table AccountAuthentification
                new_cookies = ""
                if media_name  in ["facebook","instagram"]:
                    new_cookies = cookie
                AccountAuthentification.objects.filter(user_id=account.user_id).update(
                    cookie=new_cookies,
                    cookie_real_end=session_real_end,
                    cookie_valid=False,
                    account_active=False,
                    account_valid=False,
                )
                print(f"{account.user_id} session has finished and it should stop for 3 hours")
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
        if media not in  ['facebook','instagram']:
            new_account = AccountAuthentification(login=login,
                                              password=password,
                                              user_id=user_id,
                                              media=media,
                                              ip=ip)
        else :
            new_account = AccountAuthentification(login=login,
                                              password=password,
                                              user_id=user_id,
                                              media=media,
                                              ip=ip,
                                              cookie=cookie,
                                              cookie_valid=True,
                                              account_active=True,
                                              account_valid=True)
        new_account.save()
        output_serializer = AccountAuthentificationSerializer(new_account)
        return Response(status=status.HTTP_200_OK, data=output_serializer.data)

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
        session = AccountAuthentification.objects.get(user_id=user_id)
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
        accounts = AccountAuthentification.objects.filter(user_id=user_id)
        if not accounts:
            Response(status=status.HTTP_200_OK, data={})
        cookie = accounts[0].cookie if accounts[0].cookie else ""
        print("cookie : ", cookie)
        return Response(status=status.HTTP_200_OK, data=cookie)

    @action(detail=False, methods=['POST'])
    def get_cookie_end_time_by_account(self, username):
        user_id = username.data["user_id"]
        accounts = AccountAuthentification.objects.filter(user_id=user_id)
        response = (accounts[0].cookie, accounts[0].cookie_end)
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
        print("user_id : ", user_id)
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
        print(dag_run_id)
        try:
            account = AirflowDAGRUN.objects.filter(dag_run_id=dag_run_id)
            account.delete()
        except Exception as ex:
            raise APIException(f"[EXCEPTION] when trying to delete all accounts, Message: {ex}")
        return Response(status=status.HTTP_200_OK, data={"status": "ok"})
