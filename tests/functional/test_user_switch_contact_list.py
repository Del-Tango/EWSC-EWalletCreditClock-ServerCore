import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionSwitchContactList(unittest.TestCase):
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
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()
        # Generate new Client ID to be able to request a Session Token
        print('[...]: User action Request Client ID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )
        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: User action Request Session Token')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )
        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']
        # Create new user account to use as SystemCore account mockup
        print('[...]: User action Create New Account')
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
        print('[...]: User action Account Login')
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=cls.client_id, session_token=cls.session_token,
            user_name=cls.user_name_2, user_pass=cls.user_pass_2,
        )
        # Create second contact list to have for user action switch
        print('[...]: User action Create Contact List')
        create = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact',
            contact='list', client_id=cls.client_id,
            session_token=cls.session_token,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_switch_contact_list(self):
        print('\n[ * ]: User action Switch Contact List')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'switch',
            'switch': 'contact_list', 'list_id': 2, 'client_id': self.client_id,
            'session_token': self.session_token
        }
        switch = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(switch) + '\n'
        )
        self.assertTrue(isinstance(switch, dict))
        self.assertEqual(len(switch.keys()), 3)
        self.assertFalse(switch.get('failed'))
        self.assertTrue(isinstance(switch.get('contact_list'), int))
        self.assertTrue(isinstance(switch.get('list_data'), dict))
        self.assertTrue(isinstance(switch['list_data'].get('id'), int))
        self.assertTrue(isinstance(switch['list_data'].get('user'), int))
        self.assertTrue(isinstance(switch['list_data'].get('reference'), str))
        self.assertTrue(isinstance(switch['list_data'].get('create_date'), str))
        self.assertTrue(isinstance(switch['list_data'].get('write_date'), str))
        self.assertTrue(isinstance(switch['list_data'].get('records'), dict))
