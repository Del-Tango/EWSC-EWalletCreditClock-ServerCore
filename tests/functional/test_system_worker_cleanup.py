import os
import unittest
import datetime
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemWorkerSweepCleanup(unittest.TestCase):
    session_manager = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        cls.session_manager = session_manager

        # Spawn 4 EWallet Session Workers

        # [ NOTE ]: On cleanup, one of the vacant workers should be reserved if
        #           not passed over worker limit defined in config file to handle new
        #           session token requests

        print('[...]: System action CreateWorker (1)')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

        print('[...]: System action CreateWorker (2)')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

        print('[...]: System action CreateWorker (3)')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

        print('[...]: System action CreateWorker (4)')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

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

    def test_system_action_cleanup_worker_functionality(self):
        print('\n[ * ]: System action SweepCleanupWorkers')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'cleanup',
            'cleanup': 'workers'
        }
        clean = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(clean) + '\n'
        )
        self.assertTrue(isinstance(clean, dict))
        self.assertEqual(len(clean.keys()), 7)
        self.assertFalse(clean.get('failed'))
        self.assertTrue(isinstance(clean['workers_cleaned'], int))
        self.assertTrue(isinstance(clean['cleanup_failures'], int))
        self.assertTrue(isinstance(clean['worker_pool'], dict))
        self.assertTrue(isinstance(clean.get('worker_reserved'), int))
        self.assertTrue(isinstance(clean['workers'], list))
        self.assertTrue(isinstance(clean['orphaned_stokens'], list))
