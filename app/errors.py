from flask import render_template

from app import app, db


@app.errorhandler(404)
def fnf_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/404.html'), 403
