import os
import datetime
import unittest
from base import ewallet_session_manager as manager


class TestEWalletSessionManagerSystemUnfreezeMaster(unittest.TestCase):
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

        # Create first EWallet Session Worker
        print('[...]: System action CreateWorker')
        worker = session_manager.session_manager_controller(
            controller='system', ctype='action', action='new', new='worker'
        )

        # Create datetime object 30 hours in the past
        past_date = datetime.datetime.now() - datetime.timedelta(days=31)

        # EWallet Server users
        print('[...]: Client action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        print('[...]: Client action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id'],
            expiration_date=past_date
        )

        # Create new master user account to acquire
        print('[...]: Client action CreateMaster')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_name=cls.user_name_3, user_pass=cls.user_pass_3,
            user_email=cls.user_email_3, user_phone=cls.user_phone_3,
            user_alias=cls.user_alias_3, company=cls.user_company_3,
            address=cls.user_address_3,
        )

        print('[...]: Client action AcquireMaster')
        acquire = session_manager.session_manager_controller(
            controller='client', ctype='action', action='acquire',
            acquire='master', master=cls.user_email_3, key=cls.master_key_code,
            client_id=client_id['client_id'],
            session_token=session_token['session_token']
        )

        print('[...]: User action CreateAccount')
        new_account = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new',
            new='account', client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_name=cls.user_name_1, user_pass=cls.user_pass_1,
            user_email=cls.user_email_1
        )

        print('[...]: System action FreezeMaster')
        freeze_master = session_manager.session_manager_controller(
            controller='system', ctype='action', action='freeze',
            freeze='master', master_id=master['account_data']['id'],
        )

        # Set global values
        cls.session_manager = session_manager
        cls.worker = worker
        cls.client_id = client_id
        cls.session_token = session_token
        cls.master = master

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

    def test_system_action_unfreeze_master_account(self):
        print('\n[ * ]: System action UnfreezeMaster')
        instruction_set = {
            'controller': 'system', 'ctype': 'action', 'action': 'unfreeze',
            'unfreeze': 'master', 'master_id': self.master['account_data']['id']
        }
        clean = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(clean) + '\n'
        )
        self.assertTrue(isinstance(clean, dict))
        self.assertEqual(len(clean.keys()), 7)
        self.assertFalse(clean.get('failed'))
        self.assertTrue(isinstance(clean['masters'], list))
        self.assertTrue(isinstance(clean['subordonates'], list))
        self.assertTrue(isinstance(clean['masters_activated'], int))
        self.assertTrue(isinstance(clean['subordonates_activated'], int))
        self.assertTrue(isinstance(clean['activation_failures'], int))
        self.assertTrue(isinstance(clean['activation_count'], int))

