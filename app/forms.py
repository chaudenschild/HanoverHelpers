import datetime as dt

import pandas as pd
import phonenumbers
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, RadioField, SelectField,
                     SelectMultipleField, StringField, SubmitField,
                     TextAreaField, widgets)
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app import app, db
from app.models import Recipient, Transaction, Volunteer, get_user


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ResetPasswordEmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class RegistrationForm(FlaskForm):
    user_type = RadioField(validators=[
        DataRequired()], choices=[('volunteer', 'Helper'), ('recipient', 'Recipient')])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):

        user_vol = Volunteer.query.filter_by(
            username=username.data).first()
        user_rec = Recipient.query.filter_by(
            username=username.data).first()

        if user_vol is not None or user_rec is not None:  # check uniqueness in both user types
            raise ValidationError('Username already in use.')


class EditLoginForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField('Confirm New Password', validators=[
                                  DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Save Changes')

    def validate_old_password(self, old_password):

        if not current_user.check_password(old_password.data):
            raise ValidationError('Incorrect password')


class InfoForm(FlaskForm):
    def validate_phone(self, phone):
        try:
            p = phonenumbers.parse(phone.data, "US")
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')


class VolunteerInfoForm(InfoForm):
    name = StringField('Preferred Name')
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone number', validators=[DataRequired()])
    submit = SubmitField('Save Preferences')


class RecipientInfoForm(InfoForm):
    name = StringField('Preferred Name')
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone number', validators=[DataRequired()])
    address = SelectField('Address (if Other, please provide address in Delivery Notes)', choices=[
        (x, x) for x in ['Kendal', 'Other']],
        validators=[DataRequired()])
    submit = SubmitField('Save Preferences')


class DeliveryPreferencesForm(FlaskForm):

    delivery_days = ['Friday', 'Saturday']

    store_list = ['Hanover Coop', 'Lebanon Coop', "Hannaford's",
                  'CVS', "BJ's", 'NH Liquor Outlet']

    store = SelectField('Store', choices=[
        (x, x) for x in store_list], validators=[DataRequired()])
    dropoff_day = SelectField('Preferred Delivery Day', choices=[
                              (x, x) for x in delivery_days])
    dropoff_notes = TextAreaField('Standard Delivery Notes')
    payment_notes = TextAreaField('Standard Payment Notes')
    submit = SubmitField('Save Preferences')


class TransactionForm(FlaskForm):

    store_list = ['Hanover Coop', 'Lebanon Coop', "Hannaford's",
                  'CVS', "BJ's", 'NH Liquor Outlet']

    store = SelectField('Store', choices=[
        (x, x) for x in store_list], validators=[DataRequired()])
    date = DateField('Date (Either Friday or Saturday)',
                     validators=[DataRequired()])
    grocery_list = TextAreaField('Grocery List', validators=[DataRequired()])
    dropoff_notes = TextAreaField('Delivery Notes')
    submit = SubmitField('Book Delivery')

    def __init__(self, username=None, **kwargs):
        super().__init__(**kwargs)
        self.username = username

    def validate_date(self, date):

        # Find next Thursday
        d = dt.datetime.today()
        while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
            d += dt.timedelta(1)
        # 6PM
        cutoff = dt.datetime(d.year, d.month, d.day,
                             app.config['CUTOFF_DAYTIME']['Hour'])

        if dt.datetime.now() > cutoff:
            flash('Please note that the deadline for making changes to your order has passed. If you wish to cancel your order, please call Natalie at 401-575-3142.')
            raise ValidationError

        if pd.to_datetime(date.data).weekday() not in [4, 5]:
            raise ValidationError(
                'Orders/modifications must be placed on Friday or Saturday')

        if self.username is not None:

            early_window = pd.to_datetime(
                date.data) - pd.Timedelta(days=2)
            late_window = pd.to_datetime(date.data) + pd.Timedelta(days=2)
            counts = db.session.query(Transaction, Recipient).join(Recipient) \
                .filter_by(username=self.username)\
                .filter(Transaction.date >= early_window)\
                .filter(Transaction.date <= late_window)\
                .count()
            if counts >= 1:
                raise ValidationError(
                    'Only one delivery allowed per week')


class InvoiceForm(FlaskForm):
    invoice = StringField('Amount')
    submit = SubmitField('Submit')
