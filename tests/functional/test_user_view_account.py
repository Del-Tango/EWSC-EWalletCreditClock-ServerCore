import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionViewAccount(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None
    user_name_1 = 'TestEWalletUser1'
    user_email_1 = 'ewallet1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'
    user_name_2 = 'TestEWalletUser2'
    user_email_2 = 'ewallet2@alvearesolutions.ro'
    user_pass_2 = 'Secret!@#123abc'
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
        print('[ + ]: Prerequisits -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Generate new Client ID to be able to request a Session Token
        print('[...]: User action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: User action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id']
        )

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']

        print('[...]: Client action NewMasterAccount')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_3,
            user_pass=cls.user_pass_3, user_email=cls.user_email_3,
            user_phone=cls.user_phone_3, user_alias=cls.user_alias_3,
            company=cls.user_company_3, address=cls.user_address_3,
        )

        print('[...]: Client action AcquireMaster')
        acquire = session_manager.session_manager_controller(
            controller='client', ctype='action', action='acquire',
            acquire='master', master=cls.user_email_3, key=cls.master_key_code,
            client_id=client_id['client_id'],
            session_token=session_token['session_token']
        )

        # Create new user account to use as SystemCore account mockup
        print('[...]: User action CreateNewAccount (1)')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_1,
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
        )

        # Create new user account to user as Client account mockup
        print('[...]: User action CreateNewAccount (2)')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_2,
            user_pass=cls.user_pass_2, user_email=cls.user_email_2,
            user_phone='123454321', user_alias='Test Alias'
        )

        # Login to new user account
        print('[...]: User action AccountLogin (2)')
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=cls.client_id, session_token=cls.session_token,
            user_email=cls.user_email_2, user_pass=cls.user_pass_2,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_view_account(self):
        print('\n[ * ]: User action ViewAccount')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'view',
            'view': 'account', 'client_id': self.client_id,
            'session_token': self.session_token
        }
        view = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(view) + '\n'
        )
        self.assertTrue(isinstance(view, dict))
        self.assertEqual(len(view.keys()), 3)
        self.assertFalse(view.get('failed'))
        self.assertTrue(isinstance(view.get('account'), str))
        self.assertTrue(isinstance(view.get('account_data'), dict))
        self.assertTrue(isinstance(view['account_data'].get('id'), int))
        self.assertTrue(isinstance(view['account_data'].get('name'), str))
        self.assertTrue(isinstance(view['account_data'].get('create_date'), str))
        self.assertTrue(isinstance(view['account_data'].get('write_date'), str))
        self.assertTrue(isinstance(view['account_data'].get('ewallet'), int))
        self.assertTrue(isinstance(view['account_data'].get('contact_list'), int))
        self.assertTrue(isinstance(view['account_data'].get('email'), str))
        self.assertTrue(isinstance(view['account_data'].get('phone'), str))
        self.assertTrue(isinstance(view['account_data'].get('alias'), str))
        self.assertTrue(isinstance(view['account_data'].get('ewallet_archive'), dict))
        self.assertTrue(isinstance(view['account_data'].get('contact_list_archive'), dict))
