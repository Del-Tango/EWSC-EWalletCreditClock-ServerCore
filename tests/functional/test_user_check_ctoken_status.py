import os
import unittest
from base import ewallet_session_manager as manager


class TestEWalletUserActionCheckCTokenStatus(unittest.TestCase):
    session_manager = None
    client_id = None
    user_name_1 = 'TestEWalletMaster1'
    user_alias_1 = 'TEWM1'
    user_email_1 = 'master1@alvearesolutions.ro'
    user_pass_1 = 'abc123!@#Secret'
    user_phone_1 = '555 555 555'
    user_company_1 = 'TestClient INC'
    user_address_1 = 'Iasi, jud. Iasi, Str. Canta, Nr. 40'
    master_key_code = 'EWSC-Master-Key-Code'

    @classmethod
    def setUpClass(cls):
        print('[ + ]: Prerequisites -')
        # Create new EWallet Session Manager instance
        session_manager = manager.EWalletSessionManager()

        # Request client id for session token request
        print('[...]: Client action RequestClientID')
        client_id = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='client_id'
        )

        # Request a Session Token to be able to operate within a EWalletSession
        print('[...]: Client action RequestSessionToken')
        session_token = session_manager.session_manager_controller(
            controller='client', ctype='action', action='request',
            request='session_token', client_id=client_id['client_id']
        )

        print('[...]: Client action NewMaster')
        master = session_manager.session_manager_controller(
            controller='client', ctype='action', action='new', new='master',
            master='account', client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            user_name=cls.user_name_1, user_email=cls.user_email_1,
            user_pass=cls.user_pass_1
        )

        print('[...]: Client action AcquireMaster')
        acquire = session_manager.session_manager_controller(
            controller='client', ctype='action', action='acquire',
            acquire='master', key=cls.master_key_code, master=cls.user_email_1,
            client_id=client_id['client_id'],
            session_token=session_token['session_token']
        )

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']

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

    def test_user_check_ctoken_status_functionality(self):
        print('\n[ * ]: Client action CheckCTokenStatus')
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'verify',
            'verify': 'ctoken', 'ctoken': 'status',
            'client_id': self.client_id
        }
        check = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(check) + '\n'
        )
        self.assertTrue(isinstance(check, dict))
        self.assertEqual(len(check.keys()), 9)
        self.assertFalse(check.get('failed'))
        self.assertTrue(isinstance(check.get('client_id'), str))
        self.assertTrue(check.get('valid'))
        self.assertTrue(check.get('linked'))
        self.assertTrue(check.get('plugged'))
        self.assertTrue(check.get('master'))
        self.assertTrue(isinstance(check.get('session_token'), str))
        self.assertTrue(isinstance(check.get('session'), int))
        self.assertTrue(isinstance(check.get('acquired'), str))
