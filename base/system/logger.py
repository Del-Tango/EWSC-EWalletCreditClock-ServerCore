import datetime

from .config import Config

config = Config().config


class WalletLog():

    def __init__(self, **kwargs):
        self.user_name = kwargs.get('user_name')

    def fetch_write_values(self, **kwargs):
        _values = {
            'user_name': self.user_name,
            'message': kwargs.get('message'),
            'datetime': datetime.datetime.now(),
            'level': kwargs.get('level') or config['log']['level'],
            'log_file': self.username + '/' + config['log']['files'][kwargs.get('level')],
        }
        return _values

    def write_string_format(self, values):
        _formatted_msg = '{} [ {} ] - {} - {}.'.format(
            values.get('datetime'), values.get('level').upper(),
            values.get('user_name'), values.get('message'),
        )
        return _formatted_msg

    # [ INPUT ]: values = {'message': '', 'level': ''}
    def write(self, **kwargs):
        _values = self.fetch_write_values(**kwargs)
        _msg_string = self.write_string_format(_values)
        with open(_values.get('log_file'), 'a') as log_file:
            log_file.write(_msg_string)
        log_file.close()
        return _msg_string



