import pandas as pd
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


class Recipient(UserMixin, db.Model):
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

    def get_transactions(self, completed, table_id, html=True):

        query_list = [Recipient.username,
                      Volunteer.name,
                      Volunteer.phone,
                      Transaction.booking_date,
                      Transaction.date,
                      Transaction.list,
                      Transaction.notes]

        column_aliases = {'name': 'Volunteer Name',
                          'phone': 'Volunteer Phone',
                          'booking_date': 'Booking Date',
                          'date': 'Delivery Date',
                          'list': 'List',
                          'notes': 'Notes'}

        if completed:
            query_list += [Transaction.invoice]
            column_aliases['invoice'] = 'Invoice'

        query = db.session.query(*query_list) \
                          .join(Transaction,
                                Recipient.id == Transaction.recipient_id) \
                          .outerjoin(Volunteer,
                                     Transaction.volunteer_id == Volunteer.id) \
                          .filter(Recipient.username == self.username) \
                          .filter(Transaction.completed == completed)

        df = pd.read_sql(query.statement, db.session.bind)
        df = df.drop(columns='username')
        df = df.rename(columns=column_aliases)

        if html:
            df = self._make_html(df, table_id)

        return df

    def _make_html(self, df, table_id):
        df[''] = 'Edit'

        def add_autoscroll(x):
            return '<div style="overflow:scroll; height:100px;">' + x + '</div>'

        formatters = {'Delivery Date': lambda x: '<b>' + str(x) + '</b>',
                      'Edit': lambda x: '<a href="None">Edit</a>',
                      'List': add_autoscroll,
                      'Notes': add_autoscroll}

        return df.to_html(index=False, table_id=table_id, escape=False, formatters=formatters, classes=['table table-hover table-responsive display'])

    def __repr__(self):
        return f"<Recipient(name='{self.name}', username='{self.username}')>"


class Volunteer(UserMixin, db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    password_hash = db.Column(db.String(128))

    transactions = db.relationship('Transaction', back_populates='volunteer')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

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

    recipient = db.relationship('Recipient', back_populates='transactions')

    volunteer = db.relationship('Volunteer', back_populates='transactions')

    def assign_recipient(self, recipient):
        self.recipient = recipient
        self.recipient_id = recipient.id

    def assign_volunteer(self, volunteer):
        self.volunteer = volunteer
        self.volunteer_id = volunteer.id
        self.claimed = True

    def close(self):
        self.completed = True

    def set_invoice(self, amount):
        self.invoice = amount

    def __repr__(self):
        return f"Transaction(recipient={self.recipient}, volunteer={self.volunteer})"
