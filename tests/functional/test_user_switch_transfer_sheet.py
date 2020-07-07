import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionSwitchTransferSheet(unittest.TestCase):
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
        # Create new user account to use as SystemCore account mockup
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_1,
            user_pass=cls.user_pass_1, user_email=cls.user_email_1
        )
        # Create new user account to user as Client account mockup
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=cls.client_id,
            session_token=cls.session_token, user_name=cls.user_name_2,
            user_pass=cls.user_pass_2, user_email=cls.user_email_2
        )
        # Login to new user account
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=cls.client_id, session_token=cls.session_token,
            user_name=cls.user_name_2, user_pass=cls.user_pass_2,
        )
        # Create second transfer sheet to have for user action switch
        create = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='transfer',
            transfer='list', client_id=cls.client_id,
            session_token=cls.session_token
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_switch_transfer_sheet(self):
        print('[ * ]: User action Switch Transfer Sheet')
        switch = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='transfer_sheet',
            client_id=self.client_id, session_token=self.session_token,
            sheet_id=2
        )
        print(str(switch) + '\n')
        self.assertTrue(isinstance(switch, dict))
        self.assertEqual(len(switch.keys()), 3)
        self.assertFalse(switch.get('failed'))
        self.assertTrue(isinstance(switch.get('transfer_sheet'), int))
        self.assertTrue(isinstance(switch.get('sheet_data'), dict))
        self.assertTrue(isinstance(switch['sheet_data'].get('id'), int))
        self.assertTrue(isinstance(switch['sheet_data'].get('wallet_id'), int))
        self.assertTrue(isinstance(switch['sheet_data'].get('reference'), str))
        self.assertTrue(isinstance(switch['sheet_data'].get('create_date'), str))
        self.assertTrue(isinstance(switch['sheet_data'].get('write_date'), str))
        self.assertTrue(isinstance(switch['sheet_data'].get('records'), dict))

