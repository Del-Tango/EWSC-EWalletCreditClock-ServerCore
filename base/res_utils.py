import datetime
import logging
import pysnooper
from pytz import timezone

from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


# TODO
class ResUtils():

    def fetch_now_eet(*args, **kwargs):
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_eet = now_utc.astimezone(timezone('EET'))
        return now_eet.timetuple()

    def sequencer(self):
        log.debug('')
        num = 1
        while True:
            yield num
            num += 1



