import os
import unittest
import base64
from base import ewallet_session_manager as manager


class TestEWalletUserActionIssueReport(unittest.TestCase):
    session_manager = None
    client_id = None
    session_token = None

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

        # Set global values
        cls.session_manager = session_manager
        cls.client_id = client_id['client_id']
        cls.session_token = session_token['session_token']
        log_file_content = '[ ERROR ]: WTF, I did not expect that to happen...'
        content_bytes = log_file_content.encode('ascii')
        base64_bytes = base64.b64encode(content_bytes)
        base64_message = base64_bytes.decode('ascii')
        cls.base64_log = base64_message

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

    def test_user_issue_report_functionality(self):
        print('\n[ * ]: Client action IssueReport')
        issue = {
            'name': 'TestIssue',
            'log': self.base64_log,
            'email': 'test.client@email.com',
            'details': [
                'Error-Type1', 42, None,
                {'failed': True, 'warning': 'Test warning message'},
            ],
        }
        instruction_set = {
            'controller': 'client', 'ctype': 'action', 'action': 'report',
            'report': 'issue', 'session_token': self.session_token,
            'client_id': self.client_id, 'issue': issue
        }
        report = self.session_manager.session_manager_controller(
            **instruction_set
        )
        print(
            '[ > ]: Instruction Set: ' + str(instruction_set) +
            '\n[ < ]: Response: ' + str(report) + '\n'
        )
        self.assertTrue(isinstance(report, dict))
        self.assertEqual(len(report.keys()), 5)
        self.assertFalse(report.get('failed'))
        self.assertTrue(isinstance(report.get('issue'), str))
        self.assertTrue(isinstance(report.get('timestamp'), str))
        self.assertTrue(isinstance(report.get('source'), str))
        self.assertTrue(isinstance(report.get('contact'), str))
