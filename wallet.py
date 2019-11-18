import datetime
import random
import pysnooper
import time


class client_ewallet():

    def __init__(self, **kwargs):
        self.user_name = 'test_user'
        self.user_pass = '1234'
        self.user_email = 'admin@ewallet.com'
        self.user_phone = '555 555 55'
        self.client_ewallet = credit_ewallet()
        self.ewallet_session_key = None
        self.credit_transfer_records = []
        self.client_partners = []

    def create_transfer_record(self, **kwargs):
        _transfer_record = client_transfer_record(
            transfer_type=kwargs.get('transfer_type'),
            transfer_from=kwargs.get('transfer_from'),
            transfer_to=kwargs.get('transfer_to'),
            transfer_of=kwargs.get('transfer_of'),
            transfer_on=kwargs.get('transfer_on'),
        )
        self.client_transfer_records += _transfer_record
        return _transfer_record

    # TODO
    def wallet_transfer_incomming(self):
        return False

    # TODO
    def wallet_transfer_outgoing(self):
        return False

    def wallet_create_account(self):
        user_name = 'test_user'
        user_pass = '1234'
        self.client_ewallet.main_controller(
                create_account=True, user_name=self.user_name, user_pass=self.user_pass
                )
        return True

    def wallet_login(self):
        global ewallet_session_key
        session_key = self.client_ewallet.main_controller(
                login=True, user_name='test_user', user_pass='1234'
                )
        if not session_key:
            print('WARNING: Unable to login to ewallet.')
            return False
        self.ewallet_session_key = session_key
        print('CONNECTED: Successfuly with session key {}.'.format(session_key))
        return session_key

    def wallet_test(self):
        self.wallet_create_account()
        self.wallet_login()

        self.client_ewallet.main_controller(
                supply=True, credits=100, session_key=self.ewallet_session_key
                )
        self.client_ewallet.main_controller(
                extract=True, credits=55, session_key=self.ewallet_session_key
                )
        _credits = self.client_ewallet.main_controller(
                interogate=True, session_key=self.ewallet_session_key
                )

        print('You have {} credits left.'.format(_credits))
        print('Last connection {}.'.format(self.client_ewallet.last_conn_date))

client = client_ewallet()
client.wallet_test()


