from base.ewallet_session_manager import EWalletSessionManager
from base.config import Config
from base.res_utils import ResUtils
import logging
import datetime
import time

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletServer(EWalletSessionManager):
    pass

if __name__ == '__main__':
    ewallet_server = EWalletServer()


