import flask_login
from flask import Flask
from flask_admin import Admin
from flask_basicauth import BasicAuth
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
basic_auth = BasicAuth(app)
admin = Admin(app, name='Hanover Helpers Admin', template_mode='bootstrap3')
bootstrap = Bootstrap(app)
mail = Mail(app)

from app import models, routes, admin_utils

admin.add_view(admin_utils.VolunteerView(models.Volunteer, db.session))
admin.add_view(admin_utils.RecipientView(models.Recipient, db.session))
admin.add_view(admin_utils.TransactionView(models.Transaction, db.session))
