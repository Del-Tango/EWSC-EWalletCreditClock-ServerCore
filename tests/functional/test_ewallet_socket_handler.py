import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSocketHandler(unittest.TestCase):
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

        # Spawn new EWallet Session with no active user or session token
        print('[...]: System action CreateSession\n')
        session = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            reference='EWallet Session Test'
        )

        print('[ * ]: System Action OpenSockets')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'open',
            'opening': 'sockets', 'in_port': 8080, 'out_port': 8081,
        }
        print('[ > ] Instruction Set: {}'.format(instruction_set))
        _in_port = cls.session_manager.session_manager_controller(**instruction_set)
        print('[ < ] Response: {}'.format(str(_in_port)) + '\n')

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

#   def test_open_instruction_listener_port(self):
#       print('[ * ]: System Action OpenSockets')
#       instruction_set = {
#           'controller': 'system', 'ctype': 'action', 'action': 'open',
#           'opening': 'sockets', 'in_port': 8080, 'out_port': 8081,
#       }
#       print('[ > ] Instruction Set: {}'.format(instruction_set))
#       _in_port = self.session_manager.session_manager_controller(**instruction_set)
#       print('[ < ] Response: {}'.format(str(_in_port)) + '\n')
#       return _in_port

    '''
    [ NOTE ]: For interactive testing only with a listener on specified
              instruction response port.

    [ USE CASE ]:
        $~ nc -l -p 8081
        $~ python3 -m unittest <test>.py
        $~ echo "{'controller': 'system', ...}" | nc localhost 8080

    [ WARNING ]: Uncommented will hang upon running the entire test suit.
    '''
#   def test_instruction_set_listener(self):
#       print('[ * ]: System Action StartInstructionListener')
#       instruction_set = {
#           'controller': 'system', 'ctype': 'action', 'action': 'start',
#           'start': 'listener',
#       }
#       print('[ > ] Instruction Set: {}'.format(instruction_set))
#       listen = self.session_manager.session_manager_controller(**instruction_set)
#       print('[ < ] Response: {}'.format(str(listen)) + '\n')
#       return listen

    def test_close_instruction_listener_port(self):
        print('[ * ]: System Action CloseSockets')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'close',
            'closing': 'sockets',
        }
        print('[ > ] Instruction Set: {}'.format(instruction_set))
        _in_port = self.session_manager.session_manager_controller(**instruction_set)
        print('[ < ] Response: {}'.format(str(_in_port)) + '\n')
        return _in_port
