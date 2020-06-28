import time
import datetime
import random
import hashlib
import logging
import pysnooper
#from validate_email import validate_email
from sqlalchemy import Table, Column, String, Integer, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy import orm
from sqlalchemy.orm import relationship

from .res_user import ResUser
from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class EWalletLogin(Base):
    '''
    [ NOTE ]: EWallet user login handler and journal record.
    '''
    __tablename__ = 'ewallet_login'

    login_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    login_date = Column(DateTime, default=datetime.datetime.now())
    login_status = Column(Boolean, server_default=u'false')

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.get('user_id') or None
        self.login_status = kwargs.get('login_status') or False

    def fetch_all_user_records(self, active_session=None):
        '''
        [ NOTE   ]: Fetches all user records from database.
        [ INPUT  ]: active_session=<session>
        [ RETURN ]: (ResUser set | False)
        '''
        log.debug('')
        if not active_session:
            return self.error_no_active_session_found()
        _user_records = active_session.query(ResUser).all()
        if not _user_records:
            log.info('No user records found.')
        return _user_records

    def fetch_all_user_names(self, active_session=None):
        '''
        [ NOTE   ]: Fetches the names for all existing user accounts.
        [ INPUT  ]: active_session=<session>
        [ RETURN ]: (User name set | False)
        '''
        log.debug('')
        if not active_session:
            return self.error_no_active_session_found()
        _user_names = [
                str(item.user_name) for item in self.fetch_all_user_records(
                    active_session=active_session
                )
            ]
        return _user_names

    def fetch_user_by_name(self, user_name=None, active_session=None):
        '''
        [ NOTE   ]: Fetches specified user account object by user name.
        [ INPUT  ]: user_name=<name>, active_session=<session>
        [ RETURN ]: (ResUser object | False)
        '''
        if not active_session:
            return self.error_no_active_session_found()
        _user = active_session.query(ResUser) \
                .filter(ResUser.user_name==user_name) #\
#               .one()
        return _user or self.error_no_user_record_found_by_name(user_name)

    def set_user_id(self, user_id):
        '''
        [ NOTE   ]: Sets user account record id to EWallet Login Record.
        [ INPUT  ]: <user_id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not user_id:
            return self.error_no_user_id_found()
        self.user_id = user_id
        return True

    def set_login_status(self, login_status):
        '''
        [ NOTE   ]: Sets user account login status to EWallet Login Record in the form of a boolean flag.
        [ INPUT  ]: (True | False)
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not isinstance(login_status, bool):
            return self.error_invalid_login_status()
        self.login_status = login_status
        return True

    def set_login_record_data(self, **kwargs):
        '''
        [ NOTE   ]: Sets user login record data to EWallet Login Record.
        [ INPUT  ]: user_id=<id>, login_status=<status>
        [ RETURN ]: {'user_id': (True | False), 'login_status': (True | False)}
        '''
        log.debug('')
        _values = {
                'user_id': self.set_user_id(kwargs.get('user_id')),
                'login_status': self.set_login_status(kwargs.get('login_status')),
                }
        return _values

    def hash_password(self, password):
        '''
        [ NOTE   ]: Uses the sha256 algorithm to hash password string.
        [ INPUT  ]: <password>
        [ RETURN ]: Password Hash
        '''
        log.debug('')
        return str(hashlib.sha256(password.encode()).hexdigest())

#   @pysnooper.snoop()
    def check_user_name_exists(self, user_name, active_session):
        '''
        [ NOTE   ]: Checks if a user name exists in database associated with a ResUser record.
        [ INPUT  ]: <user_name>, <active_session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        _user = self.fetch_user_by_name(
                user_name, active_session=active_session
                )
        return _user or False

#   @pysnooper.snoop()
    def check_user_pass_hash(self, user_pass, known_hash):
        '''
        [ NOTE   ]: Checks if user password and known sha256 hash match.
        [ INPUT  ]: <user_pass>, <know_hash>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        _pass_hash = self.hash_password(user_pass)
        if str(_pass_hash) == str(known_hash):
            return True
        return False

#   @pysnooper.snoop()
    def authenticate_user(self, **kwargs):
        '''
        [ NOTE   ]: Tries to authenticate user using given credentials so the EWallet session can be updated.
        [ INPUT  ]: user_name=<name>, user_pass=<pass>, active_session=<session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        _user_query = self.check_user_name_exists(
                kwargs['user_name'], kwargs.get('active_session')
                )
        if not _user_query:
            return self.warning_user_name_not_found()
        if _user_query.count() > 1:
            self.warning_user_not_found_by_name(kwargs['user_name'])
        try:
            _user = list(_user_query)[0]
        except:
            return self.warning_user_name_not_found()
        _pass_check = self.check_user_pass_hash(
                kwargs['user_pass'], _user.fetch_user_pass_hash()
                )
        if not _pass_check:
            return self.warning_user_password_incorrect()
        return _user

    def action_login(self, **kwargs):
        '''
        [ NOTE   ]: User action 'login', accessible from external api call.
        [ INPUT  ]: user_name=<name>, user_pass=<pass>, active_session=<session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return self.error_handler_action_login(
                    user_name=kwargs.get('user_name'),
                    user_pass=kwargs.get('user_pass'),
                    )
        _authenticated_user = self.authenticate_user(**kwargs)
        if not _authenticated_user:
            _set_login_data = self.set_login_record_data(
                    login_status=False,
                    )
            return self.error_invalid_login_credentials()
        _set_login_data = self.set_login_record_data(
                user_id=_authenticated_user.user_id,
                login_status=True,
                )
        _set_user_state = _authenticated_user.set_user_state(
                set_by='code', state_code=1
                )
        return _authenticated_user

    def action_create_new_account(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new account', accessible from external api call.
        [ INPUT  ]: user_name=<name>, user_pas=<pass>, user_email=<email>,
                    user_phone=<phone>, user_alias=<alias>, active_session=<session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        _ewallet_new_user = EWalletCreateUser()
        _new_user = _ewallet_new_user.action_create_new_user(**kwargs)
        if not _new_user:
            return self.warning_could_not_create_new_user_account()
        return _new_user

    def ewallet_login_controller(self, **kwargs):
        '''
        [ NOTE   ]: Jump table controller for EWallet login handler object.
        [ INPUT  ]: action=('login' | 'new_account')
        [ RETURN ]: Action variable correspondent.
        '''
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

    def error_no_active_session_found(self):
        log.error('No active user found.')
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

    def error_no_user_record_found_by_name(self, user_name):
        log.error('No user record found by name {}.'.format(user_name))
        return False

    def error_no_user_id_found(self):
        log.error('No user id found.')
        return False

    def error_invalid_login_status(self):
        log.error('Invalid login status. Defaults to False.')
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

    def warning_user_not_found_by_name(self, user_name):
        log.warning('No user found by name {}.'.format(user_name))
        return False

    def warning_multiple_user_accounts_found(self, **kwargs):
        log.warning(
                'Multiple user accounts found for user name {}. '
                'Fetching first.'.format(kwargs.get('user_name'))
                )
        return False


class EWalletCreateUser(EWalletLogin):
    '''
    [ NOTE ]: EWallet user account creator.
    '''

    def fetch_all_user_records(self, active_session=None):
        '''
        [ NOTE   ]: Fetches all ResUser objects recorded in database.
        [ INPUT  ]: active_session=<session>
        [ RETURN ]: (ResUser object set | False)
        '''
        log.debug('')
        if not active_session:
            return self.error_no_active_session_found()
        _user_records = active_session.query(ResUser).all()
        if not _user_records:
            log.info('No user records found.')
        return _user_records

    def fetch_all_user_names(self, active_session=None):
        '''
        [ NOTE   ]: Fetches all user names recorded in database.
        [ INPUT  ]: active_session=<session>
        [ RETURN ]: (User name set | False)
        '''
        log.debug('')
        if not active_session:
            return self.error_no_active_session_found(active_session)
        user_names = [
            str(item.user_name) for item in self.fetch_all_user_records(
                active_session=active_session
            )
        ]
        return user_names

#   @pysnooper.snoop()
    def check_user_name_ensure_one(self, user_name, user_names):
        '''
        [ NOTE   ]: Checks if given user name already exists in database records associated with a user account.
        [ INPUT  ]: <user_name>, <user_name_set>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not user_names:
            return True
        _existing_user_name = [
                item for item in user_names if user_name == item
                ]
        if not _existing_user_name:
            return True
        return False

    def check_user_pass_length(self, user_pass):
        '''
        [ NOTE   ]: Password check for corresponding EWallet password length standards.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if len(user_pass) < 8:
            return self.warning_invalid_user_password_length()
        return True

    def check_user_pass_letters(self, user_pass):
        '''
        [ NOTE   ]: Password check for corresponding EWallet letter standards.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        lower_case = 'abcdefghijklmnopqrstuvwxyz'
        upper_case = lower_case.upper()
        for item in list(user_pass):
            if item in lower_case or item in upper_case:
                return True
        return False

    def check_user_pass_numbers(self, user_pass):
        '''
        [ NOTE   ]: Password check for corresponding EWallet number standards.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        numbers = '1234567890'
        for item in list(user_pass):
            if item in numbers:
                return True
        return False

    def check_user_pass_symbols(self, user_pass):
        '''
        [ NOTE   ]: Password check for corresponding EWallet symbol standards.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        symbols = '!@#$%^&*()_+[]{};.<>/?\\|-='
        for item in list(user_pass):
            if item in symbols:
                return True
        return False

    def check_user_pass_characters(self, user_pass):
        '''
        [ NOTE   ]: Checks if password structure corresponds with EWallet standards.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
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
        '''
        [ NOTE   ]: System action 'check user password' verifying both length
                    and structure, not accessible from external api call.
        [ INPUT  ]: <user_pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        _checks = {
                'length': self.check_user_pass_length(user_pass),
                'characters': self.check_user_pass_characters(user_pass),
                }
        if False in _checks.values():
            return False
        return True

    # TODO - FIX ME
    def check_user_email_is_valid(self, user_email):
        log.debug('')
#       return validate_email(user_email)
        return True

    # [ NOTE ]: Requires pydns
    def check_user_email_host_has_smtp(self, user_email):
        log.debug('')
        return validate_email(user_email, check_mx=True)

    # [ NOTE ]: Requires pydns
    def check_user_email_host_smtp_has_address(self, user_email):
        log.debug('')
        return validate_email(user_email, verify=True)

    def check_user_email(self, user_email, severity=None):
        '''
        [ NOTE   ]: System action 'check user email' using jump table for security level jump table.
        [ INPUT  ]: <user_email>, severity=(1 | 2 | 3)
        [ RETURN ]: (True | False)
        '''
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
        '''
        [ NOTE   ]: Checks new users' name, password and email.
        [ INPUT  ]: user_name=<name>, user_pass=<pass>, user_email=<email>,
                    active_session=<session>
        [ RETURN ]: {
            'user_name': (True | False),
            'user_pass': (True | False),
            'user_email': (True | False)
        }
        '''
        log.debug('')
        _user_names = self.fetch_all_user_names(
                active_session=kwargs.get('active_session')
                )
        _checks = {
                'user_name': self.check_user_name_ensure_one(
                    kwargs['user_name'], _user_names
                    ),
                'user_pass': self.check_user_pass(
                    kwargs['user_pass']
                    ),
                'user_email': self.check_user_email(
                    kwargs['user_email'], severity=1
                    ),
                }
        return _checks

#   @pysnooper.snoop('logs/ewallet.log')
    def create_res_user(self, **kwargs):
        '''
        [ NOTE   ]: Creates new user account and password hash record.
        [ INPUT  ]: active_session=<session, user_name=<name>, user_email=<email>,
                    user_phone=<phone>, user_alias=<alias>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        pass_hash = self.hash_password(kwargs['user_pass'])
        new_user = ResUser(
            user_name=kwargs['user_name'],
            user_pass_hash=pass_hash,
            user_email=kwargs['user_email'],
            user_phone=kwargs.get('user_phone'),
            user_alias=kwargs.get('user_alias'),
            active_session=kwargs['active_session'],
        )
        kwargs['active_session'].add(new_user)
        pass_hash_record = new_user.create_user_pass_hash_record(
            pass_hash=pass_hash,
        )
        kwargs['active_session'].add(pass_hash_record)
        kwargs['active_session'].commit()
        return new_user

    # ACTIONS

    def action_create_new_user(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new user', accessible from external api call.
        [ INPUT  ]: active_session=<session, user_name=<name>, user_email=<email>,
                    user_phone=<phone>, user_alias=<alias>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        if not kwargs.get('user_name') or not kwargs.get('user_pass'):
            return self.error_handler_action_create_new_user(
                user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
            )
        parameter_checks = self.perform_new_user_checks(**kwargs)
        if False in parameter_checks.values():
            return self.warning_handler_action_create_new_user(
                parameter_checks=parameter_checks
            )
        new_user = self.create_res_user(**kwargs)
        return new_user

    # WARNINGS

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

    # ERRORS

    def error_no_active_session_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No active sqlalchemy orm session found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

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


###############################################################################
# CODE DUMP
###############################################################################

