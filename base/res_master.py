import datetime
import logging
import pysnooper

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean #Table,Float,Date,
from sqlalchemy.orm import relationship

from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .res_user_pass_hash_archive import ResUserPassHashArchive
from .transaction_handler import EWalletTransactionHandler
from .res_user import ResUser
from .client_id import ClientID
from .res_utils import ResUtils
from .config import Config

res_utils, config = ResUtils(), Config()
log_config = config.log_config
log = logging.getLogger(log_config['log_name'])


class ResMaster(ResUser):
    __tablename__ = 'res_master'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    user_create_date = Column(DateTime)
    user_write_date = Column(DateTime)
    user_create_uid = Column(Integer, ForeignKey('res_user.user_id'))
    user_write_uid = Column(Integer, ForeignKey('res_user.user_id'))
    user_pass_hash = Column(String)
    user_email = Column(String)
    user_phone = Column(String)
    user_alias = Column(String)
    user_state_code = Column(Integer)
    to_unlink = Column(Boolean)
    to_unlink_timestamp = Column(DateTime)
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    active_session = relationship(
       'EWallet', back_populates='active_master'
    )
    key_code = Column(String)
    account_limit = Column(Integer)
    company = Column(String)
    address = Column(String)
    subordonate_pool = relationship(
       'ResUser', foreign_keys='ResUser.master_account_id'
    )
    acquired_ctokens = Column(Integer)
    is_active = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'res_master',
        'concrete': True,
    }

    def __init__(self, **kwargs):
        log.debug('')
        self.account_limit = kwargs.get('account_limit') or \
            self.fetch_default_master_account_subpool_size_limit()
        self.company = kwargs.get('company')
        self.user_pass_hash = kwargs.get('user_pass_hash')
        self.address = kwargs.get('address')
        self.key_code = kwargs.get('key_code') or \
            self.fetch_default_master_account_key_code()
        self.subordonate_pool = kwargs.get('subordonate_pool', [])
        self.acquired_ctokens = kwargs.get('acquired_ctokens', 0)
        self.is_active = kwargs.get('is_active', True)
        return super(ResMaster, self).__init__(master=True, **kwargs)

    # FETCHERS

    def fetch_is_active_flag(self):
        log.debug('')
        return self.is_active

    def fetch_subpool_email_address_set(self):
        log.debug('')
        subpool = self.fetch_subordonate_account_pool()
        if not subpool:
            return self.warning_master_account_subordonate_pool_empty(
                subpool
            )
        email_set = list(
            set(account.fetch_user_email() for account in subpool)
        )
        return email_set

    def fetch_acquired_ctoken_count(self):
        log.debug('')
        return self.acquired_ctokens

    def fetch_subordonate_account_pool_size_limit(self):
        log.debug('')
        return self.account_limit

    def fetch_key_code(self):
        log.debug('')
        return self.key_code

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_subordonate_account_pool(self):
        log.debug('')
        return self.subordonate_pool

    def fetch_subbordonate_account_pool_size(self):
        log.debug('')
        subpool = self.fetch_subordonate_account_pool()
        return len(subpool)

    def fetch_default_master_account_key_code(self):
        log.debug('')
        return str(config.master_config['master_key_code'])

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_default_master_account_subpool_size_limit(self):
        log.debug('')
        return int(config.master_config['subordonate_pool_size'])

    def fetch_user_values(self):
        log.debug('')
        values = {
            'id': self.user_id,
            'name': self.user_name,
            'create_date': self.user_create_date.strftime('%d-%m-%Y %H:%M:%S'),
            'write_date': self.user_write_date.strftime('%d-%m-%Y %H:%M:%S'),
            'email': self.user_email,
            'phone': self.user_phone,
            'alias': self.user_alias,
            'key_code': self.key_code,
            'account_limit': self.account_limit,
            'company': self.company,
            'address': self.address,
            'subordonate_pool': self.subordonate_pool,
            'acquired_ctokens': self.acquired_ctokens,
            'active': self.is_active,
        }
        return values

    # SETTERS

    def set_subordonate_account_limit(self, account_limit):
        log.debug('')
        try:
            self.account_limit = account_limit
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_master_account_limit(
                account_limit, self.account_limit, e
            )
        return True

    def set_subordonate_user_account_to_pool(self, subordonate):
        log.debug('')
        try:
            self.subordonate_pool.append(subordonate)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_subordonate_user_account_to_pool(
                subordonate, self.subordonate_pool, e
            )
        return True

    def set_account_key_code(self, key_code):
        log.debug('')
        try:
            self.key_code = key_code
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_master_account_key_code(
                key_code, self.key_code, e
            )
        return True

    def set_acquired_ctoken_to_pool(self, ctokens):
        log.debug('')
        try:
            self.acquired_ctokens = ctokens
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_master_acquired_ctoken_count(
                ctokens, self.acquired_ctokens, e
            )
        return True

    # CHECKERS

    def check_master_account_frozen(self):
        log.debug('')
        active = self.fetch_is_active_flag()
        return False if active else True

    def check_user_in_subpool_by_email(self, user_email):
        log.debug('')
        subpool_email_set = self.fetch_subpool_email_address_set()
        if not subpool_email_set or isinstance(subpool_email_set, dict) and \
                subpool_email_set.get('failed'):
            return self.warning_could_not_fetch_subordonate_account_pool_email_set(
                user_email, subpool_email_set
            )
        return True if user_email in subpool_email_set else False

#   @pysnooper.snoop('logs/ewallet.log')
    def check_subordonate_account_pool_size_limit_reached(self):
        log.debug('')
        subpool_size = self.fetch_subbordonate_account_pool_size()
        size_limit = self.fetch_subordonate_account_pool_size_limit()
        return True if subpool_size >= size_limit else False

    # GENERAL

#   @pysnooper.snoop('logs/ewallet.log')
    def add_ctoken_to_acquired(self, client_id):
        log.debug('')
        acquired = self.fetch_acquired_ctoken_count() + 1
        set_to_pool = self.set_acquired_ctoken_to_pool(acquired)
        if isinstance(set_to_pool, dict) and set_to_pool.get('failed'):
            return self.warning_could_not_add_acquired_ctoken_to_pool(
                client_id, acquired, set_to_pool
            )
        return set_to_pool

#   @pysnooper.snoop('logs/ewallet.log')
    def decrease_subordonate_account_pool_size_limit(self, decrease_by):
        log.debug('')
        current_pool_size = self.fetch_subordonate_account_pool_size_limit()
        new_pool_size = current_pool_size - decrease_by
        if new_pool_size < 0:
            return self.warning_cannot_decrease_to_negative_pool_size(
                decrease_by, current_pool_size, new_pool_size
            )
        set_subpool_size = self.set_subordonate_account_limit(new_pool_size)
        if not set_subpool_size or isinstance(set_subpool_size, dict) and \
                set_subpool_size.get('failed'):
            return self.warning_could_not_decrease_subordonate_account_pool_size_limit(
                decrease_by, current_pool_size, new_pool_size, set_subpool_size
            )
        command_chain_response = {
            'failed': False,
            'subpool_size': new_pool_size,
            'decreased_by': decrease_by,
            'master_data': self.fetch_user_values(),
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def increase_subordonate_account_pool_size_limit(self, increase_by):
        log.debug('')
        current_pool_size = self.fetch_subordonate_account_pool_size_limit()
        new_pool_size = current_pool_size + increase_by
        set_subpool_size = self.set_subordonate_account_limit(new_pool_size)
        if not set_subpool_size or isinstance(set_subpool_size, dict) and \
                set_subpool_size.get('failed'):
            return self.warning_could_not_increase_subordonate_account_pool_size_limit(
                increase_by, current_pool_size, new_pool_size, set_subpool_size
            )
        command_chain_response = {
            'failed': False,
            'subpool_size': new_pool_size,
            'increased_by': increase_by,
            'master_data': self.fetch_user_values(),
        }
        return command_chain_response

    def add_subordonate_to_pool(self, subordonate_account):
        log.debug('')
        set_to_pool = self.set_subordonate_user_account_to_pool(
            subordonate_account
        )
        if isinstance(set_to_pool, dict) and set_to_pool.get('failed'):
            return self.warning_could_not_add_new_subordonate_account(
                subordonate_account, set_to_pool
            )
        return set_to_pool

    # VALIDATORS

    def validate_key_code(self, key_code):
        log.debug('')
        secret_key = self.fetch_key_code()
        return False if key_code != secret_key else True

    # CONTROLLERS

    # WARNINGS

    def warning_could_not_fetch_subordonate_account_pool_email_set(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch email addresses from Master account '
                       'Subordonate pool users. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_account_subordonate_pool_empty(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Master account Subordonate pool empty. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_cannot_decrease_to_negative_pool_size(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Cannot decrease to a negative pool size, '
                       'requested number of slots too high. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_decrease_subordonate_account_pool_size_limit(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not decrease Subordonate account pool '
                       'size limit. Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_increase_subordonate_account_pool_size_limit(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not increase Subordonate account pool '
                       'size limit. Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_add_acquired_ctoken_to_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not add acquired CToken to pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_add_new_subordonate_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not add new subordonate user account to pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS

    def error_could_not_set_master_acquired_ctoken_count(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set Master account acquired CToken count. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def error_could_not_set_master_account_limit(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set Master account Subordonate user '
                     'account pool size limit. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def error_could_not_set_master_account_key_code(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set master user account key code. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def error_could_not_set_subordonate_user_account_to_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set subordonate user account to pool. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

