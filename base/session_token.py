import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config
from .token import Token

res_utils, config = ResUtils(), Config()
log_config = config.log_config
log = logging.getLogger(log_config['log_name'])


class SessionToken(Token):

    def __init__(self, *args, **kwargs):
        self.label = kwargs.get('session_token') or str()
        self.active = kwargs.get('active') or True
        self.unlink_flag = kwargs.get('unlink') or False
        self.valid_to = kwargs.get('expires_on') or None
        return super(SessionToken, self).__init__(
            label=self.label, active=self.active, unlink_flag=self.unlink_flag,
            valid_to=self.valid_to, *args, **kwargs
        )

    # FETCHERS

    # GENERAL

    def keep_alive(self, *args, **kwargs):
        log.debug('')
        return super(SessionToken, self).keep_alive(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        log.debug('')
        return super(SessionToken, self).deactivate(*args, **kwargs)

    def activate(self, *args, **kwargs):
        log.debug('')
        return super(SessionToken, self).activate(*args, **kwargs)

    # ERRORS

