from flask_login import current_user
from flask import redirect, url_for, request, flash
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import func
from wtforms import SelectField, StringField, PasswordField
from models import db, User


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'Admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class UserAdminView(MyModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True

    column_list = ['id', 'username', 'role']
    column_searchable_list = ['username', 'role']
    column_exclude_list = ['password']  # Exclude password from being displayed

    # Form configuration
    form_columns = ['username', 'email', 'password']  # Specify form fields
    form_excluded_columns = ['password']  # Exclude the password from list view, not form

    # Define ALL form fields explicitly
    form_extra_fields = {
        'username': StringField('Username'),
        'email': StringField('email'),
        'password': PasswordField('Password'),
    }

    def get_query(self):
        """Override get_query to filter out Admin users from the list"""
        return self.session.query(self.model).filter(self.model.role != 'Admin')

    def get_count_query(self):
        """Override get_count_query to return a proper query object"""
        return self.session.query(func.count('*')).select_from(self.model).filter(self.model.role != 'Admin')

class PostAdminView(MyModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True

    column_list = ['id', 'user_id', 'text', 'timestamp']
    column_searchable_list = ['text']
    column_filters = ['user_id', 'timestamp']
    form_columns = ['user_id', 'text', 'image_data', 'image_mime_type']

class LikeAdminView(MyModelView):
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True

    column_list = ['id', 'user_id', 'post_id']
    column_filters = ['user_id', 'post_id']

class FollowAdminView(MyModelView):
    can_create = False  # Disabling creation since this is typically automatic
    can_edit = False    # Disabling edit to prevent unauthorized tampering
    can_delete = True   # Allow deletion for cleanup purposes
    can_export = True

    column_list = ['id', 'follower_id', 'followed_id', 'timestamp']
    column_filters = ['follower_id', 'followed_id', 'timestamp']

class GameSessionView(MyModelView):
    can_create = False
    can_edit = False
    can_delete = True
    column_list = ['id', 'player1_id', 'player1.username', 'player2_id', 'player2.username',
                   'player1_joined', 'player2_joined', 'status', 'winner.username']

class SignoutView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('logout'))