import os
import unittest
import pysnooper
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerUserReleaseMasterAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'
    user_name_3 = 'TestEWalletMaster3'
    user_alias_3 = 'TEWM3'
    user_email_3 = 'master3@alvearesolutions.ro'
    user_pass_3 = 'abc123!@#Secret'
    user_phone_3 = '555 555 555'
    user_company_3 = 'TestClient INC'
    user_address_3 = 'Iasi, jud. Iasi, Str. Canta, Nr. 40'
    master_key_code = 'EWSC-Master-Key-Code'

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
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id']
        )

        # Create new master user account to acquire
        print('[...]: Client action CreateMaster')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_email=cls.user_email_3, user_pass=cls.user_pass_3,
            user_name=cls.user_name_3,
        )

        print('[...]: Client action AcquireMaster')
        acquire = session_manager.session_manager_controller(
            controller='client', ctype='action', action='acquire',
            acquire='master', master=cls.user_email_3,
            key=cls.master_key_code, client_id=client_id['client_id'],
            session_token=session_token['session_token']
        )

        print('[...]: User action CreateAccount')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='account',
            client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_name=cls.user_name_1, user_pass=cls.user_pass_1,
            user_email=cls.user_email_1
        )

        print('[...]: User action AccountLogin')
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
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

    def test_user_action_release_master_account_functionality(self):
        print('\n[ * ]: Client action ReleaseMaster')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'release',
            'release': 'master', 'client_id': self.client_id,
            'session_token': self.session_token,
            'master': self.user_email_1, 'key': self.master_key_code,
        }
        release_master = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(release_master) + '\n'
        )
        self.assertTrue(isinstance(release_master, dict))
        self.assertEqual(len(release_master.keys()), 4)
        self.assertFalse(release_master.get('failed'))
        self.assertTrue(isinstance(release_master.get('client_id'), str))
        self.assertTrue(isinstance(release_master.get('released'), str))
        self.assertTrue(isinstance(release_master.get('ctoken_data'), dict))

