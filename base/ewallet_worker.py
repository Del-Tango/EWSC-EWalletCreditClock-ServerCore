from base.config import Config
from base.res_utils import ResUtils

import time
import datetime
import random
import hashlib
import logging
import datetime
import pysnooper
import threading

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletWorker():

    create_date = None
    session_worker_state_code = int()
    session_worker_state_label = str()
    session_worker_state_timestamp = None
    session_pool = list()
    token_session_map = dict()

    def __init__(self, *args, **kwargs):
        _now = datetime.datetime.now()
        self.create_date = _now
        # [ NOTE ]: Worker states [(0, vacant), (1, in_use), (2, full)]
        self.session_worker_state_code = 0
        self.session_worker_state_label = 'vacant'
        self.session_worker_state_timestamp = _now

    # FETCHERS

    def fetch_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_session_worker_state_code(self):
        log.debug('')
        return self.session_worker_state_code

    def fetch_session_worker_state_label(self):
        log.debug('')
        return self.session_worker_state_label

    def fetch_session_worker_state_timestamp(self):
        log.debug('')
        return self.session_worker_state_timestamp

    def fetch_session_worker_state_code_label_map(self):
        log.debug('')
        return {0: 'vacant', 1: 'in_use', 2: 'full'}

    # TODO
    def fetch_session_pool(self):
        pass
    def fetch_token_session_map(self):
        pass
    def fetch_ewallet_session(self, session_id=None):
        pass
    def fetch_ewallet_user_session_set(self, user_id=None):
        pass

    # SETTERS

    def set_create_date(self, create_date):
        log.debug('')
        self.create_date = create_date
        return True

    '''
    [ NOTE   ]: State codes are used by the session manager to decide what worker
    to place a new session in, what workers are idle, and what workers need to
    be scraped.
    [ INPUT  ]: (0 | 1 | 2), code_map=[0, 1, 2]
    [ RETURN ]: (True | False)
    '''
    def set_session_worker_state_code(self, state_code, **kwargs):
        log.debug('')
        if state_code not in kwargs.get('code_map') or \
                self.fetch_session_worker_state_code_label_map().keys():
            return self.error_invalid_session_worker_state_code()
        self.session_worker_state_code = state_code
        return True

    '''
    [ NOTE   ]: State labels offer a human readable view of a workers activity.
    [ INPUT  ]: ('vacant' | 'in_use' | 'full'), label_map=['vacant', 'in_use', 'full']
    [ RETURN ]: (True | False)
    '''
    def set_session_worker_state_label(self, state_label, **kwargs):
        log.debug('')
        if state_label not in kwargs.get('label_map') or \
                self.fetch_session_worker_state_code_label_map().values():
            return self.error_invalid_session_worker_state_label()
        self.session_worker_state_label = state_label
        return True

    '''
    [ NOTE   ]: The state timestamp marks the moment of the last worker state
    change, used mainly to check worker idle time.
    [ INPUT  ]: Timestamp in the form of a datetime object.
    [ RETURN ]: (True | False)
    '''
    def set_session_worker_state_timestamp(self, timestamp):
        log.debug('')
        self.session_worker_state_timestamp = timestamp
        return True

    # TODO
    def set_session_pool_add_record(self, record):
        pass
    def set_session_pool_remove_record(self, record):
        pass
    def set_session_pool_clear_records(self):
        pass
    def set_session_pool_update_records(self):
        pass

    # UPDATERS

    '''
    [ NOTE   ]: Update worker state using state code.
    [ INPUT  ]: (0 | 1 | 2)
    [ RETURN ]: {
        'state_code': (True | False),
        'state_label': (True | False),
        'state_timestamp': (True | False)
        }
    '''
    def update_session_worker_state(self, state_code):
        log.debug('')
        _mapper = self.fetch_session-worker_state_code_label_map()
        _state_label = _mapper.get(state_code)
        _timestamp = datetime.datetime.now()
        _updates = {
            'state_code': self.set_session_worker_state_code(
                state_code, code_map=_mapper.keys()
                ),
            'state_label': self.set_session_worker_state_label(
                _state_label, label_map=_mapper.values()
                ),
            'state_timestamp': self.set_session_worker_state_timestamp(
                _timestamp
                ),
        }
        return _updates

    # CLEANERS

    '''
    [ NOTE   ]: Remove EWallet Session record from database.
    [ INPUT  ]: Ewallet session object.
    [ RETURN ]: (True | False)
    '''
    def cleanup_session(self, ewallet_session):
        if not ewallet_session:
            return self.error_no_ewallet_session_found()
        _working_session = ewallet_session.fetch_active_session()
        if not _working_session:
            return self.error_no_sqlalchemy_active_session_found()
        _working_session.query(EWallet) \
                        .filter_by(id=ewallet.fetch_active_session_id()) \
                        .delete()
        _working_session.commit()
        _working_session.close()
        return True

    # ACTIONS

    # TODO
    def action_spawn_new_session(self, **kwargs):
        pass
    def action_unlink_session(self, **kwargs):
        pass
    def action_add_session_to_pool(self, **kwargs):
        pass
    def action_fetch_session_from_pool(self, **kwargs):
        pass
    def action_remove_session_from_pool(self, **kwargs):
        pass

    # GENERIC

    # TODO
    def validate_session_command_chain(self, command_chain=None, **kwargs):
        pass
    def process_session_command_chain(self, command_chain=None, **kwargs):
        pass

    # HANDLERS

    # TODO
    def handle_client_action_spawn(self):
        pass
    def handle_client_action_update(self):
        pass
    def handle_client_action_view(self):
        pass
    def handle_client_action_unlink(self):
        pass
    def handle_system_action_spawn(self):
        pass
    def handle_system_action_update(self):
        pass
    def handle_system_action_view(self):
        pass
    def handle_system_action_unlink(self):
        pass

    # CONTROLLERS

    # TODO
    def client_action_controller(self):
        pass
    def client_event_controller(self):
        pass
    def system_action_controller(self):
        pass
    def system_event_controller(self):
        pass
    def client_controller(self):
        pass
    def system_controller(self):
        pass
    def main_controller(self):
        pass

    # ERRORS

    def error_invalid_session_worker_state_code(self):
        log.error('Invalid session worker state code.')
        return False

    def error_invalid_session_worker_state_label(self):
        log.error('Invalid session worker state label.')
        return False

    def error_no_ewallet_session_found(self):
        log.error('No EWallet session found.')
        return False

    def error_no_sqlalchemy_active_session_found(self):
        log.error('No sqlalchemt active session found.')
        return False

    # TESTS
