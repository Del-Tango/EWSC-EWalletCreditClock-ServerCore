import datetime
import logging
import pysnooper

from .res_utils import ResUtils, Base
from .config import Config
from .token import Token

res_utils, config = ResUtils(), Config()
log_config = config.log_config
log = logging.getLogger(log_config['log_name'])


class ClientID(Token):

    def __init__(self, *args, **kwargs):
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

    # GENERAL

    def inspect(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).inspect(*args, **kwargs)

    def keep_alive(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).keep_alive(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).deactivate(*args, **kwargs)

    def activate(self, *args, **kwargs):
        log.debug('')
        return super(ClientID, self).activate(*args, **kwargs)

    # ERRORS

