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
    add_account_url = "http://54.36.177.119:8011/api/ip_accounts/add_account/"
    requests.post(
                    add_account_url,
                    auth=auth,
            data={"login":"user12@gmail.com","user_id":"user12","password":"user12[]{}","media": "instagram", 'ip':"http://54.36.177.119:4450",'cookie':json.dumps(user12),"client_name":"crawlserver"},

                    verify=False,
                ).json()



### **How to get the available accounts?**
To get the available accounts for a specific platform you should use the get_available_accounts api and specify the following parameters:

* media: name of the plateform
* nb_jobs: number of jobs to execute (number of accounts)
* client_name: name of the client (crawlserver, profile_search, signaling_system) 

Example : 

    import requests
    import json
    auth = ("user", "password")
    get_account_url = "http://54.36.177.119:8011/api/ip_accounts/get_available_accounts/"
    requests.post(
                    get_account_url,
                    auth=auth,
                    data={"media": "adoasis", "nb_jobs": 1,"client_name":"crawlserver"},
                    verify=False,
                ).json()


### **How to update cookies ?**
To update an account cookies you should use the update_cookies api and specify the following parameters:

* login: email address
* media: name of the plateform
* cookie: the new cookies
* client_name: name of the client (crawlserver, profile_search, signaling_system) 

Example : 

    import requests
    import json
    auth = ("user", "password")
    dauth_url = "http://54.36.177.119:8011/api/ip_accounts/update_cookies/"
    requests.post(
                    dauth_url,
                    auth=auth,
                    data={"login":"bond25k25@proton.me", "client_name":"profile_search", "media":"instagram","cookies":json.dumps(cookies)},
                    verify=False,
                ).json()



### **How to update a dag run account ?**
To update a dag run account you should use the update_dagrun_account_mappings api and specify the following parameters:

* dag_run_id: the dag run id in Airflow
* start: the start date of the dag run
* end: the expected end date of the dag run
* user_id: the user_id related to the used account
* media: the name of the plateform 

Example : 

    from datetime import datetime, timedelta
    execution_date = datetime.now()
    dag_run_start = execution_date
    dag_run_end_expected = execution_date + timedelta(hours=1)

    data= {
                "dag_run_id": 1,
                "start": dag_run_start,
                "user_id": user_id,
                "end": dag_run_end_expected,
                "media":"facebook"
            }
    dauth_url = "http://54.36.177.119:8011/api/ip_accounts/update_dagrun_account_mappings/"

    requests.post(
                    dauth_url,
                    auth=auth,
                    data=data,
                    verify=False,
                ).json()



### **How to delete a dag run?**
To delete a dag run from Airflow dagruns you need to use the API delete_dag_run

* dag_run_id: the dag run id in Airflow

Example : 

    dauth_url = "http://54.36.177.119:8011/api/ip_accounts/delete_dag_run/"

    requests.delete(
                    dauth_url,
                    auth=auth,
                    data={"dag_run_id": 1},
                    verify=False,
                ).json()



### **How to set the cookie error message?**
To set a cookie error message for a specific account you need to use the set_cookie_error_message API

* user_id: user_id of the account that has an error
* error: error message

Example : 

    dauth_url = "http://54.36.177.119:8011/api/ip_accounts/set_cookie_error_message/"
    requests.post(
                    dauth_url,
                    auth=auth,
                    data={"user_id":"100090320618957",  "error":"Login with cookies failed", "media":"facebook"},
                    verify=False,
                ).json()