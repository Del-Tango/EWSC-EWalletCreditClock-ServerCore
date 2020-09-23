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
        self.subordonate_pool = kwargs.get('subordonate_pool', [])
        self.is_active = kwargs.get('is_active', True)
        self.acquired_ctokens = kwargs.get('acquired_ctokens', [])
        return super(ResMaster, self).__init__(master=True, **kwargs)

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
            'account_limit': self.account_limit,
            'company': self.company,
            'address': self.address,
            'subordonate_pool': self.subordonate_pool,
            'acquired_ctokens': self.acquired_ctokens,
        }
        return values
