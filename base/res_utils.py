from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import logging
import string
import time
import random
import pysnooper

from .config import Config
config, Base = Config(), declarative_base()


class ResUtils():

    engine = create_engine('sqlite:///data/ewallet.db')
    _SessionFactory = sessionmaker(bind=engine)

    def remove_tags_from_command_chain(self, command_chain, *args):
        for item in args:
            try:
                del command_chain[item]
            except KeyError:
                continue
        return command_chain

    #@pysnooper.snoop('logs/ewallet.log')
    def create_system_user(self, ewallet_session):
        if not ewallet_session:
            return False
        _system_user_values = config.system_user_values
        score = ewallet_session.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                **_system_user_values
                )
        return score

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

    def generate_random_alpha_numeric_string(self, string_length=8):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join((random.choice(letters_and_digits) for i in range(string_length)))


res_utils = ResUtils()

'''
[ NOTE ]: Setting up EWallet logger.
'''
def log_init():
    log_config = config.log_config
    log = logging.getLogger(log_config['log_name'])
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(
        log_config['log_dir'] + '/' + log_config['log_file'], 'a'
        )
    formatter = logging.Formatter(
        log_config['log_record_format'],
        log_config['log_date_format']
        )
    logging.Formatter.converter = res_utils.fetch_now_eet
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    return log

log = log_init()

