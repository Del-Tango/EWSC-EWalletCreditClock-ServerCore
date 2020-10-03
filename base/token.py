import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class Token():

    create_date = datetime.datetime.now()
    write_date = datetime.datetime.now()
    label = str()
    active = bool()
    unlink_flag = bool()
    valid_to = None

    def __init__(self, *args, **kwargs):
        self.create_date = kwargs.get('create_date') or \
            datetime.datetime.now()
        self.write_date = kwargs.get('write_date') or \
            datetime.datetime.now()
        self.label = kwargs.get('label') or str()
        self.active = kwargs.get('active') or True
        self.unlink_flag = kwargs.get('unlink_flag') or False
        self.valid_to = kwargs.get('valid_to') or None

    # FETCHERS

    def fetch_token_expiration_date(self):
        log.debug('')
        return self.valid_to

    def fetch_token_values(self):
        log.debug('')
        return {
            'create_date': res_utils.format_datetime(self.create_date) or \
                self.error_no_token_create_date_found(),
            'write_date': res_utils.format_datetime(self.write_date) or \
                self.error_no_token_write_date_found(),
            'label': self.label or \
                self.error_no_token_label_found(),
            'active': self.active,
            'unlink': self.unlink_flag,
            'valid_to': res_utils.format_datetime(self.valid_to) or \
                self.error_no_valid_to_date_found(),
        }

    # SETTERS

    def set_write_date(self, write_datetime):
        log.debug('')
        try:
            self.write_date = write_datetime
        except Exception as e:
            return self.error_could_not_set_token_write_date(
                write_datetime, self.write_date, e
            )
        return True

    def set_valid_to(self, timestamp):
        log.debug('')
        try:
            self.valid_to = timestamp
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_token_expiration_date(
                timestamp, self.valid_to, e
            )
        return True

    def set_active_flag(self, flag):
        log.debug('')
        try:
            self.active = flag
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_token_active_flag(
                flag, self.active, e
            )
        return True

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        now = datetime.datetime.now()
        return self.set_write_date(now)

    # CHECKERS

    def check_token_expired(self):
        log.debug('')
        now = datetime.datetime.now()
        expiration_date = self.fetch_token_expiration_date()
        return True if now > expiration_date else False

    # GENERAL

    def is_active(self, *args, **kwargs):
        log.debug('')
        return self.active

    def to_unlink(self, *args, **kwargs):
        log.debug('')
        return self.unlink_flag

#   @pysnooper.snoop('logs/ewallet.log')
    def keep_alive(self, *args, **kwargs):
        log.debug('')
        self.set_valid_to(kwargs.get('valid_to'))
        self.set_active_flag(True)
        return True

    def inspect(self, *args, **kwargs):
        log.debug('')
        values = self.fetch_token_values()
        values.update(kwargs)
        return values

    def deactivate(self, *args, **kwargs):
        log.debug('')
        self.active = False
        return True

    def activate(self, *args, **kwargs):
        log.debug('')
        self.active = True
        return True

    def expired(self, *args, **kwargs):
        log.debug('')
        now = datetime.datetime.now()
        return True if now > self.valid_to else False

    def unlink(self, *args, **kwargs):
        log.debug('')
        self.unlink_flag = True
        return True

    # ERRORS

    def error_could_not_set_token_active_flag(self, *args):
        response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set Token active flag. '
                     'Details: {}'.format(args)
        }
        log.error(response['error'])
        return response

    def error_could_not_set_token_expiration_date(self, *args):
        response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set Token expiration date. '
                     'Details: {}'.format(args)
        }
        log.error(response['error'])
        return response

    def error_no_token_create_date_found(self):
        log.error('No token create date found.')
        return False

    def error_no_token_write_date_found(self):
        log.error('No token write date found.')
        return False

    def error_no_token_label_found(self):
        log.error('No token label found.')
        return False

    def error_no_valid_to_date_found(self):
        log.error('No valid to date found.')
        return False


