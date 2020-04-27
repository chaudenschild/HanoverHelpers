import calendar
import datetime as dt

import flask
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import app, basic_auth, db
from app.forms import (DeliveryPreferencesForm, EditLoginForm, LoginForm,
                       RegistrationForm, TransactionForm, UserInfoForm)
from app.models import (Recipient, Transaction, Volunteer, assign_user_type,
                        get_transactions)


@app.route('/')
def root():
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    return render_template('admin/master.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:  # catch already logged in user
        return redirect(url_for('user', username=current_user.username))

    form = LoginForm()

    if form.validate_on_submit():
        User = assign_user_type(form.username.data)
        user = User.query.filter_by(
            username=form.username.data).first() if User is not None else None

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('user', username=user.username))

    return render_template('login_form.html', header='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('user', username=current_user.username))

    form = RegistrationForm()

    if form.validate_on_submit():
        if form.user_type.data == 'volunteer':
            user = Volunteer(username=form.username.data)
        elif form.user_type.data == 'recipient':
            user = Recipient(username=form.username.data)

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thank you for registering for Hanover Helpers!')
        login_user(user)
        return redirect(url_for('edit_user_info', username=current_user.username))
    return render_template('standard_form.html', header='Register', form=form)


@app.route('/user/<username>/edit_user_info', methods=['GET', 'POST'])
@login_required
def edit_user_info(username):
    form = UserInfoForm()

    if form.validate_on_submit():
        User = assign_user_type(username)
        user = User.query.filter_by(username=username)

        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.address = form.address.data

        db.session.add(user)
        db.session.commit()
        flash('User information saved!')

        return redirect(url_for('user', username=username))
    return render_template('standard_form.html', header='Edit User Info', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    User = assign_user_type(username)
    user = User.query.filter_by(username=username).first()

    user.clean_grocery_list = user.grocery_list.split('\n') # fix list rendering in HTML

    usertype = assign_user_type(username, return_string=True)

    return render_template('user_landing_page.html', user=user, usertype=usertype)


@app.route('/user/<username>/edit_login', methods=["GET", "POST"])
@login_required
def edit_login(username):

    form = EditLoginForm()

    if form.validate_on_submit():
        User = assign_user_type(current_user.username)
        user = User.query.filter_by(username=current_user.username).first()

        user.set_password(form.new_password.data)
        db.session.add(user)
        db.session.commit()
        flash('Password successfully updated')
        return redirect(url_for('user', username=user.username))

    return render_template('standard_form.html', header='Set Password', form=form)


@app.route('/user/<username>/edit_delivery_preferences', methods=["GET", "POST"])
@login_required
def edit_delivery_preferences(username):
    form = DeliveryPreferencesForm()

    if form.validate_on_submit():
        User = assign_user_type(current_user.username)
        user = User.query.filter_by(username=current_user.username).first()

        user.store = form.store.data
        user.grocery_list = form.grocery_list.data
        user.dropoff_day = form.dropoff_day.data
        user.dropoff_notes = form.dropoff_notes.data
        user.payment_notes = form.payment_notes.data

        db.session.add(user)
        db.session.commit()

        flash('Delivery preferences saved')
        return redirect(url_for('user', username=user.username))

    elif request.method == 'GET':

        form.store.data = current_user.store
        form.grocery_list.data = current_user.grocery_list
        form.dropoff_day.data = current_user.dropoff_day
        form.dropoff_notes.data = current_user.dropoff_notes
        form.payment_notes.data = current_user.payment_notes

    return render_template('standard_form.html', header='Edit Delivery Preferences', form=form)


@app.route('/book', methods=["GET", "POST"])
def book():

    form = TransactionForm()

    User = assign_user_type(current_user.username)
    user = User.query.filter_by(username=current_user.username).first()

    if form.validate_on_submit():

        current_date_str = dt.date.today()

        trans = Transaction(store=form.store.data, date=pd.to_datetime(form.date.data),
                            list=form.grocery_list.data, notes=form.dropoff_notes.data,
                            booking_date=current_date_str)
        trans.assign_recipient(user)

        db.session.add(trans)
        db.session.commit()

        day_of_week = calendar.day_name[pd.to_datetime(
            form.date.data).weekday()]
        str_date = form.date.data.strftime('%m/%d')
        flash(f'Delivery booked for {day_of_week}, {str_date}!')

        return redirect(url_for('user', username=user.username))

    elif request.method == 'GET':

        d = dt.datetime.today()
        if user.dropoff_day is not None:
            while d.weekday() != list(calendar.day_name).index(user.dropoff_day) - 1:
                d += dt.timedelta(1)

        form.store.data = user.store
        form.date.data = d + dt.timedelta(1)

        form.grocery_list.data = user.grocery_list
        form.dropoff_notes.data = user.dropoff_notes

    return render_template('edit_make_transaction_form.html', header='Book Delivery', form=form)


@app.route('/delivery_signup', methods=['GET', 'POST'])
def delivery_signup():

    transaction_html = get_transactions(claimed=False)

    return render_template('delivery_signup.html', transaction_html=transaction_html)
