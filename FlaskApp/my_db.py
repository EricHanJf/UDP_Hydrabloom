from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    user_id = db.Column(db.String(21))
    # token = db.Column(db.String(255))
    token = db.Column(db.Text)
    login = db.Column(db.Integer)
    read_access = db.Column(db.Integer)
    write_access = db.Column(db.Integer)

    def __init__(self, name, user_id, token, login, read_access, write_access):
        self.name = name
        self.user_id = user_id
        self.token = token
        self.login = login
        self.read_access = read_access
        self.write_access = write_access


class Plant(db.Model):
    __tablename__ = "plant"

    id = db.Column(db.Integer, primary_key=True)
    plantname = db.Column(db.String(255))  # Name of the plant
    waterrequirement = db.Column(db.String(50))  # Watering requirement
    planttype = db.Column(db.String(100))  # Type of the plant
    plantlocation = db.Column(db.String(255))  # Location of the plant
    create_time = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp
    user_id = db.Column(db.String(21), db.ForeignKey("user.user_id"))
    gmail = db.Column(db.String(255))
    plantpicture = db.Column(db.String(255))

    # Relationship to the User table
    user = db.relationship("User", backref="plants", lazy=True)

    def __init__(
        self,
        plantname,
        waterrequirement,
        planttype,
        plantlocation,
        user_id,
        gmail,
        plantpicture=None,
    ):
        self.plantname = plantname
        self.waterrequirement = waterrequirement
        self.planttype = planttype
        self.plantlocation = plantlocation
        self.user_id = user_id
        self.gmail = gmail
        self.plantpicture = plantpicture


# dht22Data table
class dht22Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

    def __init__(self, temperature, humidity):
        self.temperature = temperature
        self.humidity = humidity


# tsl2561Data table
class tsl2561Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lux = db.Column(db.Float, nullable=False)

    def __init__(self, lux):
        self.lux = lux


# SoilMoisture Data table
class SoilMoistureData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    soil_moisture = db.Column(db.Float, nullable=False)  # Soil moisture as a percentage

    def __init__(self, soil_moisture):
        self.soil_moisture = soil_moisture


def delete_all():
    try:
        db.session.query(User).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()


def get_user_row_if_exists(user_id):
    get_user_row = User.query.filter_by(user_id=user_id).first()
    if get_user_row is not None:
        return get_user_row
    else:
        print("That user does not exist")
        return False


def add_user_and_login(name, user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.login = 1
        db.session.commit()
    else:
        new_user = User(name, user_id, None, 1, 0, 0)
        db.session.add(new_user)
        db.session.commit()


def user_logout(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.login = 0
        db.session.commit()


def add_token(user_id, token):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.token = token
        db.session.commit()


def get_token(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        return row.token
    else:
        print("User with id: " + user_id + " doesn't exist")


def view_all():
    all_rows = User.query.all()
    print_results(all_rows)


def print_results(all_rows):
    for n in range(0, len(all_rows)):
        print(
            f"{all_rows[n].id} | {all_rows[n].name} | {all_rows[n].token} | {all_rows[n].login} | {all_rows[n].read_access} | {all_rows[n].write_access}"
        )


def get_all_logged_in_users():
    rows = User.query.filter_by(login=1).all()
    print_results(rows)
    online_users = {"users": []}
    for row in rows:
        if row.read_access == 0 and row.write_access == 0:
            read = "unchecked"
            write = "unchecked"
        elif row.read_access == 1 and row.write_access == 0:
            read = "checked"
            write = "unchecked"
        elif row.read_access == 0 and row.write_access == 1:
            read = "unchecked"
            write = "checked"
        else:
            read = "checked"
            write = "checked"
        online_users["users"].append([row.name, row.user_id, read, write])
    return online_users


def add_user_permission(user_id, read, write):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        if read == "true":
            row.read_access = 1
        elif read == "false":
            row.read_access = 0
        if write == "true":
            row.write_access = 1
        elif write == "false":
            row.write_access = 0
        db.session.commit()


def delete_revoked_token(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.token = None
        db.session.commit()
