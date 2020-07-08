import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSocketHandler(unittest.TestCase):
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
