import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hanover-helpers-admin'

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASIC_AUTH_USERNAME = 'milo'
    BASIC_AUTH_PASSWORD = 'numberonehelper'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['hanoverhelpers@gmail.com']
    CUTOFF_DAYTIME = {'Day': 3, 'Hour': 18}  # Thursday 6PM
    RECIPIENT_EMAIL_SEND_TIME = {'timezone': 'America/New_York',
                                 'day_of_week': 'thu', 'hour': '1', 'minute': '40-44/1'}  # Should be friday 6am; different for debugging


# Set environment vars for local testing
'''
(venv) $ export MAIL_SERVER=smtp.googlemail.com
(venv) $ export MAIL_PORT=587
(venv) $ export MAIL_USE_TLS=1
(venv) $ export MAIL_USERNAME=<your-gmail-username> + the @gmail.com
(venv) $ export MAIL_PASSWORD=<your-gmail-password>
'''
