#ADOBE-Learn-1
demo video link: https://youtu.be/qb2G5kMTCVQ

This project is built for topcoder challenge Adobe-learning-chanllenge.

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

in the Config.py, change the Adobe-ID to your own.
```
Config = {
->  "AdobeClientID": "401ce579a51d4f8382bb714dd0483ef4",
}
```
keep in mind it's domain restricted.

Change the Application ID and secret, as well as the 'localhost' part in redirect uri to your own
The ShardLocation can vary depending on the location of your adobe account, if you're in NA, use na1, otherwise use eu2.
```
    "AdobeSignID": "CBJCHBCAABAATuR_b-G58wkm..",
    "AdobeSignSecret": "LQ_AJinoPV45VnvNil9..",
    "AdobeSignRedirectUri": "https://localhost:8080/registerOAuth/",
    "ShardLocation": "eu2",
```

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
After you gave access to the program (for your account). The website will be deployed under `localhost:8080` in a moment.


##Brief Introduction
- Login-page is clear to itself, provide username and email.

- Admin-email cannot be used to sign as confirmed by copilot, so please put another email inside the user field.

- Once you login and choosed the role, you're send to their starting page, for student it's draft page, for professor it's submitted page.

- Student can press the "+" sign on draft page to upload new doc or docx to transform to pdf.

- each pdf will have a view content button, student will have a edit, submit and delete for draft pdf and professor have approve and reject for submitted pdf.

- pdf editing is not implemented due to time restriction.

- When a user try to submit/approve/reject, the program will upload and create agreement for user to sign, after the agreement is signed the website will update.

- Professor can give reason when approving/rejecting.

**PDF TOOL USAGE:**
- PDF tool is used to transform static html to pdf.
