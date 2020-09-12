import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config
from .token import Token

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class ClientID(Token):

    stoken = None

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
        return super(ClientID, self).__init__(
            label=self.label, active=self.active,
            unlink_flag=self.unlink_flag, valid_to=self.valid_to, *args, **kwargs
        )

    # FETCHERS

    def fetch_label(self):
        log.debug('')
        return self.label

    def fetch_stoken(self):
        log.debug('')
        return self.stoken

    # CHECKERS

    def check_has_stoken(self, stoken_label):
        log.debug('')
        stoken = self.fetch_stoken()
        if not stoken:
            return False
        return True if stoken.fetch_label() == stoken_label else False

    # SETTERS

    def set_stoken(self, stoken):
        log.debug('')
        if not isinstance(stoken, object) and isinstance != None:
            return self.error_invalid_session_token(stoken)
        try:
            self.stoken = stoken
        except Exception as e:
            return self.warning_could_not_set_session_token(stoken, e)
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

    def error_invalid_session_token(self, session_token, *args):
        response = {
            'failed': True,
            'error': 'Invalid session token {}. Details: {}'
                     .format(session_token, args),
        }
        log.error(response['error'])
        return response
