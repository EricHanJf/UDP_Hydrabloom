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
    jsonify,
)
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from .config import config
from . import my_db, pb
from .my_db import Plant, dht22Data, tsl2561Data, SoilMoistureData
from werkzeug.utils import secure_filename

# for sensor database.
from datetime import datetime, timedelta


db = my_db.db
app = Flask(__name__)
app.secret_key = config.get("APP_SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = config.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

#

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


@app.route("/protected_area", endpoint="protected_area")
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


@app.route("/vase", methods=["GET"], endpoint="vase")
@login_is_required
def vase():
    plantpicture = request.args.get("plantpicture")
    plantname = request.args.get("plantname")
    selected_date = request.args.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    # Fetch data for the selected date
    start_time = datetime.strptime(selected_date, "%Y-%m-%d")
    end_time = start_time + timedelta(days=1)

    dht_data = dht22Data.query.filter(
        dht22Data.timestamp.between(start_time, end_time)
    ).all()
    tsl_data = tsl2561Data.query.filter(
        tsl2561Data.timestamp.between(start_time, end_time)
    ).all()
    soil_moisture_data = SoilMoistureData.query.filter(
        SoilMoistureData.timestamp.between(start_time, end_time)
    ).all()

    # Combine data by timestamp
    combined_data = {}
    for record in dht_data:
        key = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        combined_data[key] = {
            "timestamp": record.timestamp,
            "temperature": record.temperature,
            "humidity": record.humidity,
            "lux": None,
            "soil_moisture": None,
        }
    for record in tsl_data:
        key = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if key in combined_data:
            combined_data[key]["lux"] = record.lux
        else:
            combined_data[key] = {
                "timestamp": record.timestamp,
                "temperature": None,
                "humidity": None,
                "lux": record.lux,
                "soil_moisture": None,
            }
    for record in soil_moisture_data:
        key = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if key in combined_data:
            combined_data[key]["soil_moisture"] = record.soil_moisture
        else:
            combined_data[key] = {
                "timestamp": record.timestamp,
                "temperature": None,
                "humidity": None,
                "lux": None,
                "soil_moisture": record.soil_moisture,
            }

    # Sort combined data by timestamp
    combined_data = sorted(combined_data.values(), key=lambda x: x["timestamp"])

    return render_template(
        "vase.html",
        plantpicture=plantpicture,
        plantname=plantname,
        combined_data=combined_data,
        selected_date=selected_date,
    )


# pass google_admin_id Globally Using context_processor
@app.context_processor
def inject_admin_id():
    google_admin_id = config.get("GOOGLE_ADMIN_ID")
    return {"google_admin_id": google_admin_id}


# admin_dashboard page Route
@app.route("/admin_dashboard", endpoint="admin_dashboard")
@login_is_required
def admin_dashboard():
    try:
        user_id = session["google_id"]
        user_name = session.get("name")
        google_admin_id = config.get("GOOGLE_ADMIN_ID")

        if not user_id or not user_name or user_id != google_admin_id:
            return redirect(url_for("signin"))

        online_users = my_db.get_all_logged_in_users()
        # google_admin_id = config.get("GOOGLE_ADMIN_ID")

        return render_template(
            "admin_dashboard.html",
            user_id=user_id,
            google_admin_id=google_admin_id,
            online_users=online_users,
        )
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        return "An error occurred while loading the dashboard.", 500


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


UPLOAD_FOLDER = "var/www/FlaskApp/FlaskApp/static/uploads/plants"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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
            plantpicture = request.files.get("plantpicture")  # Get the uploaded file

            # Validate required fields
            if not all([plantname, waterrequirement, planttype, plantlocation, gmail]):
                flash("All fields are required.", "danger")
                return redirect(url_for("addPlant"))

            plantpicture_path = None
            # Process image file if provided
            if plantpicture and allowed_file(plantpicture.filename):
                filename = secure_filename(plantpicture.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                plantpicture.save(filepath)  # Save the file
                plantpicture_path = f"uploads/plants/{filename}"  # Store relative path

            # Create a new plant record
            new_plant = Plant(
                plantname=plantname,
                waterrequirement=waterrequirement,
                planttype=planttype,
                plantlocation=plantlocation,
                user_id=session["google_id"],
                gmail=gmail,
                plantpicture=plantpicture_path,  # Add the picture path
            )

            # Save the plant to the database
            db.session.add(new_plant)
            db.session.commit()

            flash("Plant added successfully!", "success")
            return redirect(url_for("plants"))

        except Exception as e:
            app.logger.error(f"Error adding plant: {e}")
            flash("An error occurred while adding the plant.", "danger")
            return redirect(url_for("addPlant"))
    else:
        return render_template("addPlant.html")


# Plants page route
@app.route("/plants", methods=["GET"], endpoint="plants")
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


@app.route(
    "/delete_user/<string:user_id>", methods=["GET", "POST"], endpoint="delete_user"
)
@login_is_required
def delete_user(user_id):
    try:
        if request.method == "GET":
            return f"Delete user: {user_id}"
        # Verify if the current user is an admin (based on some admin logic, e.g., a token or ID check)
        if session["user_id"] != config.get("ADMIN_USER_ID"):
            flash("You do not have permission to delete users.", "danger")
            return redirect(url_for("admin_dashboard"))

        # Fetch the user from the database
        user = my_db.User.query.filter_by(user_id=user_id).first()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        flash("User deleted successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    except Exception as e:
        app.logger.error(f"Error deleting user: {e}")
        flash("An error occurred while deleting the user.", "danger")
        return redirect(url_for("admin_dashboard"))


@app.route("/api/store_dht22_data", methods=["POST"])
def store_dht22_data():
    data = request.get_json()

    if "temperature" not in data or "humidity" not in data:
        return jsonify({"error": "Missing temperature or humidity data"}), 400

    # Store DHT22 data
    new_data = dht22Data(temperature=data["temperature"], humidity=data["humidity"])

    db.session.add(new_data)
    db.session.commit()

    return jsonify({"message": "DHT22 data stored successfully"}), 201


@app.route("/api/store_tsl2561_data", methods=["POST"])
def store_tsl2561_data():
    data = request.get_json()

    if "lux" not in data:
        return jsonify({"error": "Missing lux data"}), 400

    # Store TSL2561 data
    new_data = tsl2561Data(lux=data["lux"])

    db.session.add(new_data)
    db.session.commit()

    return jsonify({"message": "TSL2561 data stored successfully"}), 201


@app.route("/api/store_soil_moisture_data", methods=["POST"])
def store_soil_moisture_data():
    data = request.get_json()

    # Check if the soil moisture data is present
    if "soilMoisture" not in data:
        return jsonify({"error": "Missing soil moisture data"}), 400
    try:
        # Store Soil Moisture data
        new_data = SoilMoistureData(  # Ensure this matches your SQLAlchemy model name
            soil_moisture=data["soilMoisture"]  # Matches the key sent from the frontend
        )

        db.session.add(new_data)
        db.session.commit()

        return jsonify({"message": "Soil moisture data stored successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to store data: {str(e)}"}), 500


@app.route("/grant-<user_id>-<read>-<write>", methods=["POST"])
def grant_access(user_id, read, write):
    if session.get("google_id"):
        if session["google_id"] == config.get("GOOGLE_ADMIN_ID"):
            print(f"Admin granting {user_id}-{read}-{write}")
            my_db.add_user_permission(user_id, read, write)
            if read == "true" and write == "true":
                token = pb.grant_read_and_write_access(user_id)
                my_db.add_token(user_id, token)
                access_response = {
                    "token": token,
                    "cipher_key": pb.cipher_key,
                    "uuid": user_id,
                }
                return json.dumps(access_response)
            elif read == True and write == True:
                token = pb.grant_read_and_write_access(user_id)
                my_db.add_token(user_id, token)
                return token
            elif read == "true" and write == "false":
                token = pb.grant_read_access(user_id)
                my_db.add_token(user_id, token)
                access_response = {
                    "token": token,
                    "cipher_key": pb.cipher_key,
                    "uuid": user_id,
                }
                return json.dumps(access_response)
            elif read == "false" and write == "true":
                token = pb.grant_write_access(user_id)
                my_db.add_token(user_id, token)
                access_response = {
                    "token": token,
                    "cipher_key": pb.cipher_key,
                    "uuid": user_id,
                }
                return json.dumps(access_response)
            else:
                # Remove any existing token from the database
                my_db.delete_revoked_token(user_id)
                access_response = {
                    "token": 1234,
                    "cipher_key": pb.cipher_key,
                    "uuid": user_id,
                }
                return json.dumps(access_response)
        else:
            print(f"Non admin attempting to grant privileges {user_id}-{read}-{write}")
            my_db.add_user_permission(user_id, read, write)
            token = my_db.get_token(user_id)
            if token is not None:
                timestamp, ttl, user_id, read, write = pb.parse_token(token)
                current_time = time.time
                if (timestamp + (ttl * 60)) - current_time > 0:
                    print("Token is still valid")
                    access_response = {
                        "token": token,
                        "cipher_key": pb.cipher_key,
                        "uuid": user_id,
                    }
                    return json.dumps(access_response)
                else:
                    print("Token refresh needed")
                    if read and write:
                        token = pb.grant_read_write_access(user_id)
                        my_db.add_token(user_id, token)
                        access_response = {
                            "token": token,
                            "cipher_key": pb.cipher_key,
                            "uuid": user_id,
                        }
                        return json.dumps(access_response)
                    elif read:
                        token = pb.grant_read_access(user_id)
                        my_db.add_token(user_id, token)
                        access_response = {
                            "token": token,
                            "cipher_key": pb.cipher_key,
                            "uuid": user_id,
                        }
                        return json.dumps(access_response)
                    elif read:
                        token = pb.gran_write_access(user_id)
                        my_db.add_token(user_id, token)
                        access_response = {
                            "token": token,
                            "cipher_key": pb.cipher_key,
                            "uuid": user_id,
                        }
                        return json.dumps(access_response)
                    else:
                        access_response = {
                            "token": 123,
                            "cipher_key": pb.cipher_key,
                            "uuid": user_id,
                        }
                        return json.dumps(access_response)


@app.route("/get_user_token", methods=["POST"])
def get_user_token():
    user_id = session["google_id"]
    token = my_db.get_token(user_id)

    if token is not None:
        # Token found, return it
        token_response = {"token": token, "cipher_key": pb.cipher_key, "uuid": user_id}
    else:
        # Token not found, generate a new one
        token = pb.generate_new_token(user_id)  # Generate a new token
        if token:
            # Store the new token in the database
            my_db.store_token(user_id, token)
            # Return the new token with cipher key and user ID
            token_response = {
                "token": token,
                "cipher_key": pb.cipher_key,
                "uuid": user_id,
            }
        else:
            # Handle the error if token generation fails
            token_response = {"error": "Failed to generate token"}

    return token_response


def get_or_refresh_token(token):
    timestamp, ttl, uuid, read, write = pb.parse_token(token)
    current_time = time.time()
    if (timestamp + (ttl * 60)) - current_time > 0:
        return token
    else:
        # The token has expired
        return grant_access(uuid, read, write)


if __name__ == "__main__":
    app.run()
