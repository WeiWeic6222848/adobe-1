# unknown = 0
# student = 1
# teacher = 2
from datetime import datetime
from enum import Enum


class ContractStatus(Enum):
    Unknown = 0
    Draft = 1
    Finalized = 2
    ApprovedByCandidate = 3
    ApprovedByCompany = 4
    Approved = 5
    Signed = 6
    # Draft, Finalized, Approved by the candidate, Approved by the company,
    # Approved and Signed.


class DraftStatus(Enum):
    Unknown = 0
    InitialDraft = 1
    IndividualDraft = 2


class SignStatus(Enum):
    UnSigned = 0
    SignedByCandidate = 1
    SignedByCompany = 2
    Signed = 3


class UserRole(Enum):
    Unknown = 0
    Company = 1
    Candidate = 2


class Contract:
    """
    PDF classes
    """
    title = ""
    company = ""
    status = ContractStatus.Unknown.value
    signStatus = SignStatus.UnSigned.value
    uuid = ""  # uuid of object
    related = set()
    annotations = dict()  # dictionary linking annotation id to annotations
    fileLocation = ""
    draftStatus = DraftStatus.Unknown.value
    htmlData = ""
    modified = datetime.now()
    lastSigning = datetime.now()
    signing = None

    def __init__(self, title, company, related, fileLocation):
        self.uuid = ""
        self.title = title
        self.status = ContractStatus.Draft.value
        self.company = company
        self.related = related
        self.annotations = dict()
        self.fileLocation = fileLocation
        self.draftStatus = DraftStatus.InitialDraft.value
        self.htmlData = ""
        self.modified = datetime.now()
        self.lastSigning = datetime.now()
        self.signing = None

    def todict(self):
        """
        helper function to create dictionary from object
        :return: dictionary of self, excluding annotations
        """
        mydict = dict()
        mydict["uuid"] = self.uuid
        return mydict

    def addAnnotation(self, annotation):
        """
        add annotation
        :param annotation: annotation as dict
        :return:
        """
        annotation['creator']['id'] = 'computer'
        self.annotations[annotation["id"]] = annotation

    def removeAnnotation(self, annotation):
        """
        remove annotation
        :param annotation: annotation as dict
        :return:
        """
        self.annotations.pop(annotation["id"], None)


class User:
    name = ""
    username = ""
    email = ""
    company = ""
    role = UserRole.Unknown.value  # 1=company,2=candidate
    password = ""
    laborContracts = set()

    # callback for flask-login
    auth = False
    is_anonymous = False
    is_active = True

    def __init__(self, username="", email="", roles=UserRole.Unknown.value,
                 company="", name="", password=""):
        if (roles == UserRole.Candidate.value) and name == "":
            raise Exception("A candidate user must have a valid name")
        self.name = name
        self.username = username
        self.email = email
        self.company = company
        self.role = roles
        self.password = password
        self.auth = False
        self.is_anonymous = False
        self.is_active = True
        self.laborContracts = set()

    # callback for flask login
    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.auth

    def addContract(self, contractuuid):
        self.laborContracts.add(contractuuid)

    def deleteContract(self, contractuuid):
        self.laborContracts.discard(contractuuid)
