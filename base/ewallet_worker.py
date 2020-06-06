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
    '''
    [ NOTE ]: Worker states [(0, vacant), (1, in_use), (2, full)]
    '''
    create_date = None
    session_worker_state_code = int()
    session_worker_state_label = str()
    session_worker_state_timestamp = None
    session_pool = list()
    token_session_map = dict()

    def __init__(self, *args, **kwargs):
        _now = datetime.datetime.now()
        self.create_date = _now
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

    def fetch_session_token_map(self):
        return self.token_session_map

    # TODO
    def fetch_session_pool(self):
        pass
    def fetch_ewallet_session(self, session_id=None):
        pass

    # SETTERS

    def set_new_ewallet_session_to_pool(self, ewallet_session):
        log.debug('')
        try:
            self.session_pool.append(ewallet_session)
        except:
            return self.error_could_not_add_new_session_to_pool()
        return True

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
        except:
            return self.error_could_not_set_worker_create_date()
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

    def action_add_new_session(self, **kwargs):
        log.debug('')
        return self.set_new_ewallet_session_to_pool(kwargs.get('session'))

    # GENERAL

    def search_ewallet_session(self, session_token):
        log.debug('')
        token_map = self.fetch_session_token_map()
        if not token_map:
            return self.warning_empty_session_token_map()
        for client_id in token_map:
            if token_map[client_id]['token'] == session_token:
                return token_map[client_id]['session']
        return False

#   @pysnooper.snoop()
    def action_add_client_id_session_token_map_entry(self, **kwargs):
        '''
        [ NOTE   ]: Maps an existing client_id with a new session token and object.
        [ INPUT  ]: client_id=<id>, session_token=<token>, session=<session-obj>
        [ RETURN ]: {client_id: {'token': session_token, 'session': session}}
        '''
        log.debug('')
        if None in [kwargs.get('client_id'), kwargs.get('session_token'),
                kwargs.get('session')]:
            return self.error_required_session_token_map_entry_data_not_found()
        map_entry = {kwargs['client_id']: {
            'token': kwargs['session_token'],
            'session': kwargs['session']
            }
        }
        self.token_session_map.update(map_entry)
        return map_entry

    # HANDLERS

    def handle_system_action_search_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_found()
        ewallet_session = self.search_ewallet_session(kwargs['session_token'])
        return self.warning_session_token_not_mapped(kwargs['session_token']) \
                if not ewallet_session else ewallet_session

    def handle_system_action_search(self, **kwargs):
        log.debug('')
        if not kwargs.get('search'):
            return self.error_no_worker_action_search_target_specified()
        _handlers = {
                'session': self.handle_system_action_search_session,
                }
        return _handlers[kwargs['search']](**kwargs)

    def handle_system_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_worker_action_new_target_specified()
        _handlers = {
                'session': self.action_add_new_session,
                'session_map': self.action_add_client_id_session_token_map_entry,
                }
        return _handlers[kwargs['add']](**kwargs)

    # CONTROLLERS

    def system_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_worker_action_specified()
        _handlers = {
                'add': self.handle_system_action_add,
                'search': self.handle_system_action_search,
                }
        return _handlers[kwargs['action']](**kwargs)

    # TODO
    def system_event_controller(self):
        pass

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_worker_controller_specified()
        _handlers = {
                'action': self.system_action_controller,
                'event': self.system_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_worker_controller_specified()
        _handlers = {
                'system': self.system_controller,
                }
        return _handlers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_empty_session_token_map(self):
        log.warning('Empty worker session token map.')
        return False

    def warning_session_token_not_mapped(self, session_token):
        log.warning('Session token not mapped {}.'.format(session_token))
        return False

    # ERRORS

    def error_no_session_token_found(self):
        log.error('No session token found.')
        return False

    def error_no_worker_action_search_target_specified(self):
        log.error('No EWallet Session Manager search target specified.')
        return False

    def error_required_session_token_map_entry_data_not_found(self):
        log.error('Required session token map entry not found.')
        return False

    def error_could_not_set_worker_create_date(self):
        log.error('Something went wrong. Could not set worker create date.')
        return False

    def error_could_not_add_new_session_to_pool(self, ewallet_sesion):
        log.error(
                'Something went wrong. Could not set new EWallet Session {} to worker session pool.'\
                    .format(ewallet_session)
                )
        return False

    def error_no_worker_action_new_target_specified(self):
        log.error('No worker action new target specified.')
        return False

    def error_no_system_session_manager_worker_action_specified(self):
        log.error('No system session manager worker action specified.')
        return False

    def error_no_session_manager_controller_specified(self):
        log.error('No session manager worker controller specified.')
        return False

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
