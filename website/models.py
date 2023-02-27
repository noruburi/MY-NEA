from . import db
from flask_login import UserMixin


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, index=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(25))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    role_approved = db.Column(db.Boolean, default=False)
    role_request = db.Column(db.Boolean, default=False)
    role_requested_on = db.Column(db.DateTime) # add this line

    def is_admin(self):
        return self.role.name == 'admin'
    
    def is_teacher(self):
        return self.role.name == 'teacher'

class Account(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer)

class Transactions(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    sequence = db.Column(db.Integer)
    from_account_id = db.Column(db.Integer)
    dateTime = db.Column(db.DateTime)
    to_account_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    
class TeacherRequestHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('teacher_requests_history', lazy=True))
    status = db.Column(db.String(20), nullable=False)
    date_resolved = db.Column(db.DateTime)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])

    def __repr__(self):
        return f"<TeacherRequestHistory {self.id}>"
