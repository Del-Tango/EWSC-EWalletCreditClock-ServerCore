import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionInterogateWorkers(unittest.TestCase):
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
        # Spawn new EWallet Session with no active user or session token
        print('[...]: System action New EWallet Session')
        session = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            reference='EWallet Session Test'
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_system_action_interogate_ewallet_workers_functionality(self):
        print('[ * ]: System action Interogate EWallet Workers')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'interogate',
            'interogate': 'workers'
        }
        interogate = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(interogate) + '\n'
        )
        self.assertTrue(isinstance(interogate, dict))
        self.assertEqual(len(interogate.keys()), 2)
        self.assertFalse(interogate.get('failed'))
        self.assertTrue(isinstance(interogate.get('workers'), dict))


