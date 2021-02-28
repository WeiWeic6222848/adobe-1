from flask import *
from Config import Config
import requests

tempapp = Flask(__name__)
tempapp.secret_key = Config["FlaskSecret"]


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@tempapp.route("/registerOAuth/", methods=["GET"])
def registerAdmin():
    HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get('code')
    api = request.args.get('api_access_point')
    url = api + \
        "oauth/token?code={}&client_id={}&client_secret=" \
        "{}&redirect_uri={}&grant_type=authorization_code".format(
            code, Config["AdobeSignID"], Config["AdobeSignSecret"],
            Config["AdobeSignRedirectUri"])
    Config["SignAPI"] = api

    responds = requests.post(url, headers=HEADERS)
    if responds.status_code == 200:
        responds = responds.json()
        Config['AdminAccessToken'] = responds['access_token']
        Config['AdminRefreshToken'] = responds['refresh_token']
    shutdown_server()
    return 'Admin Acesstoken received, ' \
           'server shutting down.. real server starting up..'
