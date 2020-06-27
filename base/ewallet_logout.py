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


class EWalletLogout(Base):
    __tablename__ = 'ewallet_logout'

    logout_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    logout_date = Column(DateTime, default=datetime.datetime.now())
    logout_status = Column(Boolean, server_default=u'false')

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.get('user_id') or None
        self.logout_status = kwargs.get('logout_status') or False
