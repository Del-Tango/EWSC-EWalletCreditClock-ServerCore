import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config
from .token import Token

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class ClientID(Token):

    stoken = None           # <stoken type-object>
    acquired_master = None  # <master-id type-int>

    def __init__(self, *args, **kwargs):
        self.stoken = kwargs.get('session_token')
        self.label = str() if not kwargs.get('client_id') \
            else kwargs.pop('client_id')
        self.active = True if not kwargs.get('active') \
            else kwargs.pop('active')
        self.unlink_flag = False if not isinstance(kwargs.get('unlink'), bool) \
            else kwargs.pop('unlink')
        self.valid_to = None if not kwargs.get('expires_on') \
            else kwargs.pop('expires_on')
        self.acquired_master = None if not kwargs.get('acquired_master') \
            else kwargs.pop('acquired_master')
        return super(ClientID, self).__init__(
            label=self.label, active=self.active,
            unlink_flag=self.unlink_flag, valid_to=self.valid_to,
            *args, **kwargs
        )

    # FETCHERS

    def fetch_token_values(self, **kwargs):
        log.debug('')
        res = super(ClientID, self).fetch_token_values()
        values = {
            'stoken': self.stoken.fetch_label(),
            'acquired_master': self.acquired_master,
        }
        values.update(res)
        return values

    def fetch_label(self):
        log.debug('')
        return self.label

    def fetch_stoken(self):
        log.debug('')
        return self.stoken

    def fetch_master(self):
        log.debug('')
        return self.acquired_master

    # CHECKERS

    def check_has_stoken(self, stoken_label):
        log.debug('')
        stoken = self.fetch_stoken()
        if not stoken:
            return False
        return True if stoken.fetch_label() == stoken_label else False

    def check_has_master(self, master_id):
        log.debug('')
        acquired_master_id = self.fetch_master()
        if not master_id:
            return False
        return True if acquired_master_id == master_id else False

    # SETTERS

    def set_stoken(self, stoken):
        log.debug('')
        if not isinstance(stoken, object) and isinstance != None:
            return self.error_invalid_session_token(stoken)
        try:
            self.stoken = stoken
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_session_token(
                stoken, self.stoken, e
            )
        return True

    def set_master(self, master_id):
        log.debug('')
        if not isinstance(master_id, int):
            return self.error_invalid_master_id(master_id)
        try:
            self.acquired_master = master_id
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_acquired_master(
                master_id, self.acquired_master, e
            )
        return True

    # CLEANERS

    def clear_stoken(self):
        log.debug('')
        return self.set_stoken(None)

    # GENERAL

    def inspect(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).inspect(
            stoken=self.session_token, *args, **kwargs
        )

    def keep_alive(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).keep_alive(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).deactivate(*args, **kwargs)

    def activate(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).activate(*args, **kwargs)

    # WARNINGS

    def warning_could_not_set_acquired_master(self, *args):
        response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set acquired master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(response['warning'])
        return response

    def warning_could_not_set_session_token(self, session_token, *args):
        response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set session token {} to client token {}. '
                       'Details: {}'.format(session_token, self.label, args),
        }
        log.warning(response['warning'])
        return response

    # ERRORS

    def error_invalid_master_id(self, *args):
        response = {
            'failed': True,
            'error': 'Invalid master user account ID. '
                     'Details: {}'.format(args),
        }
        log.error(response['error'])
        return response

    def error_invalid_session_token(self, session_token, *args):
        response = {
            'failed': True,
            'error': 'Invalid session token {}. Details: {}'
                     .format(session_token, args),
        }
        log.error(response['error'])
        return response
