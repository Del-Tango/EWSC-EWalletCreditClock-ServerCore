import datetime
import pysnooper


class Config():

    # TODO - Get target file from ewallet.py
    def __init__(self, **kwargs):
#       if not kwargs.get('target_file'):
#           return
        self.sys_boot_date = datetime.datetime.now()
        self.log_config = {
                'log_name': 'EWallet',
                'log_dir': 'logs',
                'log_level': 'DEBUG',
                'file_main': 'ewallet.log',
                'file_debug': 'debug.log',
                'file_info': 'info.log',
                'file_warning': 'warning.log',
                'file_error': 'error.log',
                'file_critical': 'critical.log',
                'record_format': '%(asctime)s [ %(levelname)s ] - %(funcName)s - %(message)s',
                'date_format': "%Y-%m-%d %H:%M:%S",
                }
        self.client_config = {
                'keep_logged_in': None,
                }
        self.wallet_config = {
                'wallet_id': None,
               }
        # TODO - Uncomment file parser
#       self.config_file_parser(kwargs.get('target_file'))

    def fetch_config_dicts(self, **kwargs):
        return [self.log_config, self.client_config, self.wallet_config]

    def fetch_config_dict_by_key(self, dict_set, key):
        found = []
        for item in dict_set:
            if key in item.keys():
                found.append(item)
        if len(found) > 1:
            print('More than one config dict found by key {}'.format(key))
        return found[0] or False

    @pysnooper.snoop()
    def set_config_value(self, **kwargs):
        if not kwargs.get('dct') or not kwargs.get('key'):
            return False
        kwargs['dct'][kwargs['key']] = kwargs.get('val')
        return kwargs['dct']

    @pysnooper.snoop()
    def config_file_parser(self, target_file):
        config_dicts = self.fetch_config_dicts()
        with open(target_file, 'r') as target:
            lines = target.readlines()
            for line in lines:
                key_val = line.split(':')
                dict_search = self.fetch_config_dict_by_key(
                        config_dicts, key_val[0]
                        )
                set_config_value(
                        dct=dict_search,
                        key=key_val[0],
                        val=str(key_val[1]).strip('\n')
                        )
        return True


