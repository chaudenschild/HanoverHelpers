import datetime as dt
import time

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
        Transaction.date >= dt.datetime.today().date()).filter(Transaction.date < next_week_cutoff).filter(Transaction.claimed == True).all()

    with app.app_context():
        count = 0
        for transaction in transactions:
            print(f'{transaction.volunteer.name}, {transaction.recipient.name}')
            print(f'count = {count}')
            time.sleep(2)
            try:
                send_confirmation(transaction.volunteer,
                                  'volunteer_reminder', transaction)
                count += 1
            except Exception:
                print('exception raised')
                continue


sched.start()
