import flask_login
from flask import redirect, request, url_for
from flask_admin.contrib.sqla import ModelView


class CustomModelView(ModelView):

    def is_accessible(self):
        return flask_login.current_user.is_authenticated and flask_login.current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class VolunteerView(ModelView):
    column_exclude_list = ['directory_listing', 'password_hash']
    column_searchable_list = ['name']
    can_export = True


class RecipientView(ModelView):
    column_exclude_list = ['directory_listing', 'password_hash']
    column_searchable_list = ['name', 'address']
    column_filters = ['name', 'address']
    can_export = True


class TransactionView(ModelView):
    column_exclude_list = ['list', 'notes']
    column_filters = ['store', 'recipient',
                      'volunteer', 'claimed', 'completed', 'paid']
    column_formatters = dict(volunteer=lambda v, c, m, p: m.volunteer.name if m.volunteer is not None else None,
                             recipient=lambda v, c, m, p: m.recipient.name if m.recipient is not None else None)
    can_edit = True
    can_view_details = True
    can_export = True
