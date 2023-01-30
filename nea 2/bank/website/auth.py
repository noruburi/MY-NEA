from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__) #defines auth blueprint to create url


@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html", boolean=True)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login_user'))

@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'post':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            flash('passwords don\'t match')
        else:
            flash('account created !')


    return render_template("sign_up.html", boolean=True)