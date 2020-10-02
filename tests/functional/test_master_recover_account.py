import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerMasterUnlinkAccount(unittest.TestCase):
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

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']

        print('[...]: Client action CreateMaster')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_3,
            user_pass=cls.user_pass_3, user_email=cls.user_email_3,
            user_phone=cls.user_phone_3, user_alias=cls.user_alias_3,
            company=cls.user_company_3, address=cls.user_address_3,
        )

        print('[...]: Master action AccountLogin')
        login = cls.session_manager.session_manager_controller(
            controller='master', ctype='action', action='login',
            client_id= cls.client_id, session_token=cls.session_token,
            user_email=cls.user_email_3, user_pass=cls.user_pass_3,
        )

        print('[...]: Master action UnlinkAccount')
        unlink = cls.session_manager.session_manager_controller(
            controller='master', ctype='action', action='unlink',
            unlink='account', client_id=cls.client_id,
            session_token=cls.session_token,
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

    def test_master_action_recover_account_functionality(self):
        print('\n[ * ]: Master action RecoverAccount')
        instruction_set = {
            'controller': 'master', 'ctype': 'action', 'action': 'recover',
            'recover': 'account', 'client_id': self.client_id,
            'session_token': self.session_token,
        }
        recover = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(recover) + '\n'
        )
        self.assertTrue(isinstance(recover, dict))
        self.assertEqual(len(recover.keys()), 4)
        self.assertFalse(recover.get('failed'))
        self.assertTrue(isinstance(recover.get('account'), str))
        self.assertTrue(isinstance(recover.get('account_data'), dict))
        self.assertTrue(isinstance(recover.get('session_data'), dict))
