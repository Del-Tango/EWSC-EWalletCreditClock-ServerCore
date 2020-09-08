import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManageUserActionViewInvoiceRecord(unittest.TestCase):
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
        print('[...]: User action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWallet Session
        print('[...]: User action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request', request='session_token',
            client_id=client_id['client_id']
        )

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']

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
            user_pass=cls.user_pass_2, user_email=cls.user_email_2
        )

        # Login to new user account
        print('[...]: User action AccountLogin (2)')
        login = session_manager.session_manager_controller(
            controller='client', ctype='action', action='login',
            client_id=cls.client_id, session_token=cls.session_token,
            user_pass=cls.user_pass_2, user_email=cls.user_email_2
        )

        # Supply EWallet with credits to have available for pay
        print('[...]: User action SupplyCredits')
        supply = session_manager.session_manager_controller(
            controller='client', ctype='action', action='supply',
            supply='credits', client_id=cls.client_id,
            session_token=cls.session_token, currency='RON',
            credits=100, cost=4.7,
            notes='EWallet user action SupplyCredits notes added by '
                  'EWSC functional test suit.'
        )

        # Pay partner to generate invoice sheet
        print('[...]: User action PayCredits')
        pay = cls.session_manager.session_manager_controller(
            controller='client', ctype='action', action='pay',
            pay=cls.user_email_1, credits=50, client_id=cls.client_id,
            session_token=cls.session_token,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean Sqlite3 database used for testing environment
        if os.path.isfile('data/ewallet.db'):
            os.remove('data/ewallet.db')

    def test_user_action_view_invoice_record(self):
        print('\n[ * ]: User action ViewInvoiceRecord')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'view',
            'view': 'invoice', 'invoice': 'record', 'record_id': 2,
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
        self.assertTrue(isinstance(view.get('invoice_sheet'), int))
        self.assertTrue(isinstance(view.get('invoice_record'), int))
        self.assertTrue(isinstance(view.get('record_data'), dict))
        self.assertTrue(isinstance(view['record_data'].get('id'), int))
        self.assertTrue(isinstance(view['record_data'].get('invoice_sheet'), int))
        self.assertTrue(isinstance(view['record_data'].get('reference'), str))
        self.assertTrue(isinstance(view['record_data'].get('create_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('write_date'), str))
        self.assertTrue(isinstance(view['record_data'].get('credits'), int))
        self.assertTrue(isinstance(view['record_data'].get('currency'), str))
        self.assertTrue(isinstance(view['record_data'].get('cost'), float))
        self.assertTrue(isinstance(view['record_data'].get('seller'), int))
        self.assertTrue(isinstance(view['record_data'].get('notes'), str))
