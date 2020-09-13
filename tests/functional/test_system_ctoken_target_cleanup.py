import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemCTokenTargetCleanup(unittest.TestCase):
    session_manager = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Create first EWallet Session Worker
        print('[...]: System action New Session Worker')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        cls.session_manager = session_manager

        # Create datetime object 30 hours in the past
        past_date = datetime.datetime.now() - datetime.timedelta(hours=30)

        # Spawn 3 client ids to create 3 different session tokens with. Mocks 3

        # EWallet Server users
        print('[...]: User action RequestClientID (1)')
        client_id1 = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id', expires_on=past_date
        )

        print('[...]: User action RequestClientID (2)')
        client_id2 = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id', expires_on=past_date
        )

        print('[...]: User action RequestClientID (3)')
        client_id3 = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id', expires_on=past_date
        )

        cls.client_id = client_id1['client_id']

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_system_action_sweep_cleanup_client_tokens(self):
        print('\n[ * ]: System action SweepCleanupCTokens')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'cleanup',
            'cleanup': 'ctokens', 'client_id': self.client_id,
        }
        clean = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(clean) + '\n'
        )
        self.assertTrue(isinstance(clean, dict))
        self.assertEqual(len(clean.keys()), 10)
        self.assertFalse(clean.get('failed'))
        self.assertTrue(isinstance(clean['ctokens_cleaned'], int))
        self.assertTrue(isinstance(clean['sessions_cleaned'], int))
        self.assertTrue(isinstance(clean['cleanup_failures'], int))
        self.assertTrue(isinstance(clean['ctokens'], list))
        self.assertTrue(isinstance(clean['stokens_cleaned'], int))
        self.assertTrue(isinstance(clean['stokens'], list))
        self.assertTrue(isinstance(clean['worker_count'], int))
        self.assertTrue(isinstance(clean['workers'], list))
        self.assertTrue(isinstance(clean['sessions'], list))
