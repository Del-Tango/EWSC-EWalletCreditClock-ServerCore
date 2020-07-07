from .config import Config
from .res_utils import ResUtils
from .ewallet import EWallet

# import time
import datetime
# import random
# import hashlib
import logging
import pysnooper
# import threading

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

    def fetch_ewallet_session_from_pool_by_id(self, ewallet_session_id):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        for ewallet_session in session_pool:
            if ewallet_session.fetch_active_session_id() == ewallet_session_id:
                return ewallet_session
        return self.warning_could_not_fetch_ewallet_session_from_pool_by_id(
            ewallet_session_id
        )

#   @pysnooper.snoop()
    def fetch_ewallet_session_map_client_id_by_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session'):
            return self.error_no_ewallet_session_found(kwargs)
        token_session_map = self.fetch_session_token_map()
        if not token_session_map or isinstance(token_session_map, dict) and \
                token_session_map.get('failed'):
            return self.warning_worker_session_token_map_empty(kwargs)

        # TODO - REMOVE
        log.info('\n\nTOKEN SESSION MAP : {}\n'.format(token_session_map))


        for client_id in token_session_map:
            details = token_session_map[client_id]
            if kwargs['session'] is details['session']:

                # TODO - REMOVE
                log.info('\n\nWOOHOO - CLIENT ID : {}\n'.format(client_id))

                return client_id
        return self.warning_ewallet_session_associated_client_id_not_found_in_map(
            kwargs
        )

    def fetch_session_worker_ewallet_session_pool(self):
        log.debug('')
        return self.session_pool

    def fetch_session_worker_values(self):
        log.debug('')
        session_pool = {}
        for session in self.session_pool:
            session_id = session.fetch_active_session_id()
            user_account = session.fetch_active_session_user()
            session_pool.update({
                session_id: None if not user_account else user_account.fetch_user_id()
            })
        values = {
            'create_date': self.create_date,
            'state_code': self.session_worker_state_code,
            'state_label': self.session_worker_state_label,
            'state_timestamp': self.session_worker_state_timestamp,
            'session_pool': session_pool,
            'token_session_map': {} if not self.token_session_map else \
                self.token_session_map
        }
        return values

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
    def fetch_ewallet_session(self, session_id=None):
        pass

    # SETTERS

    def set_session_worker_token_session_map_entry(self, map_entry):
        log.debug('')
        if not isinstance(map_entry, dict):
            return self.error_invalid_session_worker_token_session_map_entry(map_entry)
        try:
            self.token_session_map.update(map_entry)
        except:
            return self.error_could_not_set_session_worker_token_session_map_entry(map_entry)
        return True

    def set_new_ewallet_session_to_pool(self, ewallet_session):
        log.debug('')
        if isinstance(ewallet_session, dict):
            return self.error_invalid_ewallet_session_for_worker_session_pool(ewallet_session)
        try:
            self.session_pool.append(ewallet_session)
        except:
            return self.error_could_not_add_new_session_to_pool(ewallet_session)
        return True

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
        except:
            return self.error_could_not_set_worker_create_date()
        return True

    def set_session_worker_state_code(self, state_code, **kwargs):
        '''
        [ NOTE   ]: State codes are used by the session manager to decide what worker
                    to place a new session in, what workers are idle, and what workers need to
                    be scraped.
        [ INPUT  ]: (0 | 1 | 2)
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if state_code not in self.fetch_session_worker_state_code_label_map().keys():
            return self.error_invalid_session_worker_state_code(state_code)
        self.session_worker_state_code = state_code
        return True

    def set_session_worker_state_label(self, state_label, **kwargs):
        '''
        [ NOTE   ]: State labels offer a human readable view of a workers activity.
        [ INPUT  ]: ('vacant' | 'in_use' | 'full'), label_map=['vacant', 'in_use', 'full']
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if state_label not in kwargs.get('label_map') or \
                self.fetch_session_worker_state_code_label_map().values():
            return self.error_invalid_session_worker_state_label()
        self.session_worker_state_label = state_label
        return True

    def set_session_worker_state_timestamp(self, timestamp):
        '''
        [ NOTE   ]: The state timestamp marks the moment of the last worker state
                    change, used mainly to check worker idle time.
        [ INPUT  ]: Timestamp in the form of a datetime object.
        [ RETURN ]: (True | False)
        '''
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

    def update_session_worker_state(self, state_code):
        '''
        [ NOTE   ]: Update worker state using state code.
        [ INPUT  ]: (0 | 1 | 2)
        [ RETURN ]: {
            'state_code': (True | False),
            'state_label': (True | False),
            'state_timestamp': (True | False)
            }
        '''
        log.debug('')
        _mapper = self.fetch_session_worker_state_code_label_map()
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

    # CHECKERS

    def check_ewallet_session_in_worker_session_pool_by_id(self, ewallet_session_id):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        for ewallet_session in session_pool:
            if ewallet_session.fetch_active_session_id() == ewallet_session_id:
                return True
        return False

    # CLEANERS

#   @pysnooper.snoop()
    def cleanup_session(self, ewallet_session):
        '''
        [ NOTE   ]: Remove EWallet Session record from database.
        [ INPUT  ]: Ewallet session object.
        [ RETURN ]: (True | False)
        '''
        log.debug('TODO - FIX ME')
        if not ewallet_session:
            return self.error_no_ewallet_session_found(ewallet_session)
        orm_session = ewallet_session.fetch_active_session()
        if not orm_session:
            return self.error_no_sqlalchemy_active_session_found(ewallet_session)
        ewallet_session_query = orm_session.query(
            EWallet
        ).filter_by(
            id=ewallet_session.fetch_active_session_id()
        )
        if not list(ewallet_session_query):
            return self.warning_no_ewallet_session_found_on_disk_by_id(ewallet_session)
        try:
            ewallet_session_query.delete()
        except:
            return self.error_could_not_remove_ewallet_session_from_database(ewallet_session)
        orm_session.commit()
        orm_session.close()
        return True

    # GENERAL

    def remove_session_token_map_entry(self, client_id):
        log.debug('')
        try:
            del self.token_session_map[client_id]
        except:
            return self.error_could_not_remove_session_token_map_entry(client_id)
        instruction_set_response = {
            'failed': False,
            'session_token_map': self.fetch_session_token_map(),
        }
        return instruction_set_response

#   @pysnooper.snoop()
    def remove_ewallet_session_from_worker_pool(self, ewallet_session):
        log.debug('')
        try:
            self.session_pool.remove(ewallet_session)
        except:
            return self.error_could_not_remove_ewallet_session_from_worker_session_pool(
                ewallet_session
            )
        instruction_set_response = {
            'failed': False,
            'session_pool': self.fetch_session_worker_ewallet_session_pool(),
        }
        return instruction_set_response

    def search_ewallet_session(self, session_token):
        log.debug('')
        token_map = self.fetch_session_token_map()
        if not token_map:
            return self.warning_empty_session_token_map()
        for client_id in token_map:
            if token_map[client_id]['token'] == session_token:
                return token_map[client_id]['session']
        return self.warning_no_ewallet_session_found_by_session_token(session_token)

    # ACTIONS

    def action_interogate_session_pool(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if not session_pool or isinstance(session_pool, dict) and \
                session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(kwargs)
        instruction_set_response = {
            'failed': False,
            'session_pool': session_pool,
        }
        return instruction_set_response

    def action_add_new_session(self, **kwargs):
        log.debug('')
        ewallet_session_id = kwargs['session'].fetch_active_session_id()
        check_session_in_pool = self.check_ewallet_session_in_worker_session_pool_by_id(
            ewallet_session_id
        )
        if not check_session_in_pool:
            set_to_pool = self.set_new_ewallet_session_to_pool(kwargs.get('session'))
            if not set_to_pool or isinstance(set_to_pool, dict) and \
                    set_to_pool.get('failed'):
                return self.error_could_not_add_new_ewallet_session_to_session_pool(kwargs)
        self.handle_system_action_session_worker_state_check()
        instruction_set_response = {
            'failed': False,
            'ewallet_session': ewallet_session_id,
        }
        return instruction_set_response

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
        set_entry = self.set_session_worker_token_session_map_entry(map_entry)
        if set_entry or isinstance(set_entry, dict) and not set_entry.get('failed'):
            self.handle_system_action_session_worker_state_check()
        instruction_set_response = {
            'failed': False,
            'map_entry': map_entry,
        }
        return self.warning_could_not_set_session_worker_ewallet_session_token_map_entry(kwargs) \
            if not set_entry or isinstance(set_entry, dict) and \
            set_entry.get('failed') else instruction_set_response

    # HANDLERS

    def handle_system_action_interogate_session_pool(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool(**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_worker_action_interogate_target_specified(kwargs)
        handlers = {
            'session_pool': self.handle_system_action_interogate_session_pool,
        }
        return handlers[kwargs['interogate']](**kwargs)

    def handle_system_action_remove_session_map_by_ewallet_session(self, **kwargs):
        log.debug('')
        client_id = self.fetch_ewallet_session_map_client_id_by_ewallet_session(**kwargs)
        if not client_id or isinstance(client_id, dict) and client_id.get('failed'):
            return self.warning_could_not_fetch_ewallet_associated_client_id_from_map(
                kwargs
            )
        remove_entry = self.remove_session_token_map_entry(client_id)
        if not remove_entry or isinstance(remove_entry, dict) and \
                remove_entry.get('failed'):
            return self.warning_could_not_remove_session_token_map_entry(**kwargs)
        instruction_set_response = {
            'failed': False,
            'session_token_map': remove_entry['session_token_map'],
        }
        return instruction_set_response

    def handle_system_action_remove_session_map(self, **kwargs):
        log.debug('TODO')
        if not kwargs.get('identifier'):
            return self.error_no_worker_action_remove_session_map_identifier_specified(
                kwargs
            )
        handlers = {
            'ewallet_session': self.handle_system_action_remove_session_map_by_ewallet_session,
#           'session_token': self.handle_system_action_remove_session_map_by_session_token,
#           'client_id': self.handle_system_action_remove_session_map_by_client_id,
        }
        return handlers[kwargs['identifier']](**kwargs)

#   @pysnooper.snoop()
    def handle_system_action_remove_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session'):
            return self.error_no_worker_action_remove_session_specified(kwargs)
        remove_from_pool = self.remove_ewallet_session_from_worker_pool(kwargs['session'])
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'remove'
        )
        remove_from_map = self.system_controller(
            ctype='action', action='remove', remove='session_map',
            identifier='ewallet_session', **sanitized_instruction_set
        )
        clean_session = self.cleanup_session(kwargs['session'])
        if not clean_session or isinstance(clean_session, dict) and \
                clean_session.get('failed'):
            return self.warning_could_not_remove_ewallet_session(kwargs)
        update_state = self.handle_system_action_session_worker_state_check()
        instruction_chain_response = {
            'failed': False,
            'worker_state': self.fetch_session_worker_state_code()
        }
        return instruction_chain_response

    def handle_system_action_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('remove'):
            return self.error_no_worker_action_remove_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_remove_session,
            'session_map': self.handle_system_action_remove_session_map,
        }
        return handlers[kwargs['remove']](**kwargs)

    def handle_system_action_session_worker_state_check(self):
        log.debug('')
        current_state = self.fetch_session_worker_state_code()
        if current_state == 2:
            return self.warning_session_worker_ewallet_session_pool_full(current_state)
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        set_state = self.set_session_worker_state_code(
            1 if len(session_pool) >= 1 else 0
        )
        instruction_set_response = {
            'failed': False,
            'worker_state': current_state,
        }
        return self.warning_could_not_perform_session_worker_state_check(session_pool) \
            if not set_state or isinstance(set_state, dict) and set_state.get('failed') \
            else instruction_set_response

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
        handlers = {
            'session': self.handle_system_action_search_session,
        }
        return handlers[kwargs['search']](**kwargs)

    def handle_system_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_worker_action_new_target_specified()
        handlers = {
            'session': self.action_add_new_session,
            'session_map': self.action_add_client_id_session_token_map_entry,
        }
        return handlers[kwargs['add']](**kwargs)

    # CONTROLLERS

    def system_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_worker_action_specified()
        handlers = {
            'add': self.handle_system_action_add,
            'search': self.handle_system_action_search,
            'interogate': self.handle_system_action_interogate,
            'remove': self.handle_system_action_remove,
        }
        return handlers[kwargs['action']](**kwargs)

    # TODO
    def system_event_controller(self):
        pass

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_worker_controller_specified()
        handlers = {
            'action': self.system_action_controller,
            'event': self.system_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_worker_controller_specified()
        handlers = {
            'system': self.system_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_could_not_fetch_ewallet_session_from_pool_by_id(self, ewallet_session_id):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not find EWallet Session in session worker pool by id {}.'\
                       .format(ewallet_session_id),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_worker_session_token_map_empty(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Session Worker session token map empty. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_ewallet_session(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not remove EWallet Session '\
                       'from database. Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_ewallet_session_found_on_disk_by_id(self, ewallet_session):
        command_chain_response = {
            'failed': True,
            'warning': 'No EWallet session with id {} found in database. '\
                     .format(ewallet_session.fetch_active_session_id()),
        }
        log.error(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_session_token_map_entry(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong.Could not remove session token map entry. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_ewallet_associated_client_id_from_map(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch ewallet session '\
                       'associated client id from session token map. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_ewallet_session_associated_client_id_not_found_in_map(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'No ewallet session client id found in session token map. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_perform_session_worker_state_check(self, session_pool):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not perform session worker '\
                       'state check. Session pool details : {}'.format(session_pool),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_session_worker_ewallet_session_pool_full(self, current_state):
        instruction_set_response = {
            'failed': True,
            'warning': 'Session worker state {}. Ewallet session pool full.'\
                       .formaT(current_state),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_ewallet_session_found_by_session_token(self, session_token):
        instruction_set_response = {
            'failed': True,
            'warning': 'No ewallet session found by session token {}.'.format(session_token),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_empty_session_token_map(self):
        log.warning('Empty worker session token map.')
        return False

    def warning_session_token_not_mapped(self, session_token):
        log.warning('Session token not mapped {}.'.format(session_token))
        return False

    # ERRORS

    def error_could_not_remove_ewallet_session_from_database(self, ewallet_session):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove EWallet Session record '\
                     'with id {} from database.'.format(ewallet_session.fetch_active_session_id()),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_ewallet_session_pool(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch ewallet session pool. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_session_token_map_entry(self, client_id):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove session token map entry '\
                     'by client id {}.'.format(client_id),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_session_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet session found. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_worker_action_remove_session_map_identifier_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No session map identifier specified for session worker action remove. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_sqlalchemy_active_session_found(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'error': 'No active SqlAlchemy session found associated with '\
                     'ewallet session {}.'.format(ewallet_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_ewallet_session_from_worker_session_pool(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove ewallet session {} '\
                     'from worker session pool.'.format(ewallet_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_worker_action_remove_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No worker action remove target specified. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_worker_action_remove_session_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet session specified for worker action remove. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_add_new_ewallet_session_to_session_pool(self, instruction_set):
        instruction_set_response = {
            'failed': False,
            'error': 'Something went wrong. Could not add new ewallet session to '\
                     'worker session pool. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_session_worker_state_code(self, state_code):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid state code {} for session worker.'.format(state_code),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_add_new_session_to_pool(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not add new EWallet Session {} '\
                     'to worker session pool.'.format(ewallet_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_session_worker_token_session_map_entry(self, map_entry):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid token session map entry {} for session worker.'\
                     .format(map_entry),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_session_worker_token_session_map_entru(self, map_entry):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not set token session map '\
                     'entry {} to session worker.'.format(map_entry),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_ewallet_session_for_worker_session_pool(self, ewallet_session):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid ewallet session {} for worker session pool.'\
                     .format(ewallet_session),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

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

    def error_no_worker_action_new_target_specified(self):
        log.error('No worker action new target specified.')
        return False

    def error_no_system_session_manager_worker_action_specified(self):
        log.error('No system session manager worker action specified.')
        return False

    def error_no_session_manager_controller_specified(self):
        log.error('No session manager worker controller specified.')
        return False

    def error_invalid_session_worker_state_label(self):
        log.error('Invalid session worker state label.')
        return False

    # TESTS
