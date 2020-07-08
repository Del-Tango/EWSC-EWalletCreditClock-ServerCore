import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionNewSession(unittest.TestCase):
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

    def test_system_new_session_functionality(self):
        print('[ * ]: System Action New Session')
        session = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            reference='EWallet Session Test'
        )
        print(str(session) + '\n')
        self.assertTrue(isinstance(session, dict))
        self.assertEqual(len(session.keys()), 3)
        self.assertFalse(session.get('failed'))
        self.assertTrue(session.get('ewallet_session'))
        self.assertTrue(isinstance(session.get('session_data'), dict))
        self.assertTrue(isinstance(session['session_data']['id'], int))
        self.assertTrue(session['session_data']['orm_session'])


