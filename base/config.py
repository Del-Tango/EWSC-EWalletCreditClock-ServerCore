import datetime
import pysnooper
import os
import string
import random


class Config():

    def __init__(self, **kwargs):
        self.sys_boot_date = datetime.datetime.now()
        self.system_config = {
            'run_mode': 'prepay',
            'server_directory': os.path.dirname(os.path.realpath(__file__)),
            'conf_file': 'ewallet.conf',
            'conf_dir': 'conf',
            'socket_handler_address': '127.0.0.1',
            'esm_instruction_port': 8080,
            'esm_response_port': 8081,
        }
        self.worker_config = {
            'worker_limit': 10,
            'worker_sigterm': 'terminate_worker',
        }
        self.log_config = {
            'log_name': 'EWallet',
            'log_dir': 'logs',
            'log_level': 'DEBUG',
            'log_file': 'ewallet.log',
            'log_record_format': '[ %(asctime)s ] %(name)s ' \
                '[ %(levelname)-9s ] - %(thread)d - %(filename)s - %(lineno)d: ' \
                '%(funcName)s - %(message)s',
            'log_date_format': "%d-$m-%Y %H:%M:%S",
        }
        self.client_config = {
            'keep_logged_in': 0,
            'client_id_prefix': 'ewsm-uid',
            'client_id_length': 20,
            'client_id_validity': 30,
            'session_token_prefix': 'ewsm-st',
            'session_token_length': 20,
            'session_token_validity': 30,
        }
        self.wallet_config = {
            'wallet_reference': 'EWallet',
        }
        self.clock_config = {
            'clock_reference': 'CreditClock'
        }
        self.contact_list_config = {
            'contact_list_reference': 'ContactList',
            'contact_record_reference': 'ContactRecord',
        }
        self.time_sheet_config = {
            'time_sheet_reference': 'TimeSheet',
            'time_record_reference': 'TimeRecord',
        }
        self.conversion_sheet_config = {
            'conversion_sheet_reference': 'ConversionSheet',
            'conversion_record_reference': 'ConversionRecord',
        }
        self.transfer_sheet_config = {
            'transfer_sheet_reference': 'TransferSheet',
            'transfer_record_reference': 'TransferRecord',
        }
        self.invoice_sheet_config = {
            'invoice_sheet_reference': 'InvoiceSheet',
            'invoice_record_reference': 'InvoiceRecord',
        }
        self.system_user_values = {
            'user_name': 'SystemCore',
            'user_pass': self.generate_pseudorandom_password(),
            'user_email': 'ewsc.systemcore@alvearesolutions.ro',
            'user_alias': 'S:Core',
        }
        self.config_file_parser(
            self.system_config['conf_dir'] + '/' \
            + self.system_config['conf_file']
        )

    def fetch_config_values(self):
        return self.__dict__

    def generate_pseudorandom_password(self, passLen=36):
        character_set = string.ascii_lowercase \
            + string.ascii_uppercase \
            + string.digits + '~!@#$%^&*()_+=-`][\'".,;:}{'
        return ''.join((random.choice(character_set) for i in range(passLen)))

    def fetch_config_dicts(self, **kwargs):
        return [
            self.log_config, self.client_config, self.wallet_config,
            self.clock_config, self.time_sheet_config,
            self.conversion_sheet_config, self.transfer_sheet_config,
            self.invoice_sheet_config, self.system_config,
            self.system_user_values, self.contact_list_config,
            self.worker_config,
        ]

    def fetch_config_dict_by_key(self, dict_set, key):
        found = [item for item in dict_set if key in item.keys()]
        if len(found) > 1:
            print('More than one config dict found by key {}'.format(key))
        return False if not found else found[0]

#   @pysnooper.snoop()
    def set_config_value(self, **kwargs):
        if not kwargs.get('dct') or not kwargs.get('key'):
            return False
        kwargs['dct'][kwargs['key']] = kwargs.get('val')
        return kwargs['dct']

#   @pysnooper.snoop()
    def config_file_parser_compute(self, config_dicts, line):
        if line[0] == '#':
            return False
        key_val = line.split(' : ')
        if len(key_val) == 1:
            return False
        dict_search = self.fetch_config_dict_by_key(config_dicts, key_val[0])
        self.set_config_value(
            dct=dict_search, key=key_val[0], val=str(key_val[1]).strip('\n')
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


if __name__ == '__main__':
    print(Config().fetch_config_values())
