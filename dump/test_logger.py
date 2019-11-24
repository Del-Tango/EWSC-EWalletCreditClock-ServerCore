import logging

FORMAT = '%(asctime)s - [%(levelname)s] - %(clientip)s - %(user)s: %(message)s'
logging.basicConfig(format=FORMAT, filename='test.log', filemode='w', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

d = {'clientip': '127.0.0.1', 'user': 'test_user'}

logger.info('Test INFO', extra=d)
logger.warning('Test Demo Logger', extra=d)
logger.debug('Test Debug', extra=d)

logger.debug('This message should go into the log file.', extra=d)
logger.info('So should this.', extra=d)
logger.warning('This too.', extra=d)


