import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config
from .token import Token

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class SessionToken(Token):

    ctoken = None
    worker_id = int()

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now()
        self.ctoken = kwargs.get('client_token')
        self.create_date = now
        self.write_date = now
        self.worker_id = kwargs.get('worker_id') or int()
        self.label = kwargs.get('session_token') or str()
        self.active = kwargs.get('active') or True
        self.unlink_flag = kwargs.get('unlink') or False
        self.valid_to = kwargs.get('expires_on')
        return super(SessionToken, self).__init__(
            label=self.label, active=self.active, unlink_flag=self.unlink_flag,
            valid_to=self.valid_to, *args, **kwargs
        )

    # FETCHERS

    def fetch_token_values(self):
        log.debug('')
        res = super(SessionToken, self).fetch_token_values()
        values = {
            'ctoken': self.ctoken.fetch_label(),
            'worker_id': self.worker_id,
        }
        values.update(res)
        return values

    def fetch_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_label(self):
        log.debug('')
        return self.label

    def fetch_ctoken(self):
        log.debug('')
        return self.ctoken

    def fetch_worker_id(self):
        log.debug('')
        return self.worker_id

    def fetch_validity_interval(self):
        log.debug('')
        return int(config.client_config['session_token_validity'])

    # SETTERS

    def set_worker_id(self, worker_id):
        log.debug('')
        if not isinstance(worker_id, int):
            return self.error_invalid_worker_id(worker_id)
        try:
            self.worker_id = worker_id
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_worker_id(worker_id)
        return True

    def set_ctoken(self, ctoken):
        log.debug('')
        if not isinstance(ctoken, object):
            return self.error_invalid_client_token(ctoken)
        try:
            self.ctoken = ctoken
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_client_token(ctoken, e)
        return True

    # GENERAL

    def keep_alive(self, *args, **kwargs):
        log.debug('')
        now = datetime.datetime.now()
        stoken_validity_interval = self.fetch_validity_interval()
        future_date = res_utils.fetch_future_expiration_date(
            unit='minutes', minutes=stoken_validity_interval
        )
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'valid_to'
        )
        return super(SessionToken, self).keep_alive(
            valid_to=future_date, *args, **sanitized_instruction_set
        )

    def deactivate(self, *args, **kwargs):
        log.debug('')
        return super(SessionToken, self).deactivate(*args, **kwargs)

    def activate(self, *args, **kwargs):
        log.debug('')
        return super(SessionToken, self).activate(*args, **kwargs)

    # WARNINGS

    def warning_could_not_set_worker_id(self, worker_id, *args):
        response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set worker id to session token. '
                     'Details: {}'.format(worker_id, args)
        }
        log.warning(response['warning'])
        return response

    def warning_could_not_set_client_token(self, client_token, *args):
        response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set client token {} to session token {} object. '
                       'Details: {}'.format(client_token, self.label, args)
        }
        log.warning(response['warnings'])
        return response

    # ERRORS

    def error_invalid_worker_id(self, worker_id, *args):
        response = {
            'failed': True,
            'error': 'Invalid worker id {}. Details: {}'.format(worker_id, args)
        }
        log.error(response['error'])
        return response

    def error_invalid_client_token(self, client_token, args):
        response = {
            'failed': True,
            'error': 'Invalid client token {}. Details: {}'\
                     .format(client_token, args)
        }
        log.error(response['error'])
        return response

