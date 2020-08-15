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

    def fetch_token_values(self):
        log.debug('')
        return {
            'create_date': self.create_date or \
                self.error_no_token_create_date_found(),
            'write_date': self.write_date or \
                self.error_no_token_write_date_found(),
            'label': self.label or \
                self.error_no_token_label_found(),
            'active': self.active,
            'unlink': self.unlink_flag,
            'valid_to': self.valid_to or \
                self.error_no_valid_to_date_found(),
        }

    # GENERAL

    def is_active(self, *args, **kwargs):
        log.debug('')
        return self.active

    def to_unlink(self, *args, **kwargs):
        log.debug('')
        return self.unlink_flag

    def keep_alive(self, *args, **kwargs):
        log.debug('')
        self.valid_to = kwargs.get('valid_to')
        self.active = True
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


