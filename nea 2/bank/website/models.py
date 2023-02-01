from . import db
from flask_login import UserMixin

class User(db.model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.coulmn(db.String(150), unique=True)