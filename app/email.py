from flask import render_template
from flask_mail import Message

from app import app, mail


def send_email(subject, recipients, text_body, html_body, sender=None):
    if sender is not None:
        msg = Message(subject, sender=sender, recipients=recipients)
    else:
        msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset(user):
    token = user.get_reset_password_token()
    send_email('Hanover Helpers Password Reset',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password_email.html',
                                         user=user, token=token))


def send_booking_confirmation(user, transaction):
    date_str = transaction.date.strftime('%m/%d')
    subject = f'Delivery confirmed for {date_str}'
    send_email(subject,
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/recipient_notification.txt',
                                         user=user, date=date_str),
               html_body=render_template('email/recipient_notification.html',
                                         user=user, date=date_str))
# TODO: volunteer notification


# TODO: recipient notifications
# book delivery
# order picked up
# Change order
# delivery status changed
