import tempfile
import time
from datetime import datetime
from zipfile import ZipFile
from flask import *
from flask_login import LoginManager, login_user, login_required, \
    logout_user, current_user
from User import User, Contract, ContractStatus, UserRole, SignStatus, \
    DraftStatus
from Config import Config
import os
import os.path as path
import uuid
import subprocess
from werkzeug.utils import secure_filename
from shutil import rmtree, copy
import requests
import webbrowser
from bs4 import BeautifulSoup
import bleach

# region setup
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = Config["FlaskSecret"]

userDB = dict()  # database for all users
contractDB = dict()  # database for all contracts
companyContractDB = dict()  # database linking company to their contracts
companyUsers = dict()  # databse linking company to their users


# endregion

# region helperfunctions

def make_unique(string):
    """
    creates unique filenames for pdf files
    :param string: input filename
    :return: id+filename
    """
    ident = uuid.uuid4().__str__()[:8]
    return f"{ident}-{string}"


def setup():
    """
    checks if config is filled in good before starting the program.
    :return:
    """
    # required configurations
    configRequirement = ["AdobeClientID",
                         "AdobeSignID",
                         "AdobeSignSecret",
                         "DeploymentURL",
                         "ShardLocation",
                         "UpdateInterval",
                         "FlaskSecret"]
    for i in configRequirement:
        if i not in Config.keys():
            raise Exception(
                "please check that everything except admin token is filled in")

    Config["SignAPI"] = "https://api.{}.adobesign.com/".format(
        Config["ShardLocation"])
    Config["AdobeSignRedirectUri"] = "https://{}/registerOAuth/".format(
        Config["DeploymentURL"])
    Config["SignCompleteUri"] = "https://{}/signComplete/".format(
        Config["DeploymentURL"])


def getAvailableContractsUUID():
    """
    returns the available contracts for the current user
    :return: list of contracts that the user can edit/view
    """
    if current_user.role == 1:
        return companyContractDB.get(current_user.company, [])
    elif current_user.role == 2:
        return current_user.laborContracts
    return []


def getAvailableContracts():
    """
    returns the available contracts for the current user
    :return: list of contracts that the user can edit/view
    """
    if current_user.role == 1:
        return uuidListToContracts(
            companyContractDB.get(current_user.company, []))
    elif current_user.role == 2:
        return [i for i in
                uuidListToContracts(current_user.laborContracts) if
                i.draftStatus == 2]

    return []


def uuidListToContracts(uuids):
    """
    function that accepts lists of uuids and searches them in contractsDB
    :param uuids: list of uuids
    :return: list of contracts found
    """
    contracts = [contractDB.get(i, None) for i in uuids if
                 contractDB.get(i, None) is not None]
    return contracts


def getAccessTokenOfAdmin():
    """
    opens a browser window to require admin token
    :return: nothing, user need to operate on the webbrowser
    """
    url = "https://secure.{}.adobesign.com/public/" \
          "oauth?redirect_uri={}&response_type=code&client_id={}&" \
          "scope=user_read:self+user_write:self+user_login:self+" \
          "agreement_read:account+" \
          "agreement_write:account+agreement_send:account".format(
        Config["ShardLocation"],
        Config["AdobeSignRedirectUri"],
        Config["AdobeSignID"])
    webbrowser.open(url)


def requestNewAccessToken():
    """
    refresh the token of current user
    :return: nothing, it updates the current user.
    """
    HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
    api = Config['SignAPI']

    url = api + "oauth/refresh?" \
                "refresh_token={}&client_id={}" \
                "&client_secret={}" \
                "&redirect_uri={}&grant_type=refresh_token".format(
        Config['AdminRefreshToken'], Config["AdobeSignID"],
        Config["AdobeSignSecret"],
        Config["AdobeSignRedirectUri"])

    responds = requests.post(url, headers=HEADERS)
    if responds.status_code == 200:
        responds = responds.json()
        Config['AdminAccessToken'] = responds['access_token']


def uploadDocumentToSignAPI(file_path):
    """
    Uploads document to EchoSign and returns its ID
    :param file_path: Absolute or relative path to File
    """
    headers = {
        # Your access token or integration key here.
        'Authorization': 'Bearer ' + Config['AdminAccessToken'],
    }
    data = {
        'Mime-Type': 'application/pdf',
        'File-Name': path.split(file_path)[1]
    }
    url = Config['SignAPI'] + "api/rest/v6/transientDocuments"
    files = {'File': open(file_path, 'rb')}
    responds = requests.post(url, headers=headers, data=data,
                             files=files)
    return responds.json().get('transientDocumentId', None)


def createAgreement(transID):
    """
    Create a agreement for a transient doc
    :param transID: docid
    :return: agreementID
    """
    headers = {
        # Your access token or integration key here.
        'Authorization': 'Bearer ' + Config['AdminAccessToken'],
    }
    json = {
        'fileInfos': [{'transientDocumentId': transID}],
        'name': "Default Agreement",
        'participantSetsInfo': [
            {"memberInfos": [{"email": current_user.email}], "order": 1,
             "role": "SIGNER"}],
        "signatureType": "ESIGN",
        "state": "IN_PROCESS",
        "postSignOption": {
            "redirectDelay": 1,
            "redirectUrl": Config["SignCompleteUri"]
        }
    }
    url = Config['SignAPI'] + "api/rest/v6/agreements"
    responds = requests.post(url, headers=headers, json=json)
    return responds.json().get('id', None)


def getSignURL(agreementID):
    """
    retrieve the signing url for the user
    :param agreementID:
    :return: url
    """
    headers = {
        # Your access token or integration key here.
        'Authorization': 'Bearer ' + Config['AdminAccessToken'],
    }
    url = Config['SignAPI'] + \
          "/api/rest/v6/agreements/{}/signingUrls".format(agreementID)
    responds = requests.get(url, headers=headers)
    return responds.json().get(
        'signingUrlSetInfos', [
            {}])[0].get(
        "signingUrls", [
            {}])[0].get(
        "esignUrl", "")


def getAgreementStatus(agreementID):
    """
    check agreement status
    :param agreementID:
    :return: status
    """
    headers = {
        # Your access token or integration key here.
        'Authorization': 'Bearer ' + Config['AdminAccessToken'],
    }
    url = Config['SignAPI'] + \
          "/api/rest/v6/agreements/{}".format(agreementID)
    responds = requests.get(url, headers=headers)
    return responds.json().get('status', "")


def getSignedAgreement(agreementID):
    """
    get signed agreement
    :param agreementID:
    :return: agreement pdf
    """
    headers = {
        # Your access token or integration key here.
        'Authorization': 'Bearer ' + Config['AdminAccessToken'],
    }
    url = Config['SignAPI'] + \
          "/api/rest/v6/agreements/{}/combinedDocument/url".format(agreementID)
    responds = requests.get(url, headers=headers)
    url = responds.json().get('url', None)
    if url is not None:
        responds = requests.get(url)
        return responds.content
    return None


def uploadAndReturnAgreementAndSignURL(contractsname):
    """
    sequence of actions that uploads and returns agreement signing url
    :param contractsname:
    :return:
    """
    givenID = contractsname
    # upload document for signing
    # requestNewAccessToken() # if admin token is going to expire
    contracts = contractDB.get(givenID, None)
    if contracts is None:
        return "cannot find contract", 403

    contracts.lastSigning = datetime.now()
    contracts.signing = current_user.username

    contractsFilePath = contracts.fileLocation
    transID = uploadDocumentToSignAPI(contractsFilePath)
    if not transID:
        return "upload to signAPI failed", 403
    agreementID = createAgreement(transID)
    if not agreementID:
        return "agreement creation failed", 403
    time.sleep(2)
    # get signing url
    timecount = 0
    signURL = ""
    while signURL == "" and timecount < 5:
        time.sleep(1)
        timecount += 1
        signURL = getSignURL(agreementID)
    if not signURL:
        return "signurl creation failed", 403
    return {"url": signURL, "agreement": agreementID}, 200


# endregion

# region login_callbacks
@login_manager.user_loader
def load_user(userid):
    """
    login manager callback
    :param userid: user id
    :return: found user or nothing.
    """
    return userDB.get(userid, None)


@login_manager.unauthorized_handler
def unauthorized_callback():
    """
    login manager callback
    :return: if user not logged in, send them back to login
    """
    return redirect(url_for('login'))


# endregion

# region login_logout_register
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # if the current user is logged in,
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        # check formdata
        username = request.form.get('username', None)
        password = request.form.get('pass', None)
        if not (username and password):
            error = 'the informations given wasn\'t correct!'

        # check user
        user = load_user(username)
        if not user:
            error = 'user not found!'

        # if everything is fine
        if not error:
            if user.password == password:
                # Login and validate the user.
                # user should be an instance of your `User` class
                login_user(user)
                return redirect(url_for('index'))
            else:
                error = 'the given password is incorrect!'

    return render_template('login.html', error=error)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    # if the current user is logged in,
    if not current_user.is_anonymous:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        # check if everything is neatly filled
        username = request.form.get('username', None)
        name = request.form.get('name', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        company = request.form.get('company', None)
        role = request.form.get('role', None)
        role = int(role)  # convert to int if it's a string

        if not (name and email and password and username and company and role):
            error = 'the informations given wasn\'t correct!'
            return error, 400

        if userDB.get(username, None):
            error = 'That email has already been registered!'
            return error, 400

        # create user and add it into the db
        user = User(username, email, role, company, name, password)
        userDB[username] = user
        login_user(user)

        companylist = companyUsers.get(company, [])
        companylist.append(user)
        companyUsers[company] = companylist

        return redirect(url_for('index'))
    else:
        return render_template('register.html', error=error)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# endregion

@app.route('/signComplete/', methods=['GET'])
@login_required
def signComplete():
    return render_template('OAuth.html')


# region index
@app.route('/', methods=['GET'])
@login_required
def index():
    contracts = getAvailableContracts()
    candidates = companyUsers.get(current_user.company, [])
    candidates = [i for i in candidates if i.role == 2]
    return render_template(
        'index.html',
        contracts=contracts,
        OAuthRequest={
            "ID": Config["AdobeSignID"],
            "Redirect": Config["AdobeSignRedirectUri"],
            "Location": Config["ShardLocation"]},
        AdobeID=Config['AdobeClientID'],
        candidates=candidates,
        statusEncoding=["Unknown",
                        "Draft",
                        "Finalized",
                        "ApprovedByCandidate",
                        "ApprovedByCompany",
                        "Approved",
                        "Signed"],
        UpdateInterval=Config[
            'UpdateInterval'])


# endregion

# region newContract
def newContractCall(contractName, candidateList, current_user):
    # save the contract in the users current company folder
    userFolder = current_user.company

    # create dir if not exist
    dirname = path.join(".", "contracts", userFolder)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    # create unique filename
    contractName = secure_filename(contractName + ".pdf")
    fileName = make_unique(contractName)
    contractsFilename = path.join(dirname, fileName)

    # search in the userDB for given candidates
    candidateIdentifier = ""
    foundcandidates = set()
    for candidate in candidateList:
        candidateIdentifier += candidate
        user = userDB.get(candidate, None)
        if user is not None:
            foundcandidates.add(user)

    # pdf will be hashed based on the name of the contract.
    uuidIdentifier = contractsFilename

    # overwrite old contracts if exist
    if path.isfile(contractsFilename):
        os.remove(contractsFilename)

    # copy the empty pdf file to user folder
    copy(path.join('.', 'static', 'pdf', 'empty.pdf'),
         contractsFilename)

    if path.isfile(contractsFilename):
        # successfully created from upload
        # create contract object and store to databse
        contract = Contract(contractName, current_user.company,
                            foundcandidates, contractsFilename)
        contract.uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, uuidIdentifier))

        if len(foundcandidates) <= 1:
            contract.draftStatus = DraftStatus.IndividualDraft.value
            for candidate in foundcandidates:
                candidate.addContract(contract.uuid)

        contractDB[contract.uuid] = contract

        # store to company table
        new = companyContractDB.get(current_user.company, [])
        new.append(contract.uuid)
        companyContractDB[current_user.company] = new

        # store to current user
        current_user.addContract(contract.uuid)
    else:
        # upload failed
        error = 'transition to contracts failed!'
        return error, 400

    return "success", 200


@app.route('/newContract/', methods=['POST'])
@login_required
def newContract():
    if current_user.role != UserRole.Company.value:
        return "access denial", 403
    contractName = request.form.get('contractName', None)
    candidateList = request.form.getlist('candidateList[]')
    if not contractName or len(candidateList) == 0:
        return "wrong payload", 400

    # call the function
    return newContractCall(contractName, candidateList, current_user)


# endregion

# region delete
def deleteContractCall(contractuuid):
    # retrieve contract from DB
    contract = contractDB.get(contractuuid, None)

    # if contract cannot be found in db, it is already deleted.
    if contract is None:
        return "success", 200

    # delete from candidate list, current user, company db and contract DB
    for candidate in contract.related:
        candidate.deleteContract(contractuuid)
    current_user.deleteContract(contractuuid)
    contractDB[contractuuid] = None
    companyDB = companyContractDB.get(current_user.company, [])
    while contractuuid in companyDB:
        companyDB.remove(contractuuid)
    return "success", 200


@app.route('/delete/', methods=['POST'])
@login_required
def deleteContract():
    if current_user.role != UserRole.Company.value:
        return "access denial", 403
    contractuuid = request.form.get('contractuuid', None)
    if contractuuid not in getAvailableContractsUUID():
        return "contract not found in current users data", 403

    # call the function
    return deleteContractCall(contractuuid)


# endregion


# region non-sign operations

# status shift data
statusShiftDict = {
    (ContractStatus.Draft.value, UserRole.Company.value,
     'finalize'): ContractStatus.Finalized.value,
    (ContractStatus.Finalized.value, UserRole.Company.value,
     'approve'): ContractStatus.ApprovedByCompany.value,
    (ContractStatus.ApprovedByCandidate.value, UserRole.Company.value,
     'approve'): ContractStatus.Approved.value,
    (ContractStatus.Approved.value, UserRole.Company.value,
     'disapprove'): ContractStatus.ApprovedByCandidate.value,
    (ContractStatus.ApprovedByCompany.value, UserRole.Company.value,
     'disapprove'): ContractStatus.Finalized.value,

    (ContractStatus.Finalized.value, UserRole.Candidate.value,
     'approve'): ContractStatus.ApprovedByCandidate.value,
    (ContractStatus.ApprovedByCompany.value,
     UserRole.Candidate.value,
     'approve'): ContractStatus.Approved.value,
    (ContractStatus.Approved.value, UserRole.Candidate.value,
     'disapprove'): ContractStatus.ApprovedByCompany.value,
    (ContractStatus.ApprovedByCandidate.value, UserRole.Candidate.value,
     'disapprove'): ContractStatus.Finalized.value,
}


@app.route('/copy/', methods=['POST'])
@login_required
def copyContract():
    if current_user.role != UserRole.Company.value:
        return "access denialed", 403
    else:
        contractuuid = request.form.get("contractuuid", None)
        if not contractuuid:
            return "wrong payload", 400
        contract = contractDB[contractuuid]
        if not contract:
            return "cannot find contract", 400
        if contract.company != current_user.company:
            return "cannot edit contract of other company", 403
        # create copies for each candidate
        for candidate in contract.related:
            # create copy of original pdf
            title = secure_filename(contract.title)
            filename = make_unique(title)
            location = path.join(
                path.dirname(
                    contract.fileLocation),
                filename)
            copy(contract.fileLocation, location)

            # create new contract object inside databse
            newcontract = Contract(contract.title, contract.company,
                                   {candidate}, location)
            newcontract.signStatus = contract.signStatus
            newcontract.status = contract.status
            newcontract.draftStatus = DraftStatus.IndividualDraft.value
            newcontract.htmlData = contract.htmlData

            # assign new contract to company user and candidate
            newcontract.uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, location))
            contractDB[newcontract.uuid] = newcontract

            new = companyContractDB.get(current_user.company, [])
            new.append(newcontract.uuid)
            companyContractDB[current_user.company] = new
            current_user.addContract(newcontract.uuid)
            candidate.addContract(newcontract.uuid)

        # in the end, delete the current contract as it is splitted.
        deleteContractCall(contractuuid)
        return "success", 200


@app.route('/finalize/', methods=['POST'])
@login_required
def finalizeContract():
    if current_user.role != UserRole.Company.value:
        return "access denialed", 403
    else:
        contractuuid = request.form.get("contractuuid", None)
        if not contractuuid:
            return "wrong payload", 400
        contract = contractDB[contractuuid]
        if not contract:
            return "cannot find contract", 400
        if contract.company != current_user.company:
            return "cannot edit contract of other company", 403
        contract.status = statusShiftDict.get(
            (contract.status, current_user.role, 'finalize'), contract.status)
        return "success", 200


# signStatus dictionary
signStatusShiftDict = {
    (SignStatus.UnSigned.value,
     UserRole.Company.value): SignStatus.SignedByCompany.value,
    (SignStatus.SignedByCandidate.value,
     UserRole.Company.value): SignStatus.Signed.value,
    (SignStatus.UnSigned.value,
     UserRole.Candidate.value): SignStatus.SignedByCandidate.value,
    (SignStatus.SignedByCompany.value,
     UserRole.Candidate.value): SignStatus.Signed.value,
}


@app.route('/approve/', methods=['POST'])
@login_required
def approveContract():
    contractuuid = request.form.get('contractuuid', None)
    if contractuuid not in getAvailableContractsUUID():
        return "contract not found in current users data", 403
    contract = contractDB.get(contractuuid, None)
    if contract is None:
        return "cannot find contract", 400
    contract.status = statusShiftDict.get(
        (contract.status, current_user.role, 'approve'), contract.status)
    return "success", 200


@app.route('/disapprove/', methods=['POST'])
@login_required
def disapproveContract():
    contractuuid = request.form.get('contractuuid', None)
    if contractuuid not in getAvailableContractsUUID():
        return "contract not found in current users data", 403
    contract = contractDB.get(contractuuid, None)
    if contract is None:
        return "cannot find contract", 400
    contract.status = statusShiftDict.get(
        (contract.status, current_user.role, 'disapprove'), contract.status)
    return "success", 200


# endregion

# region sign operation
@app.route('/sign/', methods=['POST'])
@login_required
def signContract():
    givenID = request.form.get('contractuuid', None)
    contract = contractDB.get(givenID, None)
    if contract:
        if current_user.username != contract.signing:
            if (datetime.now() - contract.lastSigning).total_seconds() < 5:
                return "someone else is signing right now, please try again later!", 400
    else:
        return "contract not found", 400

    if request.form.get("agreement", None) is None:
        uuid = request.form.get('contractuuid', None)
        if uuid is None:
            return "wrong payload", 400

        return uploadAndReturnAgreementAndSignURL(uuid)
    else:

        # check contract existance
        givenID = request.form.get('contractuuid', None)

        contract = contractDB.get(givenID, None)
        if contract:
            contract.lastSigning = datetime.now()
            contract.signing = current_user.username
        else:
            return {'status': "not found"}, 400

        # check if agreement is signed
        agreementStatus = getAgreementStatus(
            request.form.get("agreement"))

        if agreementStatus == "SIGNED":
            # only submit if you're the one uploaded it
            signedContract = getSignedAgreement(
                request.form.get("agreement"))
            if givenID in getAvailableContractsUUID():
                if contract is not None and signedContract is not None:
                    file = open(contract.fileLocation, 'wb')
                    file.write(signedContract)
                    contract.signStatus = signStatusShiftDict.get(
                        (contract.signStatus, current_user.role),
                        contract.signStatus)
                    if contract.signStatus == SignStatus.Signed.value:
                        contract.status = ContractStatus.Signed.value
        return {'status': agreementStatus}, 200


# endregion

# region view
@app.route('/view/', methods=['POST', 'GET'])
@login_required
def viewContract():
    if request.method == 'POST':
        givenID = request.form.get('contractuuid', None)
    else:
        givenID = request.args.get('contractuuid', None)
    for uuid in companyContractDB.get(current_user.company, []):
        if uuid == givenID:
            contract = contractDB.get(uuid, None)
            if contract is not None:
                contractpath = contract.fileLocation
                if path.isfile(contractpath):
                    if request.method == "GET":
                        return send_file(
                            contractpath,
                            attachment_filename=contract.title,
                            as_attachment=True,
                            mimetype='application/pdf')
                    elif request.method == "POST":
                        annotations = contract.annotations
                        return {
                            'data': annotations,
                            'title': contract.title,
                            'html': contract.htmlData,
                            'modified': contract.modified,
                            'status': contract.status}
    return 'cannot found file!', 403


# endregion

# region annotation
@app.route('/annotation/', methods=['POST'])
@login_required
def UpdateAnnotation():
    # check annotation exists
    annotation = request.get_json()
    if annotation:
        # upload the annotation on the pdf object
        source = annotation.get("belongsToPDF", None)

        error = 'corrupted annotation data!'
        if not source:
            return error, 400
        creator = annotation.get("creator", None)
        if not creator:
            return error, 400
        creatorname = creator.get("name", None)
        if not creatorname:
            return error, 400

        # check current user is the same as creator
        if current_user.username != creatorname:
            error = 'different user'
            return error, 403

        # add/delete the annotation to the contract
        contract = contractDB.get(source, None)
        if annotation.get('deleting', False):
            contract.removeAnnotation(annotation)
            return {"result": "deleted", "contract": contract.title,
                    "annotation": annotation,
                    "username": current_user.username}
        else:
            annotation['creator']['id'] = "computer"
            contract.addAnnotation(annotation)
            return {"result": "added", "contract": contract.title,
                    "annotation": annotation,
                    "username": current_user.username}
    else:
        error = 'Incomeplete request information'
        return error, 400


# endregion

@app.route('/edit/', methods=['POST'])
@login_required
def editContract():
    if current_user.role != UserRole.Company.value:
        return "access denial", 403
    title = request.form.get('contractName', None)
    content = request.form.get('content', None)
    contractuuid = request.form.get('contractuuid', None)

    if not title or not content or not contractuuid:
        error = 'wrong payload'
        return error, 400

    # validate html
    if not bool(BeautifulSoup(content, "html.parser").find()):
        return "Given content is not a valid html!", 400

    # sanitize html to prevent xss attack
    content = bleach.clean(content, tags=['h1', 'h2', 'h3',
                                          'p', 'u', 'ul', 'em',
                                          'i', 'li', 'ol', 'strong',
                                          'ul', 'a', 'br'])

    if contractuuid not in getAvailableContractsUUID():
        return 'access denial', 400
    contract = contractDB.get(contractuuid, None)
    if contract is None:
        return 'cannot find contract', 400

    temporaryFile = tempfile.NamedTemporaryFile('w', delete=False)

    # write html code, center the image captured
    writeString = "{}".format(content)
    temporaryFile.write(writeString)
    temporaryFile.close()

    zipFile = tempfile.NamedTemporaryFile('w', suffix='.zip', delete=False)
    zipFile.close()
    # zip the temporary file
    zipObj = ZipFile(zipFile.name, 'w')
    zipObj.write(temporaryFile.name, arcname="index.html")
    zipObj.close()

    outputpath = contract.fileLocation

    # call subprocess
    args = ['node', path.join('.', 'pdf_creator', 'bin', 'pdf_creator.js'),
            zipFile.name, outputpath]
    process = subprocess.Popen(args)
    process.wait()

    # delete temporary files
    try:
        os.remove(temporaryFile.name)
        os.remove(zipFile.name)
    except BaseException:
        pass

    contract.title = title
    contract.htmlData = content
    contract.modified = datetime.now()
    return 'success', 200


# region testSetup
def testSetup():
    userDB["qwe"] = User("qwe", "c62222848@gmail.com", 1,
                         "testcomp", "weiwei", "123")
    userDB["qwee"] = User("qwee", "c62222848@gmail.com", 2, "testcomp",
                          "weiwei", "123")
    userDB["asd"] = User("asd", "c6152848@gmail.com", 2, "testcomp",
                         "hei hei", "123")
    companyUsers["testcomp"] = {
        userDB["qwe"],
        userDB["qwee"],
        userDB["asd"]}
    # newContractCall("testContract", [userDB["qwee"].username],
    #                 userDB["qwe"])
    newContractCall("testContract2", ["qwee", "asd"],
                    userDB["qwe"])

    contract = next(iter(contractDB.values()))
    contract.status = 5


@app.before_first_request
def before_first_request():
    testSetup()


# endregion

if __name__ == '__main__':
    setup()
    context = ('server.crt', 'server.key')  # certificate and key files
    rmtree('contracts', ignore_errors=True)  # remove previous contract
    if (Config["AdminRefreshToken"] == ""):
        # start a process to request the token of a admin email, this email is
        # going to be used to create agreement
        getAccessTokenOfAdmin()
        from temporaryAdminApp import tempapp

        tempapp.run(host='localhost', port=8080, ssl_context=context)
    else:
        requestNewAccessToken()
    app.run(host='localhost', port=8080, ssl_context=context)
