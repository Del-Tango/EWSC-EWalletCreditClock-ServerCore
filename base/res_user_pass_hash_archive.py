import datetime
import random
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils
from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class ResUserPassHashArchive(Base):
    __tablename__ = 'res_user_hash_archive'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    user_pass_hash = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id')
        self.user_pass_hash = kwargs.get('user_pass_hash')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_pass_hash_archive_id(self):
        log.debug('')
        return self.id

    def fetch_pass_hash_archive_pass_hash(self):
        log.debug('')
        return self.user_pass_hash

    def fetch_pass_hash_archive_values(self):
        log.debug('')
        values = {
            'id': self.id,
            'user_id': self.user_id,
            'user_pass_hash': self.user_pass_hash,
            'create_data': self.create_date,
            'write_date': self.write_date,
        }
        return values


