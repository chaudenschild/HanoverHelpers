from app import app, db
from app.models import Recipient, Transaction, Volunteer


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Recipient': Recipient, 'Volunteer': Volunteer, 'Transaction': Transaction}
