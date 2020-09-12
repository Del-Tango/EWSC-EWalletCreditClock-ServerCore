import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionStartWorkerCleanerCron(unittest.TestCase):
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
        print('[...]: User action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: User action RequestSessionToken')
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

    def test_system_action_start_worker_cleaner_cron_functionality(self):
        print('\n[ * ]: System action StartWorkerCleaner')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'start',
            'start': 'cleaner', 'clean': 'workers',
        }
        start = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ] Instruction Set: ' + str(instruction_set) +
            '\n[ < ] Response: ' + str(start) + '\n'
        )
        self.assertTrue(isinstance(start, dict))
        self.assertEqual(len(start.keys()), 3)
        self.assertFalse(start.get('failed'))
        self.assertTrue(isinstance(start.get('cron'), str))
        self.assertTrue(isinstance(start.get('pool_entry'), dict))

