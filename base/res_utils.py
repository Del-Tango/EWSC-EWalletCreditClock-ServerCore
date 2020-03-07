from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import logging
import pysnooper

from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])

Base = declarative_base()

# TODO
class ResUtils():

    engine = create_engine('sqlite:///data/ewallet.db')
    _SessionFactory = sessionmaker(bind=engine)

#   def __init__(self, *args, **kwargs):
#       self.engine = create_engine('sqlite:///data/ewallet.db')
        #'postgresql://dbuser:dbpassword@localhost:5432/sqlalchemy-orm-tutorial'
        # use session_factory() to get a new Session
#       self._SessionFactory = sessionmaker(bind=self.engine)
#       self.Base = declarative_base()

    def session_factory(self):
        global Base
        global _SessionFactory
        Base.metadata.create_all(self.engine)
        return self._SessionFactory()

    def fetch_now_eet(*args, **kwargs):
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_eet = now_utc.astimezone(timezone('EET'))
        return now_eet.timetuple()

    def sequencer(self):
        log.debug('')
        num = 1
        while True:
            yield num
            num += 1



