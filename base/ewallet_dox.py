import logging
import pysnooper

from base.config import Config
from base.res_utils import ResUtils

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])

# TODO - Fetch user action manual content from doc files, evaluate type

def display_user_action_recover_account_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateAccount',
            'AccountLogin',
            'UnlinkAccount',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'recover',
            'recover': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'account_data': {
                'id': '<account-id type-int>',
                'name': '<account-user-name type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'ewallet': '<active-ewallet-id type-int>',
                'contact_list': '<active-contact-list-id type-int>',
                'email': '<account-user-email type-str>',
                'phone': '<account-user-phone type-str>',
                'alias': '<account-user-alias type-str>',
                'state_code': '<account-state-code type-int>',
                'state_name': '<account-state-label type-int>',
                'to_unlink': '<flag type-bool>',
                'to_unlink_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC or None>',
                'ewallet_archive': {
                    '<ewallet-id type-int>': '<ewallet-reference type-str>'
                },
                'contact_list_archive':{
                    '<contact-list-id type-int>': '<contact-list-reference type-str>'
                },
            },
            'session_data': {
                'session_user_account': '<account-user-email type-str>',
                'session_credit_ewallet': '<active-session-ewallet-id type-int>',
                'session_contact_list': '<active-session-contact-list-id type-int>',
                'session_account_archive': {
                    '<account-user-email type-str>': '<account-user-name type-str>',
                },
            },
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_pause_clock_timer_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
            'StartClockTimer',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'pause',
            'pause': 'clock_timer',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<clock-id type-int>',
            'pending_time': '<minutes-spent-pending type-float>',
            'start_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'pause_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'pending_count': '<number-of-session-pendings type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_resume_clock_timer_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
            'StartClockTimer',
            'PauseClockTimer',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'resume',
            'resume': 'clock_timer',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>'
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<clock-id type-int>',
            'pending_time': '<minutes-spent-pending type-float>',
            'pause_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'resume_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'pending_count': '<number-of-session-pendings type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_start_clock_timer_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'start',
            'start': 'clock_timer',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<clock-id type-int>',
            'start_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_stop_clock_timer_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyEWalletCredits',
            'ConvertCreditsToClock',
            'StartClockTimer',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'stop',
            'stop': 'clock_timer',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>'
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<clock-id type-int>',
            'pending_count': '<number-of-session-pendings type-int>',
            'pending_time': '<minutes-spent-pending type-float>',
            'start_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'stop_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
            'minutes_spent': '<clock-minutes-used type-float>',
            'time_record': '<record-id type-int>',
            'record_data': {
                'id': '<record-id type-int>',
                'time_sheet': '<time-sheet-id type-int>',
                'reference': '<record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_start': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_stop': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_spent': '<clock-minutes-used type-float>',
                'time_pending': '<minutes-spent-pending type-float>',
                'pending_count': '<number-of-session-pendings type-int>',
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_account_login_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'login',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'user_name': '<account-user-name type-str>',
            'user_pass': '<account-user-pass type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'session_data': {
                'session_user_account': '<account-user-email type-str>',
                'session_credit_ewallet': '<active-session-ewallet-id type-int>',
                'session_contact_list': '<active-session-contact-list-id type-int>',
                'session_account_archive': {
                    '<account-user-email type-str>': '<account-user-name type-str>',
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_account_logout_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'logout',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': False,
            'account': '<account-user-email type-(str|none)>',
            'session_data': {
                'session_user_account': '<next-account-user-email type-(str|none)>',
                'session_credit_ewallet': '<next-active-session-ewallet-id type-(int|none)>',
                'session_contact_list': '<next-active-session-contact-list-id type-(int|none)>',
                'session_account_archive': {
                    '<account-user-email type-str>': '<account-user-name type-(str|none)>',
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_add_contact_list_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'contact',
            'contact': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'user_name': '<contact-name type-str>',
            'user_email': '<contact-email type-str>',
            'user_phone': '<contact-phone type-str>',
            'user_reference': '<contact-reference type-str>',
            'notes': '<contact-notes type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_record': '<contact-record-id type-int>',
            'contact_list': '<contact-list-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_convert_clock_to_credits_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'convert',
            'convert': 'clock2credits',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'minutes': '<minutes-to-convert type-float>',
            'notes': '<notes type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_record': '<conversion-record-id type-int>',
            'ewallet_credits': '<available-ewallet-credits type-int>',
            'credit_clock': '<available-clock-time type-float>',
            'converted_minutes': '<minutes-converted-to-credits type-float>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_convert_credits_to_clock_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyEWalletCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'convert',
            'convert': 'credits2clock',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'credits': '<ewallet-credits type-int>',
            'notes': '<conversion-notes type-str>'},
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_record': '<conversion-record-id type-int>',
            'ewallet_credits': '<available-ewallet-credits type-int>',
            'credit_clock': '<available-clock-time type-float>',
            'converted_credits': '<credits-converted-to-clock type-int>'
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_new_account_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'user_name': '<account-user-name type-str>',
            'user_pass': '<account-user-pass type-str>',
            'user_email': '<account-user-email type-str>'
        },
        'response_ok': {
            'failed': '<flag type-bool value-true>',
            'account': '<account-user-email type-str>',
            'account_data': {
                'id': '<account-id type-int>',
                'name': '<account-user-name type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'ewallet': '<active-ewallet-id type-int>',
                'contact_list': '<active-contact-list-id type-int>',
                'email': '<account-user-email type-str>',
                'phone': '<account-user-phone type-str>',
                'alias': '<account-user-alias type-str>',
                'state_code': '<account-state-code type-int>',
                'state_name': '<account-state-label type-str>',
                'ewallet_archive': {
                    '<ewallet-id type-int>': '<ewallet-reference type-str>'
                },
                'contact_list_archive': {
                    '<contact-list-id type-int>': '<contact-list-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_contact_list_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'contact',
            'contact': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-true>',
            'contact_list': '<contact-list-id type-int>',
            'list_data': {
                'id': '<contact-list-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<contact-list-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<contact-record-id type-int>': '<contact-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_conversion_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'conversion',
            'conversion': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_sheet': '<conversion-sheet-id type-int>',
            'sheet_data': {
                'id': '<conversion-sheet-id type-int>',
                'clock': '<credit-clock-id type-int>',
                'reference': '<conversion-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<conversion-record-id type-int>': '<conversion-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_credit_clock_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'credit',
            'credit': 'clock',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<credit-clock-id type-int>',
            'clock_data': {
                'id': '<credit-clock-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<credit-clock-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credit_clock': '<available-clock-minutes type-float>',
                'clock_state': '<clock-timer-state type-str>',
                'time_sheet': '<active-time-sheet-id type-int>',
                'time_sheet_archive': {
                    '<time-sheet-id type-int>': '<time-sheet-reference type-str>'
                },
                'conversion_sheet': '<active-conversion-sheet-id type-int>',
                'conversion_sheet_archive': {
                    '<conversion-sheet-id type-int>': '<conversion-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_credit_ewallet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'credit',
            'credit': 'ewallet',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'ewallet': '<ewallet-id type-int>',
            'ewallet_data': {
                'id': '<ewallet-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<ewallet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credits': '<available-credits type-int>',
                'clock': '<credit-clock-id type-int>',
                'clock_archive': {
                    '<credit-clock-id type-int>': '<credit-clock-reference type-str>'
                },
                'transfer_sheet': '<active-transfer-sheet-id type-int>',
                'transfer_sheet_archive': {
                    '<transfer-sheet-id type-int>': '<transfer-sheet-reference type-str>'
                },
                'invoice_sheet': '<active-invoice-sheet-id type-int>',
                'invoice_sheet_archive': {
                    '<invoice-sheet-id type-int>': '<invoice-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_invoice_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'invoice',
            'invoice': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
            'sheet_data': {
                'id': '<invoice-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<invoice-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<invoice-record-id type-int>': '<invoice-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_time_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'time',
            'time': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
            'sheet_data': {
                'id': '<time-sheet-id type-int>',
                'clock': '<credit-clock-id type-int>',
                'reference': '<time-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<time-record-id type-int>': '<time-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_create_transfer_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'new',
            'new': 'transfer',
            'transfer': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
            'sheet_data': {
                'id': '<transfer-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<transfer-sheet-reference type-int>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<time-record-id type-int>': '<time-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_edit_account_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'edit',
            'edit': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'user_name': '<account-user-name type-str>',
            'user_phone': '<account-user-phone type-str>',
            'user_email': '<account-user-email type-str>',
            'user_pass': '<account-user-pass type-str>',
            'user_alias': '<account-user-alias type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'edit': {
                'name': '<flag type-bool>',
                'pass': '<flag type-bool>',
                'alias': '<flag type-bool>',
                'email': '<flag type-bool>',
                'phone': '<flag type-bool>',
            },
            'account_data': {
                'id': '<account-id type-int>',
                'name': '<account-user-name type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'ewallet': '<active-ewallet-id type-int>',
                'contact_list': '<active-contact-list-id type-int>',
                'email': '<account-user-email type-str>',
                'phone': '<account-user-phone type-str',
                'alias': '<account-user-alias type-str>',
                'state_code': '<account-state-code type-int>',
                'state_name': '<account-state-label type-str>',
                'ewallet_archive': {
                    '<ewallet-id type-int>': '<ewallet-reference type-str>'
                },
                'contact_list_archive': {
                    '<contact-list-id type-int>': '<contact-list-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_pay_credits_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'pay',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'pay': '<account-user-email type-str>',
            'credits': '<ewallet-credits type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'payed': '<account-user-email type-str>',
            'ewallet_credits': '<available-ewallet-credits type-int>',
            'spent_credits': '<credits-consumed type-int>',
            'invoice_record': '<invoice-record-id type-int>',
            'transfer_record': '<transfer-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_request_client_id_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'request',
            'request': 'client_id'
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'client_id': '<client-id type-str>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_request_session_token_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'request',
            'request': 'session_token',
            'client_id': '<client-id type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'session_token': '<session-token type-str>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_supply_credits_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'supply',
            'supply': 'credits',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'currency': '<currency-label type-str>',
            'credits': '<ewallet-credits type-int>',
            'cost': '<currency-cost-per-credit type-float>',
            'notes': '<supply-notes type-str>'
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'ewallet_credits': '<available-ewallet-credits type-int>',
            'supplied_credits': '<supplied-ewallet-credits type-int>',
            'transfer_record': '<transfer-record-id type-int>',
            'invoice_record': '<invoice-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_active_session_user_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount (1)',
            'CreateNewAccount (2)',
            'AccountLogin (1)',
            'AccountLogin (2)',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'account': '<account-user-email type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'session_data': {
                'session_user_account': '<account-user-email type-str>',
                'session_credit_ewallet': '<credit-ewallet-id type-int>',
                'session_contact_list': '<contact-list-id type-int>',
                'session_account_archive': {
                    '<account-user-email type-str>': '<account-user-name type-str>',
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_contact_list_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateContactList',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'contact',
            'contact': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<contact-list-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_list': '<contact-list-id type-int>',
            'list_data': {
                'id': '<contact-list-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<contact-list-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<contact-record-id type-int>': '<contact-record-email type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_conversion_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateConversionSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'conversion',
            'conversion': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'sheet_id': '<conversion-sheet-id type-int>',
        },
        'response_ok': {
            'failed': False,
            'conversion_sheet': '<conversion-sheet-id type-int>',
            'sheet_data': {
                'id': '<conversion-sheet-id type-int>',
                'clock': '<conversion-sheet-id type-int>',
                'reference': '<conversion-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<conversion-record-id type-int>': '<conversion-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_credit_clock_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateCreditClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'credit',
            'credit': 'clock',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'clock_id': '<credit-clock-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<credit-clock-id type-int>',
            'clock_data': {
                'id': '<credit-clock-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<credit-clock-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credit_clock': '<available-clock-minutes type-float>',
                'clock_state': '<clock-timer-state type-str>',
                'time_sheet': '<active-time-sheet-id type-int>',
                'time_sheet_archive': {
                    '<time-sheet-id type-int>': '<time-sheet-reference type-str>'
                },
                'conversion_sheet': '<active-conversion-sheet-id type-int>',
                'conversion_sheet_archive': {
                    '<conversion-sheet-id type-int>': '<conversion-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_credit_ewallet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateCreditEWallet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'credit',
            'credit': 'ewallet',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'ewallet_id': '<ewallet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'ewallet': '<ewallet-id type-int>',
            'ewallet_data': {
                'id': '<ewallet-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<ewallet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credits': '<available-credits type-int>',
                'clock': '<active-credit-clock-id type-int>',
                'clock_archive': {
                    '<credit-clock-id type-int>': '<credit-clock-reference type-str>'
                },
                'transfer_sheet': '<active-transfer-sheet-id type-int>',
                'transfer_sheet_archive': {
                    '<transfer-sheet-id type-int>': '<transfer-sheet-reference type-str>'
                },
                'invoice_sheet': '<active-invoice-sheet-id type-int>',
                'invoice_sheet_archive': {
                    '<invoice-sheet-id type-int>': '<invoice-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_invoice_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateInvoiceSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'invoice',
            'invoice': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'sheet_id': '<invoice-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
            'sheet_data': {
                'id': '<invoice-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<invoice-sheet-reference type-int>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<invoice-record-id type-int>': '<invoice-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_time_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateTimeSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'time',
            'time': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'sheet_id': '<time-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
            'sheet_data': {
                'id': '<time-sheet-id type-int>',
                'clock': '<credit-clock-id type-int>',
                'reference': '<time-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<time-record-id type-int>': '<time-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_switch_transfer_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateTransferSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'switch',
            'switch': 'transfer',
            'transfer': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'sheet_id': '<transfer-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
            'sheet_data': {
                'id': '<transfer-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<transfer-sheet-reference type-int>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<transfer-record-id type-int>': '<transfer-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_transfer_credits_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'NewContactRecord',
            'SupplyCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'transfer',
            'transfer': 'credits',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'transfer_to': '<account-user-email type-str>',
            'credits': '<ewallet-credits type-int>'
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfered_to': '<account-user-email type-str>',
            'ewallet_credits': '<available-ewallet-credits type-int>',
            'transfered_credits': '<credits-consumed type-int>',
            'transfer_record': '<transfer-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_account_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_contact_list_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateContactList',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'contact',
            'contact': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<contact-list-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_list': '<contact-list-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_contact_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'NewContactRecord',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'contact',
            'contact': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<contact-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_list': '<contact-list-id type-int>',
            'contact_record': '<contact-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_conversion_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'ConvertCreditsToClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'conversion',
            'conversion': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<conversion-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_sheet': '<conversion-sheet-id type-int>',
            'conversion_record': '<conversion-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_conversion_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateConversionSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'conversion',
            'conversion': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<conversion-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_sheet': '<conversion-sheet-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_credit_clock_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateCreditClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'credit',
            'credit': 'clock',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'clock_id': '<credit-clock-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'credit_clock': '<credit-clock-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_credit_ewallet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateCreditEWallet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'credit',
            'credit': 'ewallet',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'ewallet_id': '<ewallet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'ewallet': '<ewallet-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_invoice_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'PayCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'invoice',
            'invoice': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<invoice-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
            'invoice_record': '<invoice-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_invoice_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateInvoiceSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'invoice',
            'invoice': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<invoice-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_time_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'StartClockTimer',
            'StopClockTimer',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'time',
            'time': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<time-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
            'time_record': '<time-record-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_time_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateTimeSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'time',
            'time': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<time-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_transfer_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'TransferCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'transfer',
            'transfer': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<transfer-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
            'transfer_record': '<transfer-record-id type-int>'
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_unlink_transfer_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'CreateTransferSheet',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'unlink',
            'unlink': 'transfer',
            'transfer': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'list_id': '<transfer-sheet-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_account_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'account',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'account_data': {
                'id': '<account-id type-int>',
                'name': '<account-user-name type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'ewallet': '<active-ewallet-id type-int>',
                'contact_list': '<active-contact-list-id type-int>',
                'email': '<account-user-email type-str>',
                'phone': '<account-user-phone type-str>',
                'alias': '<account-user-alias type-str>',
                'state_code': '<account-state-code type-int>',
                'state_name': '<account-state-label type-int>',
                'to_unlink': '<flag type-bool>',
                'to_unlink_timestamp': '<%d-%m-%Y %H:%M:%S type-str tz-UTC or None>',
                'ewallet_archive': {
                    '<ewallet-id type-int>': '<ewallet-reference type-str>'
                },
                'contact_list_archive':{
                    '<contact-list-id type-int>': '<contact-list-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_contact_list_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNew Account',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'contact',
            'contact': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_list': '<contact-list-id type-int>',
            'list_data': {
                'id': '<contact-list-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<contact-list-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<contact-record-id type-int>': '<contact-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_contact_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNew Account',
            'AccountLogin',
            'NewContactRecord',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'contact',
            'contact': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<contact-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'contact_list': '<contact-list-id type-int>',
            'contact_record': '<contact-record-id type-int>',
            'record_data': {
                'id': '<contact-record-id type-int>',
                'contact_list': '<contact-list-id type-int>',
                'reference': '<contact-record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'name': '<contact-record-name type-str>',
                'email': '<contact-record-email type-str>',
                'phone': '<contact-record-phone type-str>',
                'notes': '<contact-record-notes type-str>'
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_conversion_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'conversion',
            'conversion': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<conversion-record-id>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_sheet': '<conversion-sheet-id type-int>',
            'conversion_record': '<conversion-record-id type-int>',
            'record_data': {
                'id': '<conversion-record-id type-int>',
                'conversion_sheet': '<conversion-sheet-id type-int>',
                'reference': '<conversion-record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'conversion_type': '<conversion-type type-str>',
                'minutes': '<conversion-minutes type-float>',
                'credits': '<conversion-credits type-int>',
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_conversion_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'conversion',
            'conversion': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'conversion_sheet': '<conversion-sheet-id type-int>',
            'sheet_data': {
                'id': '<conversion-sheet-id type-int>',
                'clock': '<credit-clock-id type-int>',
                'reference': '<conversion-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<conversion-record-id type-int>': '<conversion-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_credit_clock_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'credit',
            'credit': 'clock',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'clock': '<credit-clock-id type-int>',
            'clock_data': {
                'id': '<credit-clock-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<credit-clock-reference type-int>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credit_clock': '<available-clock-minutes type-float>',
                'clock_state': '<clock-timer-state type-str>',
                'time_sheet': '<active-time-sheet-id type-int>',
                'time_sheet_archive': {
                    '<time-sheet-id type-int>': '<time-sheet-reference type-str>'
                },
                'conversion_sheet': '<active-conversion-sheet-id type-int>',
                'conversion_sheet_archive': {
                    '<conversion-sheet-id type-int>': '<conversion-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_credit_ewallet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'credit',
            'credit': 'ewallet',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'ewallet': '<ewallet-id type-int>',
            'ewallet_data': {
                'id': '<ewallet-id type-int>',
                'user': '<account-id type-int>',
                'reference': '<ewallet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credits': '<available-credits type-int>',
                'clock': '<active-credit-clock-id type-int>',
                'clock_archive': {
                    '<credit-clock-id type-int>': '<credit-clock-reference type-str>'
                },
                'transfer_sheet': '<active-transfer-sheet-id type-int>',
                'transfer_sheet_archive': {
                    '<transfer-sheet-id type-int>': '<transfer-sheet-reference type-str>'
                },
                'invoice_sheet': '<active-invoice-sheet-id type-int>',
                'invoice_sheet_archive': {
                    '<invoice-sheet-id type-int>': '<invoice-sheet-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_invoice_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'invoice',
            'invoice': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<invoice-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
            'invoice_record': '<invoice-record-id type-int>',
            'record_data': {
                'id': '<invoice-record-id type-int>',
                'invoice_sheet': '<invoice-sheet-id type-int>',
                'reference': '<invoice-record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'credits': '<invoice-credits type-int>',
                'currency': '<invoice-currency-label type-str>',
                'cost': '<invoice-currency-credit-cost type-float>',
                'seller': '<invoice-account-id type-int>',
                'notes': '<invoice-record-notes type-str>'
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_invoice_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'invoice',
            'invoice': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'invoice_sheet': '<invoice-sheet-id type-int>',
            'sheet_data': {
                'id': '<invoice-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<invoice-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<invoice-record-id type-int>': '<invoice-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_login_records_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'login',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'login_records': {
                '<login-record-id type-int>': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>'
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_logout_records_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'AccountLogout',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'logout',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'account': '<account-user-email type-str>',
            'logout_records': {
                '<logout-record-id type-int>': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>'
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_time_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'SupplyCredits',
            'ConvertCreditsToClock',
            'StartClockTimer',
            'StopClockTimer',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'time',
            'time': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<time-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
            'time_record': '<time-record-id type-int>',
            'record_data': {
                'id': '<time-record-id type-int>',
                'time_sheet': '<time-sheet-id type-int>',
                'reference': '<time-record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_start': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_stop': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'time_spent': '<clock-minutes-consumed type-float>',
                'time_pending': '<minutes-spent-pending type-float>',
                'pending_count': '<number-of-session-pendings type-int>',
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_time_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'time',
            'time': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'time_sheet': '<time-sheet-id type-int>',
            'sheet_data': {
                'id': '<time-sheet-id type-int>',
                'clock': '<credit-clock-id type-int>',
                'reference': '<time-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<time-record-id type-int>': '<time-record-reference type-str>'
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_transfer_record_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
            'NewContactRecord',
            'SupplyEWalletCredits',
            'TransferCredits',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'transfer',
            'transfer': 'record',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
            'record_id': '<transfer-record-id type-int>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
            'transfer_record': '<transfer-record-id type-int>',
            'record_data': {
                'id': '<transfer-record-id type-int>',
                'transfer_sheet': '<transfer-sheet-id type-int>',
                'reference': '<trasfer-record-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'transfer_type': '<transfer-type type-str>',
                'transfer_from': '<account-user-email type-str>',
                'transfer_to': '<account-user-email type-str>',
                'credits': '<credits-transfered type-int>',
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

def display_user_action_view_transfer_sheet_instruction_set_example(**kwargs):
    log.debug('')
    instruction_set_response = {
        'failed': False,
        'prerequisits': [
            'RequestClientID',
            'RequestSessionToken',
            'CreateNewAccount',
            'AccountLogin',
        ],
        'instruction_set': {
            'controller': 'client',
            'ctype': 'action',
            'action': 'view',
            'view': 'transfer',
            'transfer': 'list',
            'client_id': '<client-id type-str>',
            'session_token': '<session-token type-str>',
        },
        'response_ok': {
            'failed': '<flag type-bool value-false>',
            'transfer_sheet': '<transfer-sheet-id type-int>',
            'sheet_data': {
                'id': '<transfer-sheet-id type-int>',
                'ewallet': '<ewallet-id type-int>',
                'reference': '<transfer-sheet-reference type-str>',
                'create_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'write_date': '<%d-%m-%Y %H:%M:%S type-str tz-UTC>',
                'records': {
                    '<transfer-record-id type-int>': '<transfer-record-reference type-str>',
                }
            }
        },
        'response_nok': {
            'failed': '<flag type-bool value-true>',
            'error': '<error-message type-str>',
            'warning': '<warning-message type-str>'
        },
    }
    return instruction_set_response

available_user_actions = {
    'PauseClockTimer': display_user_action_pause_clock_timer_instruction_set_example,
    'ResumeClockTimer': display_user_action_resume_clock_timer_instruction_set_example,
    'StartClockTimer': display_user_action_start_clock_timer_instruction_set_example,
    'StopClockTimer': display_user_action_stop_clock_timer_instruction_set_example,
    'AccountLogin': display_user_action_account_login_instruction_set_example,
    'AccountLogout': display_user_action_account_logout_instruction_set_example,
    'RecoverAccount': display_user_action_recover_account_instruction_set_example,
    'AddContactListRecord': display_user_action_add_contact_list_record_instruction_set_example,
    'ConvertClockToCredits': display_user_action_convert_clock_to_credits_instruction_set_example,
    'ConvertCreditsToClock': display_user_action_convert_credits_to_clock_instruction_set_example,
    'CreateNewAccount': display_user_action_create_new_account_instruction_set_example,
    'CreateContactList': display_user_action_create_contact_list_instruction_set_example,
    'CreateConversionSheet': display_user_action_create_conversion_sheet_instruction_set_example,
    'CreateCreditClock': display_user_action_create_credit_clock_instruction_set_example,
    'CreateCreditEWallet': display_user_action_create_credit_ewallet_instruction_set_example,
    'CreateInvoiceSheet': display_user_action_create_invoice_sheet_instruction_set_example,
    'CreateTimeSheet': display_user_action_create_time_sheet_instruction_set_example,
    'CreateTransferSheet': display_user_action_create_transfer_sheet_instruction_set_example,
    'EditAccount': display_user_action_edit_account_instruction_set_example,
    'PayCredits': display_user_action_pay_credits_instruction_set_example,
    'RequestClientID': display_user_action_request_client_id_instruction_set_example,
    'RequestSessionToken': display_user_action_request_session_token_instruction_set_example,
    'SupplyCredits': display_user_action_supply_credits_instruction_set_example,
    'SwitchSessionUser': display_user_action_switch_active_session_user_instruction_set_example,
    'SwitchContactList': display_user_action_switch_contact_list_instruction_set_example,
    'SwitchConversionSheet': display_user_action_switch_conversion_sheet_instruction_set_example,
    'SwitchCreditClock': display_user_action_switch_credit_clock_instruction_set_example,
    'SwitchCreditEWallet': display_user_action_switch_credit_ewallet_instruction_set_example,
    'SwitchInvoiceSheet': display_user_action_switch_invoice_sheet_instruction_set_example,
    'SwitchTimeSheet': display_user_action_switch_time_sheet_instruction_set_example,
    'SwitchTransferSheet': display_user_action_switch_transfer_sheet_instruction_set_example,
    'TransferCredits': display_user_action_transfer_credits_instruction_set_example,
    'UnlinkAccount': display_user_action_unlink_account_instruction_set_example,
    'UnlinkContactList': display_user_action_unlink_contact_list_instruction_set_example,
    'UnlinkContactRecord': display_user_action_unlink_contact_record_instruction_set_example,
    'UnlinkConversionRecord': display_user_action_unlink_conversion_record_instruction_set_example,
    'UnlinkConversionSheet': display_user_action_unlink_conversion_sheet_instruction_set_example,
    'UnlinkCreditClock': display_user_action_unlink_credit_clock_instruction_set_example,
    'UnlinkCreditEWallet': display_user_action_unlink_credit_ewallet_instruction_set_example,
    'UnlinkInvoiceRecord': display_user_action_unlink_invoice_record_instruction_set_example,
    'UnlinkInvoiceSheet': display_user_action_unlink_invoice_sheet_instruction_set_example,
    'UnlinkTimeRecord': display_user_action_unlink_time_record_instruction_set_example,
    'UnlinkTimeSheet': display_user_action_unlink_time_sheet_instruction_set_example,
    'UnlinkTransferRecord': display_user_action_unlink_transfer_record_instruction_set_example,
    'UnlinkTransferSheet': display_user_action_unlink_transfer_sheet_instruction_set_example,
    'ViewAccount': display_user_action_view_account_instruction_set_example,
    'ViewContactList': display_user_action_view_contact_list_instruction_set_example,
    'ViewContactRecord': display_user_action_view_contact_record_instruction_set_example,
    'ViewConversionRecord': display_user_action_view_conversion_record_instruction_set_example,
    'ViewConversionSheet': display_user_action_view_conversion_sheet_instruction_set_example,
    'ViewCreditClock': display_user_action_view_credit_clock_instruction_set_example,
    'ViewCreditEWallet': display_user_action_view_credit_ewallet_instruction_set_example,
    'ViewInvoiceRecord': display_user_action_view_invoice_record_instruction_set_example,
    'ViewInvoiceSheet': display_user_action_view_invoice_sheet_instruction_set_example,
    'ViewLoginRecords': display_user_action_view_login_records_instruction_set_example,
    'ViewLogoutRecords': display_user_action_view_logout_records_instruction_set_example,
    'ViewTimeRecord': display_user_action_view_time_record_instruction_set_example,
    'ViewTimeSheet': display_user_action_view_time_sheet_instruction_set_example,
    'ViewTransferRecord': display_user_action_view_transfer_record_instruction_set_example,
    'ViewTransferSheet': display_user_action_view_transfer_sheet_instruction_set_example,
}

# DISPLAY

#@pysnooper.snoop('logs/ewallet.log')
def display_ewallet_session_manager_instruction_set_options():
    log.debug('')
    return {
        'available_actions': list(available_user_actions.keys()),
        'available_events': ['[ WARNING ]: User events not supported.'],
        'help': {
            'option': '( action | event )',
            'action': '<available-action>',
            'event': '<available-event>',
        }
    }

def display_ewallet_session_manager_instruction_set_actions(**kwargs):
    log.debug('')
    if not kwargs or not kwargs.get('action') or kwargs.get('action') not in \
            available_user_actions.keys():
        return error_invalid_ewallet_instruction_set_action(kwargs)
    return available_user_actions[kwargs['action']](**kwargs)

# TODO - Document EWallet Session Manger User Events
def display_ewallet_session_manager_instruction_set_events(**kwargs):
    log.debug('TODO')
    return {
        'failed': True,
        'warning': 'EWallet user events not yet supported.'
    }

def display_ewallet_session_manager_instruction_set_option(**kwargs):
    log.debug('')
    options = {
        'action': display_ewallet_session_manager_instruction_set_actions,
        'event': display_ewallet_session_manager_instruction_set_events,
    }
    if not kwargs or not kwargs.get('option') or kwargs.get('option') not in \
            options.keys():
        return error_invalid_ewallet_instruction_set_option(kwargs)
    return options[kwargs['option']](**kwargs)

# ERRORS

def error_invalid_ewallet_instruction_set_event(instruction_set):
    instruction_set_response = {
        'failed': True,
        'error': 'Invalid EWallet instruction set event. Details: {}'\
                 .format(instruction_set)
    }
    log.error(instruction_set_response['error'])
    return instruction_set_response

def error_invalid_ewallet_instruction_set_action(instruction_set):
    instruction_set_response = {
        'failed': True,
        'error': 'Invalid EWallet instruction set action. Details: {}'\
                 .format(instruction_set)
    }
    log.error(instruction_set_response['error'])
    return instruction_set_response

def error_invalid_ewallet_instruction_set_option(instruction_set):
    instruction_set_response = {
        'failed': True,
        'error': 'Invalid EWallet instruction set option. Details: {}'\
                 .format(instruction_set)
    }
    log.error(instruction_set_response['error'])
    return instruction_set_response

# CODE DUMP

