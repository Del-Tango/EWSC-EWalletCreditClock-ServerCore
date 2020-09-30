import os
import unittest
import pysnooper
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerUserAcquireMasterAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletMaster1'
    user_alias_1 = 'TEWM1'
    user_email_1 = 'master1@alvearesolutions.ro'
    user_key_1 = 'EWSC-Master-Key-Code'
    user_pass_1 = 'abc123!@#Secret'
    user_phone_1 = '555 555 555'
    user_company_1 = 'TestClient INC'
    user_address_1 = 'Iasi, jud. Iasi, Str. Canta, Nr. 40'

    @classmethod
#   @pysnooper.snoop()
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Generate new Client ID to be able to request a Session Token
        print('[...]: Client action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: Client action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )

        # Create new master user account to acquire
        print('[...]: Client action NewMaster')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_email=cls.user_email_1, user_pass=cls.user_pass_1,
            user_name=cls.user_name_1,
        )

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']
        cls.master = master

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

    def test_user_action_acquire_master_account_functionality(self):
        print('\n[ * ]: Client action AcquireMaster')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'acquire',
            'acquire': 'master', 'client_id': self.client_id,
            'session_token': self.session_token, 'master': self.user_email_1,
            'key': self.user_key_1,
        }
        acquire_master = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(acquire_master) + '\n'
        )
        self.assertTrue(isinstance(acquire_master, dict))
        self.assertEqual(len(acquire_master.keys()), 3)
        self.assertFalse(acquire_master.get('failed'))
        self.assertTrue(isinstance(acquire_master.get('client_id'), str))
        self.assertTrue(isinstance(acquire_master.get('master'), str))

