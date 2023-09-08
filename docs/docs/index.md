**Dauthenticator:** A Django project for account management and authentication


**Main objectives:**

* Add, update and delete accounts 
* Manage rest time for each account
* Manage number of simultanious sessions of each account

**Project Context:**

For most social networks, if for each crawl we pass the login page (every 5 minutes), the internal social network server will think that we are a robot, either it gives us a Captcha, or it blocks our account, or it records our activities and gives us request limits. <br>


Problems on the Twitter & Instagram & Tiktok account that we have already encountered so far (in general):

1. Twitter login with Captcha
2. Twitter login page changes its CSS style and even page structure <br>
    I. Ask to enter the email and password separately, in two different pages <br>
    II. Ask for username (which is after @ for the account) instead of email and it's decided randomly <br>
    III. Request phone number <br>
3. If we use PROXY, the different IP address will also decrease the health of the account, Twitter and Instagram will record the ip address and the device where you first registered, if you change your ip address frequently to crawler (log in), your account will be on alert. Thus, it is better to crawl in the same ip address that you registered (at least in the same ip address that you pass login)
4. Instagram redirect you to the account verification page asking for your mobile number.
5. Instagram has access limit for comments if we abuse with an account (Errors when load comments), the page only loads a comment or it does not display anything except the image in the publication of the post. (It is 80%+ that the number of scroll-view exceeds the threshold)
6. Captcha for Tiktok even if you have already logged in
7. Impossible to login if you go directly to the tiktok login page

These problems hinder us a lot for unlimited crawls, since our crawl must pass every 5 minutes to crawl in real time.
Thanks to the cookie, we can launch our drivers on the basis of selenium without going through the login page, so it will help us to protect the account, however, it becomes essential to have an account management system, i.e. the storage of account information for various social networks, their cookie, their usage status, who is using this cookie (account), is the cookie enabled or not ?. This system is called Dauthenticator.

