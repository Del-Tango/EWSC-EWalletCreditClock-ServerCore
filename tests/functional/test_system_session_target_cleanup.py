import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemSessionCleanupTarget(unittest.TestCase):
    session_manager = None

    @classmethod
    def setUpClass(cls):
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Create first EWallet Session Worker
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        cls.session_manager = session_manager
        # Create datetime object 30 hours in the past
        past_date = datetime.datetime.now() - datetime.timedelta(hours=30)
        # Spawn 3 client ids to create 3 different session tokens with. Mocks 3
        # EWallet Server users
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id'], expiration_date=past_date
        )
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id'], expiration_date=past_date
        )
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id'], expiration_date=past_date
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_system_action_cleanup_target_session(self):
        session = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            expiration_date=datetime.datetime.now() - datetime.timedelta(hours=30)
        )
        print('[ * ]: System action Cleanup Target Ewallet Session')
        clean = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='cleanup',
            cleanup='sessions', session_id=3
        )
        print(str(clean) + '\n')
        self.assertTrue(isinstance(clean, dict))
        self.assertEqual(len(clean.keys()), 2)
        self.assertFalse(clean.get('failed'))
        self.assertTrue(isinstance(clean['sessions_cleaned'], int))
        self.assertEqual(clean['sessions_cleaned'], 1)


