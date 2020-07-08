import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletUserActionRequestSessionToken(unittest.TestCase):
    session_manager = None
    client_id = None

    @classmethod
    def setUpClass(cls):
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Request client id for session token request
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_request_session_token_functionality(self):
        print('[ * ]: User action Request Session Token')
        session_token = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=self.client_id
        )
        print(str(session_token) + '\n')
        self.assertTrue(isinstance(session_token, dict))
        self.assertEqual(len(session_token.keys()), 2)
        self.assertFalse(session_token.get('failed'))
        self.assertTrue(session_token.get('session_token'))
