from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, login_user
from werkzeug.security import generate_password_hash


db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_NAME  #store database inside the directory of the init.py file
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    login_manager.login_message_category = 'info'
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @app.before_first_request
    def create_admin_user():
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()

        teacher_role = Role.query.filter_by(name='teacher').first()
        if not teacher_role:
            teacher_role = Role(name='teacher')
            db.session.add(teacher_role)
            db.session.commit()
            
        student_role = Role.query.filter_by(name='student').first()
        if not student_role:
            student_role = Role(name='student')
            db.session.add(student_role)
            db.session.commit()

        admin = User.query.filter_by(email='admin@Kimberley.com').first()
        if not admin:
            admin = User(email='admin@Kimberley.com', password=generate_password_hash('secret', method='sha256'), first_name='Admin', role_id=admin_role.id)
            db.session.add(admin)
            db.session.commit()

        teacher = User.query.filter_by(email='teacher@Kimberley.com').first()
        if not teacher:
            teacher = User(email='teacher@Kimberley.com', password=generate_password_hash('secret', method='sha256'), first_name='Teacher', role_id=teacher_role.id)
            db.session.add(teacher)
            db.session.commit()
        teacher_account = Account.query.filter_by(user_id=teacher.id).first()
        if not teacher_account:
            teacher_account = Account(user=teacher, balance=0)
            db.session.add(teacher_account)
            db.session.commit()

        student = User.query.filter_by(email='student@Kimberley.com').first()
        if not student:
            student = User(email='student@Kimberley.com', password=generate_password_hash('secret', method='sha256'), first_name='Student', role_id=student_role.id)
            db.session.add(student)
            db.session.commit()
        student_account = Account.query.filter_by(user_id=student.id).first()
        if not student_account:
            student_account = Account(user=student, balance=0)
            db.session.add(student_account)
            db.session.commit()

        teacher.account_id = teacher_account.id
        student.account_id = student_account.id
        db.session.commit()
    
        subjects_list = ['Math', 'English', 'Science', 'History', 'Geography', 'Art', 'Physical Education', 'Music']
        for subject_name in subjects_list:
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                new_subject = Subject(name=subject_name)
                db.session.add(new_subject)
                db.session.commit()

    from .models import User, Role, Subject, Account   

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .views import views as views_blueprint
    app.register_blueprint(views_blueprint)

    with app.app_context():
        db.create_all()
        

    return app

def create_database(app):
    with app.app_context():
        if not path.exists('website/' + DB_NAME):
            db.create_all()
            print('create_database')

def recreate_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        print('Database recreated')

