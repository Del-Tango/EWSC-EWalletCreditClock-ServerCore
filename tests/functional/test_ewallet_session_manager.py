import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemController(unittest.TestCase):
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

    def test_system_action_interogate_ewallet_session_functionality(self):
        print('[ * ]: System action Interogate EWallet Session')
        interogate = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='interogate',
            interogate='session', session_id=1
        )
        print(str(interogate) + '\n')
        self.assertTrue(isinstance(interogate, dict))
        self.assertEqual(len(interogate.keys()), 3)
        self.assertFalse(interogate.get('failed'))
        self.assertTrue(isinstance(interogate.get('ewallet_session'), int))
        self.assertTrue(isinstance(interogate.get('session_data'), dict))

    def test_system_action_interogate_ewallet_workers_functionality(self):
        print('[ * ]: System action Interogate EWallet Workers')
        interogate = self.session_manager.session_manager_controller(
            controller='system', ctype='action', action='interogate',
            interogate='workers'
        )
        print(str(interogate) + '\n')
        self.assertTrue(isinstance(interogate, dict))
        self.assertEqual(len(interogate.keys()), 2)
        self.assertFalse(interogate.get('failed'))
        self.assertTrue(isinstance(interogate.get('workers'), dict))

#   def test_instruction_set_listener(self):
#       log.debug('')
#       print('[ * ]: System Action Start Instruction Set Listener')
#       listen = self.session_manager_controller(
#               controller='system', ctype='action', action='start',
#               start='instruction_listener'
#               )
#       print(str(listen) + '\n')
#       return listen

#   def test_open_instruction_listener_port(self):
#       log.debug('')
#       print('[ * ]: System Action Open Instruction Listener Port')
#       _in_port = self.session_manager_controller(
#               controller='system', ctype='action', action='open',
#               opening='sockets', in_port=8080, out_port=8081
#               )
#       print(str(_in_port) + '\n')
#       return _in_port

#   def test_close_instruction_listener_port(self):
#       log.debug('')
#       print('[ * ]: System Action Close Instruction Listener Port')
#       _in_port = self.session_manager_controller(
#               controller='system', ctype='action', action='close',
#               closing='sockets',
#               )
#       print(str(_in_port) + '\n')
#       return _in_port


class TestEWalletSessionManager(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None

    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'

    user_name_2 = 'TestEWalletUser2'
    user_email_2 = 'ewallet2@alvearesolutions.ro'
    user_pass_2 = 'Secret!@#123abc'

    @classmethod
    def setUpClass(cls):
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Generate new Client ID to be able to request a Session Token
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        # Request a Session Token to be able to operate within a EWallet Session
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )
        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']


    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_request_client_id_functionality(self):
        print('[ * ]: User Action Request Client ID')
        client_id = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        print(str(client_id) + '\n')
        self.assertTrue(isinstance(client_id, dict))
        self.assertEqual(len(client_id.keys()), 2)
        self.assertFalse(client_id.get('failed'))
        self.assertTrue(client_id.get('client_id'))

    def test_user_request_session_token_functionality(self):
        print('[ * ]: User action Request Session Token')
        session_token = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=self.client_id
        )
        print(str(session_token) + '\n')
        self.assertTrue(isinstance(session_token, dict))
        self.assertEqual(len(session_token.keys()), 2)
        self.assertFalse(session_token.get('failed'))
        self.assertTrue(session_token.get('session_token'))

if __name__ == '__main__':
    unittest.main()


