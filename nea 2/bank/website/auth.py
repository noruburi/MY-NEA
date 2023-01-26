from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__) #defines auth blueprint to create url


@auth.route('/login')
def login():
    return render_template("login.html", boolean=True)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login_user'))

@auth.route('/sign_up')
def sign_up():
    return render_template("sign_up.html", boolean=True)