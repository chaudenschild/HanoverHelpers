import calendar
import datetime as dt

import flask
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import app, basic_auth, db
from app.forms import (DeliveryPreferencesForm, EditLoginForm, InvoiceForm,
                       LoginForm, RecipientInfoForm, RegistrationForm,
                       TransactionForm, VolunteerInfoForm)
from app.models import (Recipient, Transaction, Volunteer, assign_user_type,
                        transaction_signup_view)


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

    User, user_type = assign_user_type(
        username), assign_user_type(username, return_string=True)
    user = User.query.filter_by(username=username).first()

    form = RecipientInfoForm() if user_type == 'recipient' else VolunteerInfoForm()

    if form.validate_on_submit():

        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data

        if type(form) == RecipientInfoForm:
            user.address = form.address.data

        db.session.add(user)
        db.session.commit()
        flash('User information saved!')
        return redirect(url_for('user', username=username))

    elif request.method == 'GET':

        form.name.data = current_user.name
        form.email.data = current_user.email
        form.phone.data = current_user.phone

        if type(form) == RecipientInfoForm:
            form.address.data = current_user.address

    return render_template('standard_form.html', header='Edit User Info', form=form)


@app.route('/user/<username>/profile')
@login_required
def user(username):
    User = assign_user_type(username)
    user = User.query.filter_by(username=username).first()

    if hasattr(user, 'grocery_list') and user.grocery_list is not None:
        user.clean_grocery_list = user.grocery_list.split(
            '\n')  # fix list rendering in HTML

    usertype = assign_user_type(username, return_string=True)

    return render_template('user/profile.html', user=user, usertype=usertype)


@app.route('/user/<username>/deliveries')
@login_required
def deliveries(username):
    User = assign_user_type(username)
    user = User.query.filter_by(username=username).first()

    if hasattr(user, 'grocery_list') and user.grocery_list is not None:
        user.clean_grocery_list = user.grocery_list.split(
            '\n')  # fix list rendering in HTML

    usertype = assign_user_type(username, return_string=True)

    return render_template('user/deliveries.html', user=user, usertype=usertype)


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
@login_required
def book():

    form = TransactionForm(current_user.username)
    User = assign_user_type(current_user.username)
    user = User.query.filter_by(username=current_user.username).first()

    if form.validate_on_submit():

        trans = Transaction(store=form.store.data, date=pd.to_datetime(form.date.data),
                            list=form.grocery_list.data, notes=form.dropoff_notes.data,
                            booking_date=dt.date.today())
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

    return render_template('standard_form.html', header='Book Delivery', form=form)


@app.route('/delivery_signup/', methods=['GET', 'POST'])
@login_required
def delivery_signup():

    transaction_html = transaction_signup_view(claimed=False)

    return render_template('delivery_signup.html', transaction_html=transaction_html)


@app.route('/signup_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def signup_transaction(transaction_id):
    User = assign_user_type(current_user.username)
    user = User.query.filter_by(username=current_user.username).first()
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    transaction.assign_volunteer(user)
    db.session.add(transaction)
    db.session.commit()

    flash(f'Signed up for delivery on {transaction.date}!')
    return redirect(url_for('user', username=current_user.username))


@app.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):

    form = TransactionForm()
    User = assign_user_type(current_user.username)
    user = User.query.filter_by(username=current_user.username).first()

    transaction = Transaction.query.filter_by(id=transaction_id).first()

    if transaction.modification_count >= 2:
        flash('You\'ve exceeded the 2 allowable modifications on this delivery')
        return redirect(url_for('user', username=user.username))

    if form.validate_on_submit():

        current_date_str = dt.date.today()

        transaction.store = form.store.data
        transaction.date = form.date.data
        transaction.list = form.grocery_list.data
        transaction.notes = form.dropoff_notes.data
        transaction.booking_date = dt.datetime.today()

        transaction.modification_count += 1

        db.session.add(transaction)
        db.session.commit()

        flash(f'Delivery modified!')

        return redirect(url_for('user', username=user.username))

    elif request.method == 'GET':

        form.store.data = transaction.store
        form.date.data = transaction.date
        form.grocery_list.data = transaction.list
        form.dropoff_notes.data = transaction.notes

    return render_template('standard_form.html', header='Edit Delivery', form=form)


@app.route('/view/<transaction_id>', methods=['GET', 'POST'])
@login_required
def view_list(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    return render_template('view.html', transaction=transaction, recipient=transaction.recipient)


@app.route('/drop/<transaction_id>', methods=['GET', 'POST'])
@login_required
def drop_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    transaction.drop_volunteer()
    db.session.add(transaction)
    db.session.commit()
    flash('Delivery dropped')

    return redirect(url_for('user', username=current_user.username))


@app.route('/cancel/<transaction_id>', methods=['GET', 'POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    db.session.delete(transaction)
    db.session.commit()
    flash('Delivery canceled')

    return redirect(url_for('user', username=current_user.username))


@app.route('/mark_complete/<transaction_id>', methods=['GET', 'POST'])
@login_required
def mark_complete(transaction_id):
    form = InvoiceForm()
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    if form.validate_on_submit():
        transaction.mark_as_completed()
        transaction.set_invoice(form.invoice.data)
        db.session.commit()
        flash('Delivery marked as complete')

        return redirect(url_for('deliveries', username=current_user.username))

    return render_template('standard_form.html', header='Invoice', form=form)
