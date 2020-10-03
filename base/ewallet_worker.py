import datetime
import os
import logging
import pysnooper
import ast
import time

from multiprocessing import Process, Value, Queue, Lock

from .config import Config
from .res_utils import ResUtils
from .ewallet import EWallet

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletWorker():
    '''
    [ NOTE ]: Worker states [(0, vacant), (1, available), (2, occupied)]
    '''

    id = int()
    reference = str()
    create_date = None
    write_date = None
    session_worker_state_code = int()           # (0 | 1 | 2)
    session_worker_state_label = str()          # (vacant | available | occupied)
    session_worker_state_timestamp = None
    session_pool = dict()                       # {id: <EWallet>}
    ctoken_pool = list()                        # [<CToken.label>]
    stoken_pool = list()                        # [<SToken.label>]
    token_session_map = dict()                  # {<CToken.label>: {<SToken.label>: <EWalletSession>}}
    instruction_set_recv = None                 # <multiprocessing.Queue(1)>
    instruction_set_resp = None                 # <multiprocessing.Queue(1)>
    lock = None                                 # <multiprocessing.Value('i', 0)>
    session_limit = int()

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now()
        self.id = kwargs.get('id') or int()
        self.reference = kwargs.get('reference') or str()
        self.create_date = kwargs.get('create_date') or now
        self.write_date = kwargs.get('write_date') or now
        self.session_worker_state_code = kwargs.get('state_code') or 0
        self.session_worker_state_label = kwargs.get('state_label') or 'vacant'
        self.session_worker_state_timestamp = now
        self.instruction_set_recv = kwargs.get('instruction_set_recv') or Queue(1)
        self.instruction_set_resp = kwargs.get('instruction_set_resp') or Queue(1)
        self.sigterm = kwargs.get('sigterm') or \
            str(config.worker_config['worker_sigter'])
        self.lock = kwargs.get('lock') or Value('i', 0)
        self.session_limit = kwargs.get('session_limit') or \
            int(config.worker_config['session_limit'])

    # FETCHERS

    def fetch_stoken_pool(self):
        log.debug('')
        return self.stoken_pool

    def fetch_next_empty_ewallet_session_from_pool(self, ewallet_session_pool):
        log.debug('')
        empty_session = self.fetch_empty_ewallet_sessions_from_pool(
            ewallet_session_pool, ensure_one=True
        )
        if not empty_session:
            log.info('No empty ewallet session found in session pool.')
        return empty_session or \
            self.error_could_not_fetch_next_empty_ewallet_session_from_pool(
                ewallet_session_pool, empty_session
            )

    def fetch_command_chain_for_ewallet_session_check_empty(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session',
            'session': 'empty',
        }

    def fetch_empty_ewallet_sessions_from_pool(self, ewallet_session_pool, **kwargs):
        log.debug('')
        command_chain = self.fetch_command_chain_for_ewallet_session_check_empty()
        empty_session_ids = []
        for session_id in ewallet_session_pool:
            try:
                response = ewallet_session_pool[session_id].ewallet_controller(
                    **command_chain
                )
            except Exception as e:
                return self.error_could_not_execute_ewallet_session_command_chain(
                    ewallet_session_pool, session_id, command_chain, e
                )
            if not response or isinstance(response, dict) and \
                    response.get('failed'):
                return self.error_could_not_check_if_ewallet_session_empty(
                    ewallet_session_pool, session_id, command_chain, response
                )
            if not response.get('empty'):
                continue
            elif not empty_session_ids:
                if kwargs.get('ensure_one'):
                    return session_id
            empty_session_ids.append(session_id)
        return empty_session_ids

    def fetch_expired_ewallet_sessions_from_pool(self, ewallet_session_pool, **kwargs):
        log.debug('')
        command_chain = self.fetch_command_chain_for_ewallet_session_check_expired()
        expired_session_ids = []
        for session_id in ewallet_session_pool:
            try:
                response = ewallet_session_pool[session_id].ewallet_controller(
                    **command_chain
                )
            except Exception as e:
                return self.error_could_not_execute_ewallet_session_command_chain(
                    ewallet_session_pool, session_id, command_chain, e
                )
            if not response or isinstance(response, dict) and \
                    response.get('failed'):
                return self.error_could_not_check_if_ewallet_session_expired(
                    ewallet_session_pool, session_id, command_chain, response
                )
            if not response.get('expired'):
                continue
            elif not expired_session_ids:
                if kwargs.get('ensure_one'):
                    return session_id
            expired_session_ids.append(session_id)
        return expired_session_ids

    def fetch_session_token_label_by_ewallet_session(self, ewallet_session, **kwargs):
        log.debug('')
        cstoken_map = self.fetch_session_token_map()
        stoken_maps = list(cstoken_map.values())
        for stoken_map in stoken_maps:
            session = list(stoken_map.values())
            if not session:
                continue
            if session[0] is ewallet_session:
                return list(stoken_map.keys())[0]
        return self.error_could_not_fetch_session_token_label_by_ewallet_session(
            ewallet_session, kwargs, cstoken_map, stoken_maps,
            stoken_map, session
        )

    def fetch_default_ewallet_session_validity_interval_in_minutes(self, **kwargs):
        log.debug('')
        return int(config.session_config['ewallet_session_validity'])

    def fetch_default_ewallet_session_validity_interval_in_hours(self, **kwargs):
        log.debug('')
        minutes = int(config.session_config['ewallet_session_validity'])
        minutes_in_hour = 60
        return minutes / minutes_in_hour

    def fetch_default_ewallet_session_validity_interval_in_days(self, **kwargs):
        log.debug('')
        minutes = int(config.session_config['ewallet_session_validity'])
        minutes_in_hour, hours_in_day = 60, 24
        return (100 * (minutes / minutes_in_hour)) / hours_in_day

    def fetch_session_worker_session_limit(self):
        log.debug('')
        return self.session_limit

    def fetch_session_worker_ewallet_session_pool(self):
        log.debug('')
        return self.session_pool

    def fetch_ewallet_session_cleanup_command(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'cleanup',
            'cleanup': 'session',
        }

    def fetch_ewallet_session_state_check_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session',
            'session': 'state',
        }

    def fetch_ewallet_session_from_pool_by_id(self, ewallet_session_id):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        ewallet_session = session_pool.get(ewallet_session_id)
        return self.warning_could_not_fetch_ewallet_session_from_pool_by_id(
            ewallet_session_id, session_pool
        ) if not ewallet_session else ewallet_session

    def fetch_ewallet_session_expiration_date(self):
        log.debug('')
        validity_hours = self.fetch_default_ewallet_session_validity_interval(
            number_of='hours'
        )
        now = datetime.datetime.now()
        return now + datetime.timedelta(hours=validity_hours)

    def fetch_worker_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_next_expired_ewallet_session_from_pool(self, ewallet_session_pool):
        log.debug('')
        expired_session = self.fetch_expired_ewallet_sessions_from_pool(
            ewallet_session_pool, ensure_one=True
        )
        if not expired_session:
            log.info('No expired ewallet session found in session pool.')
        return expired_session or \
            self.error_could_not_fetch_next_expired_ewallet_session_from_pool(
                ewallet_session_pool, expired_session
            )

    def fetch_worker_id(self):
        log.debug('')
        return self.id

    def fetch_command_chain_for_ewallet_session_check_expired(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session',
            'session': 'expired',
        }

    def fetch_ewallet_session_by_client_session_tokens(self, client_id, session_token):
        log.debug('')
        st_map = self.fetch_session_token_map()
        if client_id not in st_map:
            if client_id not in self.fetch_session_worker_ctoken_pool().keys():
                return self.error_invalid_client_token(client_id, session_token, st_map)
            return self.warning_client_token_not_mapped(client_id, session_token, st_map)
        if session_token not in st_map[client_id]:
            return self.error_invalid_session_token(client_id, session_token, st_map)
        return st_map[client_id][session_token]

    def fetch_session_token_map(self):
        log.debug('')
        return self.token_session_map

    def fetch_session_worker_ctoken_pool(self):
        log.debug('')
        return self.ctoken_pool

    def fetch_session_worker_stoken_pool(self):
        log.debug('')
        return self.stoken_pool

    def fetch_default_ewallet_session_validity_interval(self, **kwargs):
        log.debug('')
        number_of = kwargs.get('number_of') or 'minutes'
        handlers = {
            'minutes': self.fetch_default_ewallet_session_validity_interval_in_minutes,
            'hours': self.fetch_default_ewallet_session_validity_interval_in_hours,
            'days': self.fetch_default_ewallet_session_validity_interval_in_days,
        }
        return self.error_invalid_validity_interval_specified(kwargs) if \
            number_of not in handlers else handlers[number_of](**kwargs)

    def fetch_worker_instruction_queue(self):
        log.debug('')
        return self.instruction_set_recv

    def fetch_worker_response_queue(self):
        log.debug('')
        return self.instruction_set_resp

    def fetch_session_worker_values(self):
        log.debug('')
        values = {
            'id': self.id,
            'reference': self.reference,
            'create_date': self.create_date,
            'state_code': self.session_worker_state_code,
            'state_label': self.session_worker_state_label,
            'state_timestamp': self.session_worker_state_timestamp,
            'session_pool': self.session_pool,
            'token_session_map': self.token_session_map,
            'ctoken_pool': self.ctoken_pool,
            'stoken_pool': self.stoken_pool,
            'instruction_set_recv': self.instruction_set_recv,
            'instruction_set_resp': self.instruction_set_resp,
            'sigterm': self.sigterm,
            'lock': self.lock,
        }
        return values

#   @pysnooper.snoop()
    def fetch_ewallet_session_map_client_id_by_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session'):
            return self.error_no_ewallet_session_found(kwargs)
        token_session_map = self.fetch_session_token_map()
        if not token_session_map or isinstance(token_session_map, dict) and \
                token_session_map.get('failed'):
            return self.warning_worker_session_token_map_empty(kwargs)
        for client_id in token_session_map:
            details = token_session_map[client_id]
            if kwargs['session'] is details['session']:
                return client_id
        return self.warning_ewallet_session_associated_client_id_not_found_in_map(
            kwargs
        )

    def fetch_id(self):
        log.debug('')
        return self.id

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

    # SETTERS
    '''
    [ NOTE ]: Write date updates are done here.
    '''

#   @pysnooper.snoop('logs/ewallet.log')
    def remove_ewallet_session_from_disk(self, ewallet_session_id, orm_session):
        log.debug('')
        try:
            removed = EWallet.__table__\
                .delete().where(EWallet.id.in_([ewallet_session_id]))
            orm_session.execute(removed)
            orm_session.commit()
            orm_session.close()
        except Exception as e:
            return self.error_could_not_remove_ewallet_session_from_disk(
                ewallet_session_id, e
            )
        log.info('Successfully removed ewallet session from disk.')
        return True

    def remove_ewallet_sessions_from_disk(self, session_set):
        log.debug('')
        sessions_removed, removal_failures = [], 0
        for ewallet_session in session_set:
            orm_session = ewallet_session.fetch_active_session()
            remove = self.remove_ewallet_session_from_disk(
                ewallet_session.fetch_active_session_id(), orm_session
            )
            if isinstance(remove, dict) and remove.get('failed'):
                self.warning_could_not_remove_ewallet_session_from_disk(
                    session_set, ewallet_session, orm_session, remove
                )
                removal_failures += 1
                continue
            sessions_removed.append(ewallet_session)
            orm_session.commit()
            orm_session.close()
        if not sessions_removed:
            return self.error_could_not_remove_ewallet_session_set_from_disk(
                session_set
            )
        return {
            'failed': False,
            'sessions_removed': sessions_removed,
            'removal_failures': removal_failures,
        }

    def set_session_worker_reference(self, reference):
        log.debug('')
        try:
            self.reference = reference
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_reference(
                reference, self.reference, e
            )
        return True

#   @pysnooper.snoop()
    def remove_ewallet_session_from_worker_pool(self, ewallet_session_id):
        log.debug('')
        try:
            del self.session_pool[ewallet_session_id]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_remove_ewallet_session_from_worker_session_pool(
                ewallet_session_id, self.session_pool, e
            )
        instruction_set_response = {
            'failed': False,
            'session_removed': ewallet_session_id,
            'session_pool': self.fetch_session_worker_ewallet_session_pool(),
        }
        return instruction_set_response

    def set_ewallet_session_map_entry_to_pool(self, map_entry):
        log.debug('')
        try:
            self.session_pool.update(map_entry)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_add_ewallet_session_map_entry_to_pool(
                map_entry, self.session_pool, e
            )
        return True

    def remove_ewallet_sessions_from_worker_pool(self, ewallet_session_set):
        log.debug('')
        sessions_removed, removal_failures = [], 0
        for session in ewallet_session_set:
            session_id = session.fetch_active_session_id()
            remove = self.remove_ewallet_session_from_worker_pool(
                session_id
            )
            if not remove or isinstance(remove, dict) and \
                    remove.get('failed'):
                self.warning_could_not_remove_session_set_item_from_pool(
                    ewallet_session_set, session, remove
                )
                removal_failures += 1
                continue
            sessions_removed.append(session_id)
        instruction_set_response = self.error_no_ewallet_sessions_removed_from_pool(
            ewallet_session_set, sessions_removed
        ) if not sessions_removed else {
            'failed': False,
            'sessions_removed': sessions_removed,
            'removal_failures': removal_failures,
            'session_pool': self.fetch_session_worker_ewallet_session_pool(),
        }
        return instruction_set_response

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.warning_could_not_set_write_date(
                write_date, self.write_date, e
            )
        return True

    def set_client_token_to_pool(self, client_id):
        log.debug('')
        try:
            self.ctoken_pool.append(client_id)
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_ctoken_pool_entry(
                client_id, self.ctoken_pool, e
            )
        return True

    def set_session_token_to_pool(self, session_token):
        log.debug('')
        try:
            self.stoken_pool.append(session_token)
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_stoken_pool_entry(
                session_token, self.stoken_pool, e
            )
        return True

    def remove_session_token_map_entry(self, client_id):
        log.debug('')
        try:
            del self.token_session_map[client_id]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_remove_session_token_map_entry(
                client_id, self.token_session_map, e
            )
        instruction_set_response = {
            'failed': False,
            'session_token_map': self.fetch_session_token_map(),
        }
        return instruction_set_response

    def set_esession_pool(self, map_entry):
        log.debug('')
        try:
            self.session_pool.update(map_entry)
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_esession_pool_entry(
                map_entry, self.session_pool, e
            )
        return True

    def set_ctoken_pool(self, map_entry):
        log.debug('')
        try:
            self.ctoken_pool.update(map_entry)
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_ctoken_pool_entry(
                map_entry, self.ctoken_pool, e
            )
        return True

    def set_stoken_pool(self, map_entry):
        log.debug('')
        try:
            self.stoken_pool.update(map_entry)
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_stoken_pool_entry(
                map_entry, self.stoken_pool, e
            )
        return True

    def set_session_worker_token_session_map_entry(self, map_entry):
        log.debug('')
        if not isinstance(map_entry, dict):
            return self.error_invalid_session_worker_token_session_map_entry(map_entry)
        try:
            self.token_session_map.update(map_entry)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_session_worker_token_session_map_entry(
                map_entry, self.token_session_map, e
            )
        return True

    def set_lock(self, lock):
        log.debug('')
        if not isinstance(lock, object):
            return self.error_invalid_lock(lock)
        try:
            self.lock = lock
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_lock(lock, self.lock, e)
        return True

    def set_instruction_queue(self, instruction_queue):
        log.debug('')
        if not isinstance(instruction_queue, object):
            return self.error_invalid_instruction_queue(instruction_queue)
        try:
            self.instruction_set_recv = instruction_queue
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_session_worker_instruction_queue(
                instruction_queue, self.instruction_set_recv, e
            )
        return True

    def set_response_queue(self, response_queue):
        log.debug('')
        if not isinstance(response_queue, object):
            return self.error_invalid_response_queue(response_queue)
        try:
            self.instruction_set_resp = response_queue
            self.update_write_date()
        except Exception as e:
            return self.warning_could_not_set_session_worker_response_queue(
                response_queue, self.instruction_set_resp, e
            )
        return True

#   @pysnooper.snoop()
    def set_new_session_token_to_pool(self, session_token):
        log.debug('')
        try:
            self.stoken_pool.append(session_token)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_new_session_token_to_pool(
                session_token, self.stoken_pool, e
            )
        return True

    def set_new_client_token_to_pool(self, client_token):
        log.debug('')
        try:
            self.ctoken_pool.append(client_token)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_add_new_client_token_to_pool(
                client_token, self.ctoken_pool, e
            )
        return True

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_create_date(
                create_date, self.create_date, e
            )
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
        try:
            self.session_worker_state_code = state_code
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_state_code(
                state_code, self.session_worker_state_code, kwargs, e
            )
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
        try:
            self.session_worker_state_label = state_label
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_state_label(
                state_label, self.session_sorker_state_label, kwargs, e
            )
        return True

    def set_session_worker_state_timestamp(self, timestamp):
        '''
        [ NOTE   ]: The state timestamp marks the moment of the last worker state
                    change, used mainly to check worker idle time.
        [ INPUT  ]: Timestamp in the form of a datetime object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.session_worker_state_timestamp = timestamp
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_state_timestamp(
                timestamp, self.session_worker_state_timestamp, e
            )
        return True

    # UPDATERS

    def update_session_worker_state(self):
        '''
        [ NOTE   ]: Compute appropriate session worker state code and set values.
        [ RETURN ]: {
            'state_code': (True | False),
            'state_label': (True | False),
            'state_timestamp': (True | False)
        }
        '''
        log.debug('')
        session_limit = self.fetch_session_worker_session_limit()
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        state_code = 0 if not len(session_pool) else \
            (1 if len(session_pool) < session_limit else 2)
        return self.update_session_worker_state_values(state_code)

    def update_session_worker_state_values(self, state_code):
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
        mapper = self.fetch_session_worker_state_code_label_map()
        state_label = mapper.get(state_code)
        timestamp = datetime.datetime.now()
        updates = {
            'state_code': self.set_session_worker_state_code(
                state_code, code_map=mapper.keys()
            ),
            'state_label': self.set_session_worker_state_label(
                state_label, label_map=mapper.values()
            ),
            'state_timestamp': self.set_session_worker_state_timestamp(
                timestamp
            ),
        }
        return updates


    def update_ewallet_session_pool(self, map_entry):
        log.debug('')
        if not map_entry or not isinstance(map_entry, dict):
            return self.error_invalid_ewallet_session_pool_map_entry(map_entry)
        return self.set_ewallet_session_map_entry_to_pool(map_entry)

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_worker_write_date()

    def update_ewallet_session_token_map(self, map_entry):
        log.debug('')
        if not map_entry or not isinstance(map_entry, dict):
            return self.error_invalid_ewallet_session_token_map_entry(map_entry)
        session_token_map = self.fetch_session_token_map()
        for k, v in map_entry.items():
            if k in session_token_map:
                session_token_map[k].update(v)
                continue
            set_entry = self.set_session_worker_token_session_map_entry(map_entry)
            if not set_entry or isinstance(set_entry, dict) and \
                    set_entry.get('failed'):
                return set_entry
            break
        return True

    def update_client_token_pool(self, client_id):
        log.debug('')
        return self.set_client_token_to_pool(client_id)

    def update_session_token_pool(self, session_token):
        log.debug('')
        return self.set_session_token_to_pool(session_token)

    # CHECKERS

    def check_session_worker_available(self):
        log.debug('')
        state_code = self.fetch_session_worker_state_code()
        return True if state_code in [0, 1] else False

    def check_ewallet_session_id_mapped(self, session_id):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        return True if session_id in session_pool.keys() else False

    # CLEANERS

#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_ewallet_sessions(self, session_set, **kwargs):
        log.debug('')
        session_tokens, cleaned_sessions, cleanup_failures = [], [], 0
        for ewallet_session in session_set:
            session_token = self.fetch_session_token_label_by_ewallet_session(
                ewallet_session
            )
            clean = self.cleanup_session(
                ewallet_session.fetch_active_session_id()
            )
            if isinstance(clean, dict) and clean.get('failed'):
                cleanup_failures += 1
                continue
            if isinstance(session_token, str):
                session_tokens.append(session_token)
            cleaned_sessions.append(ewallet_session)
        if not cleaned_sessions:
            return self.error_could_not_cleanup_ewallet_session_set(
                session_set
            )
        return {
            'failed': False,
            'cleaned_sessions': cleaned_sessions,
            'cleanup_failures': cleanup_failures,
            'orphaned_stokens': session_tokens,
        }

#   @pysnooper.snoop()
    def cleanup_session(self, ewallet_session_id):
        '''
        [ NOTE   ]: Remove EWallet Session record from database.
        [ INPUT  ]: Ewallet session object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        command = self.fetch_ewallet_session_cleanup_command()
        ewallet_session = self.fetch_ewallet_session_from_pool_by_id(
            ewallet_session_id
        )
        return ewallet_session.ewallet_controller(**command)

    def clean_session_worker_reference(self):
        log.debug('')
        self.reference = str()

    def clean_session_worker_create_date(self):
        log.debug('')
        self.create_date = None

    def clean_session_worker_write_date(self):
        log.debug('')
        self.write_date = None

    def clean_session_worker_state_code(self):
        log.debug('')
        self.session_worker_state_code = int()

    def clean_session_worker_state_label(self):
        log.debug('')
        self.session_worker_state_label = str()

    def clean_session_worker_state_timestamp(self):
        log.debug('')
        self.session_worker_state_timestamp = None

    def clean_session_worker_session_pool(self):
        log.debug('')
        self.session_pool = dict()

    def clean_session_worker_client_token_pool(self):
        log.debug('')
        self.ctoken_pool = list()

    def clean_session_worker_session_token_pool(self):
        log.debug('')
        self.stoken_pool = list()

    def clean_session_worker_token_session_map(self):
        log.debug('')
        self.token_session_map = dict()

    def clean_session_worker_instruction_set_recv(self):
        log.debug('')
        self.instruction_set_recv = None

    def clean_session_worker_instruction_set_resp(self):
        log.debug('')
        self.instruction_set_resp = None

    def clean_session_worker_lock(self):
        log.debug('')
        self.lock = None

    def clean_session_worker_data(self, data_dct):
        log.debug('')
        handlers = {
            'session_pool': self.clean_session_worker_session_pool,
            'ctoken_pool': self.clean_session_worker_client_token_pool,
            'stoken_pool': self.clean_session_worker_session_token_pool,
            'token_session_map': self.clean_session_worker_token_session_map,
        }
        if isinstance(data_dct, dict) and not data_dct:
            data_dct = {field: True for field in handlers.keys()}
        for item in data_dct:
            if item in handlers and data_dct[item]:
                handlers[item]()
        return data_dct

    def clean_response_queue(self, response_queue):
        log.debug('')
        if not response_queue.empty():
            while not response_queue.empty():
                garbage = response_queue.get()
                self.debug_cleaning_response_queue(self.lock.value, garbage)
        self.debug_response_queue_cleaned(self.lock.value, response_queue)
        return True

    # GENERAL

#   @pysnooper.snoop()
    def search_ewallet_session(self, session_token):
        log.debug('')
        token_map = self.fetch_session_token_map()
        if not token_map:
            return self.warning_empty_session_token_map()
        for client_id in token_map:
            if list(token_map[client_id].keys())[0] == session_token:
                return {
                    'failed': False,
                    'session': token_map[client_id][session_token]\
                        .fetch_active_session_id(),
                    'stoken': session_token,
                    'ctoken': client_id,
                }
        return self.warning_no_ewallet_session_found_by_session_token(
            session_token, token_map
        )

    def search_ewallet_session_set_in_pool_by_ids(self, session_ids):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        ewallet_session_set, sessions_not_found = [], 0
        for session_id in session_ids:
            ewallet_session = session_pool.get(session_id)
            if not ewallet_session:
                self.warning_could_not_find_ewallet_session_in_pool_by_id(session_id)
                sessions_not_found += 1
                continue
            ewallet_session_set.append(ewallet_session)
        return self.error_could_not_fetch_ewallet_session_set_from_pool_by_ids(
            session_ids, session_pool,
        ) if not ewallet_session_set else {
            'failed': False,
            'sessions': ewallet_session_set,
            'not_found': sessions_not_found,
        }

    def sanitize_session_worker_values(self, values):
        log.debug('')
        sanitized_values = values.copy()
        sanitized_values['create_date'] = res_utils.format_datetime(
            values['create_date']
        )
        sanitized_values['state_timestamp'] = res_utils.format_datetime(
            values['state_timestamp']
        )
        try:
            for session_id in values['session_pool']:
                sanitized_values['session_pool'][session_id] = str(
                    values['session_pool'][session_id]
                )
        except Exception as e:
            self.warning_could_not_sanitize_ewallet_session_pool(
                values['session_pool'], e
            )
        sanitized_values['instruction_set_recv'] = str(
            values['instruction_set_recv']
        )
        sanitized_values['instruction_set_resp'] = str(
            values['instruction_set_resp']
        )
        try:
            for client_id in values['token_session_map']:
                for session_token in client_id:
                    sanitized_values['token_session_map'][client_id][session_token] = str(
                        values['token_session_map'][client_id][session_token]
                    )
        except Exception as e:
            self.warning_could_not_sanitize_token_session_map(
                values['token_session_map'], e
            )
        sanitized_values['lock'] = str(values['lock'])
        return sanitized_values

#   @pysnooper.snoop()
    def send_instruction_response(self, response, *args, **kwargs):
        '''
        [ NOTE   ]: Response to session manager through multiprocessiong Queue.
        [ INPUT  ]: <response type-dict required-true >
        [ RETURN ]: (True | {'failed': True, 'error': ...})
        '''
        log.debug('')
        response_queue = self.fetch_worker_response_queue()
        if not response_queue or isinstance(response_queue, dict) and \
                response_queue.get('failed'):
            return self.error_could_not_fetch_session_worker_response_queue(
                response_queue, response, args, kwargs
            )
        self.clean_response_queue(response_queue)
        try:
            response_queue.put(response)
        except Exception as e:
            return self.error_could_not_issue_instruction_set_response(
                response_queue, response, args, kwargs
            )
        return True

    def ensure_worker_locked(self, lock):
        log.debug('')
        if not lock.value:
            while not lock.value:
                time.sleep(0.1)
                continue
        self.debug_worker_locked(lock.value)
        return True

    def ensure_worker_unlocked(self, lock):
        log.debug('')
        if lock.value:
            while lock.value:
                time.sleep(0.1)
                continue
        self.debug_worker_unlocked(lock.value)
        return True

#   @pysnooper.snoop()
    def receive_instruction_set(self, *args, **kwargs):
        '''
        [ NOTE   ]: Fetch instruction set issues by session manager through
                    multiprocessing Queue, and respond automatically in case of
                    invalid format.
        [ RETURN ]: (
            {'failed': False, 'controller': 'client', ...} |
            {'failed': True, 'error': ...}
        )
        '''
        log.debug('')
        instruction_queue = self.fetch_worker_instruction_queue()
        instruction = instruction_queue.get()
        try:
            instruction_set = dict(instruction) #ast.literal_eval(instruction)
        except Exception as e:
            response_queue = self.fetch_worker_response_queue()
            error = self.error_invalid_instruction_set_for_worker(
                instruction, e
            )
            response_queue.put(error)
            return error
        return instruction_set

    # MAPPERS

    def map_ewallet_session(self, ewallet_session):
        log.debug('')
        return self.update_ewallet_session_pool(
            {ewallet_session.fetch_active_session_id(): ewallet_session}
        )

    def map_client_label_token(self, client_id):
        log.debug('')
        return self.update_client_token_pool(client_id)

    def map_session_label_token(self, session_token):
        log.debug('')
        return self.update_session_token_pool(session_token)

    def map_ewallet_session_token(self, client_id, session_token, esession):
        log.debug('')
        return self.update_ewallet_session_token_map(
            {client_id: {session_token: esession}}
        )

    def map_client_session(self, client_id, session_token, esession):
        log.debug('')
        return {
            'client_token': self.map_client_label_token(client_id),
            'session_token': self.map_session_label_token(session_token),
            'session': self.map_ewallet_session(esession),
            'token_set': self.map_ewallet_session_token(
                client_id, session_token, esession
            ),
        }

    # SPAWNERS

    def spawn_ewallet_session(self, orm_session, **kwargs):
        log.debug('')
        now = datetime.datetime.now()
        return EWallet(
            name=kwargs.get('reference'),
            session=orm_session,
            expiration_date=kwargs.get('expiration_date'),
            create_date=now, write_date=now
        )

    # CREATORS

#   @pysnooper.snoop()
    def create_new_ewallet_session(self, **kwargs):
        log.debug('')
        availability_check = self.check_session_worker_available()
        if not availability_check:
            return self.error_session_worker_full(kwargs)
        orm_session = res_utils.session_factory()
        ewallet_session = self.spawn_ewallet_session(orm_session, **kwargs)
        orm_session.add(ewallet_session)
        orm_session.commit()
        return ewallet_session

    # ACTIONS
    '''
    [ NOTE ]: Command chain responses are formulated here.
    '''

    def action_view_master_login_records(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_login = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='view',
            view='login', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_master_account_login_records(
            ewallet_session, kwargs, view_login
        ) if not view_login or \
            isinstance(view_login, dict) and \
            view_login.get('failed') else view_login
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_inspect_master_subordonate(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'inspect', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        inspect = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='inspect',
            inspect='subordonate', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_inspect_master_subordonate(
            ewallet_session, kwargs, inspect
        ) if not inspect or \
            isinstance(inspect, dict) and \
            inspect.get('failed') else inspect
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_inspect_master_subordonate_pool(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'inspect', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        inspect = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='inspect',
            inspect='subpool', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_inspect_master_subordonate_pool(
            ewallet_session, kwargs, inspect
        ) if not inspect or \
            isinstance(inspect, dict) and \
            inspect.get('failed') else inspect
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_inspect_master_acquired_ctokens(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        master = ewallet_session.fetch_active_session_master()
        master_id = master.fetch_user_id()
        # Formulate response
        response = self.warning_could_not_fetch_active_session_master_account_id(
            ewallet_session, kwargs, master_id
        ) if not master_id or isinstance(master_id, dict) and \
            master_id.get('failed') else {
                'failed': False,
                'master_id': master_id,
                'master': master.fetch_user_email(),
                'master_data': master.fetch_user_values(),
            }
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_recover_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'recover', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        recover_account = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='recover',
            recover='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_recover_master_account(
            ewallet_session, kwargs, recover_account
        ) if not recover_account or \
            isinstance(recover_account, dict) and \
            recover_account.get('failed') else recover_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_account = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='unlink',
            unlink='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_master_account(
            ewallet_session, kwargs, unlink_account
        ) if not unlink_account or \
            isinstance(unlink_account, dict) and \
            unlink_account.get('failed') else unlink_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_edit_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'edit', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        edit_account = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='edit',
            edit='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_edit_master_account(
            ewallet_session, kwargs, edit_account
        ) if not edit_account or \
            isinstance(edit_account, dict) and \
            edit_account.get('failed') else edit_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_account = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='view',
            view='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_master_account(
            ewallet_session, kwargs, view_account
        ) if not view_account or \
            isinstance(view_account, dict) and \
            view_account.get('failed') else view_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_logout_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'active_session', 'logout'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        account_logout = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='logout',
            logout='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_logout_master_account(
            ewallet_session, kwargs, account_logout
        ) if not account_logout or \
            isinstance(account_logout, dict) and \
            account_logout.get('failed') else account_logout
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_login_master_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'active_session', 'login',
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        account_login = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='login',
            login='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_login_master_account(
            kwargs, ewallet_session, orm_session, account_login
        ) if not account_login else account_login
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_account_login(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        account_login = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='login',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_login_user_account(
            kwargs, ewallet_session, orm_session, account_login
        ) if not account_login else account_login
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_add_new_system_session(self, **kwargs):
        # Create new ewallet session
        ewallet_session = self.create_new_ewallet_session(
            expiration_date=kwargs.get('expiration_date') or
                self.fetch_ewallet_session_expiration_date()
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return self.warning_could_not_create_new_ewallet_system_session(
                kwargs, ewallet_session
            )
        # Add map entry
        map_session = self.map_ewallet_session(ewallet_session)
        # Formulate instruction response
        response = {
            'failed': False,
            'ewallet_session': ewallet_session.fetch_active_session_id(),
        }
        # Respond to session manager
        self.send_instruction_response(response)
        return response

#   @pysnooper.snoop()
    def action_add_new_session(self, **kwargs):
        log.debug('')
        # Create new ewallet session
        ewallet_session = self.create_new_ewallet_session(
            expiration_date=kwargs.get('expiration_date') or
                self.fetch_ewallet_session_expiration_date()
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return self.warning_could_not_create_new_ewallet_session(
                kwargs, ewallet_session
            )
        # Add map entries
        map_client_session = self.map_client_session(
            kwargs['client_id'], kwargs['session_token'], ewallet_session
        )
        # Formulate instruction response
        response = {
            'failed': False,
            'ewallet_session': ewallet_session.fetch_active_session_id(),
        }
        # Respond to session manager
        self.send_instruction_response(response)
        return response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_add_master_acquired_ctoken_to_pool(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'add', 'ctoken',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        add_ctoken = ewallet_session.ewallet_controller(
            controller='master', ctype='action', action='add', add='ctoken',
            ctoken='acquired', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_add_master_acquired_ctoken_to_pool(
             add_ctoken, ewallet_session, kwargs
        ) if not add_ctoken or isinstance(add_ctoken, dict) and \
            add_ctoken.get('failed') else add_ctoken
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_acquire_master_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'acquire',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        master_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='search', search='master',
            search_by='email', active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_fetch_master_account_by_email(
             master_account, ewallet_session, kwargs
        ) if not master_account or isinstance(master_account, dict) and \
            master_account.get('failed') else master_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_master_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'master',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='master',
            master='account', active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_master_account(
             new_account, ewallet_session, kwargs
        ) if not new_account or isinstance(new_account, dict) and \
            new_account.get('failed') else new_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_create_new_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_user_account(
             new_account, ewallet_session, kwargs
        ) if not new_account or isinstance(new_account, dict) and \
            new_account.get('failed') else new_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_interogate_session_pool_has_empty(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if not session_pool or isinstance(session_pool, dict) and \
                session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(
                kwargs, session_pool
            )
        empty = self.fetch_next_empty_ewallet_session_from_pool(session_pool)
        if not empty:
            log.info('No empty ewallet sessions found in pool.')
        elif isinstance(empty, dict) and empty.get('failed'):
            return self.error_could_not_fetch_empty_ewallet_sessions_from_pool(
                kwargs, session_pool, empty
            )
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'has_empty': empty, # Boolean flag
        }
        self.send_instruction_response(response)
        return response

    def action_interogate_session_pool_empty(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if isinstance(session_pool, dict) and session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(
                kwargs, session_pool
            )
        empty_sessions = self.fetch_empty_ewallet_sessions_from_pool(session_pool)
        if not empty_sessions:
            log.info('No empty ewallet sessions found in pool.')
        elif isinstance(empty_sessions, dict) and \
            empty_sessions.get('failed'):
            return self.error_could_not_fetch_empty_ewallet_sessions_from_pool(
                kwargs, session_pool, empty_sessions
            )
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'session_count': len(empty_sessions),
            'empty_sessions': empty_sessions, # List of numerical ids
        }
        self.send_instruction_response(response)
        return response

    def action_interogate_session_pool_has_expired(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if not session_pool or isinstance(session_pool, dict) and \
                session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(
                kwargs, session_pool
            )
        expired = self.fetch_next_expired_ewallet_session_from_pool(session_pool)
        if not expired:
            log.info('No expired ewallet sessions found in pool.')
        elif isinstance(expired, dict) and expired.get('failed'):
            return self.error_could_not_fetch_expired_ewallet_sessions_from_pool(
                kwargs, session_pool, expired
            )
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'has_expired': expired, # Boolean flag
        }
        self.send_instruction_response(response)
        return response

    def action_interogate_session_pool_expired(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if isinstance(session_pool, dict) and session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(
                kwargs, session_pool
            )
        expired_sessions = self.fetch_expired_ewallet_sessions_from_pool(session_pool)
        if not expired_sessions:
            log.info('No expired ewallet sessions found in pool.')
        elif isinstance(expired_sessions, dict) and \
            expired_sessions.get('failed'):
            return self.error_could_not_fetch_expired_ewallet_sessions_from_pool(
                kwargs, session_pool, expired_sessions
            )
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'session_count': len(expired_sessions),
            'expired_sessions': expired_sessions, # List of numerical ids
        }
        self.send_instruction_response(response)
        return response

    def action_remove_ewallet_session_set_from_pool(self, **kwargs):
        log.debug('')
        if not kwargs.get('sessions'):
            return self.error_no_worker_action_remove_session_set_specified(kwargs)
        session_search = self.search_ewallet_session_set_in_pool_by_ids(
            kwargs['sessions']
        )
        cleanup = self.cleanup_ewallet_sessions(session_search['sessions'])
        remove_from_pool = self.remove_ewallet_sessions_from_worker_pool(
            session_search['sessions']
        )
        if not remove_from_pool or isinstance(remove_from_pool, dict) and \
                remove_from_pool.get('failed'):
            return self.warning_could_not_remove_ewallet_session_from_pool(
                kwargs, remove_from_pool, session_search['sessions'], cleanup
            )
        remove_from_disk = self.remove_ewallet_sessions_from_disk(
            session_search['sessions']
        )
        if not remove_from_disk or isinstance(remove_from_disk, dict) and \
                remove_from_disk.get('failed'):
            return self.warning_could_not_remove_ewallet_session_from_disk(
                kwargs, remove_from_disk, session_search['sessions'], cleanup,
            )
        response =  {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'sessions': kwargs['sessions'],
            'session_cleaned': remove_from_pool['sessions_removed'],
            'cleanup_failures': remove_from_disk['removal_failures'] \
                + remove_from_pool['removal_failures'] \
                + cleanup['cleanup_failures'],
            'orphaned_stokens': cleanup['orphaned_stokens'],
        }
        self.send_instruction_response(response)
        return response

    def action_remove_session_map_by_ewallet_session(self, **kwargs):
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

    def action_cleanup_session_worker(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        command = self.fetch_ewallet_session_cleanup_command()
        stoken_pool = self.fetch_stoken_pool()
        for session_id in session_pool:
            ewallet_session = session_pool[session_id]
            cleanup = ewallet_session.ewallet_controller(**command)
            if not cleanup or isinstance(cleanup, dict) and \
                    cleanup.get('failed'):
                self.warning_could_not_cleanup_ewallet_session(
                    kwargs, command, ewallet_session, cleanup
                )
                continue
            orm_session = ewallet_session.fetch_active_session()
            remove_from_disk = self.remove_ewallet_session_from_disk(
                session_id, orm_session
            )
            if not remove_from_disk or isinstance(remove_from_disk, dict) and \
                    remove_from_disk.get('failed'):
                return self.warning_could_not_remove_ewallet_session_from_disk(
                    kwargs, remove_from_disk, ewallet_session, orm_session,
                )
            remove_from_pool = self.remove_ewallet_session_from_worker_pool(
                kwargs['session_id']
            )
            if not remove_from_pool or isinstance(remove_from_pool, dict) and \
                    remove_from_pool.get('failed'):
                return self.warning_could_not_remove_ewallet_session_from_pool(
                    kwargs, remove_from_pool, ewallet_session, orm_session
                )
        self.clean_session_worker_data({})
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'worker_data': self.sanitize_session_worker_values(
                self.fetch_session_worker_values()
            ),
            'orphaned_stokens': stoken_pool,
        }
        self.send_instruction_response(response)
        return response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_remove_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_worker_action_remove_session_specified(kwargs)
        command = self.fetch_ewallet_session_cleanup_command()
        ewallet_session = self.fetch_ewallet_session_from_pool_by_id(
            kwargs['session_id']
        )
        cleanup = ewallet_session.ewallet_controller(**command)
        if not cleanup or isinstance(cleanup, dict) and cleanup.get('failed'):
            return self.warning_could_not_cleanup_ewallet_session(
                kwargs, command, ewallet_session, cleanup
            )
        remove_from_disk = self.remove_ewallet_sessions_from_disk(
            [ewallet_session]
        )
        if not remove_from_disk or isinstance(remove_from_disk, dict) and \
                remove_from_disk.get('failed'):
            return self.warning_could_not_remove_ewallet_session_from_disk(
                kwargs, remove_from_disk
            )
        remove_from_pool = self.remove_ewallet_session_from_worker_pool(
            kwargs['session_id']
        )
        if not remove_from_pool or isinstance(remove_from_pool, dict) and \
                remove_from_pool.get('failed'):
            return self.warning_could_not_remove_ewallet_session_from_pool(
                kwargs, remove_from_pool
            )
        response =  {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'sessions': list(remove_from_pool['session_pool'].keys()),
            'session_cleaned': kwargs['session_id'],
            'cleaning_failures': remove_from_disk['removal_failures'],
        }
        self.send_instruction_response(response)
        return response

#   @pysnooper.snoop()
    def action_add_client_id_session_token_map_entry(self, **kwargs):
        '''
        [ NOTE   ]: Maps an existing client_id with a new session token and object.
        [ INPUT  ]: client_id=<label>, session_token=<label>, session=<EWallet-obj>
        [ RETURN ]: {client_id: {'token': session_token, 'session': session}}
        '''
        log.debug('')
        if None in [kwargs.get('client_token'), kwargs.get('session_token'),
                kwargs.get('session')]:
            return self.error_required_session_token_map_entry_data_not_found(
                kwargs
            )
        map_entry = {
            kwargs['client_token']: {
                'token': kwargs['session_token'],
                'session': kwargs['session']
            }
        }
        set_stoken_to_pool = self.set_new_session_token_to_pool(kwargs['session_token'])
        set_entry = self.set_session_worker_token_session_map_entry(map_entry)
        if set_entry or isinstance(set_entry, dict) and not set_entry.get('failed'):
            self.handle_system_action_session_worker_state_check()
        instruction_set_response = {
            'failed': False,
            'map_entry': map_entry,
        }
        return self.warning_could_not_set_ewallet_session_token_map_entry(
            kwargs, map_entry, set_stoken_to_pool, set_entry
        ) if not set_entry or isinstance(set_entry, dict) and \
            set_entry.get('failed') else instruction_set_response

    def action_interogate_worker_state(self, **kwargs):
        log.debug('')
        state = self.fetch_session_worker_values()
        sanitized_state = self.sanitize_session_worker_values(state)
        response = {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'worker_data': sanitized_state,
        }
        self.send_instruction_response(response)
        return response

    def action_check_ewallet_session_state(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_ewallet_session_id_found(kwargs)
        ewallet_session = self.fetch_ewallet_session_from_pool_by_id(
            kwargs['session_id']
        )
        if isinstance(ewallet_session, dict) and ewallet_session.get('failed'):
            return self.warning_could_not_fetch_ewallet_session(
                kwargs, ewallet_session
            )
        instruction = self.fetch_ewallet_session_state_check_instruction()
        session_state = ewallet_session.ewallet_controller(**instruction)
        if not session_state or isinstance(session_state, dict) and \
                session_state.get('failed'):
            response = self.warning_could_not_check_ewallet_session_state(
                kwargs, ewallet_session, instruction, session_state
            )
        else:
            response = session_state
            response['session_data']['orm_session'] = str(
                response['session_data']['orm_session']
            )
            response['session_data']['create_date'] = res_utils.format_datetime(
                response['session_data']['create_date']
            )
            response['session_data']['write_date'] = res_utils.format_datetime(
                response['session_data']['write_date']
            )
            response['session_data']['expiration_date'] = res_utils.format_datetime(
                response['session_data']['expiration_date']
            )
        self.send_instruction_response(response)
        return response

    def action_interogate_worker_state_code(self, **kwargs):
        log.debug('')
        state_code = self.fetch_session_worker_state_code()
        instruction_set_response = {
            'failed': False,
            'state': state_code,
        }
        self.send_instruction_response(instruction_set_response)
        return instruction_set_response

    def action_check_ewallet_session_exists(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_ewallet_session_id_found(kwargs)
        check = self.check_ewallet_session_id_mapped(kwargs['session_id'])
        response = self.error_could_not_check_if_ewallet_session_exists(
            kwargs, check
        ) if isinstance(check, dict) and check.get('failed') else {
            'failed': False,
            'worker': self.fetch_worker_id(),
            'session': kwargs['session_id'],
            'exists': check,
        }
        self.send_instruction_response(response)
        return response

    # TODO - Refactor
#   @pysnooper.snoop()
    def action_add_client_id(self, **kwargs):
        log.debug('TODO - Refactor')
        if not kwargs.get('client_id'):
            return self.error_no_client_token_found(kwargs)
        set_to_pool = self.set_new_client_token_to_pool(kwargs['client_id'])
        return self.error_could_not_add_new_client_token_to_pool(
                set_to_pool, kwargs,
            ) if not set_to_pool or isinstance(set_to_pool, dict) and \
                set_to_pool.get('failed') else {
                'failed': False,
                'client_id': kwargs['client_id'],
            }

    def action_interogate_session_pool_state(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if not session_pool or isinstance(session_pool, dict) and \
                session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(
                kwargs, session_pool
            )
        # Formulate instruction response
        response = {
            'failed': False,
            'session_pool': list(session_pool.keys()),
        }
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='invoice', invoice='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_invoice_sheet(
            ewallet_session, kwargs, unlink_invoice_sheet
        ) if not unlink_invoice_sheet or \
            isinstance(unlink_invoice_sheet, dict) and \
            unlink_invoice_sheet.get('failed') else unlink_invoice_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_invoice_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='invoice', invoice='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_invoice_record(
            ewallet_session, kwargs, unlink_invoice_record
        ) if not unlink_invoice_record or \
            isinstance(unlink_invoice_record, dict) and \
            unlink_invoice_record.get('failed') else unlink_invoice_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_recover_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'recover', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        recover_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='recover',
            recover='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_recover_user_account(
            ewallet_session, kwargs, recover_account
        ) if not recover_account or \
            isinstance(recover_account, dict) and \
            recover_account.get('failed') else recover_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_user_account(
            ewallet_session, kwargs, switch_account
        ) if not switch_account or \
            isinstance(switch_account, dict) and \
            switch_account.get('failed') else switch_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='credit_wallet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_credit_ewallet(
            ewallet_session, kwargs, unlink_credit_ewallet
        ) if not unlink_credit_ewallet or \
            isinstance(unlink_credit_ewallet, dict) and \
            unlink_credit_ewallet.get('failed') else unlink_credit_ewallet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='credit_clock', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_credit_clock(
            ewallet_session, kwargs, unlink_credit_clock
        ) if not unlink_credit_clock or \
            isinstance(unlink_credit_clock, dict) and \
            unlink_credit_clock.get('failed') else unlink_credit_clock
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_time_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='time', time='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_time_sheet(
            ewallet_session, kwargs, unlink_time_sheet
        ) if not unlink_time_sheet or \
            isinstance(unlink_time_sheet, dict) and \
            unlink_time_sheet.get('failed') else unlink_time_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_time_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_time_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='time', time='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_time_record(
            ewallet_session, kwargs, unlink_time_record
        ) if not unlink_time_record or \
            isinstance(unlink_time_record, dict) and \
            unlink_time_record.get('failed') else unlink_time_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='transfer', transfer='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_transfer_sheet(
            ewallet_session, kwargs, unlink_transfer_sheet
        ) if not unlink_transfer_sheet or \
            isinstance(unlink_transfer_sheet, dict) and \
            unlink_transfer_sheet.get('failed') else unlink_transfer_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_transfer_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='transfer', transfer='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_transfer_record(
            ewallet_session, kwargs, unlink_transfer_record
        ) if not unlink_transfer_record or \
            isinstance(unlink_transfer_record, dict) and \
            unlink_transfer_record.get('failed') else unlink_transfer_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_conversion_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='conversion', conversion='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_conversion_sheet(
            ewallet_session, kwargs, unlink_conversion_sheet
        ) if not unlink_conversion_sheet or \
            isinstance(unlink_conversion_sheet, dict) and \
            unlink_conversion_sheet.get('failed') else unlink_conversion_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_conversion_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='conversion', conversion='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_conversion_record(
            ewallet_session, kwargs, unlink_conversion_record
        ) if not unlink_conversion_record or \
            isinstance(unlink_conversion_record, dict) and \
            unlink_conversion_record.get('failed') else unlink_conversion_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_contact_list(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'contact',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='contact', contact='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_contact_list(
            ewallet_session, kwargs, unlink_contact_list
        ) if not unlink_contact_list or \
            isinstance(unlink_contact_list, dict) and \
            unlink_contact_list.get('failed') else unlink_contact_list
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_contact_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'contact',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_contact_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='contact', contact='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_contact_record(
            ewallet_session, kwargs, unlink_contact_record
        ) if not unlink_contact_record or \
            isinstance(unlink_contact_record, dict) and \
            unlink_contact_record.get('failed') else unlink_contact_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_unlink_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        unlink_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink',
            unlink='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_unlink_user_account(
            ewallet_session, kwargs, unlink_account
        ) if not unlink_account or \
            isinstance(unlink_account, dict) and \
            unlink_account.get('failed') else unlink_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_contact_list(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'contact',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='contact_list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_contact_list(
            ewallet_session, kwargs, switch_contact_list
        ) if not switch_contact_list or \
            isinstance(switch_contact_list, dict) and \
            switch_contact_list.get('failed') else switch_contact_list
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='conversion_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_time_sheet(
            ewallet_session, kwargs, switch_conversion_sheet
        ) if not switch_conversion_sheet or \
            isinstance(switch_conversion_sheet, dict) and \
            switch_conversion_sheet.get('failed') else switch_conversion_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_time_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='time_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_time_sheet(
            ewallet_session, kwargs, switch_time_sheet
        ) if not switch_time_sheet or \
            isinstance(switch_time_sheet, dict) and \
            switch_time_sheet.get('failed') else switch_time_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='transfer_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_transfer_sheet(
            ewallet_session, kwargs, switch_transfer_sheet
        ) if not switch_transfer_sheet or \
            isinstance(switch_transfer_sheet, dict) and \
            switch_transfer_sheet.get('failed') else switch_transfer_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='invoice_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_invoice_sheet(
            ewallet_session, kwargs, switch_invoice_sheet
        ) if not switch_invoice_sheet or \
            isinstance(switch_invoice_sheet, dict) and \
            switch_invoice_sheet.get('failed') else switch_invoice_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='credit_ewallet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_credit_ewallet(
            ewallet_session, kwargs, switch_credit_ewallet
        ) if not switch_credit_ewallet or \
            isinstance(switch_credit_ewallet, dict) and \
            switch_credit_ewallet.get('failed') else switch_credit_ewallet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_switch_credit_clock(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'switch', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        switch_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch',
            switch='credit_clock', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_switch_credit_clock(
            ewallet_session, kwargs, switch_credit_clock
        ) if not switch_credit_clock or \
            isinstance(switch_credit_clock, dict) and \
            switch_credit_clock.get('failed') else switch_credit_clock
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_conversion_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='conversion_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_conversion_sheet(
            ewallet_session, kwargs, new_conversion_sheet
        ) if not new_conversion_sheet or \
            isinstance(new_conversion_sheet, dict) and \
            new_conversion_sheet.get('failed') else new_conversion_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_time_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='time_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_time_sheet(
            ewallet_session, kwargs, new_time_sheet
        ) if not new_time_sheet or \
            isinstance(new_time_sheet, dict) and \
            new_time_sheet.get('failed') else new_time_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_transfer_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='transfer_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_transfer_sheet(
            ewallet_session, kwargs, new_transfer_sheet
        ) if not new_transfer_sheet or \
            isinstance(new_transfer_sheet, dict) and \
            new_transfer_sheet.get('failed') else new_transfer_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_invoice_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='invoice_sheet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_invoice_sheet(
            ewallet_session, kwargs, new_invoice_sheet
        ) if not new_invoice_sheet or \
            isinstance(new_invoice_sheet, dict) and \
            new_invoice_sheet.get('failed') else new_invoice_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_credit_ewallet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='credit_wallet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_credit_ewallet(
            ewallet_session, kwargs, new_ewallet
        ) if not new_ewallet or \
            isinstance(new_ewallet, dict) and \
            new_ewallet.get('failed') else new_ewallet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_credit_clock(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='credit_clock', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_credit_clock(
            ewallet_session, kwargs, new_clock
        ) if not new_clock or \
            isinstance(new_clock, dict) and \
            new_clock.get('failed') else new_clock
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_logout_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        account_logout = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='logout',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_logout_user_account(
            ewallet_session, kwargs, account_logout
        ) if not account_logout or \
            isinstance(account_logout, dict) and \
            account_logout.get('failed') else account_logout
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_login_records(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_login_records = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='login', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_login_records(
            ewallet_session, kwargs, view_login_records
        ) if not view_login_records or \
            isinstance(view_login_records, dict) and \
            view_login_records.get('failed') else view_login_records
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_logout_records(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_logout_records = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='logout', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_logout_records(
            ewallet_session, kwargs, view_logout_records
        ) if not view_logout_records or \
            isinstance(view_logout_records, dict) and \
            view_logout_records.get('failed') else view_logout_records
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='invoice', invoice='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_invoice_sheet(
            ewallet_session, kwargs, view_invoice_sheet
        ) if not view_invoice_sheet or \
            isinstance(view_invoice_sheet, dict) and \
            view_invoice_sheet.get('failed') else view_invoice_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_invoice_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'invoice',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_invoice_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='invoice', invoice='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_invoice_record(
            ewallet_session, kwargs, view_invoice_record
        ) if not view_invoice_record or \
            isinstance(view_invoice_record, dict) and \
            view_invoice_record.get('failed') else view_invoice_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='credit_wallet', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_credit_ewallet(
            ewallet_session, kwargs, view_ewallet
        ) if not view_ewallet or \
            isinstance(view_ewallet, dict) and \
            view_ewallet.get('failed') else view_ewallet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_credit_clock(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'credit',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='credit_clock', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_credit_clock(
            ewallet_session, kwargs, view_clock
        ) if not view_clock or \
            isinstance(view_clock, dict) and \
            view_clock.get('failed') else view_clock
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_user_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_user_account(
            ewallet_session, kwargs, view_account
        ) if not view_account or \
            isinstance(view_account, dict) and \
            view_account.get('failed') else view_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='conversion', conversion='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_conversion_sheet(
            ewallet_session, kwargs, view_conversion_sheet
        ) if not view_conversion_sheet or \
            isinstance(view_conversion_sheet, dict) and \
            view_conversion_sheet.get('failed') else view_conversion_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_conversion_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'conversion',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_conversion_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='conversion', conversion='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_conversion_record(
            ewallet_session, kwargs, view_conversion_record
        ) if not view_conversion_record or \
            isinstance(view_conversion_record, dict) and \
            view_conversion_record.get('failed') else view_conversion_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_time_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='time', time='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_time_sheet(
            ewallet_session, kwargs, view_time_sheet
        ) if not view_time_sheet or \
            isinstance(view_time_sheet, dict) and \
            view_time_sheet.get('failed') else view_time_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_time_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'time',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_time_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='time', time='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_time_record(
            ewallet_session, kwargs, view_time_record
        ) if not view_time_record or \
            isinstance(view_time_record, dict) and \
            view_time_record.get('failed') else view_time_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_transfer_sheet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='transfer', transfer='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_transfer_sheet(
            ewallet_session, kwargs, view_transfer_sheet
        ) if not view_transfer_sheet or \
            isinstance(view_transfer_sheet, dict) and \
            view_transfer_sheet.get('failed') else view_transfer_sheet
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_transfer_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'transfer',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_transfer_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='transfer', transfer='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_transfer_record(
            ewallet_session, kwargs, view_transfer_record
        ) if not view_transfer_record or \
            isinstance(view_transfer_record, dict) and \
            view_transfer_record.get('failed') else view_transfer_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_contact_list(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'contact',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='contact', contact='list', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_contact_list(
            ewallet_session, kwargs, view_contact_list
        ) if not view_contact_list or \
            isinstance(view_contact_list, dict) and \
            view_contact_list.get('failed') else view_contact_list
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_view_contact_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'view', 'contact',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        view_contact_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            view='contact', contact='record', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_view_contact_record(
            ewallet_session, kwargs, view_contact_record
        ) if not view_contact_record or \
            isinstance(view_contact_record, dict) and \
            view_contact_record.get('failed') else view_contact_record
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_stop_clock_timer(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'stop', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        stop_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time',
            timer='stop', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_stop_clock_timer(
            kwargs, ewallet_session, orm_session, stop_timer
        ) if not stop_timer or \
            isinstance(stop_timer, dict) and \
            stop_timer.get('failed') else stop_timer
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_resume_clock_timer(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'resume', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        resume_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time',
            timer='resume', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_resume_clock_timer(
            kwargs, ewallet_session, orm_session, resume_timer
        ) if not resume_timer or \
            isinstance(resume_timer, dict) and \
            resume_timer.get('failed') else resume_timer
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_pause_clock_timer(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'pause', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        pause_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time',
            timer='pause', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_pause_clock_timer(
            kwargs, ewallet_session, orm_session, pause_timer
        ) if not pause_timer or \
            isinstance(pause_timer, dict) and \
            pause_timer.get('failed') else pause_timer
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_start_clock_timer(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'start', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        start_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time',
            timer='start', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_start_clock_timer(
            kwargs, ewallet_session, orm_session, start_timer
        ) if not start_timer or \
            isinstance(start_timer, dict) and \
            start_timer.get('failed') else start_timer
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_edit_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'edit', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        edit_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='edit',
            edit='account', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_edit_account(
            ewallet_session, kwargs, edit_account
        ) if not edit_account or \
            isinstance(edit_account, dict) and \
            edit_account.get('failed') else edit_account
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_transfer_credits(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'ttype',
            'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        transfer_credits = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='transfer', ttype='transfer',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_transfer_credits(
            ewallet_session, kwargs, transfer_credits
        ) if not transfer_credits or \
            isinstance(transfer_credits, dict) and \
            transfer_credits.get('failed') else transfer_credits
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_contact_list(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create',
            'contact', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='contact', contact='list',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_contact_list(
            ewallet_session, kwargs, new_contact_list
        ) if not new_contact_list or \
            isinstance(new_contact_list, dict) and \
            new_contact_list.get('failed') else new_contact_list
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_new_contact_record(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create',
            'contact', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        new_contact = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='contact', contact='record',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_create_new_contact_record(
            ewallet_session, kwargs, new_contact
        ) if not new_contact or \
            isinstance(new_contact, dict) and \
            new_contact.get('failed') else new_contact
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_convert_clock_to_credits(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create',
            'conversion', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        convert_clock2credits = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='conversion', conversion='clock2credits',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_convert_clock_to_credits(
            ewallet_session, kwargs, convert_clock2credits
        ) if not convert_clock2credits or \
            isinstance(convert_clock2credits, dict) and \
            convert_clock2credits.get('failed') else convert_clock2credits
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create',
            'conversion', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        convert_credits2clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='conversion', conversion='credits2clock',
            active_session=orm_session, **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_convert_credits_to_clock(
            ewallet_session, kwargs, convert_credits2clock
        ) if not convert_credits2clock or \
            isinstance(convert_credits2clock, dict) and \
            convert_credits2clock.get('failed') else convert_credits2clock
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_pay_partner_account(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create',
            'ttype', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        pay_credits = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='transfer', ttype='pay', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_pay_partner_account(
            ewallet_session, kwargs, pay_credits
        ) if not pay_credits or isinstance(pay_credits, dict) and \
            pay_credits.get('failed') else pay_credits
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    def action_supply_user_credit_ewallet(self, **kwargs):
        log.debug('')
        # Fetch ewallet session by token keys
        ewallet_session = self.fetch_ewallet_session_by_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'supply', 'create',
            'ttype', 'active_session'
        )
        # Execute action in session
        orm_session = ewallet_session.fetch_active_session()
        supply_credits = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='transfer', ttype='supply', active_session=orm_session,
            **sanitized_instruction_set
        )
        # Formulate response
        response = self.warning_could_not_supply_user_credit_ewallet(
            ewallet_session, kwargs
        ) if not supply_credits else supply_credits
        # Respond to session manager
        self.send_instruction_response(response)
        return response

    # ACTION HANDLERS

    def handle_master_action_view_login_records(self, **kwargs):
        log.debug('')
        return self.action_view_master_login_records(**kwargs)

    def handle_master_action_inspect_subordonate(self, **kwargs):
        log.debug('')
        return self.action_inspect_master_subordonate(**kwargs)

    def handle_master_action_inspect_subpool(self, **kwargs):
        log.debug('')
        return self.action_inspect_master_subordonate_pool(**kwargs)

    def handle_master_action_inspect_ctokens(self, **kwargs):
        log.debug('')
        return self.action_inspect_master_acquired_ctokens(**kwargs)

    def handle_master_action_recover_account(self, **kwargs):
        log.debug('')
        return self.action_recover_master_user_account(**kwargs)

    def handle_master_action_unlink_account(self, **kwargs):
        log.debug('')
        return self.action_unlink_master_user_account(**kwargs)

    def handle_master_action_edit_account(self, **kwargs):
        log.debug('')
        return self.action_edit_master_user_account(**kwargs)

    def handle_master_action_view_account(self, **kwargs):
        log.debug('')
        return self.action_view_master_user_account(**kwargs)

    def handle_master_action_logout(self, **kwargs):
        log.debug('')
        return self.action_logout_master_user_account(**kwargs)

    def handle_master_action_login(self, **kwargs):
        log.debug('')
        return self.action_login_master_user_account(**kwargs)

    def handle_master_action_add_acquired_ctoken(self, **kwargs):
        log.debug('')
        return self.action_add_master_acquired_ctoken_to_pool(**kwargs)

    def handle_client_action_acquire_master_account(self, **kwargs):
        log.debug('')
        return self.action_acquire_master_account(**kwargs)

    def handle_client_action_new_master_account(self, **kwargs):
        log.debug('')
        return self.action_new_master_account(**kwargs)

    def handle_system_action_interogate_session_pool_empty(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool_empty(**kwargs)

    def handle_system_action_interogate_session_pool_has_empty(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool_has_empty(**kwargs)

    def handle_system_action_remove_session_map_by_ewallet_session(self, **kwargs):
        log.debug('')
        action = self.action_remove_session_map_by_ewallet_session(**kwargs)
        self.update_session_worker_state()
        return action

    def handle_system_action_cleanup_session_worker(self, **kwargs):
        log.debug('')
        action = self.action_cleanup_session_worker(**kwargs)
        self.update_session_worker_state()
        return action

    def handle_system_action_interogate_state_info(self, **kwargs):
        log.debug('')
        return self.action_interogate_worker_state(**kwargs)

    def handle_system_action_check_ewallet_session_state(self, **kwargs):
        log.debug('')
        return self.action_check_ewallet_session_state(**kwargs)

    def handle_system_action_remove_session(self, **kwargs):
        log.debug('')
        action = self.action_remove_ewallet_session(**kwargs)
        self.update_session_worker_state()
        return action

    def handle_system_action_check_ewallet_session_exists(self, **kwargs):
        log.debug('')
        return self.action_check_ewallet_session_exists(**kwargs)

    def handle_system_action_remove_sessions(self, **kwargs):
        log.debug('')
        action = self.action_remove_ewallet_session_set_from_pool(**kwargs)
        self.update_session_worker_state()
        return action

    def handle_system_action_interogate_session_pool_expired(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool_expired(**kwargs)

    def handle_system_action_interogate_session_pool_has_expired(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool_has_expired(**kwargs)

    def handle_system_action_interogate_session_pool_state(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool_state(**kwargs)

    def handle_client_action_unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_unlink_invoice_sheet(**kwargs)

    def handle_client_action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        return self.action_unlink_invoice_record(**kwargs)

    def handle_client_action_recover_account(self, **kwargs):
        log.debug('')
        return self.action_recover_user_account(**kwargs)

    def handle_client_action_switch_account(self, **kwargs):
        log.debug('')
        return self.action_switch_user_account(**kwargs)

    def handle_client_action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        return self.action_unlink_credit_ewallet(**kwargs)

    def handle_client_action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        return self.action_unlink_credit_clock(**kwargs)

    def handle_client_action_unlink_time_sheet(self, **kwargs):
        log.debug('')
        return self.action_unlink_time_sheet(**kwargs)

    def handle_client_action_unlink_time_record(self, **kwargs):
        log.debug('')
        return self.action_unlink_time_record(**kwargs)

    def handle_client_action_unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_unlink_transfer_sheet(**kwargs)

    def handle_client_action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        return self.action_unlink_transfer_record(**kwargs)

    def handle_client_action_unlink_conversion_sheet(self, **kwargs):
        log.debug('')
        return self.action_unlink_conversion_sheet(**kwargs)

    def handle_client_action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        return self.action_unlink_conversion_record(**kwargs)

    def handle_client_action_unlink_contact_list(self, **kwargs):
        log.debug('')
        return self.action_unlink_contact_list(**kwargs)

    def handle_client_action_unlink_contact_record(self, **kwargs):
        log.debug('')
        return self.action_unlink_contact_record(**kwargs)

    def handle_client_action_unlink_account(self, **kwargs):
        log.debug('')
        return self.action_unlink_user_account(**kwargs)

    def handle_client_action_switch_contact_list(self, **kwargs):
        log.debug('')
        return self.action_switch_contact_list(**kwargs)

    def handle_client_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_conversion_sheet(**kwargs)

    def handle_client_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_time_sheet(**kwargs)

    def handle_client_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_invoice_sheet(**kwargs)

    def handle_client_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_transfer_sheet(**kwargs)

    def handle_client_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_transfer_sheet(**kwargs)

    def handle_client_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_switch_invoice_sheet(**kwargs)

    def handle_client_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        return self.action_switch_credit_ewallet(**kwargs)

    def handle_client_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        return self.action_switch_credit_clock(**kwargs)

    def handle_client_action_new_conversion(self, **kwargs):
        log.debug('')
        return self.action_new_conversion_sheet(**kwargs)

    def handle_client_action_new_time(self, **kwargs):
        log.debug('')
        return self.action_new_time_sheet(**kwargs)

    def handle_client_action_new_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_new_transfer_sheet(**kwargs)

    def handle_client_action_new_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_new_invoice_sheet(**kwargs)

    def handle_client_action_new_credit_ewallet(self, **kwargs):
        log.debug('')
        return self.action_new_credit_ewallet(**kwargs)

    def handle_client_action_new_credit_clock(self, **kwargs):
        log.debug('')
        return self.action_new_credit_clock(**kwargs)

    def handle_client_action_logout(self, **kwargs):
        log.debug('')
        return self.action_logout_user_account(**kwargs)

    def handle_client_action_view_login(self, **kwargs):
        log.debug('')
        return self.action_view_login_records(**kwargs)

    def handle_client_action_view_logout(self, **kwargs):
        log.debug('')
        return self.action_view_logout_records(**kwargs)

    def handle_client_action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_view_invoice_sheet(**kwargs)

    def handle_client_action_view_invoice_record(self, **kwargs):
        log.debug('')
        return self.action_view_invoice_record(**kwargs)

    def handle_client_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        return self.action_view_credit_ewallet(**kwargs)

    def handle_client_action_view_credit_clock(self, **kwargs):
        log.debug('')
        return self.action_view_credit_clock(**kwargs)

    def handle_client_action_view_account(self, **kwargs):
        log.debug('')
        return self.action_view_user_account(**kwargs)

    def handle_client_action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        return self.action_view_conversion_sheet(**kwargs)

    def handle_client_action_view_conversion_record(self, **kwargs):
        log.debug('')
        return self.action_view_conversion_record(**kwargs)

    def handle_client_action_view_time_sheet(self, **kwargs):
        log.debug('')
        return self.action_view_time_sheet(**kwargs)

    def handle_client_action_view_time_record(self, **kwargs):
        log.debug('')
        return self.action_view_time_record(**kwargs)

    def handle_client_action_view_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_view_transfer_sheet(**kwargs)

    def handle_client_action_view_transfer_record(self, **kwargs):
        log.debug('')
        return self.action_view_transfer_record(**kwargs)

    def handle_client_action_view_contact_list(self, **kwargs):
        log.debug('')
        return self.action_view_contact_list(**kwargs)

    def handle_client_action_view_contact_record(self, **kwargs):
        log.debug('')
        return self.action_view_contact_record(**kwargs)

    def handle_client_action_stop_clock_timer(self, **kwargs):
        log.debug('')
        return self.action_stop_clock_timer(**kwargs)

    def handle_client_action_pause_clock_timer(self, **kwargs):
        log.debug('')
        return self.action_pause_clock_timer(**kwargs)

    def handle_client_action_start_clock_timer(self, **kwargs):
        log.debug('')
        return self.action_start_clock_timer(**kwargs)

    def handle_client_action_edit_account(self, **kwargs):
        log.debug('')
        return self.action_edit_account(**kwargs)

    def handle_client_action_transfer_credits(self, **kwargs):
        log.debug('')
        return self.action_transfer_credits(**kwargs)

    def handle_client_action_new_contact_record(self, **kwargs):
        log.debug('')
        return self.action_new_contact_record(**kwargs)

    def handle_client_action_new_contact_list(self, **kwargs):
        log.debug('')
        return self.action_new_contact_list(**kwargs)

    def handle_client_action_convert_clock_to_credits(self, **kwargs):
        log.debug('')
        return self.action_convert_clock_to_credits(**kwargs)

    def handle_client_action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        return self.action_convert_credits_to_clock(**kwargs)

    def handle_client_action_pay(self, **kwargs):
        log.debug('')
        return self.action_pay_partner_account(**kwargs)

    def handle_client_action_supply_credits(self, **kwargs):
        log.debug('')
        return self.action_supply_user_credit_ewallet(**kwargs)

    def handle_client_action_account_login(self, **kwargs):
        log.debug('')
        return self.action_account_login(**kwargs)

    def handle_client_action_new_user_account(self, **kwargs):
        log.debug('')
        return self.action_create_new_user_account(**kwargs)

    def handle_system_action_interogate_state_code(self, **kwargs):
        log.debug('')
        return self.action_interogate_worker_state_code(**kwargs)

    def handle_client_action_resume_clock_timer(self, **kwargs):
        log.debug('')
        return self.action_resume_clock_timer(**kwargs)

    def handle_system_action_session_worker_state_check(self):
        log.debug('')
        current_state = self.fetch_session_worker_state_code()
        if current_state == 2:
            return self.warning_session_worker_ewallet_session_pool_full(
                current_state
            )
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        set_state = self.set_session_worker_state_code(
            1 if len(session_pool) >= 1 else 0
        )
        instruction_set_response = {
            'failed': False,
            'worker_state': current_state,
        }
        return self.warning_could_not_perform_session_worker_state_check(
            session_pool
        ) if not set_state or isinstance(set_state, dict) \
            and set_state.get('failed') else instruction_set_response

    def handle_system_action_search_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_found()
        ewallet_session = self.search_ewallet_session(kwargs['session_token'])
        return self.warning_session_token_not_mapped(kwargs['session_token']) \
                if not ewallet_session else ewallet_session

    # JUMPTABLE HANDLERS

    def handle_master_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_master_action_view_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_view_account,
            'login': self.handle_master_action_view_login_records,
#           'logout': self.handle_master_action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_master_action_inspect(self, **kwargs):
        log.debug('')
        if not kwargs.get('inspect'):
            return self.error_no_master_action_inspect_target_specified(kwargs)
        handlers = {
            'ctokens': self.handle_master_action_inspect_ctokens,
            'subpool': self.handle_master_action_inspect_subpool,
            'subordonate': self.handle_master_action_inspect_subordonate,
        }
        return handlers[kwargs['inspect']](**kwargs)

    def handle_master_action_recover(self, **kwargs):
        log.debug('')
        if not kwargs.get('recover'):
            return self.error_no_master_action_recover_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_recover_account,
        }
        return handlers[kwargs['recover']](**kwargs)

    def handle_master_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_master_action_unlink_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_unlink_account,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_master_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_master_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_master_action_add_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctoken'):
            return self.error_no_master_action_add_ctoken_target_specified(kwargs)
        handlers = {
            'acquired': self.handle_master_action_add_acquired_ctoken,
        }
        return handlers[kwargs['ctoken']](**kwargs)

    def handle_master_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_master_action_add_target_specified(kwargs)
        handlers = {
            'ctoken': self.handle_master_action_add_ctoken,
        }
        return handlers[kwargs['add']](**kwargs)

    def handle_client_action_acquire(self, **kwargs):
        log.debug('')
        if not kwargs.get('acquire'):
            return self.error_no_client_action_acquire_target_specified(kwargs)
        handlers = {
            'master': self.handle_client_action_acquire_master_account,
        }
        return handlers[kwargs['acquire']](**kwargs)

    def handle_system_action_cleanup(self, **kwargs):
        log.debug('')
        if not kwargs.get('cleanup'):
            return self.error_no_worker_cleanup_target_specified(kwargs)
        handlers = {
            'worker': self.handle_system_action_cleanup_session_worker,
        }
        return handlers[kwargs['cleanup']](**kwargs)

    def handle_system_action_interogate_state(self, **kwargs):
        log.debug('')
        if not kwargs.get('state'):
            return self.error_no_worker_state_interogation_target_specified(kwargs)
        handlers = {
            'code': self.handle_system_action_interogate_state_code,
            'info': self.handle_system_action_interogate_state_info,
        }
        return handlers[kwargs['state']](**kwargs)

    def handle_system_action_interogate_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session'):
            return self.error_no_system_action_interogate_session_target_specified(kwargs)
        handlers = {
            'exists': self.handle_system_action_check_ewallet_session_exists,
            'state': self.handle_system_action_check_ewallet_session_state,
        }
        return handlers[kwargs['session']](**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_worker_action_interogate_target_specified(kwargs)
        handlers = {
            'session_pool': self.handle_system_action_interogate_session_pool,
            'session': self.handle_system_action_interogate_session,
            'state': self.handle_system_action_interogate_state,
        }
        return handlers[kwargs['interogate']](**kwargs)

    def handle_system_action_interogate_session_pool(self, **kwargs):
        log.debug('')
        if not kwargs.get('pool'):
            return self.error_no_system_action_interogate_session_pool_target_specified(
                kwargs,
            )
        handlers = {
            'has_expired': self.handle_system_action_interogate_session_pool_has_expired,
            'has_empty': self.handle_system_action_interogate_session_pool_has_empty,
            'expired': self.handle_system_action_interogate_session_pool_expired,
            'empty': self.handle_system_action_interogate_session_pool_empty,
            'state': self.handle_system_action_interogate_session_pool_state,
        }
        return handlers[kwargs['pool']](**kwargs)

    def handle_client_action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_unlink_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_invoice_sheet,
            'record': self.handle_client_action_unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_recover(self, **kwargs):
        log.debug('')
        if not kwargs.get('recover'):
            return self.error_no_client_action_recover_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_recover_account,
        }
        return handlers[kwargs['recover']](**kwargs)

    def handle_client_action_unlink_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_unlink_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_unlink_credit_ewallet,
            'clock': self.handle_client_action_unlink_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_unlink_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_time_sheet,
            'record': self.handle_client_action_unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_unlink_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_unlink_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_transfer_sheet,
            'record': self.handle_client_action_unlink_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_unlink_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_conversion_sheet,
            'record': self.handle_client_action_unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_unlink_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_unlink_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_contact_list,
            'record': self.handle_client_action_unlink_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_client_action_unlink_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_unlink_account,
            'contact': self.handle_client_action_unlink_contact,
            'conversion': self.handle_client_action_unlink_conversion,
            'transfer': self.handle_client_action_unlink_transfer,
            'time': self.handle_client_action_unlink_time,
            'credit': self.handle_client_action_unlink_credit,
            'invoice': self.handle_client_action_unlink_invoice,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_client_action_switch_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_switch_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_contact_list,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_switch_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_switch_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_conversion_sheet,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_switch_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_switch_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_time_sheet,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_switch_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_switch_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_switch_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_switch_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_switch_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_switch_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_switch_credit_ewallet,
            'clock': self.handle_client_action_switch_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_switch(self, **kwargs):
        log.debug('')
        if not kwargs.get('switch'):
            return self.error_no_client_action_switch_target_specified(kwargs)
        handlers = {
            'credit': self.handle_client_action_switch_credit,
            'transfer': self.handle_client_action_switch_transfer,
            'invoice': self.handle_client_action_switch_invoice,
            'conversion': self.handle_client_action_switch_conversion,
            'time': self.handle_client_action_switch_time,
            'contact': self.handle_client_action_switch_contact,
            'account': self.handle_client_action_switch_account,
        }
        return handlers[kwargs['switch']](**kwargs)

    # TODO
    def handle_system_action_remove_session_map(self, **kwargs):
        log.debug('TODO - Add suport for Client and Session Token identifiers')
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

    # TOOD
    def handle_client_action_transfer(self, **kwargs):
        log.debug('TODO - Add support for user action transfer time.')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_transfer_target_specified(kwargs)
        handlers = {
            'credits': self.handle_client_action_transfer_credits,
#           'time':,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_system_action_search(self, **kwargs):
        log.debug('')
        if not kwargs.get('search'):
            return self.error_no_worker_action_search_target_specified()
        handlers = {
            'session': self.handle_system_action_search_session,
        }
        return handlers[kwargs['search']](**kwargs)

    def handle_client_action_new_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_new_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_new_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_new_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_new(self, **kwargs):
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_session_worker_client_action_new_target_specified(kwargs)
        handlers = {
            'master': self.handle_client_action_new_master_account,
            'account': self.handle_client_action_new_user_account,
            'contact': self.handle_client_action_new_contact,
            'credit': self.handle_client_action_new_credit,
            'transfer': self.handle_client_action_new_transfer,
            'invoice': self.handle_client_action_new_invoice,
            'conversion': self.handle_client_action_new_conversion,
            'time': self.handle_client_action_new_time,
        }
        return handlers[kwargs['new']](**kwargs)

    def handle_client_action_new_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_new_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_new_credit_ewallet,
            'clock': self.handle_client_action_new_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_view_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_view_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_invoice_sheet,
            'record': self.handle_client_action_view_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_view_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_view_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_view_credit_ewallet,
            'clock': self.handle_client_action_view_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_client_action_view_target_specified(kwargs)
        handlers = {
            'contact': self.handle_client_action_view_contact,
            'transfer': self.handle_client_action_view_transfer,
            'time': self.handle_client_action_view_time,
            'conversion': self.handle_client_action_view_conversion,
            'account': self.handle_client_action_view_account,
            'credit': self.handle_client_action_view_credit,
            'invoice': self.handle_client_action_view_invoice,
            'login': self.handle_client_action_view_login,
            'logout': self.handle_client_action_view_logout,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_client_action_view_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_view_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_conversion_sheet,
            'record': self.handle_client_action_view_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_view_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_view_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_time_sheet,
            'record': self.handle_client_action_view_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_view_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_view_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_transfer_sheet,
            'record': self.handle_client_action_view_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_view_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_view_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_contact_list,
            'record': self.handle_client_action_view_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_stop(self, **kwargs):
        log.debug('')
        if not kwargs.get('stop'):
            return self.error_no_client_action_stop_target_specified(kwargs)
        handlers = {
            'clock_timer': self.handle_client_action_stop_clock_timer,
        }
        return handlers[kwargs['stop']](**kwargs)

    def handle_client_action_resume(self, **kwargs):
        log.debug('')
        if not kwargs.get('resume'):
            return self.error_no_client_action_resume_target_specified(kwargs)
        handlers = {
            'clock_timer': self.handle_client_action_resume_clock_timer,
        }
        return handlers[kwargs['resume']](**kwargs)

    def handle_client_action_pause(self, **kwargs):
        log.debug('')
        if not kwargs.get('pause'):
            return self.error_no_client_action_pause_target_specified(kwargs)
        handlers = {
            'clock_timer': self.handle_client_action_pause_clock_timer,
        }
        return handlers[kwargs['pause']](**kwargs)

    def handle_client_action_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_client_action_start_target_specified(kwargs)
        handlers = {
            'clock_timer': self.handle_client_action_start_clock_timer,
        }
        return handlers[kwargs['start']](**kwargs)

    def handle_client_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_client_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_client_action_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_new_contact_target_specified(kwargs)
        handlers = {
            'record': self.handle_client_action_new_contact_record,
            'list': self.handle_client_action_new_contact_list,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_convert(self, **kwargs):
        log.debug('')
        if not kwargs.get('convert'):
            return self.error_no_client_action_convert_target_specified(kwargs)
        handlers = {
            'credits2clock': self.handle_client_action_convert_credits_to_clock,
            'clock2credits': self.handle_client_action_convert_clock_to_credits,
        }
        return handlers[kwargs['convert']](**kwargs)

    def handle_client_action_supply(self, **kwargs):
        log.debug('')
        if not kwargs.get('supply'):
            return self.error_no_client_action_supply_target_specified(kwargs)
        handlers = {
            'credits': self.handle_client_action_supply_credits,
        }
        return handlers[kwargs['supply']](**kwargs)

    def handle_system_action_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('remove'):
            return self.error_no_worker_action_remove_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_remove_session,
            'sessions': self.handle_system_action_remove_sessions,
            'session_map': self.handle_system_action_remove_session_map,
        }
        return handlers[kwargs['remove']](**kwargs)

    def handle_system_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_worker_action_new_target_specified()
        handlers = {
            'session': self.action_add_new_session,
            'system_session': self.action_add_new_system_session,
            'session_map': self.action_add_client_id_session_token_map_entry,
            'client_id': self.action_add_client_id,
        }
        return handlers[kwargs['add']](**kwargs)

    # INIT

#   @pysnooper.snoop()
    def worker_init(self):
        log.debug('TODO - Fetch termination signal from config file.')
        while True:
            if not self.lock.value:
                self.debug_waiting_for_lock_from_session_manager(self.lock.value)
                self.ensure_worker_locked(self.lock)
            self.debug_fetching_instruction(self.lock.value)
            instruction = self.receive_instruction_set()
            self.debug_validating_instruction(self.lock.value, instruction)
            try:
                instruction_set = dict(instruction)
            except Exception as e:
                self.instruction_set_resp.put(str(
                    self.error_invalid_instruction_set_for_worker(
                        instruction, e
                    )
                ))
                continue
            if instruction_set.get('terminate_worker'):
                break
            self.debug_executing_instructions(self.lock.value, instruction_set)
            response = self.main_controller(**instruction_set)
            self.send_instruction_response(response)
            self.lock.value = 0
            self.debug_execution_complete_with_response(self.lock.value, response)

    # CONTROLLERS

    def master_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_master_session_manager_worker_action_specified(kwargs)
        handlers = {
            'add': self.handle_master_action_add,
            'login': self.handle_master_action_login,
            'logout': self.handle_master_action_logout,
            'view': self.handle_master_action_view,
            'edit': self.handle_master_action_edit,
            'unlink': self.handle_master_action_unlink,
            'recover': self.handle_master_action_recover,
            'inspect': self.handle_master_action_inspect,
        }
        return handlers[kwargs['action']](**kwargs)

    def client_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_client_session_manager_worker_action_specified(kwargs)
        handlers = {
            'new': self.handle_client_action_new,
            'login': self.handle_client_action_account_login,
            'supply': self.handle_client_action_supply,
            'pay': self.handle_client_action_pay,
            'convert': self.handle_client_action_convert,
            'transfer': self.handle_client_action_transfer,
            'edit': self.handle_client_action_edit,
            'start': self.handle_client_action_start,
            'pause': self.handle_client_action_pause,
            'resume': self.handle_client_action_resume,
            'stop': self.handle_client_action_stop,
            'view': self.handle_client_action_view,
            'logout': self.handle_client_action_logout,
            'new': self.handle_client_action_new,
            'switch': self.handle_client_action_switch,
            'unlink': self.handle_client_action_unlink,
            'recover': self.handle_client_action_recover,
            'acquire': self.handle_client_action_acquire,
        }
        return handlers[kwargs['action']](**kwargs)

    def master_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_master_session_manager_worker_controller_specified(
                kwargs
            )
        handlers = {
            'action': self.master_action_controller,
#           'event': self.master_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)


    def client_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_client_session_manager_worker_controller_specified(
                kwargs
            )
        handlers = {
            'action': self.client_action_controller,
#           'event': self.client_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def system_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_worker_action_specified(
                kwargs
            )
        handlers = {
            'add': self.handle_system_action_add,
            'search': self.handle_system_action_search,
            'interogate': self.handle_system_action_interogate,
            'remove': self.handle_system_action_remove,
            'cleanup': self.handle_system_action_cleanup,
        }
        return handlers[kwargs['action']](**kwargs)

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_worker_controller_specified()
        handlers = {
            'action': self.system_action_controller,
#           'event': self.system_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_worker_controller_specified(kwargs)
        handlers = {
            'system': self.system_controller,
            'client': self.client_controller,
            'master': self.master_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_could_not_view_master_account_login_records(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view Master user account login records. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_inspect_master_subordonate_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not inspect Subordonate user account pool. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_inspect_master_subordonate(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not inspect Subordonate user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch active session Master user account ID. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_recover_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not recover Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_edit_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not edit Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_logout_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not logout Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_add_master_acquired_ctoken_to_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not add master acquired CToken to pool. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_master_account_by_email(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch master account by email address. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_master_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new master account. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_ewallet_session_found_by_session_token(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'No ewallet session found by session token. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_time_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view time record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not edit user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_resume_clock_timer(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not resume credit clock timer. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_ewallet_system_session(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new ewallet session for system. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new ewallet session for client. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_ewallet_session_from_disk(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not remove ewallet session from disk. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_find_ewallet_session_in_pool_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not find ewallet session in pool by id. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_sanitize_ewallet_session_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not sanitize worker ewallet session pool to make it pickable. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_sanitize_token_session_map(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not sanitize worker token session map to make it pickable. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set session worker reference. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_cleanup_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not cleanup ewallet session. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_ewallet_session_from_disk(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not remove ewallet session from disk. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_ewallet_session_from_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not remove ewallet session from pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_ewallet_session_token_map_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not ewallet session token map entry. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch ewallet session. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_check_ewallet_session_state(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not check ewallet session state. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_ewallet_session_from_pool_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch ewallet session from pool by id. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_ewallet_session_set_from_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not remove ewallet session set from pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_remove_session_set_item_from_pool(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not remove ewallet session set item from pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink invoice record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set session worker write date. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_recover_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not recover user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink time record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink time record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink transfer record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink conversion record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink contact record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_logout_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not logout user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_login_records(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view login records. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_logout_records(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view logout records. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_invoice_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view invoice record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_conversion_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view conversion record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_transfer_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_transfer_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view transfer record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_contact_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view contact record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_pause_clock_timer(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not pause credit clock timer. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_stop_clock_timer(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not stop credit clock timer. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_start_clock_timer(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not start credit clock timer. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_transfer_credits(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not transfer credits to partner. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_contact_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new contact record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_pay_partner_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not pay partner account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_convert_clock_to_credits(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not convert clock to credits. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_convert_credits_to_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not convert credits to clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_supply_user_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not supply user credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_client_token_not_mapped(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Client token not mapped to any ewallet session tokens. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_esession_pool_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set ewallet session pool entry. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_ctoken_pool_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set client token pool entry. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_stoken_pool_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set session token pool entry. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_lock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not set process lock {}. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_session_manager_lock_found(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'No session manager lock found. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_session_worker_instruction_queue(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not set session worker instruction queue. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_set_session_worker_response_queue(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not set session worker response queue. '
                       'Details: {}'.format(args),
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
                       .format(current_state),
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
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_no_master_action_inspect_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action Inspect target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_recover_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action Recover target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_unlink_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action Unlink target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_edit_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action Edit target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_view_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action View target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_add_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action Add target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_action_add_ctoken_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No master action AddCToken target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_session_manager_worker_action_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker master action controller specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_system_session_manager_worker_action_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker system action controller specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_master_session_manager_worker_controller_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker master controller specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_session_manager_worker_controller_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker client controller specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_acquire_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action acquire target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_next_empty_ewallet_session_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch next empty ewallet session from pool. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_empty_ewallet_sessions_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch empty ewallet sessions from pool. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_check_if_ewallet_session_empty(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not check if ewallet sesion is empty. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_token_label_by_ewallet_session(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch session token label mapped to ewallet session. '
                     'Details: {}.'.format(
                         self.fetch_session_worker_session_limit(), args
                     ),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_session_worker_full(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Session worker full. '
                     'Reached capacity limit of {} ewallet sessions. '
                     'Details: {}.'.format(
                         self.fetch_session_worker_session_limit(), args
                     ),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_ewallet_session_set_from_disk(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove ewallet session set from disk. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_cleanup_ewallet_session_set(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not cleanup ewallet sesssion set. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_set_from_pool_by_ids(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch ewallet session set from pool by ids. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_worker_response_queue(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch session worker multiprocess response queue. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_issue_instruction_set_response(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not issue instruction set response. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_worker_cleanup_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker cleanup target specified. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove EWallet session from pool. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_ewallet_session_from_disk(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove EWallet session from disk. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_required_session_token_map_entry_data_not_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Required session token map entry not found. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_worker_create_date(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set session worker create date. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_session_token_map_entry(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove session token map entry. '
                     'Details: {}.'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_session_worker_token_session_map_entry(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set token session map entry. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_session_id_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet session id found. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_check_if_ewallet_session_exists(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not check if ewallet session exists. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_system_action_interogate_session_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No system action interogate session target specified. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_session_id_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet session id found. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_ewallet_session_from_worker_session_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove ewallet session from session pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_add_ewallet_session_map_entry_to_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not add ewallet session map entry to pool.'
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_sessions_removed_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet sessions removed from pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_worker_action_remove_session_set_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No worker action remove session set specified. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_next_expired_ewallet_session_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch next expired ewallet session from pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_check_if_ewallet_session_expired(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not check if ewallet session expired. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_execute_ewallet_session_command_chain(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not execute ewallet session command chain. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_expired_ewallet_sessions_from_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch expired ewallet sessions from pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch ewallet session pool. '\
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_unlink_invoice_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink invoice target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_worker_state_code(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set session worker state code. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_worker_state_label(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set session worker state label. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_worker_state_timestamp(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set session worker state timestamp. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_resume_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action resume target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_recover_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action recover target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_time_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink time target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_transfer_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink transfer target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_conversion_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink conversion target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_contact_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink contact target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_target_secified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_conversion_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch conversion target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_time_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch time target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_invoice_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch invoice target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_transfer_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch transfer target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_credit_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch credit target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_switch_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action switch target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_new_transfer_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action new transfer target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_new_invoice_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action new invoice target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_new_credit_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action new credit target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_new_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action new target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_credit_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view credit target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_conversion_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view conversion target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_time_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view time target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_transfer_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view transfer target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_view_contact_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action view contact target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_edit_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action edit target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_transfer_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action transfer target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_new_contact_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action new contact target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_convert_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action convert target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_supply_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client action supply target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_client_token(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid client token. Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_session_token(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid session token. Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_worker_client_action_new_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No session worker client action new target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_session_manager_worker_action_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No session worker client action specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_ewallet_session_token_map_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid ewallet session token map entry. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_ewallet_session_pool_map_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid ewallet session pool map entry. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_client_token_pool_map_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid client token pool map entry. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_session_token_pool_map_entry(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid session token pool map entry. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_worker_controller_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No session worker controller specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_lock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid process lock. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_worker_state_interogation_target_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No session worker state target specified for interogation. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_instruction_set_for_worker(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid instruction set for session worker. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_instruction_queue(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid session worker instruction queue. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_response_queue(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid session worker instruction response queue. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_new_session_token_to_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not add new session token to pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_token_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'No client token found. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_add_new_client_token_to_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not add new client token to pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_client_token_by_label(self, client_id, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch client token by label {}. '\
                     'Details: {}'.format(client_id, args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_empty_session_token_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Empty worker session token pool. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_token_by_label(self, session_token, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch session token by label {}. '\
                     'Details: {}'.format(session_token, args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_ewallet_session_from_database(self, ewallet_session):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove EWallet Session record '\
                     'with id {} from database.'.format(ewallet_session.fetch_active_session_id()),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

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

    def error_no_worker_action_new_target_specified(self):
        log.error('No worker action new target specified.')
        return False

    def error_no_session_manager_controller_specified(self):
        log.error('No session manager worker controller specified.')
        return False

    def error_invalid_session_worker_state_label(self):
        log.error('Invalid session worker state label.')
        return False

    # DEBUG

    def debug_cleaning_response_queue(self, lock_value, garbage):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Cleaning response queue. Garbage {}.'.format(
                lock_value, os.getpid(), garbage
            )
        )

    def debug_response_queue_cleaned(self, lock_value, response_queue):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Successfully cleaned worker response queue {}.'.format(
                lock_value, os.getpid(), response_queue
            )
        )

    def debug_waiting_for_lock_from_session_manager(self, lock_value):
        log.debug(
            'Worker unlocked - {} - PID: {} - '
            'Waiting for lock from session manager.'.format(
                lock_value, os.getpid()
            )
        )

    def debug_executing_instructions(self, lock_value, instruction_set):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Executing instruction {}'.format(
                lock_value, os.getpid(), instruction_set
            )
        )

    def debug_execution_complete_with_response(self, lock_value, response):
        log.debug(
            'Worker unlocked - {} - PID: {} - '
            'Execution complete. Responded with {}.'.format(
                lock_value, os.getpid(), response
            )
        )

    def debug_worker_unlocked(self, lock_value):
        log.debug(
            'Worker unlocked - {} - PID: {} -'.format(lock_value, os.getpid())
        )
    def debug_worker_locked(self, lock_value):
        log.debug(
            'Worker locked - {} - PID: {} -'.format(lock_value, os.getpid())
        )

    def debug_fetching_instruction(self, lock_value):
        log.debug(
            'Worker locked - {} - PID: {} - Fetching instruction.'.format(
                lock_value, os.getpid()
            )
        )

    def debug_validating_instruction(self, lock_value, instruction):
        log.debug(
            'Worker locked - {} - PID: {} - Validating instruction {}.'
            .format(lock_value, os.getpid(), instruction)
        )


    # CODE DUMP

#   def system_event_controller(self):
#       log.debug('TODO - No events supported.')
#   def client_event_controller(self, **kwargs):
#       log.debug('TODO - No events supported.')
#   def master_event_controller(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')

#           'reference': self.clean_session_worker_reference,
#           'create_date': self.clean_session_worker_create_date,
#           'write_date': self.clean_session_worker_write_date,
#           'session_worker_state_code': self.clean_session_worker_state_code,
#           'session_worker_state_label': self.clean_session_worker_state_label,
#           'session_worker_state_timestamp': self.clean_session_worker_state_timestamp,
#           'instruction_set_recv': self.clean_session_worker_instruction_set_recv,
#           'instruction_set_resp': self.clean_session_worker_instruction_set_resp,
#           'lock': self.clean_session_worker_lock,


