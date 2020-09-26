import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerUserCreateMasterAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletMaster1'
    user_alias_1 = 'TEWM1'
    user_email_1 = 'master1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'
    user_phone_1 = '555 555 555'
    user_company_1 = 'TestClient INC'
    user_address_1 = 'Iasi, jud. Iasi, Str. Canta, Nr. 40'

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Generate new Client ID to be able to request a Session Token
        print('[...]: Client action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: Client action RequestSessionToken')
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
        try:
            del cls.session_manager
        except Exception as e:
            print(
                '[ ! ]: Could not cleanup EWallet Session Manager. '
                'Details: {}'.format(e)
            )

    def test_user_action_create_master_account_functionality(self):
        print('\n[ * ]: Client action NewMaster')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'new',
            'new': 'master', 'master': 'account', 'client_id': self.client_id,
            'session_token': self.session_token, 'user_name': self.user_name_1,
            'user_pass': self.user_pass_1, 'user_email': self.user_email_1,
            'user_phone': self.user_phone_1, 'user_alias': self.user_alias_1,
            'company': self.user_company_1, 'address': self.user_address_1,
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
        self.assertTrue(isinstance(new_account['account_data']['name'], str))
        self.assertTrue(isinstance(new_account['account_data']['alias'], str))
        self.assertTrue(isinstance(new_account['account_data']['phone'], str))
        self.assertTrue(isinstance(new_account['account_data']['create_date'], str))
        self.assertTrue(isinstance(new_account['account_data']['write_date'], str))
        self.assertTrue(isinstance(new_account['account_data']['account_limit'], int))
        self.assertTrue(isinstance(new_account['account_data']['company'], str))
        self.assertTrue(isinstance(new_account['account_data']['address'], str))
        self.assertTrue(isinstance(new_account['account_data']['subordonate_pool'], dict))
        self.assertTrue(isinstance(new_account['account_data']['acquired_ctokens'], list))
