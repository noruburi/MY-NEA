from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, Role, Transactions, TeacherRequestHistory, Account, Class, Subject, JoinRequest, Coupon
from . import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import and_

auth = Blueprint('auth', __name__) #defines auth blueprint to create url

#//login and sign-up-------------------------------------------------------------------------------------------------------------------------------------------------------------


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
                        return redirect(url_for('auth.award_points'))
                elif role.name == "student":
                    flash('Logged in as student successfully!', category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('auth.student', student_id=user.id))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html', user=current_user)




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

                    # Create a new account for the user
                    account = Account(user=new_user, balance=0)
                    db.session.add(account)
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
    return render_template('sign_up.html', user=current_user, roles=roles)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



#//login and sign-up-------------------------------------------------------------------------------------------------------------------------------------------------------------


#//admin--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

#//admin--------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#//teacher--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@auth.route('/teacher')
@login_required
def teacher():
    join_requests = JoinRequest.query.join(User).filter(User.id == 3).all()
    classes = Class.query.all()
    return render_template('teacher.html', user=current_user, join_requests=join_requests, classes=classes)



@auth.route('/join_request')
@login_required
def join_request():
    filter = request.args.get('filter', 'all')
    
    if filter == 'pending':
        join_requests = JoinRequest.query.join(User).filter(User.id == 3, JoinRequest.status == 'pending').all()
    elif filter == 'accepted_rejected':
        join_requests = JoinRequest.query.join(User).filter(User.id == 3, (JoinRequest.status == 'accepted') | (JoinRequest.status == 'rejected')).all()
    else:  # Default: Show all requests
        join_requests = JoinRequest.query.join(User).filter(User.id == 3).all()

    return render_template('join_request.html', user=current_user, join_requests=join_requests, filter=filter)



@auth.route('/respond_join_request/<int:join_request_id>/<string:action>', methods=['GET'])
@login_required
def respond_join_request(join_request_id, action):
    # Get the join request object
    join_request = JoinRequest.query.get_or_404(join_request_id)

    # Check if the current user is the teacher of the class
    if current_user.id != join_request.class_.teacher_id:
        flash('You are not authorized to respond to this join request!', category='error')
        return redirect(url_for('auth.join_request'))

    # Update the status of the join request
    if action == 'accept':
        join_request.status = 'accepted'
        flash('Join request accepted!', category='success')
    elif action == 'reject':
        join_request.status = 'rejected'
        flash('Join request rejected!', category='success')
    else:
        flash('Invalid action!', category='error')
        return redirect(url_for('auth.join_request'))

    # Commit the changes to the database
    db.session.commit()

    # Redirect to the teacher dashboard
    return redirect(url_for('auth.join_request'))


@auth.route('/award_points', methods=['GET', 'POST'])
@login_required
def award_points():
    if current_user.is_admin() or current_user.is_teacher():
        year_groups = db.session.query(Class.year_group).distinct().all()
        classes = Class.query.filter_by(teacher=current_user).all()
        students = User.query.filter_by(role_id=3).all()

        if request.method == 'POST':
            year_group = request.form['year_group']
            class_id = request.form['class_id']
            student_id = request.form['student_id']
            points = int(request.form['amount'])

            if current_user.remaining_points < points:
                flash('You do not have enough points to award.', 'danger')
                return redirect(url_for('auth.award_points'))

            if current_user.points_awarded_this_week >= current_user.weekly_point_limit:
                flash('You have exceeded your weekly point limit.', 'danger')
                return redirect(url_for('auth.award_points'))

            student = User.query.filter_by(id=student_id, role_id=3).first()

            if student:
                student_account = Account.query.filter_by(user_id=student.id).first()
                if student_account:
                    student_account.balance += points
                    db.session.commit()

                    teacher_account = Account.query.filter_by(user_id=current_user.id).first()
                    teacher_account.points_awarded += points
                    current_user.points_awarded_this_week += points
                    current_user.last_award_date = datetime.utcnow().date()  # Update last_award_date
                    db.session.commit()

                    transaction = Transactions(
                        sequence=1,
                        from_account_id=current_user.id,
                        dateTime=datetime.utcnow(),
                        to_account_id=student.id,
                        amount=points
                    )
                    db.session.add(transaction)
                    db.session.commit()

                    flash('Transaction successful!', 'success')
                    return redirect(url_for('auth.award_points'))
                else:
                    flash('Invalid student ID', 'danger')
            else:
                flash('Invalid student name or class name', 'danger')

        remaining_points = current_user.remaining_points
        remaining_point_percentage = current_user.remaining_point_percentage

        return render_template('award_points.html', year_groups=year_groups, classes=classes, students=students, user=current_user, remaining_points=remaining_points, remaining_point_percentage=remaining_point_percentage)
    else:
        return "You are not authorized to access this page."




@auth.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role.name != 'teacher':
        flash('You must be a teacher to create a class', category='error')
        return redirect(url_for('views.home'))

    subjects = Subject.query.all()

    if request.method == 'POST':
        subject_id = request.form.get('subject')
        year_group = request.form.get('year_group')

        existing_class = Class.query.filter_by(subject_id=subject_id, year_group=year_group, teacher_id=current_user.id).first()
        if existing_class:
            return render_template('create_class.html', existing_class=existing_class, user=current_user, subjects=subjects)

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

    return render_template("create_class.html", user=current_user, subjects=subjects)

#//teacher--------------------------------------------------------------------------------------------------------------------------------------------------------------------------



#//student--------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@auth.route('/student/<int:student_id>')
@login_required
def student(student_id):
    student = User.query.filter_by(id=current_user.id, role_id=3).first()
    if student:
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
        join_requests = JoinRequest.query.filter_by(student_id=student_id).all()
        
        return render_template('student.html', student=student, classes=classes, user=current_user, search_year_group=search_year_group, search_subject_id=search_subject_id, search_teacher_id=search_teacher_id, subjects=subjects, teachers=teachers)
    else:
        flash('You are not a student!', category='error')
        return redirect(url_for('views.home'))




@auth.route('/request_join_class/<int:student_id>/<int:class_id>', methods=['GET'])
def request_join_class(student_id, class_id):
    # Check if the user already has a join request for the class
    existing_join_request = JoinRequest.query.filter_by(student_id=student_id, class_id=class_id).first()
    if existing_join_request:
        flash('You already have a join request for this class.', 'warning')
        return redirect(url_for('auth.student', student_id=student_id))

    # Create a new join request object
    join_request = JoinRequest(student_id=student_id, class_id=class_id, status='pending')
    db.session.add(join_request)
    db.session.commit()

    flash('Join request sent successfully', category='success')
    return redirect(url_for('auth.student', student_id=student_id))




@auth.route('/student_rewards', methods=['GET', 'POST'])
@login_required
def student_rewards():
    student = User.query.filter_by(id=current_user.id, role_id=3).first()
    if student:
        available_items = [
            {'name': 'Pen', 'description': 'A high-quality pen', 'points': 10},
            {'name': 'Notebook', 'description': 'A durable notebook', 'points': 20},
            {'name': 'Coffee', 'description': 'A delicious cup of coffee', 'points': 30},
            {'name': 'Lunch', 'description': 'A nutritious lunch', 'points': 50},
        ]
        if request.method == 'POST':
            item_index = int(request.form.get('item_index'))
            item = available_items[item_index]
            student_account = student.account  # Fixed attribute name
            if student_account.balance >= item['points']:
                # Deduct points from student's account
                student_account.balance -= item['points']
                db.session.commit()

                coupon_code = None  # TODO: Generate unique 8-digit code
                coupon = Coupon(student_id=student.id, name=item['name'], description=item['description'], points_cost=item['points'], code=coupon_code, redeemed=False, redeem_date=None)
                db.session.add(coupon)
                db.session.commit()
                transaction = Transactions(sequence=1, from_account_id=student_account.id, dateTime=datetime.utcnow(), to_account_id=None, amount=-item['points'], account_id=student_account.id, code=coupon_code)
                db.session.add(transaction)
                db.session.commit()
                flash('Coupon purchased successfully!', 'success')
            else:
                flash('You do not have enough points to purchase this item', 'error')
    else:
        flash('You are not a student!', category='error')
        return redirect(url_for('views.home'))
            
    return render_template('student_rewards.html', available_items=available_items, student=student, user=current_user)


@auth.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    account = user.account
    balance = account.balance
    transactions = account.transactions
    return render_template('student_dashboard.html', balance=balance, transactions=transactions, user=current_user)

@auth.route('/redeem_coupon', methods=['POST'])
@login_required
def redeem_coupon():
    coupon_id = request.form.get('coupon_id')
    print("Received redeem_coupon request for coupon ID:", coupon_id)

    coupon = Coupon.query.get(coupon_id)
    
    if coupon and not coupon.redeemed:
        coupon.code = coupon.generate_code()
        coupon.redeem()
        db.session.commit()
        print("Coupon updated with code and redeem date:", coupon.code)
        return jsonify({'code': coupon.code, 'status': 'success'})
    else:
        print("Failed to redeem coupon")
        return jsonify({'status': 'failed'})


#//student--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
