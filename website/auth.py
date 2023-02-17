from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   #means from __init__.py import db
from .models import Transactions, Role  
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
                role = user.role
                if role.name == "admin":
                    flash('Logged in as admin successfully!', category='success')
                    return redirect(url_for('auth.admin_page'))
                elif role.name == "teacher":
                    if not user.is_approved:
                        flash('Teacher role not approved yet.', category='error')
                        return redirect(url_for('auth.login'))
                elif role.name == "student":
                    flash('Logged in as student successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html',user=current_user)

@auth.route('/admin')
def admin_page():
    transactions = db.session.query(Transactions).all()
    # teacher_requests = User.query.join(Role).filter(Role.name == 'teacher', User.role_approved == False).all()
    teacher_requests = User.query.filter(User.role.has(name='teacher'), User.role_request==True).all()
    return render_template('admin.html',user=current_user,transactions=transactions,teacher_requests=teacher_requests)



@auth.route('/approve-teacher-request/<int:user_id>', methods=['POST'])
@login_required
def approve_teacher_request(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('auth.admin_page'))

    if user.role.name != 'teacher':
        flash('User is not a teacher', 'error')
        return redirect(url_for('auth.admin_page'))

    user.role_approved = True
    db.session.add(user)
    db.session.commit()

    flash(f'Teacher request approved for {user.email}', 'success')
    return redirect(url_for('auth.admin_page'))



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
        role_name = request.form.get('role')

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

                # Create a new Role object and associate it with the new user
                if role_name == 'student':
                    new_user.role = Role.query.filter_by(name='student').first()
                else:
                    new_user.role_request = True
                    new_user.role = Role.query.filter_by(name='teacher').first()
                db.session.add(new_user)
                db.session.commit()
                flash('account created !', category='success')
                return redirect(url_for('views.home'))
    return render_template('signup.html', user=current_user)

