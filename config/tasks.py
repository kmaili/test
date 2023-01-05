from datetime import datetime
from celery import shared_task

import pytz
from facebook_driver.drivers import FacebookDriver


@shared_task(bind=True)
def account_state_update(self, *args):
    from dauthenticator.core.models import AccountAuthentification, AirflowDAGRUN
    current_date = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
    all_accounts = AccountAuthentification.objects.all().order_by("cookie", "cookie_real_end")
    print("all account \n",len(all_accounts),'______')
    for account in all_accounts:
        # 1. sort all_accounts in order no cookie and with cookie
        # 2. If there is an account or session available, break
        cookie_expected_end = account.cookie_expected_end
        cookie = account.cookie

        if cookie:
            dag_runs = AirflowDAGRUN.objects.filter(session=account)
            if cookie_expected_end >= current_date:
                # The session is in 3 hours
                # check if there are already two DAG_Runs using this session
                # if no, we can use this session, otherwise no
                print(f"{account.user_id} there are {len(dag_runs)} DAG_Runs using this session, ")

            else:  # The session has finished 3 hours
                hours = (current_date - cookie_expected_end).seconds // 60 // 60
                if len(dag_runs) > 1 and hours < 1.5:
                    # wait for crawl terminated
                    print(f"{account.user_id} is in using, so don't stop it and never use it")
                else:
                    session_real_end = datetime.now()
                    # update table AccountAuthentification
                    AccountAuthentification.objects.filter(user_id=account.user_id).update(
                        cookie="",
                        cookie_real_end=session_real_end,
                        cookie_valid=False,
                        account_active=False,
                        account_valid=False,
                    )
                    print(f"{account.user_id} session has finished and it should stop for 3 hours")



@shared_task(bind=True)
def facebook_cookies_update(self, *args):
    from dauthenticator.core.models import AccountAuthentification, AirflowDAGRUN
    current_date = datetime.now().astimezone(pytz.timezone('Europe/Paris'))
    all_accounts = AccountAuthentification.objects.get().order_by("cookie", "cookie_real_end")
    print("all account \n",len(all_accounts),'______')
    for account in all_accounts:
        cookie_expected_end = account.cookie_expected_end
        cookie = account.cookie
        remote_url = account.ip

        if cookie:
            driver = FacebookDriver(
                        driver_language='en-EN',
                        remote_url=remote_url,
                        headless = False,
                        cookie=cookie
                    )

            new_cookies = driver.get_login_cookies()
            
            AccountAuthentification.objects.filter(user_id=account.user_id).update(
                        cookie=new_cookies,
                    )
            driver.close()
            print(f"cookies update for {account.user_id} ")
            print("cookie",cookie)