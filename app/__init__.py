from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bootstrap import Bootstrap

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
basic_auth = BasicAuth(app)
admin = Admin(app, name='hanover-helpers', template_mode='bootstrap3')
bootstrap = Bootstrap(app)

from app import models, routes

admin.add_view(ModelView(models.Volunteer, db.session))
admin.add_view(ModelView(models.Recipient, db.session))
admin.add_view(ModelView(models.Transaction, db.session))
