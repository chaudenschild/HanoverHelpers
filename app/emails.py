import os
from threading import Thread

from flask import render_template
from flask_mail import Message

from app import app, mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body, sender=None):

    if os.environ.get('EMAIL') == 'off':  # for debug mode
        pass
    else:
        if sender is not None:
            msg = Message(subject, sender=sender, recipients=recipients)
        else:
            msg = Message(subject, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset(user):
    token = user.get_reset_password_token()
    send_email('Hanover Helpers Password Reset',
               recipients=[user.email],
               text_body=render_template('email/reset_password_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password_email.html',
                                         user=user, token=token))


def send_confirmation(user, confirmation_type, transaction):
    date_str = transaction.date.strftime('%A, %m/%d')
    if confirmation_type == 'recipient_booking':
        template = 'recipient_booking_confirmation'
        subject = f'Delivery confirmed for {date_str}'
    elif confirmation_type == 'recipient_modification':
        template = 'recipient_modification_confirmation'
        subject = f'Modification confirmed for {date_str} delivery'
    elif confirmation_type == 'volunteer_claimed':
        template = 'volunteer_claimed_confirmation'
        subject = f'Delivery claimed for {date_str}'
    elif confirmation_type == 'volunteer_reminder':
        template = 'volunteer_reminder'
        subject = f'Delivery reminder for {transaction.recipient.name}, {date_str}'
    elif confirmation_type == 'volunteer_buddy':
        template = 'volunteer_buddy_alert'
        subject = f'Your HH buddy booked a delivery'
    send_email(subject,
               recipients=[user.email],
               text_body=render_template(f'email/{template}.txt',
                                         user=user, date=date_str, transaction=transaction),
               html_body=render_template(f'email/{template}.html',
                                         user=user, date=date_str, transaction=transaction))
