import datetime as dt

from apscheduler.scheduler import Scheduler
from flask import render_template

from app import app, db
from app.emails import send_email
from app.models import Transaction, Volunteer

sched = Scheduler()
sched.start()

# Cron job that sends volunteers their delivery details at specified time (Friday morning 6am)


def send_recipient_email(user, transaction):
    print(f'chron_job triggered {dt.datetime.now()}')
    # Transactions this week must have dates earlier than next Thursday 6PM.
    d = dt.datetime.today()
    while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
        d += dt.timedelta(1)
    next_week_cutoff = dt.datetime(d.year, d.month, d.day,
                                   app.config['CUTOFF_DAYTIME']['Hour'])
    next_week_cutoff = dt.datetime(2020, 5, 3)
    transactions = db.session.query(Transaction).join(Volunteer).filter(
        Transaction.date >= dt.datetime.today()).filter(Transaction.date < next_week_cutoff)

    for transaction in transactions:

        date_str = transaction.date.strftime('%A, %m/%d')
        subject = f'Delivery for {transaction.recipient.name} on {date_str}'

        send_email(subject,
                   sender=app.config['ADMINS'][0],
                   recipients=[transaction.volunteer.email],
                   text_body=render_template(
                       'email/volunteer_reminder.txt', user=transaction.volunteer, date=date_str, transaction=transaction),
                   html_body=render_template('email/volunteer_reminder.html',
                                             user=transaction.volunteer, date=date_str, transaction=transaction))


sched.add_cron_job(send_recipient_email, **
                   app.config['RECIPIENT_EMAIL_SEND_TIME'])
