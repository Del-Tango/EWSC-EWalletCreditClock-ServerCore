import datetime
import logging
import string
import time
import random
import pysnooper
import hashlib
import base64
import os

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

    def fetch_future_expiration_date_by_minutes(self, **kwargs):
        if not kwargs.get('minutes'):
            return self.error_no_minutes_specified(kwargs)
        now = datetime.datetime.now()
        future_date = now + datetime.timedelta(minutes=kwargs['minutes'])
        return future_date

    def fetch_future_expiration_date(self, **kwargs):
        if not kwargs.get('unit'):
            return self.error_no_time_unit_specified(kwargs)
        handlers = {
            'minutes': self.fetch_future_expiration_date_by_minutes,
        }
        return handlers[kwargs['unit']](**kwargs)

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
            'level': kwargs.get('level'),
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
            'level': kwargs.get('level'),
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

#   @pysnooper.snoop()
    def write_to_file(self, file_path, file_content, mode='a'):
        log.debug('')
        with open(file_path, mode) as f:
            f.write(file_content)
            f.close()
        return True

#   @pysnooper.snoop()
    def new_issue_report_file(self, **kwargs):
        timestamp = str(kwargs.get('timestamp') or time.time())
        report_dir = config.system_config['reports_dir'] \
            + config.system_config['issues_dir']
        address = str(kwargs.get('remote_addr') or '0.0.0.0')
        email = kwargs.get('user_email') or 'SCore@system.ro'
        suffix = 'issue'
        report_file_name = address + ':' + timestamp
        issue_id = self.encode_message_base64(report_file_name)
        report_file_path = report_dir + report_file_name + '.' + suffix
        if os.path.exists(report_file_path):
            count = 1
            while True:
                report_file_name = '(' + str(count) + ')' + report_file_name
                if os.path.exists(report_dir + report_file_name + '.' + suffix):
                    count += 1
                    continue
                issue_id = self.encode_message_base64(report_file_name)
                report_file_path = report_dir + report_file_name + '.' + suffix
                break
        try:
            report_file = open(report_file_path, 'w')
            report_file.write('')
            report_file.close()
        except Exception as e:
            return self.error_could_not_create_issue_report_file(
                kwargs, timestamp, report_dir, address, email, suffix,
                report_file_name, report_file_path, e
            )
        return {
            'failed': False,
            'file_name': report_file_name,
            'file_dir': report_dir,
            'file_path': config.system_config['server_directory']
                + report_file_path,
            'issue_id': issue_id,
        }

    def encode_message_base64(self, message):
        if not isinstance(message, str):
            return self.error_invalid_message(message)
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return base64_message

    def decode_message_base64(self, base64_message):
        if not isinstance(base64_message, str):
            return self.error_invalid_message(base64_message)
        base64_bytes = base64_message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        return message

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

    # ERRORS

    def error_could_not_create_issue_report_file(self, *args):
        response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not create new IssueReport file. '
                     'Details: {}'.format(args)
        }
        return response

    def error_invalid_message(self, *args):
        response = {
            'failed': True,
            'error': 'Invalid message. '
                     'Details: {}'.format(args)
        }
        return response

    def error_no_time_unit_specified(self, *args):
        response = {
            'failed': True,
            'error': 'No time unit specified. '
                     'Details: {}'.format(args)
        }
        return response

    def error_no_minutes_specified(self, *args):
        response = {
            'failed': True,
            'error': 'No minutes specified.'
        }
        return response

res_utils = ResUtils()

'''
[ NOTE ]: Setting up EWallet logger.
'''
def log_init():
    log_config = config.log_config
    log = logging.getLogger(log_config['log_name'])
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(
        log_config['log_dir'] + log_config['log_file'], 'a'
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


