import datetime
import logging
import string
import time
import random
import pysnooper
import hashlib

from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import Config
config, Base = Config(), declarative_base()


class ResUtils():

    engine = create_engine(
        'sqlite:///data/ewallet.db', connect_args={'check_same_thread': False}
    )
    _SessionFactory = sessionmaker(bind=engine)

    # FETCHERS

    def fetch_now_eet(*args, **kwargs):
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_eet = now_utc.astimezone(timezone('EET'))
        return now_eet.timetuple()

    # CHECKERS

    def check_days_since_timestamp(self, timestamp, day_count):
        log.debug('')
        now = datetime.datetime.now()
        days_passed = (now - timestamp).days
        return False if days_passed < day_count else True

    # FORMATTERS

    def format_error_response(self, **kwargs):
        instruction_set_response = {
            'failed': kwargs.get('failed'),
            'error': kwargs.get('error'),
            'details': ''.join(map(str, [
                item for item in filter(
                    lambda ch: ch not in "\\(\')\"", str(kwargs.get('details'))
                )
            ]))
        }
        return instruction_set_response

    def format_warning_response(self, **kwargs):
        instruction_set_response = {
            'failed': kwargs.get('failed'),
            'warning': kwargs.get('warning'),
            'details': ''.join(map(str, [
                item for item in filter(
                    lambda ch: ch not in "\\(\')\"", str(kwargs.get('details'))
                )
            ]))
        }
        return instruction_set_response

    def format_timestamp(self, timestamp):
        return time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(timestamp))

    def format_datetime(self, datetime_obj):
        return datetime_obj.strftime('%d-%m-%Y %H:%M:%S')

    # COMPUTERS

    def compute_number_of_minutes_from_hours(self, hours):
        return 60 * int(hours)

    # GENERAL

    def hash_password(self, password):
        return str(hashlib.sha256(password.encode()).hexdigest())

    def remove_tags_from_command_chain(self, command_chain, *args):
        sanitized_command_chain = command_chain.copy()
        for item in args:
            try:
                del sanitized_command_chain[item]
            except KeyError:
                continue
        return sanitized_command_chain

    #@pysnooper.snoop('logs/ewallet.log')
    def create_system_user(self, ewallet_session):
        system_user_values = config.system_user_values
        active_session = ewallet_session.fetch_active_session()
        score = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='account',
            active_session=active_session, master_id='system', **system_user_values
        )
        return score

    def session_factory(self):
        global Base
        global _SessionFactory
        Base.metadata.create_all(self.engine)
        return self._SessionFactory()

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


# CODE DUMP


