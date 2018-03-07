# encoding: utf-8

import airflow
from airflow import settings, configuration
from airflow.plugins_manager import AirflowPlugin
from airflow.www import utils as wwwutils
from airflow.utils.db import provide_session
from flask import Blueprint
from flask_login import flash
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_admin.contrib.sqla.view import func
from wtforms import PasswordField

from dcmp.auth.models import DcmpUserProfile


class AirflowModelView(ModelView):
    list_template = 'airflow/model_list.html'
    edit_template = 'airflow/model_edit.html'
    create_template = 'airflow/model_create.html'
    column_display_actions = True
    page_size = 500

# 只有超级用户有权限
class DcmpUserProfileModelView(wwwutils.SuperUserMixin, AirflowModelView):
    verbose_name = "User Privilege"
    verbose_name_plural = "User Privilege"
    column_default_sort = 'user_id'
    can_create = False
    can_delete = False
    column_list = ('username', 'is_superuser', 'is_data_profiler', 'is_approver', 'approval_notification_emails', 'updated_at', )
    column_filters = ('is_superuser', 'is_data_profiler', 'is_approver', 'updated_at', )
    form_columns = ('is_superuser', 'is_data_profiler', 'is_approver', 'approval_notification_emails', )

    @action('set_is_superuser', "Set Superuser", None)
    def action_set_is_superuser(self, ids):
        self.set_profiles(ids, "is_superuser", True)

    @action('unset_is_superuser', "Unset Superuser", None)
    def action_unset_is_superuser(self, ids):
        self.set_profiles(ids, "is_superuser", False)

    @action('set_is_data_profiler', "Set Data Profiler", None)
    def action_set_is_data_profiler(self, ids):
        self.set_profiles(ids, "is_data_profiler", True)

    @action('unset_is_data_profiler', "Unset Data Profiler", None)
    def action_unset_is_data_profiler(self, ids):
        self.set_profiles(ids, "is_data_profiler", False)

    @action('set_is_approver', "Set Approver", None)
    def action_set_is_approver(self, ids):
        self.set_profiles(ids, "is_approver", True)

    @action('unset_is_approver', "Unset Approver", None)
    def action_unset_is_approver(self, ids):
        self.set_profiles(ids, "is_approver", False)

    @provide_session
    def set_profiles(self, ids, key, value, session=None):
        try:
            count = 0
            for profile in session.query(DcmpUserProfile).filter(DcmpUserProfile.id.in_(ids)).all():
                count += 1
                setattr(profile, key, value)
            session.commit()
            flash("{count} profiles '{key}' were set to '{value}'".format(**locals()))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise Exception("Ooops")
            flash('Failed to set {key}'.format(**locals()), 'error')


dcmp_user_profile_model_view = DcmpUserProfileModelView(DcmpUserProfile, settings.Session, category="Admin", name="User Privilege")

if configuration.get('webserver', 'auth_backend').endswith('dcmp.auth.backends.password_auth'):
    from dcmp.auth.backends.password_auth import PasswordUser
    
    # 
    class PasswordUserModelView( wwwutils.SuperUserMixin,AirflowModelView):
        verbose_name = "User Manager"
        verbose_name_plural = "User Manager"
        column_default_sort = 'username'
        column_list = ('username', 'email', )
        form_columns = ('username', 'email', 'password', )
        form_overrides = dict(_password=PasswordField)
        can_create = True

        # 增加限制，非超级用户只能看到自己用户的
        def get_query(self):
            if wwwutils.get_filter_by_user():
                curr_user = airflow.login.current_user
                return self.session.query(self.model).filter(self.model.username == curr_user.user.username )
            else:
                return self.session.query(self.model)
        # 增加限制，非超级用户只能看到自己用户的
        def get_count_query(self):
            if wwwutils.get_filter_by_user():
                curr_user = airflow.login.current_user
                return self.session.query(func.count('*')).filter( self.model.username == curr_user.user.username)
            else:
                return self.session.query(func.count('*'))
    
    password_user_model_view = PasswordUserModelView(PasswordUser, settings.Session, category="Admin", name="User Manager")
    
    class DcmpUserProfilePlugin(AirflowPlugin):
        name = "dcmp_user_profile"
        operators = []
        flask_blueprints = []
        hooks = []
        executors = []
        admin_views = [password_user_model_view, dcmp_user_profile_model_view]
        menu_links = []
