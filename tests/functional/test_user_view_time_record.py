import os
import unittest
import time
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionViewTimeRecord(unittest.TestCase):
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
        print('[ + ]: Prerequisits -')
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
        # Supply EWallet with credits to have available for transfer
        print('[...]: User action Supply EWallet Credits')
        supply = session_manager.session_manager_controller(
            controller='client', ctype='action', action='supply', supply='credits',
            client_id=cls.client_id, session_token=cls.session_token,
            currency='RON', credits=100, cost=4.7,
            notes='EWallet user action Supply notes added by functional test suit.'
        )
        # Convert EWallet credits to Credit Clock minutes
        print('[...]: User action Convert Credits To Clock')
        convert = session_manager.session_manager_controller(
            controller='client', ctype='action', action='convert',
            convert='credits2clock', client_id=cls.client_id,
            session_token=cls.session_token, credits=20,
            notes='EWallet user action Convert Credits To Clock notes added by functional test suit.'
        )
        # Use Credit Clock time
        print('[...]: User action Start Clock Timer')
        start = session_manager.session_manager_controller(
            controller='client', ctype='action', action='start', start='clock_timer',
            client_id=cls.client_id, session_token=cls.session_token
        )
        time.sleep(3)
        print('[...]: User action Stop Clock Timer')
        stop = session_manager.session_manager_controller(
            controller='client', ctype='action', action='stop', stop='clock_timer',
            client_id=cls.client_id, session_token=cls.session_token
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')


    def test_user_action_view_time_record(self):
        print('\n[ * ]: User action View Time Record')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'view',
            'view': 'time', 'time': 'record', 'record_id': 1,
            'client_id': self.client_id, 'session_token': self.session_token
        }
        view = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(view) + '\n'
        )
        self.assertTrue(isinstance(view, dict))
        self.assertEqual(len(view.keys()), 4)
        self.assertFalse(view.get('failed'))
        self.assertTrue(isinstance(view.get('time_sheet'), int))
        self.assertTrue(isinstance(view.get('time_record'), int))
        self.assertTrue(isinstance(view.get('record_data'), dict))
        self.assertTrue(isinstance(view['record_data'].get('id'), int))
        self.assertTrue(isinstance(view['record_data'].get('time_sheet'), int))
        self.assertTrue(isinstance(view['record_data'].get('reference'), str))
        self.assertTrue(isinstance(view['record_data'].get('create_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('write_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('time_start'), str))
        self.assertTrue(isinstance(view['record_data'].get('time_stop'), str))
        self.assertTrue(isinstance(view['record_data'].get('time_spent'), float))
        self.assertTrue(isinstance(view['record_data'].get('time_pending'), float))
        self.assertTrue(isinstance(view['record_data'].get('pending_count'), int))
