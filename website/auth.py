from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   #means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__) #defines auth blueprint to create url



@auth.route('/landing')
def landing():
    return render_template("landing.html", user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if user.role == "admin":
                    flash('Logged in as admin successfully!', category='success')
                elif user.role == "teacher":
                    if not user.is_approved:
                        flash('Teacher role not approved yet.', category='error')
                        return redirect(url_for('auth.login'))
                elif user.role == "student":
                    flash('Logged in as student successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


def password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if any(char.isdigit() for char in password):
        score += 1
    if any(char.isupper() for char in password):
        score += 1
    if any(char in set(r"!@#$%^&*()/") for char in password):
        score += 1
    if score >= 4:
        return score, "Password is strong."
    else:
        missing_requirements = []
        if len(password) < 8:
            missing_requirements.append("Password must be at least 8 characters.")
        if not any(char.isdigit() for char in password):
            missing_requirements.append("Password must contain at least one digit.")
        if not any(char.isupper() for char in password):
            missing_requirements.append("Password must contain at least one uppercase letter.")
        if not any(char in set(r"!@#$%^&*()/") for char in password):
            missing_requirements.append("Password must contain at least one symbol (!@#$%^&*()/).")
        return score, ", ".join(missing_requirements)

@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # if user:
        #     flash('Email already exists.', category='error')
        if len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstName) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')  
        elif len(password1) > 25:
            flash('Password can only be 25 or less characters.', category='error')             
        else:
            score, message = password_strength(password1)
            if score < 4:
                flash(message, category='error')
            else:
                new_user = User(email=email, first_name=firstName, password=generate_password_hash(password1, method='sha256'))
                db.session.add(new_user)
                db.session.commit()
                flash('account created !', category='success')
                return redirect(url_for('views.home'))


    return render_template("sign_up.html", user=current_user)