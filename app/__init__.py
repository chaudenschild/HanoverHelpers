import flask_login
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
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
mail = Mail(app)

from app import models, routes


class AuthenticatedModelView(ModelView):
    """
    This is an awful hack to protect the admin page for now.
    TODO(thomas): do this in a more secure way.
    """

    def is_accessible(self):
        return flask_login.current_user.is_authenticated and flask_login.current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


admin.add_view(AuthenticatedModelView(models.Volunteer, db.session))
admin.add_view(AuthenticatedModelView(models.Recipient, db.session))
admin.add_view(AuthenticatedModelView(models.Transaction, db.session))
