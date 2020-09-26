import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionCreateTransferSheet(unittest.TestCase):
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

        print('[...]: Client action NewMaster')
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
        print('[...]: User action CreateAccount (1)')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_1,
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
        )

        # Create new user account to user as Client account mockup
        print('[...]: User action CreateAccount (2)')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_2,
            user_pass=cls.user_pass_2, user_email=cls.user_email_2
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
        try:
            del cls.session_manager
        except Exception as e:
            print(
                '[ ! ]: Could not cleanup EWallet Session Manager. '
                'Details: {}'.format(e)
            )

    def test_user_action_create_transfer_sheet(self):
        print('\n[ * ]: User action CreateTransferSheet')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'new',
            'new': 'transfer', 'transfer': 'list', 'client_id': self.client_id,
            'session_token': self.session_token
        }
        create = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(create) + '\n'
        )
        self.assertTrue(isinstance(create, dict))
        self.assertEqual(len(create.keys()), 3)
        self.assertFalse(create.get('failed'))
        self.assertTrue(isinstance(create.get('transfer_sheet'), int))
        self.assertTrue(isinstance(create.get('sheet_data'), dict))
        self.assertTrue(isinstance(create['sheet_data'].get('id'), int))
        self.assertTrue(isinstance(create['sheet_data'].get('ewallet'), int))
        self.assertTrue(isinstance(create['sheet_data'].get('reference'), str))
        self.assertTrue(isinstance(create['sheet_data'].get('create_date'), str))
        self.assertTrue(isinstance(create['sheet_data'].get('write_date'), str))
        self.assertTrue(isinstance(create['sheet_data'].get('records'), dict))
