from . import db
from flask_login import UserMixin



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(25))
    first_name = db.Column(db.String(25))
    role = db.Column(db.string(20))

class Account(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    balance = db.Column(db.Integer,)

class transactions(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    sequence = db.Column(db.Integer)
    from_account_id = db.Column(db.Integer)
    dateTime = db.column(db.Integer)
    to_account_id = db.Column(db.Integer)
    ammount = db.Column(db.Integer)
    

