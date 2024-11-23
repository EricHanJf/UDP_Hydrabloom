# from flask_sqlalchemy import SQLAlchemy
import json
import time
import os
import pathlib
import requests
from flask import (
    Flask,
    session,
    abort,
    redirect,
    request,
    render_template,
    flash,
    url_for,
)
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from .config import config
from . import my_db
from .my_db import Plant

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
    print(session)
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


# admin_dashboard page Route
@app.route("/admin_dashboard", endpoint="admin_dashboard")
@login_is_required
def admin_dashboard():
    try:
        user_id = session.get("google_id")
        user_name = session.get("name")
        if not user_id or not user_name:
            return redirect(url_for("signin"))

        online_users = my_db.get_all_logged_in_users()
        google_admin_id = config.get("GOOGLE_ADMIN_ID")

        return render_template(
            "admin_dashboard.html",
            user_id=user_id,
            google_admin_id=google_admin_id,
            online_users=online_users,
        )
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        return "An error occurred while loading the dashboard.", 500


# UPLOAD_FOLDER = "static/uploads/plants"
# ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# # app.config = config.get("UPLOAD_FOLDER")


# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# @app.route("/addPlant", methods=["GET","POST"], endpoint="addPlant")
@app.route("/addPlant", methods=["GET", "POST"], endpoint="addPlant")
@login_is_required
def addPlant():
    if request.method == "POST":
        try:
            # Retrieve form data
            plantname = request.form.get("plantname")
            waterrequirement = request.form.get("waterrequirement")
            planttype = request.form.get("planttype")
            plantlocation = request.form.get("plantlocation")
            gmail = request.form.get("gmail")

            # Validate required fields
            if (
                not plantname
                or not waterrequirement
                or not planttype
                or not plantlocation
                or not gmail
            ):
                flash("All fields are required.", "danger")
                return redirect(url_for("index"))

            # Create a new plant record (without plantpicture)
            new_plant = Plant(
                plantname=plantname,
                waterrequirement=waterrequirement,
                planttype=planttype,
                plantlocation=plantlocation,
                user_id=session["google_id"],
                gmail=gmail,
            )

            # Save the plant to the database
            db.session.add(new_plant)
            db.session.commit()

            flash("Plant added successfully!", "success")
            return redirect(url_for("plants"))

        except Exception as e:
            # Log the error and notify the user
            app.logger.error(f"Error adding plant: {e}")
            flash("An error occurred while adding the plant.", "danger")
            return redirect(url_for("index"))
    else:
        # Render the add plant page on GET request
        return render_template("addPlant.html")
        # return render_template("protected_area.html")


# Plants page route
@app.route("/plants", endpoint="plants")
@login_is_required
def plants():
    try:
        user_id = session["google_id"]
        google_admin_id = config.get("GOOGLE_ADMIN_ID")
        # Fetch all plants from the database
        if user_id == google_admin_id:
            # Admin can see all plants
            all_plants = Plant.query.all()
        else:
            # Normal users can only see their own plants
            all_plants = Plant.query.filter_by(user_id=user_id).all()

        return render_template("plants.html", plants=all_plants)

    except Exception as e:
        print(f"Error fetching plants: {e}")
        return "An error occurred while fetching the plants.", 500


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
