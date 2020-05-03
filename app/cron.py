import datetime as dt

from apscheduler.schedulers.blocking import BlockingScheduler

from app import app
from app.emails import send_confirmation
from app.models import Transaction

sched = BlockingScheduler()


# Cron job that sends volunteers their delivery details at specified time (Friday morning 6am)
@sched.scheduled_job('cron', **app.config['VOLUNTEER_EMAIL_SEND_TIME'])
def send_recipient_email():
    print('email triggered')
    # Transactions this week must have dates earlier than next Thursday 6PM.
    d = dt.datetime.today()
    while d.weekday() != app.config['CUTOFF_DAYTIME']['Day']:
        d += dt.timedelta(1)
    next_week_cutoff = dt.datetime(d.year, d.month, d.day,
                                   app.config['CUTOFF_DAYTIME']['Hour'])

    transactions = Transaction.query.filter(
        Transaction.date >= dt.datetime.today().date() - dt.timedelta(2)).filter(Transaction.date < next_week_cutoff).filter(Transaction.claimed == True).all()
    print(f'length transactions = {len(transactions)}')
    with app.app_context():
        for transaction in transactions:
            vol = transaction.volunteer
            print(vol.email)
            if vol.email == 'alexandria.t.wood.tu20@tuck.dartmouth.edu':

                send_confirmation(vol,
                                  'volunteer_reminder', transaction)


sched.start()
