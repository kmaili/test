from importlib import import_module
from datetime import timedelta, datetime
import requests
import json
from requests.exceptions import ConnectionError

def load_class(dotpath: str):
    """load function in module.  function is right-most segment"""
    module_, func = dotpath.rsplit(".", maxsplit=1)
    m = import_module(module_)
    return getattr(m, func)

from typing import Tuple

# def check_cookies(cookies:str,media_name:str)->bool:
#     """check cookies expiration date"""
#     expiry=0
#     cookies = json.loads(cookies)

#     dict_name = {
#         "instagram": 'ds_user_id',
#         "facebook": 'fr'
#     }
#     name = dict_name[media_name]
#     for dic in cookies:
       
#         if dic.get('name') == name:
#             expiry = dic.get('expiry')
#             break
#     check = datetime.fromtimestamp(expiry).strftime("%Y/%d/%m") > datetime.now().strftime("%Y/%d/%m")
    

#     return check

def check_cookies(cookies:str)->Tuple:
    """check cookies expiration date"""
    expiry=0
    error = "cookies are expired"
    try:
        cookies = json.loads(cookies)
    except json.decoder.JSONDecodeError as error :
        return False, str(error)

    for dic in cookies:
       
        expiry = dic.get('expiry')
        if expiry and not (datetime.fromtimestamp(expiry).strftime("%Y/%m/%d") > datetime.now().strftime("%Y/%m/%d")) :
            print(expiry)
            return False, error

    return True, ""

def get_node_available(logger, remote_url: str) -> int:
    """
            Get number of selenium grid node available
    
            Parameters:
                remote_url (str): Selenium grid remote url
    
            Returns:
                no_of_nodes_available (int): Number of nodes available in selenium grid  # noqa E501
    
    """
    
    res = get_selenium_status(logger,remote_url)
    if res:
        try:
            ready = res["value"]["ready"]
            if ready:
                nodes = res["value"]["nodes"]
                nodes_available = [
                    node for node in nodes if not node["slots"][0]["session"]
                    ]
                no_of_nodes_available = len(nodes_available)
                logger.info(f"Number of nodes available: {no_of_nodes_available}" )
                return no_of_nodes_available
            else:
                logger.info(f"Selenium hub is not ready")

        except Exception as e:
            logger.error(f"['ERROR'] : selenium hub error => {e}")
    return 0

def get_selenium_status(logger, remote_url: str):
    url = f"{remote_url}/wd/hub/status"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("GET", url, headers=headers)
        return json.loads(response.text)
    except ConnectionError as e:
        logger.error(f" New Connection Error => {e}")
        return {}