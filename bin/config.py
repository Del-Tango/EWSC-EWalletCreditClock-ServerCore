
class Config():

    def __init__(self, **kwargs):
        self.config = {
            'log': {
                'level': 'debug',
                'files': {
                    'main': 'logs/wallet.log',
                    'debug': 'logs/debug.log',
                    'info': 'logs/info.log',
                    'warning': 'logs/warning.log',
                    'error': 'logs/error.log',
                },
            },
            'client': {
                'account': {
                    'user_name': 'test_user',
                    'user_pass': 'test_pass',
                },
                'wallet_id': 123456,
            },

        }


