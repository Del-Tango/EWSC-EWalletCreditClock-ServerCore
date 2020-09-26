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
    is_active = Column(Boolean)
    acquired_ctokens = []

    __mapper_args__ = {
        'polymorphic_identity': 'res_master',
        'concrete': True,
    }

    def __init__(self, **kwargs):
        log.debug('')
        self.account_limit = kwargs.get('account_limit') or \
            self.fetch_default_master_account_subpool_size_limit()
        self.company = kwargs.get('company')
        self.address = kwargs.get('address')
        self.key_code = kwargs.get('key_code') or \
            self.fetch_default_master_account_key_code()
        self.subordonate_pool = kwargs.get('subordonate_pool', [])
        self.is_active = kwargs.get('is_active', True)
        self.acquired_ctokens = kwargs.get('acquired_ctokens', [])
        return super(ResMaster, self).__init__(master=True, **kwargs)

    # FETCHERS

    def fetch_key_code(self):
        log.debug('')
        return self.key_code

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
        }
        return values

    # SETTERS

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

    def set_acquired_ctoken_to_pool(self, client_id):
        log.debug('')
        try:
            self.acquired_ctokens.append(client_id)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_master_acquired_ctoken(
                client_id, self.acquired_ctokens, e
            )
        return True

    # CHECKERS

#   @pysnooper.snoop('logs/ewallet.log')
    def check_subordonate_account_pool_size_limit_reached(self):
        log.debug('')
        subpool_size = self.fetch_subbordonate_account_pool_size()
        size_limit = self.fetch_default_master_account_subpool_size_limit()
        return True if subpool_size >= size_limit else False

    # GENERAL

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

    def add_ctoken_to_acquired(self, client_id):
        log.debug('')
        set_to_pool = self.set_acquired_ctoken_to_pool(client_id)
        if isinstance(set_to_pool, dict) and set_to_pool.get('failed'):
            return self.warning_could_not_add_acquired_ctoken_to_pool(
                client_id, set_to_pool
            )
        return set_to_pool

    # VALIDATORS

    def validate_key_code(self, key_code):
        log.debug('')
        secret_key = self.fetch_key_code()
        return False if key_code != secret_key else True

    # CONTROLLERS

    # WARNINGS

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

