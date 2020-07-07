import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemWorkerCleanup(unittest.TestCase):
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
        # Spawn 3 EWallet Session Workers
        # [ NOTE ]: On cleanup, one of the vacant workers should be reserved if
        # not passed over worker limit defined in config file to handle new
        # session token requests
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_system_action_cleanup_worker_functionality(self):
        print('[ * ]: System action Cleanup Session Workers')
        clean = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='cleanup',
            cleanup='workers'
        )
        print(str(clean) + '\n')
        self.assertTrue(isinstance(clean, dict))
        self.assertEqual(len(clean.keys()), 4)
        self.assertFalse(clean.get('failed'))
        self.assertTrue(isinstance(clean['workers_cleaned'], int))
        self.assertTrue(isinstance(clean.get('worker_pool'), list))
        self.assertTrue(clean.get('worker_reserved'))


