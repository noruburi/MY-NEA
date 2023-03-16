from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, Role, Transactions, TeacherRequestHistory, Account, Class, Subject, JoinRequest
from . import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import and_

auth = Blueprint('auth', __name__) #defines auth blueprint to create url



@auth.route('/landing')
def landing():
    return render_template("landing.html", user=current_user)

# @auth.route('/teacher')
# @login_required
# def teacher():
#     # Fetch classes created by the current user (teacher)
#     classes = Class.query.filter_by(teacher_id=current_user.id).all()

#     # Fetch student join requests for each class
#     join_requests = {}
#     for class_obj in classes:
#         join_requests[class_obj.id] = JoinRequest.query.filter_by(class_id=class_obj.id).all()

#     return render_template('teacher.html', user=current_user, classes=classes, join_requests=join_requests)


@auth.route('/teacher')
@login_required
def teacher():
    join_requests = JoinRequest.query.join(User).filter(User.id == 3).all()
    return render_template('teacher.html', user=current_user, join_requests=join_requests)



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
                        login_user(user, remember=True)
                        return redirect(url_for('auth.teacher'))
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
        user.role_request = False
        db.session.commit()
        flash(f'Teacher role request for {user.email} has been rejected.', 'success')
        status = 'rejected'

    # Add a check to see if date_requested is None, and set it to the current time if it is
    date_requested = user.role_requested_on

    history_entry = TeacherRequestHistory(
        user=user,
        status=status,
        date_resolved=datetime.utcnow(),
        resolved_by=current_user
    )
    db.session.add(history_entry)
    db.session.commit()

    return redirect(url_for('auth.admin_page'))


@auth.route('/teacher_requests_history')
@login_required
def view_teacher_requests():
    requests = TeacherRequestHistory.query.join(User, TeacherRequestHistory.user_id == User.id).order_by(User.role_requested_on).all()
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
    

    
def generate_username(first_name, last_name):
    base_username = first_name[:3].lower() + last_name[:3].lower()
    username = base_username
    counter = 1

    while User.query.filter_by(user_name=username).first() is not None:
        username = base_username + str(counter)
        counter += 1

    return username

def contains_digit(s):
    return any(c.isdigit() for c in s)


@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        role = request.form.get('role')


        if len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif contains_digit(first_name) or contains_digit(last_name) or len(first_name) < 2 or len(last_name) < 2:
            flash('First name and last name must not contain numbers and should be at least 2 characters long.', category='error')
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
                
                user_name = generate_username(first_name, last_name)

                role_request = request.form.get('role') == 'teacher'
                print(role_request)

                new_user = User(email=email, first_name=first_name, last_name=last_name, user_name=user_name, password=generate_password_hash(password1, method='sha256'), role=role, role_request=role_request, role_requested_on=datetime.now())
                try:
                    db.session.add(new_user)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash('Email address already exists', category='error')
                    return redirect(url_for('auth.sign_up'))
                
                if role_request:
                    # Create a new TeacherRequestHistory object with the user_id and status set to 'Pending'
                    teacher_request = TeacherRequestHistory(user_id=new_user.id, status='Pending')
                    db.session.add(teacher_request)
                    db.session.commit()
                    flash('Teacher role request sent. Please wait for approval.', category='success')
                    return redirect(url_for('auth.sign_up'))  # Redirect to sign-up page
                else:
                    flash('Registration successful', category='success')
                    login_user(new_user)
                    return redirect(url_for('views.home'))
                    

    roles = Role.query.all()
    return render_template('sign_up.html',user=current_user, roles=roles)



@auth.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if current_user.is_admin() or current_user.is_teacher():
        students = User.query.filter_by(role_id=3).all()
        if request.method == 'POST':
            student_id = request.form['student_id']
            points = request.form['points']
            student_account = Account.query.filter_by(id=student_id).first()
            if student_account:
                student_account.balance += int(points)
                db.session.commit()
                transaction = Transactions(
                    sequence=1,
                    from_account_id=current_user.id,
                    dateTime=datetime.utcnow(),
                    to_account_id=student_id,
                    amount=int(points)
                )
                db.session.add(transaction)
                db.session.commit()
                flash('Transaction successful!', 'success')
                return redirect(url_for('auth.transactions'))
            else:
                flash('Invalid student ID', 'danger')


    students = User.query.filter_by(role_id=3).all() # Assuming student role ID is 3
    return render_template('transactions.html', students=students, user=current_user)

@auth.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role.name != 'teacher':
        flash('You must be a teacher to create a class', category='error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        subject_id = request.form.get('subject')
        year_group = request.form.get('year_group')

        if subject_id and year_group:
            subject = Subject.query.get(subject_id)
            base_class_name = f"{year_group}{subject.name[0]}{current_user.first_name[0]}{current_user.last_name[0]}"
            class_name = base_class_name
            counter = 1

            while Class.query.filter_by(name=class_name).first() is not None:
                class_name = base_class_name + str(counter)
                counter += 1

            new_class = Class(name=class_name, subject_id=subject_id, year_group=year_group, teacher_id=current_user.id)
            db.session.add(new_class)
            db.session.commit()

            flash('Class created successfully', category='success')
        else:
            flash('Please fill out all fields', category='error')

    subjects = Subject.query.all()
    return render_template("create_class.html", user=current_user, subjects=subjects)


# @auth.route('/student/<int:student_id>', methods=['GET'])
# def student(student_id):
#     student = User.query.filter_by(id=student_id, role_id=3).all()
#     classes = Class.query.all()
#     return render_template('student.html', student=student, classes=classes)



@auth.route('/student/<int:student_id>', methods=['GET'])
def student(student_id):
    student = User.query.filter_by(id=student_id, role_id=3).first_or_404()
    print("student: ", student)
    
    search_year_group = request.args.get('year_group', type=int)
    search_subject_id = request.args.get('subject_id', type=int)
    search_teacher_id = request.args.get('teacher_id', type=int)  # New filter
    
    search_filters = []
    if search_year_group:
        search_filters.append(Class.year_group == search_year_group)
    if search_subject_id:
        search_filters.append(Class.subject_id == search_subject_id)
    if search_teacher_id:  # Add the filter for teacher_id
        search_filters.append(Class.teacher_id == search_teacher_id)
    
    if search_filters:
        classes = Class.query.filter(and_(*search_filters)).all()
    else:
        classes = Class.query.all()
        
    subjects = Subject.query.all()
    teachers = User.query.filter_by(role_id=2).all()  # Fetch all teachers

    print("classes: ", classes)
    return render_template('student.html', student=student, classes=classes, user=current_user, search_year_group=search_year_group, search_subject_id=search_subject_id, search_teacher_id=search_teacher_id, subjects=subjects, teachers=teachers)



@auth.route('/request_join_class/<int:student_id>/<int:class_id>', methods=['GET'])
def request_join_class(student_id, class_id):
    # Create a new join request object
    join_request = JoinRequest(student_id=student_id, class_id=class_id, status='pending')
    db.session.add(join_request)
    db.session.commit()

    flash('Join request sent successfully', category='success')
    return redirect(url_for('auth.student', student_id=student_id))
    


