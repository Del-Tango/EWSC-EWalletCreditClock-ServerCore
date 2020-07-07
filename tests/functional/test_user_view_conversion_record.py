import os
import unittest
import time
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionViewConversionRecord(unittest.TestCase):
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
        # Add new contact record to populate active contact list
        add_contact_record = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact',
            contact='record', client_id=cls.client_id,
            session_token=cls.session_token, contact_list=2,
            user_name='Test User Name', user_email=cls.user_email_1,
            user_phone='123454321', user_reference='Test Mockup',
            notes='Notes added by functional test',
        )
        # Supply EWallet with credits to have available for transfer
        supply = session_manager.session_manager_controller(
            controller='client', ctype='action', action='supply', supply='credits',
            client_id=cls.client_id, session_token=cls.session_token,
            currency='RON', credits=100, cost=4.7,
            notes='EWallet user action Supply notes added by functional test suit.'
        )
        # Convert EWallet credits to Credit Clock minutes
        convert = session_manager.session_manager_controller(
            controller='client', ctype='action', action='convert',
            convert='credits2clock', client_id=cls.client_id,
            session_token=cls.session_token, credits=20,
            notes='EWallet user action Convert Credits To Clock notes added by functional test suit.'
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_view_conversion_record(self):
        print('[ * ]: User action View Conversion Record')
        view = self.session_manager.session_manager_controller(
            controller='client', ctype='action', action='view', view='conversion',
            conversion='record', record_id=1, client_id=self.client_id,
            session_token=self.session_token
        )
        print(str(view) + '\n')
        self.assertTrue(isinstance(view, dict))
        self.assertEqual(len(view.keys()), 4)
        self.assertFalse(view.get('failed'))
        self.assertTrue(isinstance(view.get('conversion_sheet'), int))
        self.assertTrue(isinstance(view.get('conversion_record'), int))
        self.assertTrue(isinstance(view.get('record_data'), dict))
        self.assertTrue(isinstance(view['record_data'].get('id'), int))
        self.assertTrue(isinstance(view['record_data'].get('conversion_sheet_id'), int))
        self.assertTrue(isinstance(view['record_data'].get('reference'), str))
        self.assertTrue(isinstance(view['record_data'].get('create_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('write_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('conversion_type'), str))
        self.assertTrue(isinstance(view['record_data'].get('minutes'), float))
        self.assertTrue(isinstance(view['record_data'].get('credits'), int))
