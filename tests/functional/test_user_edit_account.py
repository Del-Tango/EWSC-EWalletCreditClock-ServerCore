import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionEditAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'
    user_name_2 = 'TestEWalletUser2'
    user_email_2 = 'ewallet2@alvearesolutions.ro'
    user_pass_2 = 'Secret!@#123abc'

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
        # Create new user account to use as SystemCore account mockup
        print('[...]: User action Create New Account')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_1,
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
        )
        # Create new user account to user as Client account mockup
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_2,
            user_pass=cls.user_pass_2, user_email=cls.user_email_2,
            user_phone='123454321', user_alias='Test Alias'
        )
        # Login to new user account
        print('[...]: User action Account Login')
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=cls.client_id, session_token=cls.session_token,
            user_name=cls.user_name_2, user_pass=cls.user_pass_2,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_edit_account(self):
        print('[ * ]: User action Edit Account')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'edit',
            'edit': 'account', 'client_id': self.client_id,
            'session_token': self.session_token, 'user_name': 'Edited',
            'user_phone': 'Edited', 'user_email': 'Edited', 'user_pass': 'Edited',
            'user_alias': 'Edited'
        }
        edit = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(edit) + '\n'
        )
        self.assertTrue(isinstance(edit, dict))
        self.assertEqual(len(edit.keys()), 4)
        self.assertFalse(edit.get('failed'))
        self.assertTrue(isinstance(edit.get('account'), str))
        self.assertTrue(isinstance(edit.get('edit'), dict))
        self.assertTrue(isinstance(edit['edit'].get('user_name'), bool))
        self.assertTrue(isinstance(edit['edit'].get('user_pass'), bool))
        self.assertTrue(isinstance(edit['edit'].get('user_alias'), bool))
        self.assertTrue(isinstance(edit['edit'].get('user_email'), bool))
        self.assertTrue(isinstance(edit['edit'].get('user_phone'), bool))
        self.assertTrue(isinstance(edit.get('account_data'), dict))
        self.assertTrue(isinstance(edit['account_data'].get('id'), int))
        self.assertTrue(isinstance(edit['account_data'].get('user_name'), str))
        self.assertTrue(isinstance(edit['account_data'].get('create_date'), str))
        self.assertTrue(isinstance(edit['account_data'].get('write_date'), str))
        self.assertTrue(isinstance(edit['account_data'].get('credit_wallet'), int))
        self.assertTrue(isinstance(edit['account_data'].get('contact_list'), int))
        self.assertTrue(isinstance(edit['account_data'].get('user_email'), str))
        self.assertTrue(isinstance(edit['account_data'].get('user_phone'), str))
        self.assertTrue(isinstance(edit['account_data'].get('user_alias'), str))
        self.assertTrue(isinstance(edit['account_data'].get('state_code'), int))
        self.assertTrue(isinstance(edit['account_data'].get('state_name'), str))
        self.assertTrue(isinstance(edit['account_data'].get('credit_wallet_archive'), dict))
        self.assertTrue(isinstance(edit['account_data'].get('contact_list_archive'), dict))
