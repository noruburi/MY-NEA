from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_NAME  #store database inside the directory of the init.py files
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.landing'
    login_manager.init_app(app)
    login_manager.login_message_category = 'info'
    migrate = Migrate(app, db)
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
        
        admin = User.query.filter_by(email='admin@Kimberley.com').first()
        if not admin:
            admin = User(email='admin@Kimberley.com', password=generate_password_hash('secret', method='sha256'), first_name='Admin', role_id=admin_role.id)
            db.session.add(admin)
            db.session.commit()

        db.session.commit()

    from .models import User, Role    

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

