import datetime as dt

import pandas as pd
import phonenumbers
from flask_login import current_user
from flask_wtf import FlaskForm
from sqlalchemy import or_
from wtforms import (BooleanField, FloatField, PasswordField, RadioField,
                     SelectField, StringField, SubmitField, TextAreaField)
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app import app, db
from app.models import Recipient, Transaction, UserDirectory, Volunteer


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
    submit = SubmitField('Reset Password')


class UserTypeForm(FlaskForm):
    user_type = RadioField(validators=[
        DataRequired()], choices=[('volunteer', 'Helper'), ('recipient', 'Recipient')])
    submit = SubmitField('Register')


class EditLoginForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField('Confirm New Password', validators=[
                                  DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Save Changes')

    def validate_old_password(self, old_password):

        if not current_user.check_password(old_password.data):
            raise ValidationError('Incorrect password')


class RegistrationForm(FlaskForm):
    def validate_username(self, username):

        user = UserDirectory.query.filter_by(username=username.data).first()

        if user is not None:  # check uniqueness in both user types
            raise ValidationError('Username already in use.')

    def validate_email(self, email):

        user_r = Recipient.query.filter(
            Recipient.email.ilike(email.data)).first()
        user_v = Volunteer.query.filter(
            Volunteer.email.ilike(email.data)).first()

        if user_r is not None:
            if user_r.email in app.config['EMAIL_VALIDATOR_EXEMPT']:
                pass
            else:
                raise ValidationError('Email already in use')

        if user_v is not None:
            if user_v.email in app.config['EMAIL_VALIDATOR_EXEMPT']:
                pass
            else:
                raise ValidationError('Email already in use')


class RecipientRegistrationForm(RegistrationForm):
    name = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone number', validators=[DataRequired()])
    address = SelectField('Address (if Other, please specify in Address Notes)', choices=[
        (x, x) for x in ['Kendal', 'Other']], validators=[DataRequired()])
    address_notes = StringField('Address Notes')
    submit = SubmitField('Register')


class VolunteerRegistrationForm(RegistrationForm):
    name = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone number', validators=[DataRequired()])
    submit = SubmitField('Register')


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
    address_notes = StringField('Address Notes')
    submit = SubmitField('Save Preferences')


class TransactionForm(FlaskForm):

    store = SelectField('Store', choices=[
        (x, x) for x in app.config['STORE_LIST']], validators=[DataRequired()])
    date = DateField('Date (Either Friday, Saturday, or Sunday)',
                     validators=[DataRequired()])
    payment_type = SelectField('Payment Type', validators=[DataRequired()], choices=[
                               (x, x) for x in app.config['PAYMENT_TYPE']])
    payment_notes = TextAreaField('Payment Notes')
    grocery_list = TextAreaField('Grocery List', render_kw={
                                 "rows": 10, "cols": 11}, validators=[DataRequired()])
    other_notes = TextAreaField('Other Notes')
    submit = SubmitField('Book Delivery')

    def __init__(self, username=None, **kwargs):
        super().__init__(**kwargs)
        self.username = username

    def validate_date(self, date):

        if pd.to_datetime(date.data).weekday() not in [4, 5, 6]:
            raise ValidationError(
                'Orders/modifications must be placed for Friday, Saturday, or Sunday')

        if pd.to_datetime(date.data) < dt.datetime.now():
            raise ValidationError(
                "Volunteers cannot travel back in time."
            )

        # Find next Thursday
        d = dt.datetime.today()
        while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
            d += dt.timedelta(1)
        # 6PM
        cutoff = dt.datetime(d.year, d.month, d.day,
                             app.config['CUTOFF_DAYTIME']['Hour'])

        # if cutoff < dt.datetime.now():
        #    raise ValidationError(
        #        'Please note that the deadline for making changes to your order has passed.')

        if self.username is not None:  # only on new booking
            early_window = date.data - dt.timedelta(2)
            late_window = date.data + dt.timedelta(2)
            counts = db.session.query(Transaction, Recipient).join(Recipient) \
                .filter_by(username=self.username)\
                .filter(Transaction.date >= early_window)\
                .filter(Transaction.date <= late_window)\
                .count()
            if counts >= 1:
                raise ValidationError(
                    'Only one delivery allowed per week')


class InvoiceForm(FlaskForm):
    invoice = FloatField('Amount')
    submit = SubmitField('Submit')
