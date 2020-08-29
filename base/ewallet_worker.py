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
    [ NOTE ]: Worker states [(0, vacant), (1, in_use), (2, full)]
    '''
    id = int()
    reference = str()
    create_date = None
    write_date = None
    session_worker_state_code = int() # (0 | 1 | 2)
    session_worker_state_label = str() # (vacant | in_use | full)
    session_worker_state_timestamp = None
    session_pool = dict() # {id: <EWallet>}
    ctoken_pool = list() # [<CToken.label>]
    stoken_pool = list() # [<SToken.label>]
    token_session_map = dict() # {<CToken.label>: {<SToken.label>: <EWallet Session>}}
    instruction_set_recv = None # <multiprocessing.Queue(1)>
    instruction_set_resp = None # <multiprocessing.Queue(1)>
    lock = None # <multiprocessing.Value('i', 0)>

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now()
        self.id = kwargs.get('id') or int()
        self.reference = kwargs.get('reference') or str()
        self.create_date = now
        self.write_date = now
        self.session_worker_state_code = kwargs.get('state_code') or 0
        self.session_worker_state_label = kwargs.get('state_label') or 'vacant'
        self.session_worker_state_timestamp = now
        self.instruction_set_recv = kwargs.get('instruction_set_recv') or Queue(1)
        self.instruction_set_resp = kwargs.get('instruction_set_resp') or Queue(1)
        self.sigterm = kwargs.get('sigterm') or 'terminate_worker'
        self.lock = kwargs.get('lock') or Value('i', 0)

    # FETCHERS

    # TODO
    def fetch_default_ewallet_session_validity_interval_in_minutes(self, **kwargs):
        log.debug('TODO - Fetch value from config file')
        return 60

    # TODO
    def fetch_default_ewallet_session_validity_interval_in_hours(self, **kwargs):
        log.debug('TODO - Fetch value from config file')
        return 1

    # TODO
    def fetch_default_ewallet_session_validity_interval_in_days(self, **kwargs):
        log.debug('TODO - Fetch value from config file')
        return 0.2

    # TODO - Remove - DEPRECATED
    def fetch_ewallet_session_from_pool_by_id(self, ewallet_session_id):
        log.debug('DEPRECATED')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        for ewallet_session in session_pool:
            if ewallet_session.fetch_active_session_id() == ewallet_session_id:
                return ewallet_session
        return self.warning_could_not_fetch_ewallet_session_from_pool_by_id(
            ewallet_session_id
        )

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

    def fetch_session_worker_ewallet_session_pool(self):
        log.debug('')
        return self.session_pool

    def fetch_session_worker_ctoken_pool(self):
        log.debug('')
        return self.ctoken_pool

    def fetch_session_worker_stoken_pool(self):
        log.debug('')
        return self.stoken_pool

    def fetch_ewallet_session_expiration_date(self):
        log.debug('')
        validity_hours = self.fetch_default_ewallet_session_validity_interval(
            number_of='hours'
        )
        now = datetime.datetime.now()
        return now + datetime.timedelta(hours=validity_hours)

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

    def fetch_ctoken_by_label(self, client_id):
        if not self.rtoken_pool:
            self.error_empty_client_token_pool(client_id, self.ctoken_pool)
            return False
        ctoken = [
            item for item in self.ctoken_pool if item.label == client_id
        ]
        return False if not ctoken else ctoken[0]

    def fetch_stoken_by_label(self, session_token):
        log.debug('')
        if not self.stoken_pool:
            self.error_empty_session_token_pool(session_token, self.stoken_pool)
            return False
        stoken = [
            item for item in self.stoken_pool if item.label == session_token
        ]
        return False if not stoken else stoken[0]

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

    # TODO
    def set_session_pool_add_record(self, record):
        pass
    def set_session_pool_remove_record(self, record):
        pass
    def set_session_pool_clear_records(self):
        pass
    def set_session_pool_update_records(self):
        pass

    def set_esession_pool(self, map_entry):
        log.debug('')
        try:
            self.session_pool.update(map_entry)
        except Exception as e:
            return self.warning_could_not_set_esession_pool_entry(
                map_entry, self.session_pool
            )
        return True

    def set_ctoken_pool(self, map_entry):
        log.debug('')
        try:
            self.ctoken_pool.update(map_entry)
        except Exception as e:
            return self.warning_could_not_set_ctoken_pool_entry(
                map_entry, self.ctoken_pool
            )
        return True

    def set_stoken_pool(self, map_entry):
        log.debug('')
        try:
            self.stoken_pool.update(map_entry)
        except Exception as e:
            return self.warning_could_not_set_stoken_pool_entry(
                map_entry, self.stoken_pool
            )
        return True

    def set_session_worker_token_session_map_entry(self, map_entry):
        log.debug('')
        if not isinstance(map_entry, dict):
            return self.error_invalid_session_worker_token_session_map_entry(map_entry)
        try:
            self.token_session_map.update(map_entry)
        except:
            return self.error_could_not_set_session_worker_token_session_map_entry(map_entry)
        return True

    def set_lock(self, lock):
        log.debug('')
        if not isinstance(lock, object):
            return self.error_invalid_lock(lock)
        try:
            self.lock = lock
        except Exception as e:
            return self.warning_could_not_set_lock(lock)
        return True

    def set_instruction_queue(self, instruction_queue):
        log.debug('')
        if not isinstance(instruction_queue, object):
            return self.error_invalid_instruction_queue(instruction_queue)
        try:
            self.instruction_set_recv = instruction_queue
        except Exception as e:
            return self.warning_could_not_set_session_worker_instruction_queue(
                instruction_queue
            )
        return True

    def set_response_queue(self, response_queue):
        log.debug('')
        if not isinstance(response_queue, object):
            return self.error_invalid_response_queue(response_queue)
        try:
            self.instruction_set_resp = response_queue
        except Exception as e:
            return self.warning_could_not_set_session_worker_response_queue(
                response_queue
            )
        return True

#   @pysnooper.snoop()
    def set_new_session_token_to_pool(self, session_token):
        log.debug('')
        try:
            self.stoken_pool.append(session_token)
        except:
            return self.error_could_not_set_new_session_token_to_pool(session_token)
        return True

    def set_new_client_token_to_pool(self, client_token):
        log.debug('')
        try:
            self.ctoken_pool.append(client_token)
        except:
            return self.error_could_not_add_new_client_token_to_pool(client_token)
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

    # UPDATERS

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

    def update_ewallet_session_pool(self, map_entry):
        log.debug('')
        if not map_entry or not isinstance(map_entry, dict):
            return self.error_invalid_ewallet_session_pool_map_entry(map_entry)
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        for k, v in map_entry.items():
            if k in session_pool:
                session_pool[k].update(v)
                continue
            set_entry = self.set_esession_pool(map_entry)
            if not set_entry or isinstance(set_entry, dict) and \
                    set_entry.get('failed'):
                return set_entry
            break
        return True

    def update_client_token_pool(self, client_id):
        log.debug('')
        try:
            self.ctoken_pool.append(client_id)
        except Exception as e:
            return self.warning_could_not_set_ctoken_pool_entry(
                client_id, self.ctoken_pool
            )
        return True

    def update_session_token_pool(self, session_token):
        log.debug('')
        try:
            self.stoken_pool.append(session_token)
        except Exception as e:
            return self.warning_could_not_set_stoken_pool_entry(
                session_token, self.stoken_pool
            )
        return True

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

    # CHECKERS

    # TODO - Deprecated - remove
    def check_ewallet_session_in_worker_session_pool_by_id(self, ewallet_session_id):
        log.debug('TODO - DEPRECATED')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        for ewallet_session in session_pool:
            if ewallet_session.fetch_active_session_id() == ewallet_session_id:
                return True
        return False

    # CLEANERS

    def clean_response_queue(self, response_queue):
        log.debug('')
        if not response_queue.empty():
            while not response_queue.empty():
                garbage = response_queue.get()
                self.debug_cleaning_response_queue(self.lock.value, garbage)
        self.debug_response_queue_cleaned(self.lock.value, response_queue)
        return True

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
                time.sleep(1)
                continue
        self.debug_worker_locked(lock.value)
        return True

    def ensure_worker_unlocked(self, lock):
        log.debug('')
        if lock.value:
            while lock.value:
                time.sleep(1)
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

    # TODO - Refactor - Efficiency deficit
#   @pysnooper.snoop()
    def search_ewallet_session(self, session_token):
        log.debug('')
        token_map = self.fetch_session_token_map()
        if not token_map:
            return self.warning_empty_session_token_map()
        stoken = self.fetch_stoken_by_label(session_token)
        if not stoken or isinstance(stoken, dict) and \
                stoken.get('failed'):
            return self.error_could_not_fetch_session_token_by_label(session_token, stoken)
        for client_id in token_map:
            if token_map[client_id]['token'] == stoken:
                return token_map[client_id]['session']
        return self.warning_no_ewallet_session_found_by_session_token(session_token)

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
        return EWallet(
            name=kwargs.get('reference'), session=orm_session,
            expiration_date=kwargs.get('expiration_date')
        )

    # CREATORS

#   @pysnooper.snoop()
    def create_new_ewallet_session(self, **kwargs):
        log.debug('')
        orm_session = res_utils.session_factory()
        ewallet_session = self.spawn_ewallet_session(orm_session, **kwargs)
        orm_session.add(ewallet_session)
        orm_session.commit()
        return ewallet_session

    # ACTIONS

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
            ewallet_session, kwargs, stop_timer
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
            ewallet_session, kwargs, resume_timer
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
            ewallet_session, kwargs, pause_timer
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
            ewallet_session, kwargs, start_timer
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
            ewallet_session, kwargs
        ) if not account_login else account_login
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

    def action_interogate_session_pool(self, **kwargs):
        log.debug('')
        session_pool = self.fetch_session_worker_ewallet_session_pool()
        if not session_pool or isinstance(session_pool, dict) and \
                session_pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_pool(kwargs)
        # Formulate instruction response
        response = {
            'failed': False,
            'session_pool': list(session_pool.keys()),
        }
        # Respond to session manager
        self.send_instruction_response(response)
        return response

#   @pysnooper.snoop()
    def action_add_new_session(self, **kwargs):
        log.debug('')
        # Create new ewallet session
        ewallet_session = self.create_new_ewallet_session(
            expiration_date=self.fetch_ewallet_session_expiration_date()
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

    # TODO - Refactor
#   @pysnooper.snoop()
    def action_add_client_id_session_token_map_entry(self, **kwargs):
        '''
        [ NOTE   ]: Maps an existing client_id with a new session token and object.
        [ INPUT  ]: client_id=<id>, session_token=<token>, session=<session-obj>
        [ RETURN ]: {client_id: {'token': session_token, 'session': session}}
        '''
        log.debug('TODO - Refactor')
        if None in [kwargs.get('client_token'), kwargs.get('session_token'),
                kwargs.get('session')]:
            return self.error_required_session_token_map_entry_data_not_found()
        map_entry = {kwargs['client_token']: {
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
        return self.warning_could_not_set_session_worker_ewallet_session_token_map_entry(kwargs) \
            if not set_entry or isinstance(set_entry, dict) and \
            set_entry.get('failed') else instruction_set_response

    def action_interogate_worker_state_code(self, **kwargs):
        log.debug('')
        state_code = self.fetch_session_worker_state_code()
        instruction_set_response = {
            'failed': False,
            'state': state_code,
        }
        response = self.send_instruction_response(instruction_set_response)
        return response if not response or isinstance(response, dict) and \
            response.get('failed') else instruction_set_response

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

    # ACTION HANDLERS

    def handle_client_action_unlink_account(self, **kwargs):
        log.debug('')
        return  self.action_unlink_user_account(**kwargs)

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

    def handle_system_action_interogate_session_pool(self, **kwargs):
        log.debug('')
        return self.action_interogate_session_pool(**kwargs)

    def handle_client_action_resume_clock_timer(self, **kwargs):
        log.debug('')
        return self.action_resume_clock_timer(**kwargs)

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

    # JUMPTABLE HANDLERS

    def handle_client_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_client_action_unlink_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_unlink_account,
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

    def handle_system_action_interogate_state(self, **kwargs):
        log.debug('')
        if not kwargs.get('state'):
            return self.error_no_worker_state_interogation_target_specified(kwargs)
        handlers = {
            'code': self.handle_system_action_interogate_state_code,
        }
        return handlers[kwargs['state']](**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_worker_action_interogate_target_specified(kwargs)
        handlers = {
            'session_pool': self.handle_system_action_interogate_session_pool,
            'state': self.handle_system_action_interogate_state,
        }
        return handlers[kwargs['interogate']](**kwargs)

    def handle_system_action_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('remove'):
            return self.error_no_worker_action_remove_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_remove_session,
            'session_map': self.handle_system_action_remove_session_map,
        }
        return handlers[kwargs['remove']](**kwargs)

    def handle_system_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_worker_action_new_target_specified()
        handlers = {
            'session': self.action_add_new_session,
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

    # TODO
    def system_event_controller(self):
        log.debug('TODO - No events supported.')
    def client_event_controller(self, **kwargs):
        log.debug('TODO - No events supported.')

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
        }
        return handlers[kwargs['action']](**kwargs)

    def client_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_worker_controller_specified()
        handlers = {
            'action': self.client_action_controller,
            'event': self.client_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

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
            return self.error_no_session_worker_controller_specified(kwargs)
        handlers = {
            'system': self.system_controller,
            'client': self.client_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS

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

    # DEBUG

    def debug_cleaning_response_queue(self, lock_value, garbage):
        log.debug(
            'Worker locked {} - PID: {} - '
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

    # TESTS

    # CODE DUMP

