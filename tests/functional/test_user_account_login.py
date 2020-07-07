import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerUserAccountLogin():
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'

    @classmethod
    def setUpClass(cls):
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Generate new Client ID to be able to request a Session Token
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        # Request a Session Token to be able to operate within a EWallet Session
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )
        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']
        # Create new User Account in EWallet Session using token and client id
        new_account = cls.session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_1,
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_session_login_functionality(self):
        print('[ * ]: User Action Session Login')
        login = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=self.client_id, session_token=self.session_token,
            user_name=self.user_name_1, user_pass=self.user_pass_1,
        )
        print(str(login) + '\n')
        self.assertTrue(isinstance(login, dict))
        self.assertEqual(len(login.keys()), 2)
        self.assertFalse(login.get('failed'))
        self.assertTrue(isinstance(login.get('account'), str))
        self.assertEqual(login.get('account'), self.user_email_1)
