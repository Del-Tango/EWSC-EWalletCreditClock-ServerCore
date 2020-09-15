import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletUserActionCheckCTokenValid(unittest.TestCase):
    session_manager = None
    client_id = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Request client id for session token request
        print('[...]: User action RequestClientID')
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

    def test_user_check_ctoken_valid_functionality(self):
        print('\n[ * ]: User action CheckCTokenValid')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'verify',
            'verify': 'ctoken', 'ctoken': 'validity',
            'client_id': self.client_id
        }
        check = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(check) + '\n'
        )
        self.assertTrue(isinstance(check, dict))
        self.assertEqual(len(check.keys()), 5)
        self.assertFalse(check.get('failed'))
        self.assertTrue(isinstance(check.get('client_id'), str))
        self.assertTrue(check.get('valid'))
        self.assertTrue(check.get('registered'))
        self.assertFalse(check.get('expired'))
