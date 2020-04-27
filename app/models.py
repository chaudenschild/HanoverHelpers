import pandas as pd
from flask import url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


@login.user_loader
def load_user(username):
    User = assign_user_type(username)
    user = User.query.filter_by(username=username).first()
    return user


def assign_user_type(username, return_string=False):
    if db.session.query(Volunteer.query.filter(Volunteer.username == username).exists()).scalar():
        if return_string:
            return 'volunteer'
        return Volunteer

    elif db.session.query(Recipient.query.filter(Recipient.username == username).exists()).scalar():
        if return_string:
            return 'recipient'
        return Recipient


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

    def _conditional_row_color(self, x, color='red'):
        attr = f'background_color = {color}'
        return [attr for attr in range(len(x))]

    def make_html(self, drop_cols=['username', 'completed', 'paid']):
        self.df = self.df.drop(columns=['id'])
        if drop_cols:
            self.df = self.df.drop(columns=drop_cols)
        self.df = self.df.rename(columns=self.column_aliases)
        # self.df.style.apply(self._conditional_row_color, axis=1)

        return self.df.to_html(index=False, escape=False, formatters=self.formatters, classes=['table table-hover table-responsive display'])


def transaction_signup_view(completed=None, claimed=None):
    query_list = [Transaction.id,
                  Recipient.name,
                  Transaction.store,
                  Transaction.date,
                  Transaction.list,
                  Transaction.notes
                  ]

    if completed:
        filter_statement = Transaction.completed == True
    elif claimed is not None:
        filter_statement = Transaction.claimed == claimed

    query = db.session.query(*query_list).filter(filter_statement)

    table = Table(query)
    table.add_transaction_link_column('signup_transaction', 'Pickup')
    table.add_transaction_link_column('view_list', 'View List/Notes')

    return table.make_html(drop_cols=['list'])


class BaseUser(UserMixin):

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

    def get_transactions(self, completed, html=True):

        User, user_type = assign_user_type(self.username), assign_user_type(
            self.username, return_string=True)
        Counterpart = Volunteer if user_type == 'recipient' else Recipient
        counterpart_type = 'volunteer' if user_type == 'recipient' else 'recipient'

        query_list = [User.username,
                      Transaction.id,
                      Transaction.booking_date,
                      Transaction.date,
                      Transaction.store,
                      Transaction.notes,
                      Transaction.completed,
                      Transaction.paid,
                      Counterpart.name,
                      Counterpart.phone]

        if completed:
            query_list += [Transaction.invoice]

        query = db.session.query(*query_list)\
                          .join(Transaction, User.id == getattr(Transaction, f'{user_type}_id'))\
                          .outerjoin(Counterpart, getattr(Transaction, f'{counterpart_type}_id') == Counterpart.id) \
            .filter(User.username == self.username) \
            .filter(Transaction.completed == completed)

        table = Table(query)

        if completed:
            return table.return_as_completed()

        table.add_transaction_link_column('view_list', 'View List/Notes')

        if user_type == 'recipient':
            table.add_transaction_link_column('edit_transaction', 'Edit')
            table.add_transaction_link_column('cancel_transaction', 'Cancel')

        elif user_type == 'volunteer':
            table.add_transaction_link_column('mark_complete', 'Mark Complete')
            table.add_transaction_link_column('drop_transaction', 'Drop')

        return table.make_html()


class Recipient(BaseUser, db.Model):
    __tablename__ = 'recipient'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    address = db.Column(db.String)
    store = db.Column(db.String)
    grocery_list = db.Column(db.String)
    dropoff_day = db.Column(db.String)
    dropoff_notes = db.Column(db.String)
    payment_notes = db.Column(db.String)
    password_hash = db.Column(db.String(128))

    transactions = db.relationship('Transaction', back_populates='recipient')

    def print_payment_notes(self):
        return self.payment_notes.split('/n')

    def __repr__(self):
        return f"<Recipient(name='{self.name}', username='{self.username}')>"


class Volunteer(BaseUser, db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    password_hash = db.Column(db.String(128))

    transactions = db.relationship('Transaction', back_populates='volunteer')

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
    notes = db.Column(db.String)
    claimed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    invoice = db.Column(db.Float)
    paid = db.Column(db.Boolean, default=False)
    modification_count = db.Column(db.Integer, default=0)

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
        return self.list.split('\n')

    def print_notes(self):
        return self.notes.split('\n')

    def recipient_name(self):
        return self.recipient.name

    def __repr__(self):
        return f"Transaction(recipient={self.recipient}, volunteer={self.volunteer})"
