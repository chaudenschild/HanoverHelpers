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
