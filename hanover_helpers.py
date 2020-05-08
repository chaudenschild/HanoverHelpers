from app import app, db
from app.admin_utils import TransactionView
from app.models import Recipient, Transaction, UserDirectory, Volunteer


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'UserDirectory': UserDirectory, 'Recipient': Recipient, 'Volunteer': Volunteer, 'Transaction': Transaction, 'TransactionView': TransactionView}
