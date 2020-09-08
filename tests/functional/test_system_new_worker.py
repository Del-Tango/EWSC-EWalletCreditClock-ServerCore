import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionNewWorker(unittest.TestCase):
    session_manager = None

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

    def test_system_new_worker_functionality(self):
        print('[ * ]: System action NewWorker')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'new',
            'new': 'worker'
        }
        worker = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(worker) + '\n'
        )
        self.assertTrue(isinstance(worker, dict))
        self.assertEqual(len(worker.keys()), 3)
        self.assertFalse(worker.get('failed'))
        self.assertTrue(isinstance(worker.get('worker'), int))
        self.assertTrue(isinstance(worker.get('worker_data'), dict))
        self.assertTrue(list(worker['worker_data'].keys()))

