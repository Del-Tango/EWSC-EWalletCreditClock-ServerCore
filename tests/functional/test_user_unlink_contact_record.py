import os, time
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionUnlinkContactRecord(unittest.TestCase):
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
        # Create contact record for action unlink
        add_record = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact',
            contact='record', client_id=cls.client_id,
            session_token=cls.session_token, contact_list=2,
            user_name='Test User Name', user_email=cls.user_email_1,
            user_phone='123454321', user_reference='Test Mockup',
            notes='Notes added by functional test',
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_unlink_contact_record(self):
        print('[ * ]: User action Unlink Contact Record')
        unlink = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='contact',
            contact='record', record_id=1,
            client_id=self.client_id, session_token=self.session_token
        )
        print(str(unlink) + '\n')
        self.assertTrue(isinstance(unlink, dict))
        self.assertEqual(len(unlink.keys()), 3)
        self.assertFalse(unlink.get('failed'))
        self.assertTrue(isinstance(unlink.get('contact_list'), int))
        self.assertTrue(isinstance(unlink.get('contact_record'), int))
