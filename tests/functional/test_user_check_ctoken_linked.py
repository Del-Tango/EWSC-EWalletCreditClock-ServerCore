import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletUserActionCheckCTokenLinked(unittest.TestCase):
    session_manager = None
    client_id = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Request client id for session token request
        print('[...]: Client action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: Client action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id']
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

    def test_user_check_ctoken_linked_functionality(self):
        print('\n[ * ]: Client action CheckCTokenLinked')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'verify',
            'verify': 'ctoken', 'ctoken': 'linked',
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
        self.assertEqual(len(check.keys()), 4)
        self.assertFalse(check.get('failed'))
        self.assertTrue(isinstance(check.get('client_id'), str))
        self.assertTrue(check.get('linked'))
        self.assertTrue(isinstance(check.get('session_token'), str))
