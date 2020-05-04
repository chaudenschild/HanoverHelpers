import time
from hashlib import md5

import jwt
import pandas as pd
from flask import url_for
from flask_login import UserMixin
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db, login


@login.user_loader
def load_user(userdir_id):
    user = get_user_by_userdir_id(userdir_id)
    if user is None:
        return
    return user


def get_user_by_userdir_id(userdir_id):
    userdir = db.session.query(UserDirectory).filter_by(
        id=userdir_id).first()
    if userdir is None:
        return
    if userdir.user_type == 'volunteer':
        User = Volunteer
    elif userdir.user_type == 'recipient':
        User = Recipient

    return User.query.filter_by(userdir_id=userdir_id).first()


class Table():
    column_aliases = {'name': 'Name',
                      'store': 'Store',
                      'phone': 'Phone',
                      'booking_date': 'Booking Date',
                      'date': 'Delivery Date',
                      'notes': 'Notes'}

    def __init__(self, query):
        self.query = query
        self.df = pd.read_sql(query.statement, db.session.bind)
        self.formatters = {'Delivery Date': lambda x: '<b>' + str(x) + '</b>',
                           'List': Table._add_autoscroll,
                           'Notes': Table._add_autoscroll}

    def add_column_alias(self, k, v):
        self.column_aliases[k] = v

    def add_formatter(self, k, v):
        self.formatters[k] = v

    def add_transaction_link_column(self, route, label):
        self.df[label] = self.df['id']
        self.formatters[label] = lambda x: Table._link(
            url_for(route, transaction_id=int(x)), label)

    def return_as_completed(self):
        # no hyperlinks, no id column
        self.df = self.df.drop(columns=['id', 'username'])
        self.add_column_alias('invoice', 'Invoice')
        self.df = self.df.rename(columns=self.column_aliases)
        return self.df.to_html(index=False, escape=False, formatters=self.formatters, classes=['table table-hover table-responsive display'])

    @classmethod
    def _add_autoscroll(cls, x):
        return '<div style="overflow:scroll; height:75px;">' + x + '</div>'

    @classmethod
    def _link(cls, href, label):
        return '<a href="' + href + '">' + label + '</a>'

    def make_html(self, drop_cols=['username']):
        self.df = self.df.drop(columns=['id'])
        if drop_cols:
            self.df = self.df.drop(columns=drop_cols)
        self.df = self.df.rename(columns=self.column_aliases)

        return self.df.to_html(index=False, escape=False, formatters=self.formatters, classes=['table table-hover table-responsive display'])


def transaction_signup_view(completed=None, claimed=None):
    query_list = [Transaction.id,
                  Recipient.name,
                  Transaction.store,
                  Transaction.date,
                  Transaction.notes
                  ]

    if completed:
        filter_statement = Transaction.completed == True
    elif claimed is not None:
        filter_statement = Transaction.claimed == claimed

    query = db.session.query(
        *query_list).join(Recipient).filter(filter_statement)

    table = Table(query)
    table.add_transaction_link_column('signup_transaction', 'Pickup')
    table.add_transaction_link_column('view_list', 'View List/Notes')

    return table.make_html(drop_cols=None)


class UserDirectory(db.Model):
    __tablename__ = 'userdirectory'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String(64), unique=True)
    user_type = db.Column(db.String())

    def __repr__(self):
        return f"<User(username='{self.username}', user_name='{self.user_type}')>"


class BaseUser(UserMixin):

    @property
    def user_type(self):
        return self.directory_listing.user_type

    @user_type.setter
    def user_type(self, type):
        dir_listing = db.session.query(
            UserDirectory).filter_by(id=self.userdir_id).first()
        if dir_listing is None:
            new_listing = UserDirectory(username=self.username, user_type=type)
            self.directory_listing = new_listing
            db.session.add(new_listing)
            db.session.commit()
        else:
            self.directory_listing.user_type = type

    def user_table(self):
        if self.user_type == 'volunteer':
            return Volunteer
        elif self.user_type == 'recipient':
            return Recipient

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id,
             'user_type': self.user_type,
             'exp': time.time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):

        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
            user_type = jwt.decode(token, app.config['SECRET_KEY'],
                                   algorithms=['HS256'])['user_type']
        except:
            return

        User = Volunteer if user_type == 'volunteer' else Recipient

        return User.query.get(id)

    def get_id(self):
        return self.userdir_id

    def get_transactions(self, completed, html=True):

        User = self.user_table()
        Counterpart = Volunteer if self.user_type == 'recipient' else Recipient
        counterpart_type = 'volunteer' if self.user_type == 'recipient' else 'recipient'

        query_list = [User.username,
                      Transaction.id,
                      Transaction.booking_date,
                      Transaction.date,
                      Transaction.store,
                      Counterpart.name,
                      Counterpart.phone]

        if completed:
            query_list += [Transaction.invoice]

        query = db.session.query(*query_list)\
                          .join(Transaction, User.id == getattr(Transaction, f'{self.user_type}_id'))\
                          .outerjoin(Counterpart, getattr(Transaction, f'{counterpart_type}_id') == Counterpart.id) \
            .filter(User.username == self.username) \
            .filter(Transaction.completed == completed) \
            .order_by(desc(Transaction.date))

        table = Table(query)

        if completed:
            return table.return_as_completed()

        table.add_transaction_link_column('view_list', 'View List/Notes')

        if self.user_type == 'recipient':
            table.add_transaction_link_column('edit_transaction', 'Edit')
            table.add_transaction_link_column('cancel_transaction', 'Cancel')
            table.add_column_alias('name', 'Volunteer Name')
            table.add_column_alias('phone', 'Volunteer Phone')

        elif self.user_type == 'volunteer':
            table.add_transaction_link_column('mark_complete', 'Mark Complete')
            table.add_transaction_link_column('drop_transaction', 'Drop')
            table.add_column_alias('name', 'Recipient Name')
            table.add_column_alias('phone', 'Recipient Phone')

        return table.make_html()


class Recipient(BaseUser, db.Model):
    __tablename__ = 'recipient'
    id = db.Column(db.Integer, primary_key=True)
    userdir_id = db.Column(db.Integer, db.ForeignKey(
        'userdirectory.id'), unique=True)
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    address = db.Column(db.String)
    address_notes = db.Column(db.String)
    password_hash = db.Column(db.String(128))

    transactions = db.relationship('Transaction', back_populates='recipient')
    directory_listing = db.relationship('UserDirectory',
                                        uselist=False, cascade='delete')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_type = 'recipient'

    def __repr__(self):
        return f"<Recipient(name='{self.name}', username='{self.username}')>"


class Volunteer(BaseUser, db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    userdir_id = db.Column(db.Integer, db.ForeignKey(
        'userdirectory.id'), unique=True)
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean, default=False)

    transactions = db.relationship('Transaction', back_populates='volunteer')
    directory_listing = db.relationship('UserDirectory',
                                        uselist=False, cascade='delete')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_type = 'volunteer'

    def is_admin(self):
        return self.admin

    def __repr__(self):
        return f"<Volunteer(name='{self.name}', username='{self.username}')>"


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'))
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'))
    store = db.Column(db.String)
    booking_date = db.Column(db.Date, index=True)
    date = db.Column(db.Date, index=True)
    list = db.Column(db.String)
    payment_type = db.Column(db.String)
    payment_notes = db.Column(db.String)
    notes = db.Column(db.String)
    claimed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    invoice = db.Column(db.Float)
    paid = db.Column(db.Boolean, default=False)
    tip = db.Column(db.Float)

    recipient = db.relationship('Recipient', back_populates='transactions')

    volunteer = db.relationship('Volunteer', back_populates='transactions')

    def assign_recipient(self, recipient):
        self.recipient = recipient
        self.recipient_id = recipient.id

    def assign_volunteer(self, volunteer):
        self.volunteer = volunteer
        self.volunteer_id = volunteer.id
        self.claimed = True

    def drop_volunteer(self):
        self.volunteer = None
        self.volunteer_id = None
        self.claimed = False

    def mark_as_completed(self):
        self.completed = True

    def mark_as_paid(self):
        self.paid = True

    def set_invoice(self, amount):
        self.invoice = amount

    def print_list(self):
        return self.list.split('\n') if self.list else ''

    def __repr__(self):
        return f"Transaction(recipient={self.recipient}, volunteer={self.volunteer})"
