import time
import datetime
import random
import hashlib
from validate_email import validate_email
import pysnooper

from base.res_user import ResUser
from base.credit_wallet import CreditEWallet
from base.contact_list import ContactList
from base.system.config import Config


class EWalletLogin():

    def hash_password(self, password):
        return str(hashlib.sha256(password.encode()).hexdigest())

#   @pysnooper.snoop()
    def check_user_name_exists(self, user_name, user_archive):
        for item in user_archive:
            if user_archive[item].user_name == user_name:
                return user_archive[item]
        return False

#   @pysnooper.snoop()
    def check_user_pass_hash(self, user_pass, known_hash):
        _pass_hash = self.hash_password(user_pass)
        if str(_pass_hash) == str(known_hash):
            return True
        return False

#   @pysnooper.snoop()
    def authenticate_user(self, **kwargs):
        _user = self.check_user_name_exists(
                kwargs['user_name'], user_archive=kwargs.get('user_archive')
                )
        if not _user:
            return False
        _pass_check = self.check_user_pass_hash(
                kwargs['user_pass'], _user.fetch_user_pass_hash()
                )
        if not _pass_check:
            return False
        return _user

    def action_login(self, **kwargs):
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return self.error_login_no_credentials_found(**kwargs)
        _authenticated_user = self.authenticate_user(**kwargs)
        if not _authenticated_user:
            return self.error_login_invalid_credentials(**kwargs)
        return _authenticated_user

    def action_create_new_account(self, **kwargs):
        _ewallet_new_user = EWalletCreateUser()
        _new_user = _ewallet_new_user.action_create_new_user(**kwargs)
        if not _new_user:
            return False
        return _new_user

    def ewallet_login_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'login': self.action_login,
                'new_account': self.action_create_new_account,
                }
        return _handlers[kwargs['action']](**kwargs)

    def error_login_invalid_credentials(self, **kwargs):
        msg = 'Unable to login. Invalid credentials.'
        print(msg)
        return False

    def error_login_no_credentials_found(self, **kwargs):
        msg = 'No user name or password found.'
        print(msg)
        return False


class EWalletCreateUser(EWalletLogin):

#   @pysnooper.snoop()
    def check_user_name_ensure_one(self, user_name, user_archive):
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
        if len(user_pass) < 8:
            return False
        return True

    def check_user_pass_letters(self, user_pass):
        lower_case = 'abcdefghijklmnopqrstuvwxyz'
        upper_case = lower_case.upper()
        for item in list(user_pass):
            if item in lower_case or item in upper_case:
                return True
        return False

    def check_user_pass_numbers(self, user_pass):
        numbers = '1234567890'
        for item in list(user_pass):
            if item in numbers:
                return True
        return False

    def check_user_pass_symbols(self, user_pass):
        symbols = '!@#$%^&*()_+[]{};.<>/?\\|-='
        for item in list(user_pass):
            if item in symbols:
                return True
        return False

    def check_user_pass_characters(self, user_pass):
        _checks = {
                'letters': self.check_user_pass_letters(user_pass),
                'numbers': self.check_user_pass_numbers(user_pass),
                'symbols': self.check_user_pass_symbols(user_pass),
                }
        if False in _checks.values():
            return False
        return True

    def check_user_pass(self, user_pass):
        _checks = {
                'length': self.check_user_pass_length(user_pass),
                'characters': self.check_user_pass_characters(user_pass),
                }
        if False in _checks.values():
            return False
        return True

    def check_user_email_is_valid(self, user_email):
        return validate_email(user_email)

    # [ NOTE ]: Requires pydns
    def check_user_email_host_has_smtp(self, user_email):
        return validate_email(user_email, check_mx=True)

    # [ NOTE ]: Requires pydns
    def check_user_email_host_smtp_has_address(self, user_email):
        return validate_email(user_email, verify=True)

    def check_user_email(self, user_email, severity=None):
        _severity_handlers = {
                1: self.check_user_email_is_valid,
                2: self.check_user_email_host_has_smtp,
                3: self.check_user_email_host_smtp_has_address,
                }
        if not severity:
            return _severity_handlers[1](user_email)
        if severity not in _severity_handlers.keys():
            return False
        return _severity_handlers[severity](user_email)

    def perform_new_user_checks(self, **kwargs):
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
        _new_user = ResUser(
                user_name=kwargs['user_name'],
                user_pass_hash=self.hash_password(kwargs['user_pass']),
                user_email=kwargs['user_email'],
                user_phone=kwargs.get('user_phone'),
                user_alias=kwargs.get('user_alias'),
                )
        return _new_user

    def action_create_new_user(self, **kwargs):
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return False
        _parameter_checks = self.perform_new_user_checks(**kwargs)
        if False in _parameter_checks.values():
            _error_handlers = {
                    'user_name': self.error_duplicate_user_name,
                    'user_pass': self.error_invalid_user_pass,
                    'user_email': self.error_invalid_user_email,
                    }
            _error_type = [
                    item for item in _parameter_checks
                    if not _parameter_checks[item]
                    ]
            return _error_handlers[_error_type[0]](**kwargs)
        _new_user = self.create_res_user(**kwargs)
        return _new_user

    def error_duplicate_user_name(self, **kwargs):
        msg = 'User name {} already taken.'.format(kwargs.get('user_name'))
        print(msg)
        return False

    def error_invalid_user_pass(self, **kwargs):
        msg = 'Invalid password. Please make sure password \
                corresponds with security standards.'
        print(msg)
        return False

    def error_invalid_user_email(self, **kwargs):
        msg = 'Invalid email address {}. Please choose a \
                valid email address.'.format(kwargs.get('user_email'))
        print(msg)
        return False



