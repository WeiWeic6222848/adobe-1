#ADOBE-Learn-1
demo video link: https://youtu.be/qb2G5kMTCVQ

This project is built for topcoder challenge Adobe-usecase-chanllenge.

The projects folder contains the folders
```
contracts
pdf_creator
static
templates
```
- contracts: folder containing all the user contracts
- pdf_creator: npm based commandline tool that utilizes the PDF Tool API.
- static: static server-side resources for the website
- templates: jinja2 templates for python flask

The root folder has:
```
app.py
Config.py
readme.md
requirements.txt
server.crt
server.key
temporaryAdminApp.py
User.py
```
- app.py: core python flask application.
- Config.py: configurable variables for app.py
- readme.md: this file
- requirements.txt: frozen requirement for python flask
- server.crt : https mock certificate, use a real one to deploy for real
- server.key : https mock certificate, use a real one to deploy for real
- temporaryAdminApp.py: This is a temporary server to retrieve the acces token of the website admin in order to create the agreements to sign.
- User.py: utility classes for the app.py

#requirements
(Developed in)
- python3 3.6.8
- nodejs 12.18.3
- npm 6.14.6

#Installation/setup
##Adobe Sign application
Login to your adobe sign account:
```
https://secure.eu2.adobesign.com/public/login#pageId::API_INFORMATION
```
Go to 
```
Account -> Adobe sign API -> Api applications
```
Create a new application, enable the scopes as follows:
```
user_read:self
user_write:self
user_login:self
agreement_read:account
agreement_write:account
agreement_send:account
```
set the redirect uri to where you want to deploy, here it is going to be localhost:
```
https://localhost:8080/registerOAuth/
```

##Website
make sure you have the newest version of nodejs and npm and python
```
https://nodejs.org/
https://www.npmjs.com/
https://www.python.org/downloads/
```

install the requirements via 
```
pip3 install -r requirements.txt
```

in the Config.py, change the Adobe-EmbedAPI-ID to your own.
```
Config = {
->  "AdobeClientID": "401ce579a51d4f8382bb714dd0483ef4",
}
```
keep in mind it's domain restricted.

Change the Application ID and secret, as well as the url where you're going to deploy your website
The ShardLocation can vary depending on the location of your adobe account, if you're in NA, use na1, otherwise use eu2.
```
    "AdobeSignID": "CBJCHBCAABAATuR_b-G58wkm..",
    "AdobeSignSecret": "LQ_AJinoPV45VnvNil9..",
    "DeploymentURL": "localhost:8080",
    "ShardLocation": "eu2",
```

UpdateInterval of annotations and contract editing can be configured in the config file
```
    "UpdateInterval" : 2000
```
It is in millisecond: 2000 -> check for update every 2 second.
Setting it too low might cause some unexpected behavior, 1 second is the minimum I recommend.

The admin refresh token and admin access token is an optional but strongly recommended configuration, 
as it skips the authentication procedure at the startup of the program.
I provided mine temporarily. you can change it to your own.

##pdf_creator

inside the folder `pdf_creator`:

overwrite the `dc-services-sdk-credentials.json` and `private.key` inside `pdf_creator` with your own.

then, execute the following command

```
npm install
npm link (optional)
```

#Execution
ensure the internet connection is stable and execute following in the project root folder

```
python3 app.py
```

First, if you didn't provide a accesstoken and refreshtoken, then a webbrowser page will be open requiring your account access.
I provided my own accesstoken and refreshtoken in this case, but if you remove them, then this procedure will happen.
After you gave access to the program (for your account). The website will be deployed under `localhost:8080` in a moment.


##Brief Introduction
- Admin-email cannot be used to sign as confirmed by copilot during learn chanllenge, so please put another email inside the user field.

- Login-page is clear to itself, provide username and password.

- Register page can be reached by clicking `create your account` link on the login page under the login button

- On the register page, if you have selected the role company, then you don't have to provide `Name` and it is invisible, if you selected the role candidate, then there will be an extra field `Name` which you need to fill in, as required.

- Once you login and choosed the role, you're send to their starting page, in this page all the contract which is related to you will be shown.

- contracts are sorted on the status, draft contract will be shown before finalized contracts etc..

- Company can press the "+" sign on index page to initialize new contract.

- If a contract is initialized with two or more candidates, at first, one contract will be created where the company user can edit the common part, then the user can press on send copy to create multiple copy for each candidate

- In the common editing state, the candidate wouldn't be able to see the contract, they can only see it after the company user decided to send copies.

- If a contract is initialized with one candidate, the send copy option will be skipped, the candidate will be able to view the editing process from the beginning

- seamless annotation update and pdf update is implemented

- tag is not implemented as the copilot said it is ok

- candidate and company can approve, sign, dissaprove contract after finalization

- annotations are removed after finalization

- cancel is not implemented as it is not mentioned anywhere in the forum nor requirement

- when signing, user is going to be taken to a new tab to sign.

- there can only be one person signing one document at the same time.

- a minimum responsible interface is implemented

##HIGHLIGHTS
- for both login and index page, the lighthouse score is above 90 consistently

- seamless annotation and pdf refreshing with configurable interval

- signed document can be viewed directly

- signed document will keep it's signature even if the other party disapproves and approves several times, as required


**PDF TOOL USAGE:**
- PDF tool is used to transform static html to pdf.
