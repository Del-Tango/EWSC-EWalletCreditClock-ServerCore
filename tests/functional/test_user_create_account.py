import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerUserCreateAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Generate new Client ID to be able to request a Session Token
        print('[...]: User action Request Client ID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: User action Request Session Token')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )
        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_create_account_functionality(self):
        print('[ * ]: User action Create New Account')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'new',
            'new': 'account', 'client_id': self.client_id,
            'session_token': self.session_token, 'user_name': self.user_name_1,
            'user_pass': self.user_pass_1, 'user_email': self.user_email_1
        }
        new_account = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(new_account) + '\n'
        )
        self.assertTrue(isinstance(new_account, dict))
        self.assertEqual(len(new_account.keys()), 3)
        self.assertFalse(new_account.get('failed'))
        self.assertEqual(new_account.get('account'), self.user_email_1)
        self.assertTrue(isinstance(new_account.get('account_data'), dict))
        self.assertTrue(isinstance(new_account['account_data']['id'], int))
        self.assertTrue(isinstance(new_account['account_data']['email'], str))
        self.assertTrue(isinstance(new_account['account_data']['ewallet'], int))
        self.assertTrue(isinstance(new_account['account_data']['contact_list'], int))
        self.assertTrue(isinstance(new_account['account_data']['state_code'], int))
        self.assertTrue(isinstance(new_account['account_data']['state_name'], str))
        self.assertTrue(isinstance(new_account['account_data']['ewallet_archive'], dict))
        self.assertTrue(isinstance(new_account['account_data']['contact_list_archive'], dict))
