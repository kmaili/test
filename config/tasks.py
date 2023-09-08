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
import logging as logger

def driver_update_cookies(media_name:str, cookies, remote_url,driver_info):
    """update cookies """

    try :
        driver = load_class(driver_info.import_package)(
                            driver_language='en-EN',
                            remote_url=remote_url,
                            headless = False,
                            cookie=cookies)
        if (type ( driver._driver ) == bool) :
            return None
        
    except Exception as e :
        logger.error("Driver class instanciation Failed")

    time.sleep(4)
    try :
        time.sleep(3)
        new_cookies = driver.get_login_cookies()
        driver.close()
        return new_cookies
    except Exception as e :
        logger.error("get login cookies from driver failed")
    
    return cookies


@shared_task(bind=True)
def drivers_cookies_update(self, *args):

    from dauthenticator.core.models import AccountAuthentification, Driver
    liste_drivers = []
    drivers2 = Driver.objects.filter(strategy="strategy2") 
    for d in drivers2 :
        liste_drivers.append(d.driver_name)


    all_accounts = AccountAuthentification.objects.filter(media__in =liste_drivers).order_by("cookie", "cookie_real_end")
    logger.info(f"Number of accounts to update their cookies {len(all_accounts)}")
    for account in all_accounts:
        media = account.media
        if account.cookie :
            cookies = json.loads(account.cookie)
            driver_info = Driver.objects.get(driver_name=media) 

            # print(cookies)
            remote_url = account.ip

            if cookies and get_node_available(logger,remote_url) > 0 and check_cookies(json.dumps(cookies)):
                logger.info(f'media {account.media}')

                new_cookies = driver_update_cookies(media_name=media,cookies=cookies,remote_url=remote_url,driver_info=driver_info)
                new_cookies = json.dumps(new_cookies) if new_cookies else ""
                AccountAuthentification.objects.filter(user_id=account.user_id).update(
                            cookie=new_cookies,modified_at=datetime.now().astimezone(pytz.timezone('Europe/Paris'))
                        )

                logger.info(f"cookies update for {account.user_id} ")