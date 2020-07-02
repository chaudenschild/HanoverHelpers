import os

from dotenv import load_dotenv
from flask import url_for

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

    FLASK_ADMIN_SWATCH = 'yeti'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    CUTOFF_DAYTIME = {'Day': 3, 'Hour': 18}  # Thursday 6PM
    # Default Friday 6am
    VOLUNTEER_EMAIL_SEND_TIME = {
        'day_of_week': 'fri', 'hour': 6, 'minute': 0}
    STORE_LIST = ['Hanover Coop', 'Hanover Coop Curbside Pickup', 'Lebanon Coop', "Hannaford's",
                  'CVS', "BJ's", "BJ's Curbside Pickup", 'NH Liquor Outlet', 'Price Chopper']
    PAYMENT_TYPE = ['Kendal Invoice',
                    'Coop Charge Account (Specify Account # in Payment Notes)', 'Other']

    IMAGE_UPLOAD_FOLDER = 'receipt_images'  # must be within static folder

    EMAIL_VALIDATOR_EXEMPT = ['cch360@gmail.com', 'dcurran@kah.kendal.org']


# Set environment vars for email local testing
'''
(venv) $ export MAIL_SERVER=smtp.googlemail.com
(venv) $ export MAIL_PORT=587
(venv) $ export MAIL_USE_TLS=1
(venv) $ export MAIL_USERNAME=<your-gmail-username> + the @gmail.com
(venv) $ export MAIL_PASSWORD=<your-gmail-password>
'''

# Local postgres
'''
export DATABASE_URL='postgresql:///hanover_helpers'
'''

# postgres commands to pipe from heroku directly to local db
'''
heroku run 'pg_dump -xO $DATABASE_URL' | psql hanover_helpers
'''
