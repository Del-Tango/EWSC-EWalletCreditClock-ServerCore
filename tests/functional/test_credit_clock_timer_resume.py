import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionResumeTimer(unittest.TestCase):
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
        # Supply credits to EWallet
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
        # Start EWallet Credit Clock Timer
        print('[...]: User action Start Clock Timer')
        start = session_manager.session_manager_controller(
            controller='client', ctype='action', action='start', start='clock_timer',
            client_id=cls.client_id, session_token=cls.session_token
        )
        # Pause EWallet Credit Clock Timer
        print('[...]: User action Pause Clock Timer')
        pause = session_manager.session_manager_controller(
            controller='client', ctype='action', action='pause', pause='clock_timer',
            client_id=cls.client_id, session_token=cls.session_token
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_resume_clock_timer(self):
        print('\n[ * ]: User action Resume Clock Timer')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'resume',
            'resume': 'clock_timer', 'client_id': self.client_id,
            'session_token': self.session_token
        }
        resume = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(resume) + '\n'
        )
        self.assertTrue(isinstance(resume, dict))
        self.assertEqual(len(resume.keys()), 6)
        self.assertFalse(resume.get('failed'))
        self.assertTrue(isinstance(resume.get('clock'), int))
        self.assertTrue(isinstance(resume.get('pending_count'), int))
        self.assertTrue(isinstance(resume.get('resume_timestamp'), str))
        self.assertTrue(isinstance(resume.get('pause_timestamp'), str))

