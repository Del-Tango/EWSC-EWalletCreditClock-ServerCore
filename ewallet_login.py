import time
import datetime
import random
import hashlib
import logging
import pysnooper
from validate_email import validate_email
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from base.res_user import ResUser
from base.credit_wallet import CreditEWallet
from base.contact_list import ContactList
from base.res_utils import ResUtils, Base
from base.config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class EWalletLogin(Base):
    __tablename__ = 'ewallet_login'

    login_id = Column(Integer, primary_key=True)

    def hash_password(self, password):
        log.debug('')
        return str(hashlib.sha256(password.encode()).hexdigest())

#   @pysnooper.snoop()
    def check_user_name_exists(self, user_name, user_archive):
        log.debug('')
        for item in user_archive:
            if user_archive[item].user_name == user_name:
                return user_archive[item]
        return False

#   @pysnooper.snoop()
    def check_user_pass_hash(self, user_pass, known_hash):
        log.debug('')
        _pass_hash = self.hash_password(user_pass)
        if str(_pass_hash) == str(known_hash):
            return True
        return False

#   @pysnooper.snoop()
    def authenticate_user(self, **kwargs):
        log.debug('')
        _user = self.check_user_name_exists(
                kwargs['user_name'], user_archive=kwargs.get('user_archive')
                )
        if not _user:
            return self.warning_user_name_not_found()
        _pass_check = self.check_user_pass_hash(
                kwargs['user_pass'], _user.fetch_user_pass_hash()
                )
        if not _pass_check:
            return self.warning_user_password_incorrect()
        return _user

    def action_login(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return self.error_handler_action_login(
                    user_name=kwargs.get('user_name'),
                    user_pass=kwargs.get('user_pass'),
                    )
        _authenticated_user = self.authenticate_user(**kwargs)
        if not _authenticated_user:
            return self.error_invalid_login_credentials()
        return _authenticated_user

    def action_create_new_account(self, **kwargs):
        log.debug('')
        _ewallet_new_user = EWalletCreateUser()
        _new_user = _ewallet_new_user.action_create_new_user(**kwargs)
        if not _new_user:
            return self.warning_could_not_create_new_user_account()
        return _new_user

    def ewallet_login_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_login_controller_action_specified()
        _handlers = {
                'login': self.action_login,
                'new_account': self.action_create_new_account,
                }
        return _handlers[kwargs['action']](**kwargs)

    def error_handler_action_login(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'user_name': kwargs.get('user_name'),
                    'user_pass': kwargs.get('user_pass'),
                    },
                'handlers': {
                    'user_name': self.error_no_user_name_found,
                    'user_pass': self.error_no_user_pass_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_no_user_name_found(self):
        log.error('No user name found.')
        return False

    def error_no_user_password_found(self):
        log.error('No user password found.')
        return False

    def error_no_login_controller_action_specified(self):
        log.error('No login controller action specified.')
        return False

    def error_invalid_login_credentials(self):
        log.error('Invalid login credentials.')
        return False

    def warning_could_not_create_new_user_account(self):
        log.warning(
                'Something went wrong. '
                'Could not create new user account.'
                )
        return False

    def warning_user_name_not_found(self):
        log.warning('No user found.')
        return False

    def warning_user_password_incorrect(self):
        log.warning('User password is incorrect.')
        return False


class EWalletCreateUser(EWalletLogin):

#   @pysnooper.snoop()
    def check_user_name_ensure_one(self, user_name, user_archive):
        log.debug('')
        if not user_archive:
            return True
        print(user_archive)
        _existing_user_name = [
                item for item in user_archive
                if user_archive[item].user_name == user_name
                ]
        if not _existing_user_name:
            return True
        return False

    def check_user_pass_length(self, user_pass):
        log.debug('')
        if len(user_pass) < 8:
            return self.warning_invalid_user_password_length()
        return True

    def check_user_pass_letters(self, user_pass):
        log.debug('')
        lower_case = 'abcdefghijklmnopqrstuvwxyz'
        upper_case = lower_case.upper()
        for item in list(user_pass):
            if item in lower_case or item in upper_case:
                return True
        return False

    def check_user_pass_numbers(self, user_pass):
        log.debug('')
        numbers = '1234567890'
        for item in list(user_pass):
            if item in numbers:
                return True
        return False

    def check_user_pass_symbols(self, user_pass):
        log.debug('')
        symbols = '!@#$%^&*()_+[]{};.<>/?\\|-='
        for item in list(user_pass):
            if item in symbols:
                return True
        return False

    def check_user_pass_characters(self, user_pass):
        log.debug('')
        _checks = {
                'letters': self.check_user_pass_letters(user_pass),
                'numbers': self.check_user_pass_numbers(user_pass),
                'symbols': self.check_user_pass_symbols(user_pass),
                }
        if False in _checks.values():
            return self.warning_invalid_user_password_characters()
        return True

    def check_user_pass(self, user_pass):
        log.debug('')
        _checks = {
                'length': self.check_user_pass_length(user_pass),
                'characters': self.check_user_pass_characters(user_pass),
                }
        if False in _checks.values():
            return False
        return True

    def check_user_email_is_valid(self, user_email):
        log.debug('')
        return validate_email(user_email)

    # [ NOTE ]: Requires pydns
    def check_user_email_host_has_smtp(self, user_email):
        log.debug('')
        return validate_email(user_email, check_mx=True)

    # [ NOTE ]: Requires pydns
    def check_user_email_host_smtp_has_address(self, user_email):
        log.debug('')
        return validate_email(user_email, verify=True)

    def check_user_email(self, user_email, severity=None):
        log.debug('')
        _severity_handlers = {
                1: self.check_user_email_is_valid,
                2: self.check_user_email_host_has_smtp,
                3: self.check_user_email_host_smtp_has_address,
                }
        if not severity:
            return _severity_handlers[1](user_email)
        if severity not in _severity_handlers.keys():
            return self.error_invalid_user_email_check_severity()
        return _severity_handlers[severity](user_email)

    def perform_new_user_checks(self, **kwargs):
        log.debug('')
        _checks = {
                'user_name': self.check_user_name_ensure_one(
                    kwargs['user_name'], kwargs.get('user_archive')
                    ),
                'user_pass': self.check_user_pass(
                    kwargs['user_pass']
                    ),
                'user_email': self.check_user_email(
                    kwargs['user_email'], severity=1
                    ),
                }
        return _checks

    def create_res_user(self, **kwargs):
        log.debug('')
        _new_user = ResUser(
                user_name=kwargs['user_name'],
                user_pass_hash=self.hash_password(kwargs['user_pass']),
                user_email=kwargs['user_email'],
                user_phone=kwargs.get('user_phone'),
                user_alias=kwargs.get('user_alias'),
                )
        return _new_user

    def action_create_new_user(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return self.error_handler_action_create_new_user(
                    user_name=kwargs.get('user_name'),
                    user_pass=kwargs.get('user_pass'),
                    )
        _parameter_checks = self.perform_new_user_checks(**kwargs)
        if False in _parameter_checks.values():
            return self.warning_handler_action_create_new_user(
                    parameter_checks=_parameter_checks
                    )
        _new_user = self.create_res_user(**kwargs)
        return _new_user

    def warning_handler_action_create_new_user(self, **kwargs):
        _handlers = {
                'user_name': self.warning_duplicate_user_name,
                'user_pass': self.warning_invalid_user_pass,
                'user_email': self.warning_invalid_user_email,
                }
        _warning_type = [
                item for item in kwargs['parameter_checks']
                if not kwargs['parameter_checks'][item]
                ]
        return _handlers[_warning_type[0]]()

    def error_handler_action_create_new_user(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'user_name': kwargs.get('user_name'),
                    'user_pass': kwargs.get('user_pass'),
                    },
                'handlers': {
                    'user_name': self.error_no_user_name_found,
                    'user_pass': self.error_no_user_pass_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_no_user_name_found(self):
        log.error('No user name found.')
        return False

    def error_no_user_password_found(self):
        log.error('No user password found.')
        return False

    def error_invalid_user_email_check_severity(self):
        log.error('Invalid user email check severity.')
        return False

    def warning_duplicate_user_name(self):
        log.warning('Invalid user name. Already taken.')
        return False

    def warning_invalid_user_pass(self):
        log.warning(
            'Invalid password. '
            'Please make sure password corresponds with security standards.'
            )
        return False

    def warning_invalid_user_email(self, **kwargs):
        log.warning(
            'Invalid email address. Please choose a valid email address.'
            )
        return False

    def warning_invalid_user_password_characters(self):
        log.warning(
                'Invalid user password. '
                'Characters do not corespond to security standards.'
                )
        return False

    def warning_invalid_user_password_length(self):
        log.warning(
                'Invalid user password. '
                'Length does not corespond to security standards.'
                )
        return False


###############################################################################
# CODE DUMP
###############################################################################

#   # TODO: Uncalled
#   def check_user_pass_strength(self, user_pass):
#       _values = {'msg': str(), 'verdict': False}
#       _strong_regex = '((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*]).{8,30})'
#       _weak_regex = '((\d*)([a-z]*)([A-Z]*)([!@#$%^&*]*).{8,30})'
#       if len(user_pass) >= 8:
#           if bool(re.match(_strong_regex, user_pass)) == True:
#               _values.update({
#                   'msg': 'The password is strong',
#                   'verdict': True,
#               })
#           elif bool(re.match(_weak_regex, user_pass)) == True:
#               _values.update({
#                   'msg': 'Weak password.',
#                   'verdict': True,
#               })
#       else:
#           _values.update({
#               'msg': 'Invalid password.',
#               'verdict': False,
#           })
#       return _values

