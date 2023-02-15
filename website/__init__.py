from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_NAME  #store database inside the directory of the init.py files
    db.init_app(app)


    from .views import views #imports the blueprint to show flask where to find the url
    from .auth  import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User,Role


    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.landing'
    login_manager.init_app(app)

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

            admin = User.query.filter_by(email='admin@Kimberley.com').first()
            if not admin:
                admin = User(email='admin@Kimberley.com', password=generate_password_hash('secret', method='sha256'), first_name='Admin', role_id=admin_role.id)
                db.session.add(admin)
                db.session.commit()



    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('create_database')

def recreate_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        print('Database recreated')

