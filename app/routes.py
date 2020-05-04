import calendar
import datetime as dt
import os

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename

from app import app, basic_auth, db
from app.emails import send_confirmation, send_password_reset
from app.forms import (EditLoginForm, InvoiceForm, LoginForm,
                       RecipientInfoForm, RecipientRegistrationForm,
                       ResetPasswordEmailForm, ResetPasswordForm,
                       TransactionForm, UserTypeForm, VolunteerInfoForm,
                       VolunteerRegistrationForm)
from app.models import (BaseUser, Recipient, Transaction, UserDirectory,
                        Volunteer, get_user_by_userdir_id,
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
        return redirect(url_for('deliveries', username=current_user.username))

    form = LoginForm()

    if form.validate_on_submit():
        userdir = UserDirectory.query.filter_by(
            username=form.username.data).first()

        user = get_user_by_userdir_id(
            userdir.id) if userdir is not None else None

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('deliveries', username=current_user.username))

    return render_template('login_form.html', header='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def select_user_type():
    if current_user.is_authenticated:
        return redirect(url_for('deliveries', username=current_user.username))
    form = UserTypeForm()

    if form.validate_on_submit():
        return redirect(url_for('register', user_type=form.user_type.data))

    return render_template('standard_form.html', header='Select User Type', form=form)


@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):

    if current_user.is_authenticated:
        return redirect(url_for('deliveries', username=current_user.username))

    form = RecipientRegistrationForm(
    ) if user_type == 'recipient' else VolunteerRegistrationForm()
    header = f'{user_type.capitalize()} Registration'

    if form.validate_on_submit():
        if user_type == 'volunteer':
            user = Volunteer(name=form.name.data,
                             username=form.username.data,
                             email=form.email.data,
                             phone=form.phone.data)
        elif user_type == 'recipient':
            user = Recipient(name=form.name.data,
                             username=form.username.data,
                             email=form.email.data,
                             phone=form.phone.data,
                             address=form.address.data,
                             address_notes=form.address_notes.data)

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thank you for registering for Hanover Helpers!')
        login_user(user)
        return redirect(url_for('deliveries', username=current_user.username))

    return render_template('standard_form.html', header=header, form=form)
    # return render_template('registration_form.html', user_type=user_type, form=form)


@app.route('/reset_password_email', methods=['GET', 'POST'])
def reset_password_email():

    if current_user.is_authenticated:
        return redirect(url_for('deliveries', username=current_user.username))

    form = ResetPasswordEmailForm()

    if form.validate_on_submit():
        user = Recipient.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Volunteer.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Email not in database')
        else:
            send_password_reset(user)
            flash('Password reset sent')
            return redirect(url_for('login'))
    return render_template('standard_form.html', header='Password Reset', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    if current_user.is_authenticated:
        return redirect(url_for('deliveries', username=current_user.username))

    user = BaseUser.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('standard_form.html', header='Reset Password', form=form)


@app.route('/user/<username>/edit_user_info', methods=['GET', 'POST'])
@login_required
def edit_user_info(username):

    form = RecipientInfoForm() if current_user.user_type == 'recipient' else VolunteerInfoForm()

    if form.validate_on_submit():

        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data

        if type(form) == RecipientInfoForm:
            current_user.address = form.address.data
            current_user.address_notes = form.address_notes.data

        db.session.add(current_user)
        db.session.commit()
        flash('User information saved!')
        return redirect(url_for('user', username=username))

    elif request.method == 'GET':

        form.name.data = current_user.name
        form.email.data = current_user.email
        form.phone.data = current_user.phone

        if type(form) == RecipientInfoForm:
            form.address.data = current_user.address
            form.address_notes.data = current_user.address_notes

    return render_template('standard_form.html', form=form, header='Edit User Info')


@app.route('/user/<username>/profile')
@login_required
def user(username):

    return render_template('user/profile.html', user=current_user)


@app.route('/user/<username>/deliveries')
@login_required
def deliveries(username):

    return render_template('user/deliveries.html', user=current_user)


@app.route('/user/<username>/completed_deliveries')
@login_required
def completed_deliveries(username):

    return render_template('user/completed_deliveries.html', user=current_user)


@app.route('/user/<username>/edit_login', methods=["GET", "POST"])
@login_required
def edit_login(username):

    form = EditLoginForm()

    if form.validate_on_submit():

        current_user.set_password(form.new_password.data)
        db.session.add(current_user)
        db.session.commit()
        flash('Password successfully updated')
        return redirect(url_for('deliveries', username=current_user.username))

    return render_template('standard_form.html', header='Set Password', form=form)


@app.route('/book', methods=["GET", "POST"])
@login_required
def book():

    form = TransactionForm(current_user.username)

    if form.validate_on_submit():

        trans = Transaction(store=form.store.data,
                            date=pd.to_datetime(form.date.data),
                            payment_type=form.payment_type.data, payment_notes=form.payment_notes.data,
                            list=form.grocery_list.data,
                            notes=form.other_notes.data,
                            booking_date=dt.date.today())
        trans.assign_recipient(current_user)

        db.session.add(trans)
        db.session.commit()

        day_of_week = calendar.day_name[pd.to_datetime(
            form.date.data).weekday()]
        str_date = form.date.data.strftime('%m/%d')
        flash(f'Delivery booked for {day_of_week}, {str_date}!')
        send_confirmation(current_user, 'recipient_booking', transaction=trans)

        return redirect(url_for('deliveries', username=current_user.username))

    elif request.method == 'GET':

        d = dt.datetime.today()
        # default to next Friday
        while d.weekday() != 4:
            d += dt.timedelta(1)
        form.date.data = d
        # fetch most recent store, most recent payment type, most recent payment notes
        most_recent_trans = db.session.query(Transaction).join(Recipient).filter(
            Recipient.username == current_user.username).order_by(desc(Transaction.date)).first()
        if most_recent_trans is not None:
            form.store.data = most_recent_trans.store
            form.payment_type.data = most_recent_trans.payment_type
            form.payment_notes.data = most_recent_trans.payment_notes

    return render_template('standard_form.html', header='Book Delivery', form=form)


@app.route('/delivery_signup/', methods=['GET', 'POST'])
@login_required
def delivery_signup():

    transaction_html = transaction_signup_view(claimed=False)

    return render_template('delivery_signup.html', transaction_html=transaction_html)


@app.route('/signup_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def signup_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    transaction.assign_volunteer(current_user)
    db.session.add(transaction)
    db.session.commit()

    flash(f'Signed up for delivery on {transaction.date}!')
    send_confirmation(transaction.volunteer,
                      'volunteer_claimed', transaction=transaction)

    return redirect(url_for('deliveries', username=current_user.username))


@app.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):

    form = TransactionForm()

    transaction = Transaction.query.filter_by(id=transaction_id).first()

    if form.validate_on_submit():

        transaction.store = form.store.data
        transaction.date = form.date.data
        transaction.payment_type = form.payment_type.data
        transaction.payment_notes = form.payment_notes.data
        transaction.list = form.grocery_list.data
        transaction.notes = form.other_notes.data
        transaction.booking_date = dt.datetime.today()

        db.session.add(transaction)
        db.session.commit()

        flash(f'Delivery modified!')
        send_confirmation(
            current_user, 'recipient_modification', transaction)

        return redirect(url_for('deliveries', username=current_user.username))

    elif request.method == 'GET':

        form.store.data = transaction.store
        form.date.data = transaction.date
        form.payment_type.data = transaction.payment_type
        form.payment_notes.data = transaction.payment_notes
        form.grocery_list.data = transaction.list
        form.other_notes.data = transaction.notes

    return render_template('standard_form.html', header='Edit Delivery', form=form)


@app.route('/view/<transaction_id>', methods=['GET', 'POST'])
@login_required
def view_list(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    return render_template('view.html', transaction=transaction)


@app.route('/drop/<transaction_id>', methods=['GET', 'POST'])
@login_required
def drop_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    transaction.drop_volunteer()
    db.session.add(transaction)
    db.session.commit()
    flash('Delivery dropped')

    return redirect(url_for('deliveries', current_user))


@app.route('/cancel/<transaction_id>', methods=['GET', 'POST'])
@login_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()

    # nearest Thursday
    d = dt.datetime.today()
    while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
        d += dt.timedelta(1)
    # 6PM
    cutoff = dt.datetime(d.year, d.month, d.day,
                         app.config['CUTOFF_DAYTIME']['Hour'])

    if dt.datetime.now() > cutoff:
        flash('Please note that the deadline for canceling your order has passed. If you wish to cancel your order, please call Natalie at 401-575-3142.')
    else:
        db.session.delete(transaction)
        db.session.commit()
        flash('Delivery canceled')

    return redirect(url_for('deliveries', username=current_user.username))


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

    elif request.method == 'GET':
        form.invoice.data = transaction.invoice

    return render_template('invoice_form.html', header='Invoice', form=form, transaction=transaction)


@app.route('/upload_file/<transaction_id>', methods=['GET', 'POST'])
@login_required
def upload_file(transaction_id):
    allowed_exts = ['png', 'jpg', 'jpeg']

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in allowed_exts

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file attached')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash(f'Filetype must be of {allowed_files}')
            return redirect(request.url)
        if file:

            transaction = Transaction.query.filter_by(
                id=transaction_id).first()
            # check for presence of previous receipt and delete
            if transaction.image_fname is not None:
                os.remove(os.path.join(
                    app.static_folder, app.config['IMAGE_UPLOAD_FOLDER'], transaction.image_fname))

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.static_folder,
                                   app.config['IMAGE_UPLOAD_FOLDER'], filename))

            transaction.image_fname = filename
            transaction.image_url = url_for('uploaded_file',
                                            filename=filename)
            db.session.add(transaction)
            db.session.commit()
            flash('Image added!')
            return redirect(url_for('mark_complete',
                                    transaction_id=transaction_id))
    return render_template('upload_file_form.html')


@app.route('/delete_file/<transaction_id>', methods=['GET', 'POST'])
@login_required
def delete_file(transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id).first()

    os.remove(os.path.join(app.static_folder,
                           app.config['IMAGE_UPLOAD_FOLDER'],
                           transaction.image_fname))

    transaction.image_fname = None
    transaction.image_url = None

    db.session.add(transaction)
    db.session.commit()

    flash('Image deleted!')
    return redirect(url_for('mark_complete',
                            transaction_id=transaction_id))


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    # hacky hardcode
    return send_from_directory(os.path.join(app.static_folder, app.config['IMAGE_UPLOAD_FOLDER']), filename)
