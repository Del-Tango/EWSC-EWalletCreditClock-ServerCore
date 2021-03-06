import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemActionNewSession(unittest.TestCase):
    session_manager = None

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Create first EWallet Session Worker
        print('[...]: System action CreateWorker')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )
        cls.session_manager = session_manager

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

    def test_system_new_session_functionality(self):
        print('\n[ * ]: System action CreateSession')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'new',
            'new': 'session', 'reference': 'EWallet Session Test'
        }
        session = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(session) + '\n'
        )
        self.assertTrue(isinstance(session, dict))
        self.assertEqual(len(session.keys()), 3)
        self.assertFalse(session.get('failed'))
        self.assertTrue(isinstance(session.get('worker'), int))
        self.assertTrue(isinstance(session.get('ewallet_session'), int))


