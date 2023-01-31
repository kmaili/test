from datetime import datetime
from celery import shared_task
import json
import pytz
from importlib import import_module
import time
from dauthenticator.utils import config
from dauthenticator.utils.utils import *
from dauthenticator.utils.logging import Logger

logger = Logger(config).logger


def driver_update_cookies(media_name:str, cookies, remote_url):
    """update cookies """
    driver_class = {
        "facebook": load_class("facebook_driver.drivers.FacebookDriver"),
        "instagram": load_class("instaDriver.drivers.InstaDriver"),
        # "twitter": load_class("twitter_driver.drivers.TwitterDriver"),
        # "quora": load_class("quora_driver.drivers.QuoraDriver")
    }


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
    logger.info(f"Number of accounts to update their cookies {len(all_accounts)}")
    for account in all_accounts:
        media = account.media
        cookies = json.loads(account.cookie)
        print(cookies)
        remote_url = account.ip

        if cookies and get_node_available(logger,remote_url) > 0 :

            new_cookies = driver_update_cookies(media_name=media,cookies=cookies,remote_url=remote_url)

            AccountAuthentification.objects.filter(user_id=account.user_id).update(
                        cookie=json.dumps(new_cookies),modified_at=datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                    )

            logger.info(f"cookies update for {account.user_id} ")
            
