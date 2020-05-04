import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hanover-helpers-admin'

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASIC_AUTH_USERNAME = 'milo'
    BASIC_AUTH_PASSWORD = 'numberonehelper'

    FLASK_ADMIN_SWATCH = 'yeti'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['hanoverhelpers@gmail.com']
    CUTOFF_DAYTIME = {'Day': 3, 'Hour': 18}  # Thursday 6PM
    # Should be friday 6am; different for debugging
    VOLUNTEER_EMAIL_SEND_TIME = {
        'day_of_week': 'fri', 'hour': 6, 'minute': 0}
    STORE_LIST = ['Hanover Coop', 'Lebanon Coop', "Hannaford's",
                  'CVS', "BJ's", 'NH Liquor Outlet']
    PAYMENT_TYPE = ['Check', 'Paypal',
                    'Coop Charge Account (Specify Account # in Payment Notes)', 'Other (Specify in Payment Notes)']
    IMAGE_UPLOAD_FOLDER = os.path.join(basedir, 'static/receipt_images')


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
export DATASE_URL='postgresql:///hanover_helpers'
'''

# postgres commands to pipe from heroku directly to local db
'''
heroku run 'pg_dump -xO $DATABASE_URL' | psql hanover_helpers
'''
