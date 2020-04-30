import datetime as dt

from apscheduler.schedulers.blocking import BlockingScheduler
from flask import render_template

from app import app, db
from app.emails import send_email
from app.models import Transaction, Volunteer

sched = BlockingScheduler()


# Cron job that sends volunteers their delivery details at specified time (Friday morning 6am)
@sched.scheduled_job('cron', **app.config['RECIPIENT_EMAIL_SEND_TIME'])
def send_recipient_email():
    print(f'chron_job triggered {dt.datetime.now()}')
    # Transactions this week must have dates earlier than next Thursday 6PM.
    d = dt.datetime.today()
    while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
        d += dt.timedelta(1)
    next_week_cutoff = dt.datetime(d.year, d.month, d.day,
                                   app.config['CUTOFF_DAYTIME']['Hour'])
    next_week_cutoff = dt.datetime(2020, 5, 3)
    transactions = Transaction.query.filter(
        Transaction.date >= dt.datetime.today()).filter(Transaction.date < next_week_cutoff).filter(Transaction.claimed == True).all()

    for transaction in transactions:

        date_str = transaction.date.strftime('%A, %m/%d')
        subject = f'Delivery for {transaction.recipient.name} on {date_str}'
        print(app.config['ADMINS'][0])
        print(transaction.volunteer.email)
        print(transaction.recipient)

        with app.app_context():
            send_email(subject,
                       sender=app.config['ADMINS'][0],
                       recipients=[transaction.volunteer.email],
                       text_body=render_template(
                           'email/volunteer_reminder.txt', date=date_str, transaction=transaction),
                       html_body=render_template('email/volunteer_reminder.html', date=date_str, transaction=transaction))


sched.start()
