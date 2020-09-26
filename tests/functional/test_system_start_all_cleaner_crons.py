import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionStartAllCleanerCrons(unittest.TestCase):
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
        print('[ + ]: Prerequisits:')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Generate new Client ID to be able to request a Session Token
        print('[...]: Client action RequestClientID (1)')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: Client action RequestSessionToken (1)')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id']
        )

        # Generate new Client ID to be able to request a Session Token
        print('[...]: Client action RequestClientID (2)')
        client_id2 = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: Client action RequestSessionToken (2)')
        session_token2 = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id2['client_id']
        )

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

    def test_system_action_start_all_cleaner_cros_functionality(self):
        print('\n[ * ]: System action StartAllCleaners')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'start',
            'start': 'cleaner', 'clean': 'all',
        }
        start = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ] Instruction Set: ' + str(instruction_set) +
            '\n[ < ] Response: ' + str(start) + '\n'
        )
        self.assertTrue(isinstance(start, dict))
        self.assertEqual(len(start.keys()), 2)
        self.assertFalse(start.get('failed'))
        self.assertTrue(isinstance(start.get('cleaners'), dict))

