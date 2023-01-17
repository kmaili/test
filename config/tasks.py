from datetime import datetime
from celery import shared_task
import json
import pytz
from facebook_driver.drivers import FacebookDriver
from instaDriver.drivers import InstaDriver
from importlib import import_module
import time

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


def load_class(dotpath: str):
    """load function in module.  function is right-most segment"""
    module_, func = dotpath.rsplit(".", maxsplit=1)
    print(module_)
    m = import_module(module_)
    return getattr(m, func)

def driver_update_cookies(media_name, cookies, remote_url):

    driver_class = {
        "facebook": load_class("facebook_driver.drivers.FacebookDriver"),
        "instagram": load_class("instaDriver.drivers.InstaDriver"),
        # "twitter": load_class("twitter_driver.drivers.TwitterDriver"),
        # "quora": load_class("quora_driver.drivers.QuoraDriver")
    }
    print('___________________________________')

    driver = driver_class[media_name](
                        driver_language='en-EN',
                        remote_url=remote_url,
                        headless = False,
                        cookie=cookies)
    time.sleep(4)

    new_cookies = driver.get_login_cookies()
    driver.close()
    return new_cookies

@shared_task(bind=True)
def facebook_cookies_update(self, *args):

    from dauthenticator.core.models import AccountAuthentification
    all_accounts = AccountAuthentification.objects.filter(media__in =["facebook","instagram"]).order_by("cookie", "cookie_real_end")
    print("all account \n",len(all_accounts))
    for account in all_accounts:
        media = account.media
        #print("media name =-------", media)
        cookie_expected_end = account.cookie_expected_end
        cookies = json.loads(account.cookie)
        print(cookies)
        remote_url = account.ip

        if cookies:
            new_cookies = driver_update_cookies(media_name=media,cookies=cookies,remote_url=remote_url)

            AccountAuthentification.objects.filter(user_id=account.user_id).update(
                        cookie=json.dumps(new_cookies),modified_at=datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                    )

            print(f"cookies update for {account.user_id} ")
            print("cookie",new_cookies)
