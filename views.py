from app import app

from models.article import add_article

from flask import make_response
from flask import request
from flask import abort
from flask import jsonify
from flask import render_template

import jwt
from jwt import DecodeError
from jwt import ExpiredSignature
from functools import wraps

import os
import json
import logging
from datetime import datetime
from datetime import timedelta

logger = logging.getLogger("views")



def json_dumper(obj):
    """
    if the obj has a to_dict() function we've implemented, uses it to get dict.
    from http://stackoverflow.com/a/28174796
    """
    try:
        return obj.to_dict()
    except AttributeError:
        return obj.__dict__


def json_resp_from_thing(thing):
    hide_keys = request.args.get("hide", "").split(",")
    if hide_keys is not None:
        for key_to_hide in hide_keys:
            try:
                del thing[key_to_hide]
            except KeyError:
                pass

    json_str = json.dumps(thing, sort_keys=True, default=json_dumper, indent=4)

    if request.path.endswith(".json") and (os.getenv("FLASK_DEBUG", False) == "True"):
        logger.info(u"rendering output through debug_api.html template")
        resp = make_response(render_template(
            'debug_api.html',
            data=json_str))
        resp.mimetype = "text/html"
    else:
        resp = make_response(json_str, 200)
        resp.mimetype = "application/json"
    return resp


def abort_json(status_code, msg):
    body_dict = {
        "HTTP_status_code": status_code,
        "message": msg,
        "error": True
    }
    resp_string = json.dumps(body_dict, sort_keys=True, indent=4)
    resp = make_response(resp_string, status_code)
    resp.mimetype = "application/json"
    abort(resp)


@app.route("/<path:page>")  # from http://stackoverflow.com/a/14023930/226013
@app.route("/")
def index_view(path="index", page=""):
    return render_template('index.html')










###########################################################################
# from satellizer.
# move to another file later
# this is copied from early GitHub-login version of Depsy. It's here:
# https://github.com/Impactstory/depsy/blob/ed80c0cb945a280e39089822c9b3cefd45f24274/views.py
###########################################################################

def create_token(profile):
    return create_token_from_username(profile.username)

def create_token_from_username(username):  # j added this one.
    payload = {
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=14)
    }
    key = app.config['SECRET_KEY']
    logger.info('creating a token using this username: ' + username)
    token = jwt.encode(payload, key)
    return token.decode('unicode_escape')


def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.config['SECRET_KEY'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get('Authorization'):
            response = jsonify(message='Missing authorization header')
            response.status_code = 401
            return response

        try:
            payload = parse_token(request)
        except DecodeError:
            response = jsonify(message='Token is invalid')
            response.status_code = 401
            return response
        except ExpiredSignature:
            response = jsonify(message='Token has expired')
            response.status_code = 401
            return response

        g.current_user_username = payload['sub']

        return f(*args, **kwargs)

    return decorated_function











###########################################################################
# API
###########################################################################
@app.route("/api")
def api_test():
    return jsonify({"resp": "Impactstory: The Next Generation."})


@app.route("/api/doi/<path:doi>")
@app.route("/api/doi/<path:doi>.json")
def get_doi(doi):

    resp = {"doi": doi}
    my_article = add_article(doi)
    resp["plos_metrics"] = my_article.plos_metrics()
    resp["crossref_deets"] = my_article.crossref_deets()
    resp["altmetric_metrics"] = my_article.altmetric_metrics()
        
    return jsonify(resp)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)





