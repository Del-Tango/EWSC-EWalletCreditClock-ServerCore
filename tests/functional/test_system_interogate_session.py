import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionInterogateSession(unittest.TestCase):
    session_manager = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisits:')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Create first EWallet Session Worker
        print('[...]: System action NewWorker')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        cls.session_manager = session_manager
        # Spawn new EWallet Session with no active user or session token
        print('[...]: System action NewSession')
        session = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            reference='EWallet Session Test'
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

    def test_system_action_interogate_ewallet_session_functionality(self):
        print('\n[ * ]: System action InterogateEWalletSession')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'interogate',
            'interogate': 'session', 'session_id': 2
        }
        interogate = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ] Instruction Set: ' + str(instruction_set) +
            '\n[ < ] Response: ' + str(interogate) + '\n'
        )
        self.assertTrue(isinstance(interogate, dict))
        self.assertEqual(len(interogate.keys()), 4)
        self.assertFalse(interogate.get('failed'))
        self.assertTrue(isinstance(interogate.get('ewallet_session'), int))
        self.assertTrue(isinstance(interogate.get('session_data'), dict))
        self.assertTrue(isinstance(interogate.get('worker'), int))
