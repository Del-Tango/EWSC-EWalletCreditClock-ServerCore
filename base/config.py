import datetime
import pysnooper
import os


class Config():

    def __init__(self, **kwargs):
        self.sys_boot_date = datetime.datetime.now()
        self.current_directory = os.path.dirname(os.path.realpath(__file__))
        self.target_file = 'conf/ewallet.conf'
        self.log_config = {
                'log_name': 'EWallet',
                'log_dir': 'logs',
                'log_level': 'DEBUG',
                'log_file': 'ewallet.log',
                'log_record_format': '[ %(asctime)s ] %(name)s ' \
                    '[ %(levelname)-9s ] - %(filename)s - %(lineno)d: ' \
                    '%(funcName)s - %(message)s',
                'log_date_format': "%Y-%m-%d %H:%M:%S",
                }
        self.client_config = {
                'keep_logged_in': None,
                }
        self.wallet_config = {
                'wallet_reference': None,
               }
        self.config_file_parser(self.target_file)
        self.system_user_values = {
                'user_name': 'SystemCore',
                'user_create_uid': None,
                'user_write_uid': None,
                'user_pass': 'SystemCoreDefaultPassword123!!',
                'user_email': 'system.core@alvearesolutions.com',
                'user_alias': 'S:Core',
                }

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

#   @pysnooper.snoop()
    def set_config_value(self, **kwargs):
        if not kwargs.get('dct') or not kwargs.get('key'):
            return False
        kwargs['dct'][kwargs['key']] = kwargs.get('val')
        return kwargs['dct']

    def config_file_parser_compute(self, config_dicts, line):
        if line[0] == '#':
            return False
        key_val = line.split(' : ')
        dict_search = self.fetch_config_dict_by_key(
                config_dicts, key_val[0]
                )
        self.set_config_value(
                dct=dict_search,
                key=key_val[0],
                val=str(key_val[1]).strip('\n')
                )
        return True

#   @pysnooper.snoop()
    def config_file_parser(self, target_file):
        config_dicts = self.fetch_config_dicts()
        with open(target_file, 'r') as target:
            lines = target.readlines()
            for line in lines:
                self.config_file_parser_compute(config_dicts, line)
        return True


