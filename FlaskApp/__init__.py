# from flask_sqlalchemy import SQLAlchemy
import json
import time
import os
import pathlib
import requests
from flask import Flask, session, abort, redirect, request, render_template, flash
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from .config import config
from . import my_db


db = my_db.db
app = Flask(__name__)
app.secret_key = config.get("APP_SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = config.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# google oauth id
GOOGLE_CLIENT_ID = config.get("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, ".client_secrets.json"
)

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="https://www.hydrabloom.online/callback",
)

# alive = 0
# data = {}


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


# callback function
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    # request_session = request.session()
    request_session = requests.Session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
    )

    session["google_id"] = id_info.get("sub")
    print(session["google_id"])
    session["name"] = id_info.get("name")
    print(session["name"])
    return redirect("/protected_area")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/protected_area")
@login_is_required
def protected_area():
    my_db.add_user_and_login(session["name"], session["google_id"])
    # return render_template("protected_area.html")
    return render_template(
        "protected_area.html",
        user_id=session["google_id"],
        google_admin_id=config.get("GOOGLE_ADMIN_ID"),
        online_users=my_db.get_all_logged_in_users(),
    )


# register page Route
@app.route("/register")
def register():
    return render_template("register.html")


# About page Route
@app.route("/about")
def about():
    return render_template("about.html")


# Signin page Route
@app.route("/signin")
def signin():
    return render_template("signin.html")


# buzzer sensor code down there
def motion_detection():
    data["alarm"] = False
    while True:
        if GPIO.input(PIR_pin):
            print("Motion detected")
            beep(4)
            data["motion"] = 1
        else:
            data["motion"] = 0
        if data["alarm"]:
            beep(2)
        time.sleep(1)


@app.route("/keep_alive")
def keep_alive():
    global alive, data
    alive += 1
    keep_alive_count = str(alive)
    data["keep_alive"] = keep_alive_count
    parsed_json = json.dumps(data)
    return str(parsed_json)


@app.route("/status=<name>-<action>", methods=["POST"])
def event(name, action):
    global data
    if name == "buzzer":
        if action == "on":
            data["alarm"] = True
        elif action == "off":
            data["alarm"] = False
    return str("ok")


if __name__ == "__main__":
    app.run()
