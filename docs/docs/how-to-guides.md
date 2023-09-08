This part of the project documentation focuses on a
**problem-oriented** approach. You'll tackle common
tasks that you might have, with the help of the code
provided in this project.

### **How To add an account ?**
To add an account you should use the api add_account and specify the necessary parameters:

* login: email address
* user_id: id or pseudo of the profile
* password: password of the account
* media: name of the plateform
* ip: selenium hub url
* cookie: if the plateform belongs to startegy1 pass an empty string otherwise pass the dictionary of cookies
* client_name: name of the client (crawlserver, profile_search, signaling_system) 

Example : 

    import requests
    import json
    auth = ("user", "password")
    add_account_url = "http://141.94.246.237:8011/api/ip_accounts/add_account/"
    requests.post(
                    add_account_url,
                    auth=auth,
            data={"login":"user12@gmail.com","user_id":"user12","password":"user12[]{}","media": "instagram", 'ip':"http://54.36.177.119:4450",'cookie':json.dumps(user12),"client_name":"crawlserver"},

                    verify=False,
                ).json()



### **How to get the available account?**
To get the available accounts for a specific platform you should use the get_available_accounts api and specify the following parameters:

* media: name of the plateform
* nb_jobs: number of jobs to execute (number of accounts)
* client_name: name of the client (crawlserver, profile_search, signaling_system) 

Example : 

    import requests
    import json
    auth = ("user", "password")
    get_account_url = "http://141.94.246.237:8011/api/ip_accounts/get_available_accounts/"
    requests.post(
                    get_account_url,
                    auth=auth,
                    data={"media": "adoasis", "nb_jobs": 1,"client_name":"crawlserver"},
                    verify=False,
                ).json()


### **How to update cookies ?**
To update an account cookies you should use the api update_cookies api and specify the following parameters:

* login: email address
* media: name of the plateform
* cookie: the new cookies
* client_name: name of the client (crawlserver, profile_search, signaling_system) 

Example : 

    import requests
    import json
    auth = ("user", "password")
    dauth_url = "http://141.94.246.237:8011/api/ip_accounts/update_cookies/"
    requests.post(
                    dauth_url,
                    auth=auth,
                    data={"login":"bond25k25@proton.me", "client_name":"profile_search", "media":"instagram","cookies":json.dumps(cookies)},
                    verify=False,
                ).json()
