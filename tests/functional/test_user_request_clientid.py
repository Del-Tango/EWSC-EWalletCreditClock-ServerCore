import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletUserActionRequestClientId(unittest.TestCase):
    session_manager = None
    client_id = None

    @classmethod
    def setUpClass(cls):
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Set global values
        cls.session_manager = session_manager

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

    def test_user_request_client_id_functionality(self):
        print('[ * ]: Client action RequestClientID')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'request',
            'request': 'client_id'
        }
        client_id = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(client_id) + '\n'
        )
        self.assertTrue(isinstance(client_id, dict))
        self.assertEqual(len(client_id.keys()), 2)
        self.assertFalse(client_id.get('failed'))
        self.assertTrue(client_id.get('client_id'))


