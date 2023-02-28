from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, Role, Transactions, TeacherRequestHistory
from . import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

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
                    login_user(user, remember=True)
                    return redirect(url_for('auth.admin_page'))
                elif role.name == "teacher":
                    if not user.role_approved:
                        flash('Teacher role not approved yet.', category='error')
                        return redirect(url_for('auth.login'))
                    else:
                        flash('Logged in as teacher successfully!', category='success')
                elif role.name == "student":
                    flash('Logged in as student successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html', user=current_user)


@auth.route('/admin')
def admin_page():
    # Get all transactions
    transactions = db.session.query(Transactions).all()

    # Get all pending teacher requests
    teacher_requests = User.query.filter(User.role.has(name='teacher'), User.role_request==True).all()

    # Render the admin page and pass in the transactions and teacher_requests
    return render_template('admin.html', user=current_user, transactions=transactions, teacher_requests=teacher_requests)



@auth.route('/admin/update-teacher-request', methods=['POST'])
@login_required
def update_teacher_request():
    user_id = request.form['user_id']
    user = User.query.get(user_id)

    if user is None or not user.role_request or user.role.name != 'teacher':
        flash('Invalid request.', 'error')
        return redirect(url_for('auth.admin_page'))

    if not current_user.is_admin():
        flash('You are not authorized to approve or reject teacher requests.', 'error')
        return redirect(url_for('auth.admin_page'))

    action = request.form['action']
    if action == 'approve':
        user.role_approved = True
        user.role_request = False
        db.session.commit()
        flash(f'Teacher role request for {user.email} has been approved.', 'success')
        status = 'accepted'
    elif action == 'reject':
        user.role_rejected = True
        db.session.commit()
        flash(f'Teacher role request for {user.email} has been rejected.', 'success')
        status = 'rejected'

    # Add a check to see if date_requested is None, and set it to the current time if it is
    date_requested = user.role_requested_on
    if date_requested is None:
        date_requested = datetime.utcnow()

    history_entry = TeacherRequestHistory(
        user=user,
        status=status,
        date_requested=date_requested,
        date_resolved=datetime.utcnow(),
        resolved_by=current_user
    )
    db.session.add(history_entry)
    db.session.commit()

    return redirect(url_for('auth.admin_page'))




@auth.route('/teacher_requests_history')
@login_required
def view_teacher_requests():
    requests = TeacherRequestHistory.query.order_by(TeacherRequestHistory.date_requested.desc()).all()
    return render_template('teacher_requests_history.html', requests=requests, user=current_user)


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
        role = request.form.get('role') #student or teacher

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
                role = Role.query.filter_by(name=role).first()
                if role is None:
                    flash('Invalid role selected', category='error')
                    return redirect(url_for('auth.sign_up'))
                
                role_request = request.form.get('role') == 'teacher'
                print(role_request)

                new_user = User(email=email,first_name=firstName,password=generate_password_hash(password1, method='sha256'),role=role,role_request=role_request, role_requested_on=datetime.now())
                try:
                    db.session.add(new_user)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash('Email address already exists', category='error')
                    return redirect(url_for('auth.sign_up'))
                
                if request.form.get('role') == 'teacher':
                    # Create a new TeacherRequestHistory object with the user_id and status set to 'Pending'
                    teacher_request = TeacherRequestHistory(user_id=current_user.id, status='Pending')
                    db.session.add(teacher_request)
                    db.session.commit()
                    flash('Teacher role request sent', category='success')
                    return redirect(url_for('views.home'))
                else:
                    flash('Registration successful', category='success')
                    return redirect(url_for('views.home'))
                    

    roles = Role.query.all()
    return render_template('sign_up.html',user=current_user, roles=roles)




