import datetime as dt

import pandas as pd
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, RadioField, SelectField,
                     SelectMultipleField, StringField, SubmitField,
                     TextAreaField, widgets)
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app.models import Recipient, Volunteer, assign_user_type


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


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

        User = assign_user_type(current_user.username)
        user = User.query.filter_by(username=current_user.username).first()

        if not user.check_password(old_password.data):
            raise ValidationError('Incorrect password')


class DeliveryPreferencesForm(FlaskForm):

    delivery_days = ['Friday', 'Saturday']

    name = StringField('Preferred Name')
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    store = StringField('Store')
    grocery_list = TextAreaField('Grocery List')
    dropoff_day = SelectField('Delivery Day', choices=[
                              (x, x) for x in delivery_days])
    dropoff_notes = TextAreaField('Delivery Notes')
    payment_notes = TextAreaField('Payment Notes')
    submit = SubmitField('Save Preferences')


class TransactionForm(FlaskForm):

    store = StringField('Store')
    date = DateField('Date')
    grocery_list = TextAreaField('Specific Grocery List')
    dropoff_notes = TextAreaField('Specific Delivery Notes')
    submit = SubmitField('Book Delivery')

    def validate_date(self, date):
        if pd.to_datetime(date.data) - pd.Timedelta(days=1) <= dt.datetime.now():
            raise ValidationError(
                'Orders/modifications must be made at least one day in advance')
