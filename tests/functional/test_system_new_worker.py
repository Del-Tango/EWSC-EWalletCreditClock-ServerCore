import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionNewWorker(unittest.TestCase):
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
        # Spawn new EWallet Session with no active user or session token
        session = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            reference='EWallet Session Test'
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_system_new_worker_functionality(self):
        print('[ * ]: System Action New Worker')
        worker = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        print(str(worker) + '\n')
        self.assertTrue(isinstance(worker, dict))
        self.assertEqual(len(worker.keys()), 2)
        self.assertFalse(worker.get('failed'))
        self.assertTrue(worker.get('worker'))

