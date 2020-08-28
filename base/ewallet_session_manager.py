import time
import os
import datetime
import logging
import pysnooper
import ast
import multiprocessing as mp

from multiprocessing import Process, Queue, Lock, Value

from .ewallet import EWallet
from .config import Config
from .res_utils import ResUtils
from .ewallet_worker import EWalletWorker
from .socket_handler import EWalletSocketHandler
from .client_id import ClientID
from .session_token import SessionToken

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletSessionManager():

    config = None
    res_utils = None
    socket_handler = None
    worker_pool = dict() # {<worker id>: {process: <Proc>, instruction: <Queue>, response: <Queue>, lock: <Value type-bool>}}
    client_pool = dict() # {<label>: <ClientToken>}
    stoken_pool = dict() # {<label>: <SessionToken>}
    primary_session = None

    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config') or config
        self.res_utils = kwargs.get('res_utils') or res_utils
        self.socket_handler = kwargs.get('socket_handler') or None # self.open_ewallet_session_manager_sockets()
        self.worker_pool = kwargs.get('worker_pool') or {}
        if not self.worker_pool:
            self.session_manager_controller(
                controller='system', ctype='action', action='new', new='worker'
            )
        self.client_pool = kwargs.get('client_pool') or {}
        self.stoken_pool = kwargs.get('stoken_pool') or {}
        self.primary_session = kwargs.get('primary_session') or \
            self.create_new_ewallet_session(
                reference='S:CorePrimary',
                expiration_date=None,
            )
        check_score = self.check_system_core_account_exists()
        if not check_score:
            res_utils.create_system_user(self.primary_session)

    # FETCHERS

    def fetch_client_session_tokens(self, ctoken_label, stoken_label, **kwargs):
        log.debug('')
        # Fetch client token
        ctoken = kwargs.get('ctoken') or \
            self.fetch_client_token_by_label(ctoken_label)
        if not ctoken or isinstance(ctoken, dict) and \
                ctoken.get('failed'):
            return self.error_could_not_fetch_client_token_by_label(
                ctoken_label, ctoken, kwargs
            )
        # Fetch session token
        stoken = kwargs.get('stoken') or \
            self.fetch_session_token_by_label(stoken_label)
        if not stoken or isinstance(stoken, dict) and \
                stoken.get('failed'):
            return self.error_could_not_fetch_session_token_by_label(
                stoken_label, stoken, kwargs
            )
        return {
            'failed': False,
            'ctoken': ctoken,
            'stoken': stoken,
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_next_available_worker(self):
        log.debug('')
        worker_pool = self.fetch_worker_pool()
        if not worker_pool or isinstance(worker_pool, dict) and \
                worker_pool.get('failed'):
            return worker_pool
        for worker_id in worker_pool:
            check_available = self.check_worker_is_available(
                worker_id, worker_pool=worker_pool
            )
            if not check_available or isinstance(check_available, dict) and \
                    check_available.get('failed'):
                continue
            return {
                'failed': False,
                'worker': worker_id,
                'worker_data': worker_pool[worker_id],
            }
        return self.warning_no_available_session_worker_found(worker_pool)

    def fetch_worker_pool_entry_by_id(self, worker_id):
        log.debug('')
        if not isinstance(worker_id, int):
            return self.error_invalid_worker_id(worker_id)
        wp_map = self.fetch_worker_pool()
        return wp_map.get(worker_id) or {}

#   @pysnooper.snoop()
    def fetch_available_worker_id(self, **kwargs):
        log.debug('')
        if kwargs.get('client_id'):
            worker_id = self.fetch_worker_identifier_by_client_id(kwargs['client_id'])
            if not worker_id or isinstance(worker_id, dict) and \
                    worker_id.get('failed'):
                worker = self.fetch_next_available_worker()
                if not worker:
                    worker = self.handle_system_action_new_worker()
                worker_id = None if not worker or isinstance(worker, dict) and \
                    worker.get('failed') else worker.get('worker') or \
                    list(worker.keys())[0]
            return worker_id
        worker = self.fetch_next_available_worker()
        if not worker:
            worker = self.handle_system_action_new_worker()
        worker_id = None if not worker or isinstance(worker, dict) and \
            worker.get('failed') else worker.get('worker') or \
            list(worker.keys())[0]
        return worker_id

    def fetch_worker_identifier_by_client_id(self, client_id):
        log.debug('')
        client_pool = self.fetch_client_pool()
        if client_id not in client_pool:
            return self.error_invalid_client_id(client_id, client_pool)
        ctoken = client_pool[client_id]
        if not ctoken:
            return self.warning_no_ctoken_found(ctoken, client_id,  client_pool)
        stoken = ctoken.fetch_stoken()
        if not stoken or isinstance(stoken, dict) and \
                stoken.get('failed'):
            return self.warning_no_stoken_found(client_id, client_pool, ctoken, stoken)
        worker_id = stoken.fetch_worker_id()
        return self.warning_no_worker_id_found(
            client_id, client_pool, ctoken, stoken, worker_id
        ) if not worker_id or isinstance(worker_id, dict) and \
            worker_id.get('failed') else worker_id

    def fetch_client_pool(self):
        log.debug('')
        return self.client_pool

    def fetch_client_token_by_label(self, client_id):
        log.debug('')
        client_pool = self.fetch_client_pool()
        if client_id not in client_pool:
            return self.error_invalid_client_id(client_id, client_pool)
        return client_pool[client_id]

    def fetch_worker_pool(self):
        log.debug('')
        return self.worker_pool

    def fetch_default_session_worker_termination_signal(self):
        log.debug('')
        if not self.config:
            return self.error_no_config_handler_found(self.config)
        return self.config.worker_config.get('worker_sigterm')

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_ewallet_session_worker_ids(self):
        log.debug('')
        worker_set = self.fetch_ewallet_session_manager_worker_pool()
        if not worker_set or isinstance(worker_set, dict) and \
                worker_set.get('failed'):
            return worker_set
        return list(worker_set.keys())

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_ewallet_session_manager_worker_pool(self):
        log.debug('')
        return self.error_ewallet_session_manager_worker_pool_empty(
            self.worker_pool
        ) if not self.worker_pool else self.worker_pool

    def fetch_ewallet_session_from_worker(self, session_manager_worker, instruction_set):
        log.debug('')
        if not session_manager_worker or isinstance(session_manager_worker, dict) and \
                session_manager_worker.get('failed'):
            return self.error_no_session_manager_worker_found(instruction_set)
        ewallet_session = session_manager_worker.main_controller(
            controller='system', ctype='action', action='search', search='session',
            **instruction_set
        )
        return ewallet_session

    def fetch_default_session_token_validity_interval_in_minutes(self):
        log.debug('')
        if not self.config:
            return self.error_no_config_handler_found(self.config)
        session_token_validity = int(
            self.config.client_config['client_id_validity']
        )
        return session_token_validity

    def fetch_session_token_by_label(self, session_token):
        log.debug('')
        stoken = [
            self.stoken_pool[item] for item in self.stoken_pool if item == session_token
        ]
        if len(stoken) > 1:
            self.warning_multiple_session_tokens_found_by_label(
                session_token, stoken
            )
        return False if not stoken else stoken[0]

    def fetch_default_client_id_validity_interval_in_minutes(self):
        log.debug('')
        if not self.config:
            return self.error_no_config_handler_found(self.config)
        client_id_token_validity = int(self.config.client_config['client_id_validity'])
        return client_id_token_validity

    def fetch_primary_ewallet_session(self):
        log.debug('')
        return self.primary_session

#   @pysnooper.snoop()
    def fetch_ewallet_session_assigned_worker(self, ewallet_session):
        log.debug('')
        worker_pool = self.worker_pool
        if not worker_pool:
            return self.error_worker_pool_empty()
        ewallet_session_id = ewallet_session.fetch_active_session_id()
        worker_set = []
        for worker in worker_pool:
            session_pool_ids = [
                item.fetch_active_session_id() for item in
                worker.fetch_session_worker_ewallet_session_pool()
            ]
            if ewallet_session_id in session_pool_ids:
                worker_set.append(worker)
        return self.error_no_worker_found_assigned_to_session(ewallet_session)\
            if not worker_set else worker_set[0]

#   @pysnooper.snoop()
    def fetch_ewallet_sessions_past_expiration_date(self, **kwargs):
        log.debug('')
        worker_pool = self.fetch_ewallet_session_manager_worker_pool()
        if not worker_pool:
            return self.error_could_not_fetch_session_worker_pool(kwargs)
        now, expired_sessions = datetime.datetime.now(), []
        for worker in worker_pool:
            try:
                worker_interogation = worker.main_controller(
                    controller='system', ctype='action', action='interogate',
                    interogate='session_pool',
                )
                if not worker_interogation or isinstance(worker_interogation, dict) and \
                        worker_interogation.get('failed'):
                    self.warning_could_not_interogate_worker_session_pool(worker)
                    continue
                expired_sessions += [
                    session for session in worker_interogation['session_pool'] \
                    if now >= session.fetch_active_session_expiration_date()
                ]
            except:
                self.warning_could_not_fetch_expired_ewallet_sessions_from_worker(worker)
                continue
            log.info(
                'Successfully fetched expired ewallet sessions from worker {}.'\
                .format(worker),
            )
        return self.warning_no_expired_ewallet_sessions_found(kwargs) \
            if not expired_sessions else expired_sessions

    # TODO - Refactor
#   @pysnooper.snoop()
    def fetch_ewallet_session_by_id(self, ewallet_session_id):
        log.debug('')
        if not ewallet_session_id or not isinstance(ewallet_session_id, int):
            return self.error_invalid_ewallet_session_id(ewallet_session_id)
        try:
            orm_session = self.res_utils.session_factory()
            ewallet_session = list(orm_session.query(
                EWallet
            ).filter_by(id=ewallet_session_id))
            set_orm = None if not ewallet_session else \
                ewallet_session[0].set_orm_session(orm_session)
        except:
            return self.error_could_not_fetch_ewallet_session_by_id(ewallet_session_id)
        return self.warning_no_ewallet_session_found_by_id(ewallet_session_id) \
            if not ewallet_session else ewallet_session[0]

    # TODO - Refactor
    def fetch_ewallet_session_for_system_action_using_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_session_id_found(kwargs)
        ewallet_session = self.fetch_ewallet_session_by_id(kwargs['session_id'])
        return self.warning_no_ewallet_session_found_by_id(kwargs) if not \
            ewallet_session else ewallet_session

    # TODO - Refactor
#   @pysnooper.snoop()
    def fetch_ewallet_session_for_client_action_using_instruction_set(self, instruction_set):
        log.debug('')
        if not instruction_set.get('client_id'):
            return self.error_no_client_id_found(instruction_set)
        session_manager_worker = self.fetch_client_id_mapped_session_worker(
            instruction_set['client_id']
        )
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action'
        )
        ewallet_session = self.fetch_ewallet_session_from_worker(
            session_manager_worker, sanitized_instruction_set
        )
        if ewallet_session and isinstance(ewallet_session, dict) and \
                not ewallet_session.get('failed'):
            ewallet_session = self.fetch_ewallet_session_by_id(
                ewallet_session['ewallet_session'].fetch_active_session_id()
            )
        value_set = {
            'sanitized_instruction_set': sanitized_instruction_set,
            'ewallet_session': ewallet_session,
        }
        return False if False in value_set.keys() else value_set

    def fetch_first_available_worker(self):
        log.debug('')
        pool = self.fetch_ewallet_session_manager_worker_pool()
        if not pool or isinstance(pool, dict) and pool.get('failed'):
            return self.error_could_not_fetch_ewallet_session_manager_worker_pool()
        for item in pool:
            if item.session_worker_state_code in [0, 1]:
                return item
        return self.warning_ewallet_session_manager_worker_pool_empty()

    def fetch_ewallet_session_manager_socket_handler(self):
        log.debug('')
        return self.socket_handler

    def fetch_session_token_default_prefix(self):
        log.debug('')
        return self.config.client_config.get('session_token_prefix')

    def fetch_session_token_default_length(self):
        log.debug('')
        return int(self.config.client_config.get('session_token_length'))

    def fetch_socket_handler_default_address(self):
        log.debug('')
        return self.config.system_config.get('socket_handler_address')

    def fetch_client_id_default_length(self):
        log.debug('')
        return int(self.config.client_config.get('client_id_length'))

    def fetch_client_id_default_prefix(self):
        log.debug('')
        return self.config.client_config.get('client_id_prefix')

    def fetch_default_ewallet_command_chain_reply_port(self):
        log.debug('')
        return int(self.config.system_config.get('esm_instruction_port'))

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_default_ewallet_command_chain_instruction_port(self):
        log.debug('')
        return int(self.config.system_config.get('esm_response_port'))

    # TODO
    def fetch_from_worker_pool(self):
        pass
    def fetch_from_client_pool(self):
        pass
    def fetch_from_client_session_map(self):
        pass
    def fetch_ewallet_worker_sessions(self, ewallet_worker):
        pass
    def fetch_from_ewallet_worker_session(self):
        pass

    # SETTERS

    def set_new_session_token_to_pool(self, session_token_map):
        log.debug('')
        try:
            self.stoken_pool.update(session_token_map)
#           self.stoken_pool.append(session_token)
        except Exception as e:
            return self.error_could_not_set_stoken_pool(session_token_map, e)
        return True

#   @pysnooper.snoop()
    def set_new_client_id_to_pool(self, client_id_map):
        log.debug('')
        try:
            self.client_pool.update(client_id_map)
#           self.client_pool.append(client_id)
        except Exception as e:
            return self.error_could_not_set_client_pool(client_id_map, e)
        return True

#   @pysnooper.snoop()
    def set_worker_to_pool(self, worker_pool_record):
        log.debug('')
        try:
            self.worker_pool.update(worker_pool_record)
        except Exception as e:
            return self.error_could_not_set_worker_pool(worker_pool_record, e)
        return True

    def unset_socket_handler(self):
        '''
        [ NOTE   ]: Overrides socket_handler attribute with a None value.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if self.socket_handler in (None, False):
            return False
        try:
            self.socket_handler = None
        except Exception as e:
            return self.error_could_not_unset_socket_handler(
                self.socket_handler, e
            )
        return True

    def set_socket_handler(self, socket_handler):
        '''
        [ NOTE   ]: Overrides socket_handler attribute with new EWalletSocketHandler object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.socket_handler = socket_handler
        except Exception as e:
            return self.error_could_not_set_socket_handler(socket_handler, e)
        return True

    def set_worker_pool(self, worker_pool, **kwargs):
        '''
        [ NOTE   ]: Overrides entire worker pool.
        [ INPUT  ]: [worker1, worker2, ...]
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.worker_pool = worker_pool
        except Exception as e:
            return self.error_could_not_set_worker_pool(worker_pool, )
        return True

    def set_client_pool(self, client_pool, **kwargs):
        '''
        [ NOTE   ]: Overrides entire client pool.
        [ INPUT  ]: [user_id1, user_id2, ...]
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.client_pool = client_pool
        except Exception as e:
            return self.error_coult_not_set_client_pool(client_pool, e)
        return True

    # TODO - Search ref
#   def set_client_worker_session_map(self, cw_map):
#       '''
#       [ NOTE   ]: Overrides entire client/worker map.
#       [ INPUT  ]: {user_id: worker, user_id: worker, ...}
#       [ RETURN ]: (True | False)
#       '''
#       log.debug('')
#       try:
#           self.client_worker_map = cw_map
#       except Exception as e:
#           return self.error_could_not_set_client_worker_map(cw_map, e)
#       return True

    def set_to_worker_pool(self, worker, **kwargs):
        '''
        [ NOTE   ]: Adds new work to worker pool stack.
        [ INPUT  ]: EwalletWorker object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.worker_pool.append(worker)
        except Exception as e:
            return self.error_could_not_update_worker_pool(worker, e)
        return True

    def set_to_client_pool(self, client, **kwargs):
        '''
        [ NOTE   ]: Adds new client user id to client pool stack.
        [ INPUT  ]: User ID
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.client_pool.append(client)
        except Exception as e:
            return self.error_could_not_update_client_pool(client, e)
        return True

    # TODO - Search ref
    def set_to_client_worker_session_map(self, user_id, session_token, worker):
        '''
        [ NOTE   ]: Adds new entry to client/worker map including entry in workers user_id/session token map.
        [ INPUT  ]: User ID, Session Token, EwalletWorker object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
#       values = {
#           'session_manager': {user_id: worker},
#           'worker': {user_id: session_token},
#       }
#       try:
#           self.client_worker_map.update(values['session_manager'])
#           worker.token_session_map.update(values['worker'])
#       except Exception as e:
#           return self.error_could_not_update_client_worker_session_map(
#               values, e
#           )
#       return True

    # UPDATERS

    def update_worker_pool(self, worker_pool):
        '''
        [ NOTE   ]: Overrides Session Manager Worker Pool and checks for type errors.
        [ INPUT  ]: [worker1, worker2, ...]
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not worker_pool:
            return self.error_no_worker_pool_found()
        return self.error_invalid_worker_pool(worker_pool) \
            if not isinstance(worker_pool, list) else \
            self.set_worker_pool(worker_pool)

    def update_client_pool(self, client_pool):
        '''
        [ NOTE   ]: Overrides Session Manager Client Pool and checks for type errors.
        [ INPUT  ]: [user_id1, user_id2, ...]
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not client_pool:
            return self.error_client_pool_not_found()
        return self.error_invalid_client_pool(client_pool) \
            if not isinstance(client_pool, list) else \
            self.set_client_pool(client_pool)

    def update_client_worker_map(self, cw_map):
        '''
        [ NOTE   ]: Overrides Session Manager Client Worker map and checks for type errors.
        [ INPUT  ]: {user_id: session_token, ...}
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not cw_map:
            return self.error_client_worker_map_not_found()
        return self.error_invalid_client_worker_map(cw_map) \
            if not isinstance(cw_map, dict) else \
            self.set_client_worker_session_map(cw_map)

    # CHECKERS

    def check_worker_is_available(self, worker_id, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        if not worker_pool or isinstance(worker_pool, dict) and \
                worker_pool.get('failed'):
            return worker_pool
        elif worker_id not in worker_pool:
            return self.warning_worker_not_found_in_pool_by_id(
                worker_id, worker_pool, kwargs
            )
        instruction_set = {
            'controller': 'system', 'ctype': 'action',
            'action': 'interogate', 'interogate': 'state', 'state': 'code',
        }
        if worker_pool[worker_id]['lock'].value:
            self.debug_waiting_for_unlock_to_delegate_instruction_set(
                worker_pool[worker_id]['lock'].value, instruction_set
            )
            self.ensure_worker_unlocked(worker_pool[worker_id]['lock'])
        worker_pool[worker_id]['lock'].value = 1
        self.debug_delegating_instruction_set(
            worker_pool[worker_id]['lock'].value, instruction_set
        )
        self.send_session_worker_instruction(worker_id, instruction_set)
        while worker_pool[worker_id]['lock'].value:
            self.debug_waiting_for_worker_unlock_to_read_response(
                worker_pool[worker_id]['lock'].value
            )
            time.sleep(1)
            continue
        response = self.read_session_worker_response(worker_id)
        self.debug_received_instruction_set_response(
            worker_pool[worker_id]['lock'].value, response
        )
        if not response or isinstance(response, dict) and \
                response.get('failed'):
            return False
        elif response.get('state') in [0, 1]:
            return True

#   @pysnooper.snoop('logs/ewallet.log')
    def check_system_core_account_exists(self):
        log.debug('')
        ewallet_session = self.fetch_primary_ewallet_session()
        system_core_account = ewallet_session.fetch_system_core_user_account()
        return False if not system_core_account else True

    def check_client_id_timestamp(self, timestamp):
        log.debug('')
        now = datetime.datetime.now()
        datetime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        return False if datetime_obj > now else True

    def check_client_id_prefix(self, prefix):
        log.debug('')
        default = self.fetch_client_id_default_prefix()
        return False if prefix != default else True

    def check_client_id_code(self, code):
        log.debug('')
        default_length = self.fetch_client_id_default_length()
        return False if len(code) != default_length else True

    def check_command_chain_client_id(self, client_id):
        log.debug('')
        client_id_segmented = client_id.split(':')
        checks = {
            'timestamp': self.check_client_id_timestamp(client_id_segmented[2]),
            'prefix': self.check_client_id_prefix(client_id_segmented[0]),
            'code': self.check_client_id_code(client_id_segmented[1]),
        }
        return False if False in checks.values() else True

    def check_command_chain_session_token(self):
        pass
    def check_command_chain_instruction_set(self):
        pass

    # SPAWNERS

    # TODO - EWallet session spawning should happen on the worker side.
    def spawn_ewallet_session(self, orm_session, **kwargs):
        log.debug('TODO')
        return EWallet(
            name=kwargs.get('reference'), session=orm_session,
            expiration_date=kwargs.get('expiration_date')
        )

#   @pysnooper.snoop('logs/ewallet.log')
    def spawn_ewallet_session_worker(self, *args, **kwargs):
        log.debug('')
        existing_worker_ids = self.fetch_ewallet_session_worker_ids()
        if not existing_worker_ids or isinstance(existing_worker_ids, dict) and\
                existing_worker_ids.get('failed'):
            existing_worker_ids = int()
        worker_id = self.generate_id_for_entity_set(existing_worker_ids)
        if not worker_id or isinstance(worker_id, dict) and\
                worker_id.get('failed'):
            return self.error_could_not_generate_session_worker_identifier(
                args, kwargs, worker_id, existing_worker_ids
            )
        termination_signal = self.fetch_default_session_worker_termination_signal()
        return EWalletWorker(
            id=worker_id, sigterm=termination_signal,
            *args, **kwargs
        )

    def spawn_session_token(self, *args, **kwargs):
        log.debug('')
        return SessionToken(*args, **kwargs)

    def spawn_client_id(self, *args, **kwargs):
        log.debug('')
        return ClientID(*args, **kwargs)

    def spawn_ewallet_session_manager_socket_handler(self, in_port, out_port):
        '''
        [ NOTE   ]: Perform port number validity checks and creates a EWallet Socket Handler object.
        [ INPUT  ]: In port number, Out port number
        [ RETURN ]: EWalletSocketHandler object.
        '''
        log.debug('')
        if not isinstance(in_port, int) or not isinstance(out_port, int):
            return self.error_invalid_socket_port(in_port, out_port)
        return EWalletSocketHandler(
            session_manager=self, in_port=in_port, out_port=out_port,
            host=self.fetch_socket_handler_default_address()
        )

    # SCRAPERS

#   @pysnooper.snoop()
    def scrape_ewallet_session(self, ewallet_session):
        log.debug('')
        session_worker = self.fetch_ewallet_session_assigned_worker(
            ewallet_session
        )
        if not session_worker or isinstance(session_worker, dict) and \
                session_worker.get('failed'):
            return self.error_could_not_fetch_session_worker_for_ewallet_session(
                ewallet_session
            )
        remove_from_pool = session_worker.main_controller(
            controller='system', ctype='action', action='remove',
            remove='session', session=ewallet_session
        )
        return self.error_could_not_scrape_ewallet_session(ewallet_session) \
            if not remove_from_pool or isinstance(remove_from_pool, dict) and \
            remove_from_pool.get('failed') else True

    def scrape_ewallet_session_worker(self, session_worker):
        log.debug('')
        remove_from_pool = self.remove_session_worker_from_pool(session_worker)
        return self.error_could_not_scrape_ewallet_session_worker(session_worker) \
            if not remove_from_pool or isinstance(remove_from_pool, dict) and \
            remove_from_pool.get('failed') else True

    # MAPPERS

    def map_client_session_tokens(self, ctoken, stoken):
        log.debug('')
        if not isinstance(ctoken, object) or not isinstance(stoken, object):
            return self.error_invalid_client_session_token_pair(ctoken, stoken)
        try:
            ctoken.set_stoken(stoken)
            stoken.set_ctoken(ctoken)
        except:
            return self.error_could_not_map_client_session_tokens(ctoken, stoken)
        return {
            'failed': False,
            'ctoken': ctoken,
            'stoken': stoken,
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def map_client_id_to_worker(self, client_id, assigned_worker_id):
        log.debug('')
        update_map = self.update_client_worker_map({client_id: assigned_worker_id})
        return update_map or False

    def map_client_id_to_ewallet_session(self, client_id, session_token, assigned_worker, ewallet_session):
        '''
        [ NOTE   ]: Maps Client ID to Worker for Session Manager and Client ID
                    with Session Token and EWallet Session object for Worker.
        '''
        log.debug('')
        mappers = {
            'client_to_worker': self.map_client_id_to_worker(
                client_id, assigned_worker
            ),
            'client_to_session': self.map_client_id_to_session_token(
                client_id, session_token, assigned_worker, ewallet_session
            ),
        }
        return False if False in mappers.values() else True

    def map_client_id_to_session_token(self, client_id, session_token, assigned_worker, ewallet_session):
        log.debug('')
        update_map = assigned_worker.main_controller(
            controller='system', ctype='action', action='add', add='session_map',
            client_id=client_id, session_token=session_token, session=ewallet_session
        )
        return update_map or False

    # VALIDATORS

    def validate_client_token_in_pool(self, client_token):
        log.debug('')
        return False if client_token not in self.client_pool.values() else True

#   @pysnooper.snoop()
    def validate_client_id(self, client_id):
        log.debug('')
        segmented_client_id = client_id.split(':')
        if len(segmented_client_id) != 3:
            return self.error_invalid_client_id(client_id)
        client_token = self.fetch_client_token_by_label(client_id)
        if not client_token or isinstance(client_token, dict) and \
                client_token.get('failed'):
            self.error_could_not_fetch_client_token_from_label(
                client_id, client_token
            )
            return False
        checks = {
            'token': client_token,
            'prefix': self.validate_client_id_prefix(segmented_client_id),
            'length': self.validate_client_id_length(segmented_client_id),
            'timestamp': self.validate_client_id_timestamp(segmented_client_id),
            'pool': self.validate_client_token_in_pool(client_token),
            'active': self.validate_client_token_is_active(client_token),
            'unlink': self.validate_client_token_not_marked_for_unlink(client_token),
            'expiration': self.validate_client_token_not_passed_expiration_date(client_token),
        }
        log.info(checks)
        return False if False in checks.values() else True

    # TODO
    def validate_client_id_timestamp(self, client_id):
        log.debug('TODO')
        time_stamp = client_id[2]
        return True

    # TODO
    def validate_session_token_timestamp(self, session_token):
        log.debug('TODO')
        timestamp = session_token[2]
        return True

    def validate_session_token_is_active(self, session_token):
        log.debug('')
        try:
            return session_token.is_active()
        except Exception as e:
            self.error_could_not_perform_session_token_validity_check(session_token, e)
            return False

#   @pysnooper.snoop()
    def validate_session_token_not_marked_for_unlink(self, session_token):
        log.debug('')
        try:
            unlink = session_token.to_unlink()
            return True if not unlink else False
        except Exception as e:
            self.error_could_not_perform_session_token_unlink_check(session_token, e)
            return False

    def validate_session_token_not_passed_expiration_date(self, session_token):
        log.debug('')
        try:
            expired = session_token.expired()
            return True if not expired else False
        except Exception as e:
            self.error_could_not_perform_session_token_expiration_check(session_token, e)
            return False

#   @pysnooper.snoop()
    def validate_session_token(self, session_token):
        log.debug('')
        session_token_segmented = session_token.split(':')
        if len(session_token_segmented) != 3:
            return self.error_invalid_session_token(session_token)
        stoken = self.fetch_session_token_by_label(session_token)
        if not stoken or isinstance(stoken, dict) and \
                stoken.get('failed'):
            self.error_could_not_fetch_session_token_from_label(
                session_token, stoken
            )
            return False
        checks = {
            'token': stoken,
            'prefix': self.validate_session_token_prefix(session_token_segmented),
            'length': self.validate_session_token_length(session_token_segmented),
            'timestamp': self.validate_session_token_timestamp(session_token_segmented),
            'active': self.validate_session_token_is_active(stoken),
            'unlink': self.validate_session_token_not_marked_for_unlink(stoken),
            'expiration': self.validate_session_token_not_passed_expiration_date(stoken),
        }
        return False if False in checks.values() else True

    def validate_client_token_is_active(self, client_token):
        log.debug('')
        try:
            return client_token.is_active()
        except Exception as e:
            self.error_could_not_perform_client_token_validity_check(client_token, e)
            return False

    def validate_client_token_not_marked_for_unlink(self, client_token):
        log.debug('')
        try:
            unlink = client_token.to_unlink()
            return True if not unlink else False
        except Exception as e:
            self.error_could_not_perform_client_token_unlink_check(client_token, e)
            return False

    def validate_client_token_not_passed_expiration_date(self, client_token):
        log.debug('')
        try:
            expired = client_token.expired()
            return True if not expired else False
        except Exception as e:
            self.error_could_not_perform_client_token_expiration_check(client_token, e)
            return False

    def validate_session_token_prefix(self, session_token):
        log.debug('')
        default_prefix = self.fetch_session_token_default_prefix()
        return False if session_token[0] != default_prefix else True

    def validate_session_token_length(self, session_token):
        log.debug('')
        default_length = self.fetch_session_token_default_length()
        return False if len(session_token[1]) is not default_length else True

    def validate_client_id_prefix(self, client_id):
        log.debug('')
        default_prefix = self.fetch_client_id_default_prefix()
        return False if client_id[0] != default_prefix else True

    def validate_client_id_length(self, client_id):
        log.debug('')
        default_length = self.fetch_client_id_default_length()
        return False if len(client_id[1]) is not default_length else True

#   #@pysnooper.snoop()
    def validate_instruction_set(self, instruction_set):
        log.debug('')
        if not instruction_set.get('client_id') or not instruction_set.get('session_token'):
            return self.error_invalid_instruction_set_required_data(instruction_set)
        validations = {
            'client_id': self.validate_client_id(instruction_set['client_id']),
            'session_token': self.validate_session_token(instruction_set['session_token']),
        }
        return self.error_invalid_instruction_set_required_data(instruction_set) \
            if False in validations.values() else True

    # CREATORS

#   @pysnooper.snoop()
    def create_new_ewallet_session(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        ewallet_session = self.spawn_ewallet_session(orm_session, **kwargs)
        orm_session.add(ewallet_session)
        orm_session.commit()
        return ewallet_session

    def create_client_session_token_map(self, client_id, **kwargs):
        log.debug('')
        # Validate client id label
        validation = self.validate_client_id(client_id)
        if not validation or isinstance(validation, dict) and \
                validation.get('failed'):
            return self.error_invalid_client_id(client_id, kwargs)
        # Fetch client token from client id
        client_token = self.fetch_client_token_by_label(client_id)
        if not client_token or isinstance(client_token, dict) and \
                client_token.get('failed'):
            return self.error_could_not_fetch_client_token_by_label(
                client_id, kwargs
            )
        # Generate new session token object
        session_token = self.generate_ewallet_session_token()
        if not session_token or isinstance(session_token, dict) and \
                session_token.get('failed'):
            return self.error_could_not_generate_ewallet_session_token(
                session_token, kwargs
            )
        # Map tokens
        return self.map_client_session_tokens(client_token, session_token)

    # GENERAL

#   @pysnooper.snoop()
    def send_session_worker_instruction(self, worker_id, instruction_set):
        log.debug('')
        pool_entry = self.fetch_worker_pool_entry_by_id(worker_id)
        if not pool_entry or isinstance(pool_entry, dict) and \
                pool_entry.get('failed'):
            return pool_entry
        pool_entry['instruction'].put(instruction_set)
        return True

    def execute_worker_instruction(self, worker_id, instruction):
        log.debug('')
        # Fetch worker pool entry by worker id
        pool_entry = self.fetch_worker_pool_entry_by_id(worker_id)
        if not pool_entry or isinstance(pool_entry, dict) and \
                pool_entry.get('failed'):
            return self.error_could_not_fetch_worker_pool_entry_by_id(
                instruction, worker_id, pool_entry
            )
        # Check if worker is locked on
        if pool_entry['lock'].value:
            # Wait for worker to become available
            self.debug_waiting_for_unlock_to_delegate_instruction_set(
                pool_entry['lock'].value, instruction
            )
            self.ensure_worker_unlocked(pool_entry['lock'])
        # Lock on worker
        pool_entry['lock'].value = 1
        # Delegate instruction set to worker
        self.send_session_worker_instruction(worker_id, instruction)
        # Check is worker still processing instruction
        if pool_entry['lock'].value:
            # Wait for worker to finish processing
            self.debug_waiting_for_worker_unlock_to_read_response(
                pool_entry['lock'].value
            )
            self.ensure_worker_unlocked(pool_entry['lock'])
        # Fetch instruction set response
        response = self.read_session_worker_response(worker_id)
        self.debug_received_instruction_set_response(
            pool_entry['lock'].value, response
        )
        return response

    def ensure_worker_unlocked(self, lock):
        log.debug('')
        if lock.value:
            while lock.value:
                time.sleep(1)
                continue
        self.debug_worker_unlocked(lock)
        return True

    def ensure_worker_locked(self, lock):
        log.debug('')
        if not lock.value:
            while not lock.value:
                time.sleep(1)
                continue
        self.debug_worker_locked(lock)
        return True

#   @pysnooper.snoop()
    def read_session_worker_response(self, worker_id):
        log.debug('')
        pool_entry = self.fetch_worker_pool_entry_by_id(worker_id)
        if not pool_entry or isinstance(pool_entry, dict) and \
                pool_entry.get('failed'):
            return pool_entry
        response = pool_entry['response'].get()
        return response

    def generate_id_for_entity_set(self, entity_set):
        '''
        [ NOTE   ]: Entity identifier generator, for session workers and ewallet sessions.
        [ INPUT  ]: Mode unique numeric id in set - list of numeric ids
                    Mode next uniq id from current - integer
                    Mode unique alphanemeric id in set - list of string codes
                    Mode randomly generated string - empty string
            [ EX ]: ([1, 2, 3] | [] | 13 | '' | ['alph4Num3r1c1d'])
        [ RETURN ]: (Numeric ID | AlphaNumeric ID | InstructionFailure-Error)
        '''
        log.debug('')
        if not entity_set and isinstance(entity_set, list) or \
                not entity_set and isinstance(entity_set, int):
            return 1
        elif not entity_set and isinstance(entity_set, str):
            return res_utils.generate_random_alpha_numeric_string()
        elif entity_set and isinstance(entity_set, list) and isinstance(entity_set[0], int):
            new_id = max(entity_set) + 1
            return new_id
        elif entity_set and isinstance(entity_set, int):
            return entity_set + 1
        elif entity_set and isinstance(entity_set, list) and isinstance(entity_set[0], str):
            new_id = str(res_utils.generate_random_alpha_numeric_string())
            if new_id not in entity_set:
                return new_id
            for count in range(3):
                if count > 3:
                    return self.error_could_not_generate_id_for_entity_set(
                        '3 failed alphanumeric sequence generation tries.', entity_set
                    )
                new_id = str(res_utils.generate_random_alpha_numeric_string())
                if new_id not in entity_set:
                    break
        return self.error_could_not_generate_id_for_entity_set(
            'Software error.', entity_set
        )

    def generate_ewallet_session_token(self):
        '''
        [ NOTE   ]: Generates a new unique session token using default format and prefix.
        [ NOTE   ]: Session Token follows the following format <prefix-string>:<code>:<timestamp>
        '''
        log.debug('')
        prefix = self.fetch_session_token_default_prefix()
        length = self.fetch_session_token_default_length()
        timestamp = str(time.time())
        st_code = self.res_utils.generate_random_alpha_numeric_string(
            string_length=length
        )
        label = prefix + ':' + st_code + ':' + timestamp
        session_token = self.spawn_session_token(
            session_token=label,
            expires_on=datetime.datetime.now() + \
            datetime.timedelta(
                minutes=self.fetch_default_session_token_validity_interval_in_minutes()
            ),
        )
        return session_token

#   @pysnooper.snoop()
    def generate_client_id(self):
        '''
        [ NOTE   ]: Generates a new unique client id using default format and prefix.
        [ NOTE   ]: User ID follows the following format <prefix-string>:<code>:<timestamp>
        '''
        log.debug('')
        prefix = self.fetch_client_id_default_prefix()
        length = self.fetch_client_id_default_length()
        timestamp = str(time.time())
        uid_code = self.res_utils.generate_random_alpha_numeric_string(
            string_length=length
        )
        label = prefix + ':' + uid_code + ':' + timestamp
        client_id_token = self.spawn_client_id(
            client_id=label,
            expires_on=datetime.datetime.now() + \
            datetime.timedelta(
                minutes=self.fetch_default_client_id_validity_interval_in_minutes()
            ),
        )
        return client_id_token

#   @pysnooper.snoop()
    def cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet_sessions'):
            return self.error_no_ewallet_sessions_found(kwargs)
        session_count = 0
        for session in kwargs['ewallet_sessions']:
            clean = self.scrape_ewallet_session(session)
            if not clean or isinstance(clean, dict) and clean.get('failed'):
                self.warning_could_not_clean_ewallet_session(session)
                continue
            session_count += 1
            log.info('Successfully scraped ewallet session.')
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': session_count,
        }
        return instruction_set_response

    def remove_session_worker_from_pool(self, session_worker):
        log.debug('')
        try:
            self.worker_pool.remove(session_worker)
        except:
            return self.error_could_not_remove_ewallet_session_worker_from_pool(
                session_worker
            )
        return True

    def cleanup_vacant_session_workers(self, **kwargs):
        log.debug('')
        if not kwargs.get('vacant_workers'):
            return self.error_no_vacant_session_workers_found(kwargs)
        reserved_buffer_worker = kwargs['vacant_workers'][0]
        log.info(
            'Reserved vacant ewallet session worker {}.'.format(
                reserved_buffer_worker
            )
        )
        kwargs['vacant_workers'].remove(kwargs['vacant_workers'][0])
        worker_count = len(kwargs['vacant_workers'])
        for worker in kwargs['vacant_workers']:
            clean = self.scrape_ewallet_session_worker(worker)
            if not clean or isinstance(clean, dict) and clean.get('failed'):
                self.warning_could_not_cleanup_ewallet_session_worker(worker)
                worker_count -= 1
                continue
            log.info('Successfully scraped ewallet session worker.')
        instruction_set_response = {
            'failed': False,
            'workers_cleaned': worker_count,
            'worker_reserved': reserved_buffer_worker,
            'worker_pool': self.fetch_ewallet_session_manager_worker_pool(),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def assign_new_ewallet_session_to_worker(self, new_session):
        '''
        [ NOTE   ]: Adds new EWallet Session to one of the workers session pool.
                    The worker is simply the neares available worker in pool, and
                    if none is found, one is created.
        '''
        log.debug('')
        worker = self.fetch_first_available_worker()
        if not worker or isinstance(worker, dict) and worker.get('failed'):
            self.session_manager_controller(
                controller='system', ctype='action', action='new', new='worker'
            )
            worker = self.fetch_first_available_worker()
        assign_worker = worker.main_controller(
            controller='system', ctype='action', action='add', add='session',
            session=new_session
        )
        return False if not assign_worker or isinstance(assign_worker, dict) \
            and assign_worker.get('failed') else worker

    def start_instruction_set_listener(self):
        '''
        [ NOTE   ]: Starts socket based command chain instruction set listener.
        [ NOTE   ]: Program hangs here until interrupt.
        '''
        log.debug('')
        socket_handler = self.fetch_ewallet_session_manager_socket_handler()
        if not socket_handler:
            return self.error_could_not_fetch_socket_handler()
        log.info(
            'Starting instruction set listener using socket handler values : {}.'\
            .format(socket_handler.view_handler_values())
        )
        socket_handler.start_listener()
        return True

    def open_ewallet_session_manager_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWalletSocketHandler object using default configuration values.
        '''
        log.debug('')
        in_port = kwargs.get('in_port') or self.fetch_default_ewallet_command_chain_instruction_port()
        out_port = kwargs.get('out_port') or self.fetch_default_ewallet_command_chain_reply_port()
        if not in_port or not out_port:
            return self.error_could_not_fetch_socket_handler_required_values()
        socket = self.spawn_ewallet_session_manager_socket_handler(in_port, out_port)
        return self.error_could_not_spawn_socket_handler() if not socket else socket

    # ACTIONS

    def action_execute_user_instruction_set(self, **kwargs):
        log.debug('')
        # Fetch worker id from client token label
        worker_id = self.fetch_worker_identifier_by_client_id(kwargs['client_id'])
        if not worker_id or isinstance(worker_id, dict) and \
                worker_id.get('failed'):
            return worker_id
        # Fetch client session token map
        cst_map = self.fetch_client_session_tokens(
            kwargs['client_id'], kwargs['session_token']
        )
        if not cst_map or isinstance(cst_map, dict) and cst_map.get('failed'):
            return self.error_could_not_fetch_client_session_token_map(
                kwargs, cst_map, worker_id
            )
        # Instruction set processing
        return self.execute_worker_instruction(
            worker_id, kwargs
        )

    def action_new_session(self, **kwargs):
        log.debug('')
        session = self.create_new_ewallet_session(**kwargs)
        return session

#   @pysnooper.snoop()
    def action_request_session_token(self, worker_id, cst_map, **kwargs):
        log.debug('')
        # Sanitize instruction set
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new',
        )
        # Update instruction set
        sanitized_instruction_set.update({
            'controller': 'system', 'ctype': 'action', 'action': 'add',
            'add': 'session', 'client_id': cst_map['ctoken'].label,
            'session_token': cst_map['stoken'].label
        })
        # Create new session token mapped ewallet session
        new_session = self.execute_worker_instruction(
            worker_id, sanitized_instruction_set
        )
        if not new_session or isinstance(new_session, dict) and \
                new_session.get('failed'):
            return self.error_could_not_create_new_ewallet_session(
                kwargs, new_session, worker_id, cst_map,
            )
        return new_session

    def action_request_client_id(self):
        log.debug('')
        client_id = self.generate_client_id()
        set_to_pool = self.set_new_client_id_to_pool({client_id.label: client_id})
        if not client_id or not set_to_pool or isinstance(set_to_pool, dict) \
                and set_to_pool.get('failed'):
            return self.warning_could_not_fulfill_client_id_request()
        instruction_set_response = {
            'failed': False,
            'client_id': client_id.label,
        }
        return instruction_set_response

    def action_new_worker(self):
        log.debug('')
        worker = self.spawn_ewallet_session_worker()
        instruction_queue = Queue()
        response_queue = Queue()
        worker.set_instruction_queue(instruction_queue)
        worker.set_response_queue(response_queue)
        worker.set_lock(Value('i', 0))
        return worker

    def action_sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        expired_sessions = self.fetch_ewallet_sessions_past_expiration_date(
            **kwargs
        )
        if not expired_sessions or isinstance(expired_sessions, dict) and \
                expired_sessions.get('failed'):
            return self.warning_could_not_fetch_expired_ewallet_sessions(kwargs)
        sweep_cleanup = self.cleanup_ewallet_sessions(
            ewallet_sessions=expired_sessions, **kwargs
        )
        return self.warning_could_not_sweep_cleanup_ewallet_sessions(kwargs) \
            if not sweep_cleanup or isinstance(sweep_cleanup, dict) and \
            sweep_cleanup.get('failed') else sweep_cleanup

    def action_cleanup_ewallet_session_by_id(self, **kwargs):
        log.debug('')
        ewallet_session = self.fetch_ewallet_session_by_id(kwargs['session_id'])
        if not ewallet_session:
            return self.warning_could_not_fetch_ewallet_session(kwargs)
        cleanup_session = self.cleanup_ewallet_sessions(
            ewallet_sessions=[ewallet_session], **kwargs
        )
        return self.warning_could_not_cleanup_target_ewallet_session(kwargs) \
            if not cleanup_session or isinstance(cleanup_session, dict) and \
            cleanup_session.get('failed') else cleanup_session

#   @pysnooper.snoop('logs/ewallet.log')
    def action_cleanup_session_workers(self, **kwargs):
        log.debug('')
        session_workers = self.fetch_ewallet_session_manager_worker_pool()
        if not session_workers or isinstance(session_workers, dict) and \
                session_workers.get('failed'):
            return self.warning_could_not_fetch_session_worker_pool(kwargs)
        vacant_workers = [
            worker for worker in session_workers \
            if worker.fetch_session_worker_state_code() == 0
        ]
        cleanup_workers = self.cleanup_vacant_session_workers(
            vacant_workers=vacant_workers, **kwargs
        )
        return self.warning_could_not_cleanup_ewallet_session_workers(kwargs) \
            if not cleanup_workers or isinstance(cleanup_workers, dict) and \
            cleanup_workers.get('failed') else cleanup_workers

#   @pysnooper.snoop('logs/ewallet.log')
    def action_interogate_ewallet_session_workers(self, **kwargs):
        log.debug('')
        workers = self.fetch_ewallet_session_manager_worker_pool()
        if not workers or isinstance(workers, dict) and workers.get('failed'):
            return self.warning_could_not_interogate_ewallet_session_workers(
                kwargs
            )
        command_chain_response = {
            'failed': False,
            'workers': {
                worker: worker.fetch_session_worker_values() for worker in workers
            },
        }
        return command_chain_response

#   @pysnooper.snoop()
    def action_new_ewallet_session(self, **kwargs):
        log.debug('')
        new_session = self.create_new_ewallet_session(**kwargs)
        if not new_session or isinstance(new_session, dict) and \
                new_session.get('failed'):
            return self.warning_could_not_create_new_ewallet_session(kwargs)
        orm_session = new_session.fetch_active_session()
        orm_session.add(new_session)
        orm_session.commit()
        assign_worker = self.assign_new_ewallet_session_to_worker(new_session)
        if not assign_worker or isinstance(assign_worker, dict) and \
                assign_worker.get('failed'):
            orm_session.rollback()
            return self.warning_ewallet_session_worker_assignment_failure(kwargs)
        instruction_set_response = {
            'failed': False,
            'ewallet_session': new_session,
            'session_data': new_session.fetch_active_session_values(),
        }
        return instruction_set_response

    def action_interogate_ewallet_session(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        interogate_session = ewallet_session.ewallet_controller(
            controller='system', ctype='action', action='interogate',
            interogate='session', active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_interogate_ewallet_session(
            ewallet_session, instruction_set
        ) if not interogate_session or isinstance(interogate_session, dict) and \
            interogate_session.get('failed') else interogate_session

    # EVENTS

    # TODO
    def event_session_timeout(self, **kwargs):
        pass
    def event_worker_timeout(self, **kwargs):
        pass
    def event_client_ack_timeout(self, **kwargs):
        pass
    def event_client_id_expire(self, **kwargs):
        pass
    def event_session_token_expire(self, **kwargs):
        pass

    # FORMATTERS

    def format_worker_pool_entry(self, **kwargs):
        log.debug('')
        if not kwargs.get('values') or not isinstance(kwargs['values'], dict):
            return self.error_invalid_values_for_worker_pool_entry(kwargs)
        pool_entry = {
            kwargs['values'].get('id'): {
                'process': kwargs.get('process'),
                'instruction': kwargs['values'].get('instruction_set_recv'),
                'response': kwargs['values'].get('instruction_set_resp'),
                'lock': kwargs['values'].get('lock'),
            }
        }
        return pool_entry

    # HANDLERS
    '''
    [ NOTE ]: Instruction set validation and sanitizations are performed here.
    '''

    def handle_client_action_view_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_transfer_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_transfer_record(
            kwargs, view_transfer_record
        ) if not view_transfer_record or isinstance(view_transfer_record, dict) and \
            view_transfer_record.get('failed') else view_transfer_record

    def handle_client_action_view_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_transfer_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_transfer_sheet(
            kwargs, view_transfer_sheet
        ) if not view_transfer_sheet or isinstance(view_transfer_sheet, dict) and \
            view_transfer_sheet.get('failed') else view_transfer_sheet

    def handle_client_action_view_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_contact_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_contact_record(
            kwargs, view_contact_record
        ) if not view_contact_record or isinstance(view_contact_record, dict) and \
            view_contact_record.get('failed') else view_contact_record

    def handle_client_action_view_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_contact_list = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_contact_list(
            kwargs, view_contact_list
        ) if not view_contact_list or isinstance(view_contact_list, dict) and \
            view_contact_list.get('failed') else view_contact_list

    def handle_client_action_stop(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        stop_timer = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_stop_credit_clock_timer(
            kwargs, stop_timer
        ) if not stop_timer or isinstance(stop_timer, dict) and \
            stop_timer.get('failed') else stop_timer

    def handle_client_action_resume(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        resume_timer = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_resume_credit_clock_timer(
            kwargs, resume_timer
        ) if not resume_timer or isinstance(resume_timer, dict) and \
            resume_timer.get('failed') else resume_timer

    def handle_client_action_pause(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        pause_timer = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_start_credit_clock_timer(
            kwargs, pause_timer
        ) if not pause_timer or isinstance(pause_timer, dict) and \
            pause_timer.get('failed') else pause_timer

    def handle_client_action_start_clock_timer(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        start_timer = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_start_credit_clock_timer(
            kwargs, start_timer
        ) if not start_timer or isinstance(start_timer, dict) and \
            start_timer.get('failed') else start_timer

    def handle_client_action_edit_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        edit_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_edit_user_account(
            kwargs, edit_account
        ) if not edit_account or isinstance(edit_account, dict) and \
            edit_account.get('failed') else edit_account

    def handle_client_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_client_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_client_action_transfer_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        transfer_credits = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_transfer_credits_to_partner(
            kwargs, transfer_credits
        ) if not transfer_credits or isinstance(transfer_credits, dict) and \
            transfer_credits.get('failed') else transfer_credits

    def handle_client_action_new_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        new_contact_list = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_contact_list(
            kwargs, new_contact_list
        ) if not new_contact_list or isinstance(new_contact_list, dict) and \
            new_contact_list.get('failed') else new_contact_list

    def handle_client_action_new_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        new_contact_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_contact_record(
            kwargs, new_contact_record
        ) if not new_contact_record or isinstance(new_contact_record, dict) and \
            new_contact_record.get('failed') else new_contact_record

    def handle_client_action_convert_clock_to_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        convert_clock2credits = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_convert_credit_clock_to_credits(
            kwargs, convert_clock2credits
        ) if not convert_clock2credits or isinstance(convert_clock2credits, dict) and \
            convert_clock2credits.get('failed') else convert_clock2credits

    def handle_client_action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        convert_credits2clock = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_convert_credits_to_credit_clock(
            kwargs, convert_credits2clock
        ) if not convert_credits2clock or isinstance(convert_credits2clock, dict) and \
            convert_credits2clock.get('failed') else convert_credits2clock

    def handle_client_action_pay(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        pay_credits = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_pay_partner_account(
            kwargs, pay_credits
        ) if not pay_credits or isinstance(pay_credits, dict) and \
            pay_credits.get('failed') else pay_credits

#   @pysnooper.snoop()
    def handle_client_action_supply_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        supply_credits = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_supply_user_credit_ewallet(
            kwargs, supply_credits
        ) if not supply_credits or isinstance(supply_credits, dict) and \
            supply_credits.get('failed') else supply_credits

#   @pysnooper.snoop()
    def handle_client_action_login(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        account_login = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_login_user_account(
            kwargs, account_login
        ) if not account_login or isinstance(account_login, dict) and \
            account_login.get('failed') else account_login

    def handle_client_action_new_account(self, **kwargs):
        '''
        [ NOTE   ]: Validates received instruction set, searches for worker and session
                    and proceeds to create new User Account in said session. Requiers
                    valid Client ID and Session Token.
        '''
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        new_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_user_account(
            kwargs, new_account
        ) if not new_account or isinstance(new_account, dict) and \
            new_account.get('failed') else new_account

#   @pysnooper.snoop()
    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found(kwargs)
        # Map tokens
        cst_map = self.create_client_session_token_map(kwargs['client_id'])
        if not cst_map or isinstance(cst_map, dict) and cst_map.get('failed'):
            return self.error_could_not_create_client_session_token_map(
                kwargs, cst_map
            )
        # Fetch worker id by client id
        worker_id = self.fetch_available_worker_id(client_id=kwargs['client_id'])
        if not worker_id or isinstance(worker_id, dict) and \
                worker_id.get('failed'):
            return self.warning_could_not_fetch_worker_id(
                worker_id, cst_map['ctoken'].label, cst_map['stoken'].label
            )
        # Reference worker id on session token
        cst_map['stoken'].set_worker_id(worker_id)
        # Execute instruction
        request_session_token = self.action_request_session_token(
            worker_id, cst_map, **kwargs
        )
        if not request_session_token or isinstance(request_session_token, dict) and \
                request_session_token.get('failed'):
            return self.warning_could_not_request_session_token(
                kwargs, request_session_token, worker_id, cst_map
            )
        # Set session token to pool
        set_to_pool = self.set_new_session_token_to_pool({
            cst_map['stoken'].label: cst_map['stoken']
        })
        # Formulate instruction set
        instruction_set_response = {
            'failed': False,
            'session_token': cst_map['stoken'].label,
        }
        return instruction_set_response

#   @pysnooper.snoop()
    def handle_system_action_new_worker(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session Manager Worker object and sets
                    it to worker pool.
        '''
        log.debug('')
        worker = self.action_new_worker()
        values = worker.fetch_session_worker_values()
        worker_proc = Process(
            target=worker.worker_init, args=()
        )
        worker_proc.daemon = True
        pool_entry = self.format_worker_pool_entry(
            process=worker_proc, values=values
        )
        set_to_pool = self.set_worker_to_pool(pool_entry)
        if not set_to_pool or isinstance(set_to_pool, dict) and \
                set_to_pool.get('failed'):
            return set_to_pool
        worker_proc.start()
        instruction_set_response = {
            'failed': False,
            'worker': values['id'],
            'worker_data': pool_entry,
        }
        return instruction_set_response

    def handle_client_action_recover_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet.get('ewallet_session') or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        recover_account = self.action_recover_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return recover_account

    def handle_client_action_recover(self, **kwargs):
        log.debug('')
        if not kwargs.get('recover'):
            return self.error_no_client_action_recover_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_recover_account,
        }
        return self.warning_invalid_recover_target(kwargs) \
            if kwargs['recover'] not in handlers.keys() else \
            handlers[kwargs['recover']](**kwargs)

    def handle_system_action_sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        return self.action_sweep_cleanup_ewallet_sessions(**kwargs)

    def handle_system_action_cleanup_target_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_cleanup_ewallet_session_by_id(**kwargs)

    def handle_system_action_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('session_id') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_ewallet_session,
            'sweep': self.handle_system_action_sweep_cleanup_ewallet_sessions,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_system_action_cleanup_session_workers(self, **kwargs):
        log.debug('')
        return self.action_cleanup_session_workers(**kwargs)

    def handle_system_action_cleanup(self, **kwargs):
        log.debug('')
        if not kwargs.get('cleanup'):
            return self.error_no_system_action_cleanup_target_specified(kwargs)
        handlers = {
            'workers': self.handle_system_action_cleanup_session_workers,
            'sessions': self.handle_system_action_cleanup_ewallet_sessions,
        }
        return handlers[kwargs['cleanup']](**kwargs)

    def handle_system_action_interogate_ewallet_workers(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_workers(**kwargs)

    def handle_system_action_new_session(self, **kwargs):
        log.debug('')
        return self.action_new_ewallet_session(**kwargs)

    def handle_system_action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        active_session = self.res_utils.session_factory()
        ewallet_session = self.fetch_ewallet_session_for_system_action_using_id(
            active_session=active_session, **kwargs
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return self.warning_could_not_fetch_ewallet_session(kwargs)
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'interogate'
        )
        interogate_session = self.action_interogate_ewallet_session(
            ewallet_session, sanitized_instruction_set
        )
        return interogate_session

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_system_action_interogate_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_interogate_ewallet_session,
            'workers': self.handle_system_action_interogate_ewallet_workers,
        }
        return handlers[kwargs['interogate']](**kwargs)

    def handle_client_action_logout(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        logout_account = self.action_logout_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return logout_account

    def handle_client_action_switch_user_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_user_account = self.action_switch_active_session_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_user_account

    def handle_client_action_view_logout_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_logout_records = self.action_view_logout_records(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return view_logout_records

    def handle_client_action_view_login_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_login_records = self.action_view_login_records(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return view_login_records

    def handle_client_action_unlink_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_user_account = self.action_unlink_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_user_account

    def handle_client_action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_credit_clock = self.action_unlink_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_credit_clock

    def handle_client_action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_credit_ewallet = self.action_unlink_credit_ewallet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_credit_ewallet

    def handle_client_action_unlink_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_unlink_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_unlink_credit_ewallet,
            'clock': self.handle_client_action_unlink_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_unlink_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_contact_list = self.action_unlink_contact_list(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_contact_list

    def handle_client_action_unlink_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_time_sheet = self.action_unlink_time_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_time_sheet

    def handle_client_action_unlink_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_conversion_sheet = self.action_unlink_conversion_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_conversion_sheet

    def handle_client_action_unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_invoice_sheet = self.action_unlink_invoice_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_invoice_sheet

    def handle_client_action_unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_transfer_sheet = self.action_unlink_transfer_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_transfer_sheet

    def handle_client_action_unlink_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_contact_record = self.action_unlink_contact_list_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_contact_record

    def handle_client_action_unlink_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_unlink_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_contact_list,
            'record': self.handle_client_action_unlink_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_unlink_time_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_time_record = self.action_unlink_time_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_time_record

    def handle_client_action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_unlink_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_time_sheet,
            'record': self.handle_client_action_unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_conversion_record = self.action_unlink_conversion_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_conversion_record

    def handle_client_action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_unlink_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_conversion_sheet,
            'record': self.handle_client_action_unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_invoice_record = self.action_unlink_invoice_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_invoice_record

    def handle_client_action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_unlink_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_invoice_sheet,
            'record': self.handle_client_action_unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet.get('ewallet_session') or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        unlink_transfer_record = self.action_unlink_transfer_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return unlink_transfer_record

    def handle_client_action_unlink_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_unlink_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_transfer_sheet,
            'record': self.handle_client_action_unlink_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_client_action_unlink_target_specified(kwargs)
        handlers = {
            'transfer': self.handle_client_action_unlink_transfer,
            'invoice': self.handle_client_action_unlink_invoice,
            'conversion': self.handle_client_action_unlink_conversion,
            'time': self.handle_client_action_unlink_time,
            'contact': self.handle_client_action_unlink_contact,
            'credit': self.handle_client_action_unlink_credit,
            'account': self.handle_client_action_unlink_account,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_client_action_switch_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_contact_list = self.action_switch_contact_list(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_contact_list

    def handle_client_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_time_sheet = self.action_switch_time_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_time_sheet

    def handle_client_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_conversion_sheet = self.action_switch_conversion_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_conversion_sheet

    def handle_client_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_invoice_sheet = self.action_switch_invoice_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_invoice_sheet

    def handle_client_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_transfer_sheet = self.action_switch_transfer_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_transfer_sheet

    def handle_client_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_credit_clock = self.action_switch_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_credit_clock

    def handle_client_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        switch_credit_ewallet = self.action_switch_credit_ewallet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return switch_credit_ewallet

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
            'transfer_sheet': self.handle_client_action_switch_transfer_sheet,
            'invoice_sheet': self.handle_client_action_switch_invoice_sheet,
            'conversion_sheet': self.handle_client_action_switch_conversion_sheet,
            'time_sheet': self.handle_client_action_switch_time_sheet,
            'contact_list': self.handle_client_action_switch_contact_list,
            'account': self.handle_client_action_switch_user_account,
        }
        return handlers[kwargs['switch']](**kwargs)

    def handle_client_action_new_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_time_sheet = self.action_new_time_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_time_sheet

    def handle_client_action_new_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_new_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_time_sheet,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_new_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_conversion_sheet = self.action_new_conversion_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_conversion_sheet

    def handle_client_action_new_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_new_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_conversion_sheet,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_new_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_invoice_sheet = self.action_new_invoice_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_invoice_sheet

    def handle_client_action_new_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_new_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_new_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_transfer_sheet = self.action_new_transfer_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_transfer_sheet

    def handle_client_action_new_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_new_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_new_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_credit_clock = self.action_new_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_credit_clock

    def handle_client_action_new_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_credit_ewallet = self.action_new_credit_ewallet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_credit_ewallet

    def handle_client_action_new_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_target_new_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_new_credit_ewallet,
            'clock': self.handle_client_action_new_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_view_invoice_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_invoice_record = self.action_view_invoice_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_invoice_record

    def handle_client_action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_invoice_sheet = self.action_view_invoice_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_invoice_sheet

    def handle_client_action_view_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_view_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_invoice_sheet,
            'record': self.handle_client_action_view_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_view_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_credit_clock = self.action_view_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_credit_clock

    def handle_client_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_credit_ewallet = self.action_view_credit_ewallet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_credit_ewallet

    def handle_client_action_view_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_view_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_view_credit_ewallet,
            'clock': self.handle_client_action_view_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_view_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_account = self.action_view_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_account

    def handle_client_action_view_conversion_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_conversion_record = self.action_view_conversion_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_conversion_record

    def handle_client_action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_conversion_sheet = self.action_view_conversion_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_conversion_sheet

    def handle_client_action_view_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_view_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_conversion_sheet,
            'record': self.handle_client_action_view_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_view_time_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_time_record = self.action_view_time_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_time_record

    def handle_client_action_view_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        view_time_sheet = self.action_view_time_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_time_sheet

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

    def handle_client_action_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_transfer_target_specified(kwargs)
        handlers = {
            'credits': self.handle_client_action_transfer_credits,
#           'time': self.handle_client_action_transfer_time,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_new_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_contact_list,
            'record': self.handle_client_action_new_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_view_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_view_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_contact_list,
            'record': self.handle_client_action_view_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_client_action_view_target_specified(kwargs)
        handlers = {
            'contact': self.handle_client_action_view_contact,
            'transfer': self.handle_client_action_view_transfer,
            'time': self.handle_client_action_view_time,
            'credit': self.handle_client_action_view_credit,
            'conversion': self.handle_client_action_view_conversion,
            'invoice': self.handle_client_action_view_invoice,
            'account': self.handle_client_action_view_account,
            'login': self.handle_client_action_view_login_records,
            'logout': self.handle_client_action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        return self.action_request_client_id()

    def handle_system_action_start_instruction_listener(self, **kwargs):
        '''
        [ NOTE   ]: Turn Session Manager into server listenning for socket based instructions.
        [ NOTE   ]: System hangs here until interrupt.
        '''
        log.debug('')
        return self.start_instruction_set_listener()

    def handle_system_action_open_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Create and setups Session Manager Socket Handler.
        '''
        log.debug('')
        socket_handler = self.open_ewallet_session_manager_sockets(**kwargs)
        set_socket_handler = self.set_socket_handler(socket_handler)
        return socket_handler

    # TODO - Kill process
    def handle_system_action_close_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Desociates Ewallet Socket Handler from Session Manager.
        '''
        log.debug('')
        return self.unset_socket_handler()

    # TODO
    def handle_system_event_session_timeout(self, **kwargs):
        timeout = self.event_session_timeout()
    def handle_system_event_worker_timeout(self, **kwargs):
        timeout = self.event_worker_timeout()
    def handle_system_event_client_ack_timeout(self, **kwargs):
        timeout = self.event_client_ack_timeout()
    def handle_system_event_client_id_expire(self, **kwargs):
        expire = self.event_client_id_expire()
    def handle_system_event_session_token_expire(self, **kwargs):
        expire = self.event_session_token_expire()

    def handle_client_action_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_client_action_start_target_specified()
        handlers = {
            'clock_timer': self.handle_client_action_start_clock_timer,
        }
        return handlers[kwargs['start']](**kwargs)

    def handle_client_action_convert(self, **kwargs):
        log.debug('')
        if not kwargs.get('convert'):
            return self.error_no_client_action_convert_target_specified()
        handlers = {
            'credits2clock': self.handle_client_action_convert_credits_to_clock,
            'clock2credits': self.handle_client_action_convert_clock_to_credits,
        }
        return handlers[kwargs['convert']](**kwargs)

    def handle_client_action_supply(self, **kwargs):
        log.debug('')
        if not kwargs.get('supply'):
            return self.error_no_client_action_supply_target_specified()
        handlers = {
            'credits': self.handle_client_action_supply_credits,
        }
        return handlers[kwargs['supply']](**kwargs)

    def handle_client_action_new(self, **kwargs):
        '''
        [ NOTE   ]: Client action handler for new type actions.
        '''
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_client_action_new_target_specified()
        handlers = {
            'account': self.handle_client_action_new_account,
            'contact': self.handle_client_action_new_contact,
            'credit': self.handle_client_action_new_credit,
            'transfer': self.handle_client_action_new_transfer,
            'invoice': self.handle_client_action_new_invoice,
            'conversion': self.handle_client_action_new_conversion,
            'time': self.handle_client_action_new_time,
        }
        return handlers[kwargs['new']](**kwargs)

    def handle_client_action_request(self, **kwargs):
        '''
        [ NOTE   ]: Client action handler for request type actions.
        '''
        log.debug('')
        if not kwargs.get('request'):
            return self.error_no_client_request_specified()
        _handlers = {
                'client_id': self.handle_client_action_request_client_id,
                'session_token': self.handle_client_action_request_session_token,
                }
        return _handlers[kwargs['request']](**kwargs)

    def handle_system_action_new(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for new type actions.
        '''
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_system_action_new_specified()
        handlers = {
            'worker': self.handle_system_action_new_worker,
            'session': self.handle_system_action_new_session,
        }
        return handlers[kwargs['new']](**kwargs)

    def handle_system_action_scrape(self, **kwargs):
        pass
    def handle_system_action_search(self, **kwargs):
        pass
    def handle_system_action_view(self, **kwargs):
        pass
    def handle_system_action_request(self, **kwargs):
        pass

    def handle_system_action_start(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for start type actions.
        '''
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_system_action_start_target_specified()
        _handlers = {
                'instruction_listener': self.handle_system_action_start_instruction_listener,
                }
        return _handlers[kwargs['start']](**kwargs)

    def handle_system_action_open(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for open type actions.
        '''
        log.debug('')
        if not kwargs.get('opening'):
            return self.error_no_system_action_open_target_specified()
        _handlers = {
                'sockets': self.handle_system_action_open_sockets,
                }
        return _handlers[kwargs['opening']](**kwargs)

    def handle_system_action_close(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for close type actions.
        '''
        log.debug('')
        if not kwargs.get('closing'):
            return self.error_no_system_action_close_target_specified()
        _handlers = {
                'sockets': self.handle_system_action_close_sockets,
                }
        return _handlers[kwargs['closing']](**kwargs)

    def handle_system_event_client_timeout(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for client timeout events.
        '''
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_event_client_timeout_target_specified()
        _handlers = {
                'client_ack': self.handle_system_event_client_ack_timeout,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_system_event_expire(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for expire type events.
        '''
        log.debug('')
        if not kwargs.get('expire'):
            return self.error_no_system_event_expire_specified()
        _handlers = {
                'client_id': self.handle_system_event_client_id_expire,
                'session_token': self.handle_system_event_session_token_expire,
                }
        return _handlers[kwargs['expire']](**kwargs)

    def handle_system_event_timeout(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for timeout type events.
        '''
        log.debug('')
        if not kwargs.get('timeout'):
            return self.error_no_system_event_timeout_specified()
        _handlers = {
                'session': self.handle_system_event_session_timeout,
                'worker': self.handle_system_event_worker_timeout,
                'client': self.handle_system_event_client_timeout,
                }
        return _handlers[kwargs['timeout']](**kwargs)

    # CONTROLLERS

    def client_session_manager_action_controller(self, **kwargs):
        '''
        [ NOTE   ]: Client action controller for the EWallet Session Manager, accessible
                    to regular user api calls.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_client_session_manager_action_specified()
        handlers = {
            'new': self.handle_client_action_new,
#           'scrape': self.handle_client_action_scrape,
#           'search': self.handle_client_action_search,
            'view': self.handle_client_action_view,
            'request': self.handle_client_action_request,
            'login': self.handle_client_action_login,
            'supply': self.handle_client_action_supply,
            'convert': self.handle_client_action_convert,
            'start': self.handle_client_action_start,
            'pause': self.handle_client_action_pause,
            'resume': self.handle_client_action_resume,
            'stop': self.handle_client_action_stop,
            'pay': self.handle_client_action_pay,
            'transfer': self.handle_client_action_transfer,
            'edit': self.handle_client_action_edit,
            'switch': self.handle_client_action_switch,
            'unlink': self.handle_client_action_unlink,
            'logout': self.handle_client_action_logout,
            'recover': self.handle_client_action_recover,
        }
        return handlers[kwargs['action']](**kwargs)

    def system_session_manager_action_controller(self, **kwargs):
        '''
        [ NOTE   ]: System action controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        [ NOTE   ]: Pauses active credit clock consumption timer.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_action_specified()
        handlers = {
            'new': self.handle_system_action_new,
            'start': self.handle_system_action_start,
#           'scrape': self.handle_system_action_scrape,
            'search': self.handle_system_action_search,
            'view': self.handle_system_action_view,
            'request': self.handle_system_action_request,
            'open': self.handle_system_action_open,
            'close': self.handle_system_action_close,
            'interogate': self.handle_system_action_interogate,
            'cleanup': self.handle_system_action_cleanup,
        }
        return handlers[kwargs['action']](**kwargs)

    # TODO
    def client_session_manager_event_controller(self, **kwargs):
        '''
        [ NOTE   ]: Client event controller for the EWallet Session Manager, accessible
                    to regular user api calls.
        [ INPUT  ]: event=('timeout' | 'expire')+
        [ WARNING ]: Unimplemented
        '''
        pass

    def system_session_manager_event_controller(self, **kwargs):
        '''
        [ NOTE   ]: System event controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        '''
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_system_session_manager_event_specified()
        handlers = {
            'timeout': self.handle_system_event_timout,
            'expire': self.handle_system_event_expire,
        }
        return handlers[kwargs['event']](**kwargs)

    def client_session_manager_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main client controller for the EWallet Session Manager, accessible
                    to regular user api calls.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_client_session_manager_controller_specified()
        handlers = {
            'action': self.client_session_manager_action_controller,
            'event': self.client_session_manager_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def system_session_manager_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main system controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_controller_specified()
        handlers = {
            'action': self.system_session_manager_action_controller,
            'event': self.system_session_manager_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def session_manager_controller(self, *args, **kwargs):
        '''
        [ NOTE   ]: Main controller for the EWallet Session Manager.
        '''
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_controller_specified()
        handlers = {
            'client': self.client_session_manager_controller,
            'system': self.system_session_manager_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_could_not_view_transfer_sheet_record(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_transfer_sheet(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet. '\
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_contact_record(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view contact record. '\
                       'Details : {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_contact_list(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not view active contact list. '\
                       'Details : {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_stop_credit_clock_timer(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not stop credit clock timer. '\
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_resume_credit_clock_timer(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not resume credit clock timer. '\
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_start_credit_clock_timer(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not start credit clock timer. '\
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_edit_user_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not edit user account. '\
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_transfer_credits_to_partner(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not transfer credits to partner. '\
                       'Details : {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_contact_list(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_contact_record(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new contact record. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_convert_credit_clock_to_credits(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not convert credit clock time to credits. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_convert_credits_to_credit_clock(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not convert ewallet credits to credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_pay_partner_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not pay partner account in EWallet Session. '
                       'Details : {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_supply_user_credit_ewallet(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not supply user credit wallet with credits in EWallet Session. '
                       'Details : {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_login_user_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not login user account in EWallet Session. '
                       'Details : {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_user_account(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new user account in EWallet Session. '
                       'Details : {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_request_session_token(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not request session token. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_worker_not_found_in_pool_by_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Worker not found in pool by id. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_worker_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Could not fetch worker id. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_ctoken_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'No client token found. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_stoken_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'No session token found. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_worker_id_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'No worker id found. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_available_session_worker_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'No available session worker found in pool. '
                       'Details: {}'.format(args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_multiple_session_tokens_found_by_label(self, session_token, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Multiple session tokens found by label {}. '
                       'Fetching first. Details: {}'.format(session_token, args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_multiple_client_tokens_found_by_label(self, client_id, *args):
        instruction_set_response = {
            'failed': True,
            'warning': 'Multiple client tokens found by label {}. '
                       'Fetching first. Details: {}'.format(client_id, args)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_recover_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not recover user account. '
                       'Details: {}, {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_pause_credit_clock_timer(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not pause credit clock timer in session {}. '\
                       'Details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_cleanup_ewallet_session_workers(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Could not cleanup ewallet session workers. Instruction set details {}.'\
                       .format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_expired_ewallet_sessions_from_worker(self, session_worker):
        instruction_set_response = {
            'failed': True,
            'warning': 'Could not fetch expired ewallet sessions from worker {}.'\
                       .format(session_worker),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_interogate_worker_session_pool(self, session_worker):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not interogate session worker '\
                       '{} ewallet session pool.'.format(session_worker),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_expired_ewallet_sessions_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'No expired ewallet sessions found. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_expired_ewallet_sessions(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch expired ewallet sessions. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_sweep_cleanup_ewallet_sessions(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not sweep clean ewallet sessions. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_clean_ewallet_session(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not clean ewallet session. '\
                       'Details : {}'.format({
                           'id': ewallet_session.fetch_active_session_id(),
                           'reference': ewallet_session.fetch_active_session_reference(),
                       }),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_cleanup_target_ewallet_session(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not clean up target ewallet '\
                       'session. Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_cleanup_ewallet_session_worker(self, session_worker):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not cleanup ewallet session worker {}.'\
                       .format(session_worker),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_session_worker_pool(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch session worker pool. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fulfill_client_id_request(self):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fulfill '\
                       'client id request.'
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_interogate_ewallet_session_workers(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not interogate ewallet session workers. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_ewallet_session_manager_worker_pool_empty(self):
        instruction_set_response = {
            'failed': True,
            'warning': 'Ewallet session manager worker pool empty.'
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_ewallet_session_found_by_id(self, ewallet_session_id):
        instruction_set_response = {
            'failed': True,
            'warning': 'No ewallet session found by id {}.'.format(ewallet_session_id),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_ewallet_session(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new ewallet session. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_ewallet_session_worker_assignment_failure(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not assign ewallet session to session manager worker. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_no_ewallet_session_found_by_id(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'No ewallet session found by id. Instruction set details : {}'\
                       .format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_interogate_ewallet_session(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not interogate ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_fetch_ewallet_session(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch ewallet session. '\
                       'Instruction set details : {}'.format(instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_logout_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not logout user account in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_active_session_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch active session user account in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_user_logout_records(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view user account logout records in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_user_login_records(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view user login records in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink user account in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_credit_clock(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit ewallet credit clock in ewallet session {}. '\
                       'Instruction set details :  {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_credit_ewallet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit ewallet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_conversion_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch conversion sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_contact_list(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink contact list in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_time_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink time sheet in ewallet session {}. '\
                       'Instruction Set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_conversion_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink conversion sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_invoice_sheet(self, ewallet_session, instruction_set):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink invoice sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_contact_list_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink contact list record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_time_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink time sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_conversion_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink conversion sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_invoice_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink invoice sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_unlink_transfer_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_contact_list(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch contact list in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_cound_not_switch_contact_list(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch contact list in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_time_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch time sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_invoice_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit ewallet invoice sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_transfer_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch transfer sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_credit_clock(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit clock in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_switch_credit_ewallet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit ewallet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_time_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new time sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_invoice_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new invoice sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_transfer_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Could not create new transfer sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_credit_clock(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new credit clock in ewallet session {}.'\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_invoice_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view invoice sheet record in session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_invoice_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view invoice sheet in session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_credit_clock(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view credit clock in session {}. ' \
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response


    def warning_could_not_view_credit_ewallet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view credit ewallet in session {}. ' \
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_conversion_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view conversion sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_time_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view time sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_time_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view time sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    # ERRORS

    def error_could_not_fetch_session_token_by_label(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch session token map. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_client_session_token_map(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch client session token map. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_create_client_session_token_map(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not create client session token map. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_values_for_worker_pool_entry(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid values for worker pool entry. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_create_new_ewallet_session(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not create new EWallet session. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_client_session_token_pair(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid client session token pair. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_map_client_session_tokens(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not create client session token map. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_session_worker_instruction_response(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Software error. '
                     'Invalid session worker instruction response. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_worker_id_by_client_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch session worker id by given client id. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_worker_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid worker id. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_client_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid client id. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_client_token(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid client token. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_worker_pool_entry_by_id(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch worker pool entry by worker id. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_worker_to_pool(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set worker to session manager worker pool. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_worker_pool(self, worker_pool, args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set worker pool : {}'.format(worker_pool),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_worker_pool_empty(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Session manager worker pool empty. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_generate_session_worker_identifier(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not generate EWallet Session '
                     'Worker identifier. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_generate_id_for_entity_set(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not generate unique identifier '
                     'for entity set. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_client_token_by_label(self, client_id, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch client token by label {}. '
                     'Details: {}'.format(client_id, args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_stoken_pool(self, session_token, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set session token {} to pool. '
                     'Details: {}'.format(session_token, args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_client_id(self, client_id, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid client id {}.'
                     'Details: {}'.format(client_id, args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_token_from_label(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch session token from label. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_session_token_validity_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform session token validity check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_session_token_unlink_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform session token unlink check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_session_token_expiration_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform session token validity check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_client_token_validity_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform client token validity check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_client_token_unlink_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform client token unlink check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_perform_client_token_expiration_check(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not perform client token expiration check. '
                     'Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_client_token_from_label(self, client_id, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch client token from pool by client id {}. '
                     'Details: {}'.format(client_id, args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_config_handler_found(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No configuration handler found. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_id_found(self, instruction_set, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No client id found. '\
                     'Instruction set details : {}, {}.'\
                     .format(instruction_set, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_session_found(self, instruction_set, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No EWallet session found. '\
                     'Instruction set details : {}, {}.'\
                     .format(instruction_set, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_session_manager_worker_found(self, instruction_set, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No EWallet session manager worker found. '\
                     'Instruction set details : {}, {}.'\
                     .format(instruction_set, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_mapped_session_worker_found_for_client_id(self, client_id, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No mapped session worker found for client id {}. '
                     'Details: {}'.format(client_id, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_instruction_set_required_data(self, instruction_set, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid EWallet session manager instruction set '
                     'required data. Instruction set details : {}, {}'\
                     .format(instruction_set, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_session_manager_controller_specified(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid EWallet controller. Details: {}'.format(args)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_worker_pool(self, *args, **kwargs):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch session worker pool. '\
                     'Instruction set details : {}, {}'.format(kwargs, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_scrape_ewallet_session(self, ewallet_session, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not scrape ewallet session {}. Details: {}'\
                     .format(ewallet_session, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_sessions_found(self, instruction_set, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet sessions found. '
                     'Instruction set details : {}, {}'\
                     .format(instruction_set, args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_worker_for_ewallet_session(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch session worker for '\
                     'ewallet session {}.'.format(ewallet_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_remove_ewallet_session_worker_from_pool(self, session_worker):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove ewallet session '\
                     'worker {} from session worker pool.'.format(session_worker),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_scrape_ewallet_session_worker(self, session_worker):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not scraper ewallet session '\
                     'worker {}.'.format(session_worker),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_vacant_session_workers_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No vacant session workers found. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_system_action_cleanup_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No system action cleanup target specified. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_set_client_pool(self, client_id):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not set client id {} to pool.'\
                     .format(client_id),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_spawn_new_ewallet_session(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not spawn new ewallet session. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_assign_worker_to_new_ewallet_session(self, new_session):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not assign session worker '\
                     'for new ewallet session {}.'.format(new_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_ewallet_session_manager_worker_pool_empty(self, *args):
        instruction_set_response = {
            'failed': True,
            'error': 'EWallet session manager worker pool empty. '
                     'Details: {}'.format(args),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_manager_worker_pool(self):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch ewallet '\
                     'session manager worker pool.',
        }
        log.warning(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_ewallet_session_id(self, ewallet_session_id):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid ewallet session id {}.'.format(ewallet_session_id),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_by_id(self, ewallet_session_id):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch ewallet session by id {}.'\
                     .format(ewallet_session_id),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_session_id_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet session id found. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_system_action_interogate_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No system action interogate target specified. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_unlink_time_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action unlink time target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_unlink_conversion_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action unlink conversion target specified. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_unlink_invoice_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No client action unlink invoice target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_unlink_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action unlink target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_unlink_transfer_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action unlink transfer target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_switch_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action switch target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_switch_credit_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action switch credit target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_new_time_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action new time target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_new_conversion_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action new conversion target specified. Instruction set details : {} '\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_new_invoice_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action new invoice target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_new_transfer_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action new transfer target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_new_credit_target_specified(self, instruction_set):
        instruction_set_response = {
                'failed': True,
                'error': 'No client action new credit target specified. Instruction set details : {}'\
                         .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_view_invoice_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action view invoice target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_view_credit_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action view credit target specified. Instruction set details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_edit_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action edit target specified. Instruction set details : {}'\
                     .format(instruction_set)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_view_conversion_target_specified(self, instruction_set):
        log.error()
        instruction_set_response = {
            'failed': True,
            'error': 'No client action view conversion target specified. Instruction set details : {}'\
                     .format(instruction_set)
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_client_action_view_transfer_target_specified(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client action view transfer target specified. Instruction Set Details : {}'\
                     .format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_conversion_credit_clock_time_specified(self, ewallet_session, instruction_set):
        log.error(
            'No conversion credit clock time specified in ewallet session {}. Details : {}'\
            .format(ewallet_session, instruction_set)
        )
        return False

    def error_no_client_action_transfer_target_specified(self, instruction_set):
        log.error(
            'No client action transfer target specified. Details : {}'\
            .format(instruction_set)
        )
        return False

    def error_no_client_action_new_contact_target_specified(self, instruction_set):
        log.error(
            'No client action new contact target specified. Details : {}'\
            .format(instruction_set)
        )
        return False

    def error_no_client_action_view_contact_target_specified(self, instruction_set):
        log.error(
            'No client action View Contact target specified. Details : {}'.format(instruction_set)
        )
        return False

    def error_no_client_action_view_target_specified(self, instruction_set):
        log.error(
            'No client action View target specified. Details : {}'.format(instruction_set)
        )
        return False

    def error_no_client_action_start_target_specified(self):
        log.error('No client action start target specified.')
        return False

    def error_no_conversion_credit_count_specified(self, ewallet_session, instruction_set):
        log.error(
                'No conversion credit count specified for ewallet session {}. '\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def error_no_client_action_convert_target_specified(self):
        log.error('No client action convert target specified.')
        return False

    def error_no_client_action_supply_target_specified(self):
        log.error('No client action supply target specified.')
        return False

    def error_cound_not_set_client_pool(self, client_id):
        log.error(
                'Something went wrong. Could not set client id {} to session manager client pool.'\
                .format(client_id)
                )
        return False

    def error_invalid_session_token(self, session_token):
        log.error('Invalid session token {}.'.format(session_token))
        return False

    def error_no_client_action_new_target_specified(self):
        log.error('No aclient action new target specified.')
        return False


    def error_no_worker_found_assigned_to_session(self, ewallet_session):
        log.error('No worker assigned to session {}.'.format(ewallet_session))
        return False

    def error_could_not_update_client_worker_map(self, client_id, assigned_worker):
        log.error(
                'Something went wrong. Could not update session manager client '
                'worker map with values { {}:{} }.'.format(client_id, assigned_worker)
                )
        return False

    def error_could_not_assign_worker_to_new_ewallet_sesion(self, new_session):
        log.error(
                'Something went wrong. Could not assign worker new session {}.'\
                .format(new_session)
                )
        return False

    def error_could_not_generate_ewallet_session_token(self, new_session):
        log.error(
                'Somtehing went wrong. Could not generate session token for new session {}.'\
                .format(new_session)
                )
        return False

    def error_could_not_map_client_id_to_session_token(self, client_id, session_token):
        log.error(
                'Something went wrong. Could not map client id {} with session token {}.'\
                .format(client_id, session_token)
                )
        return False

    def error_could_not_fetch_socket_handler(self):
        log.error('Something went wrong. Could not fetch socket handler.')
        return False

    def error_could_not_fetch_socket_handler_required_values(self):
        log.error('Could not fetch required values for EWallet Socket Handler.')
        return False

    def error_could_not_spawn_socket_handler(self):
        log.error('Could not spawn new EWallet Socket Handler.')
        return False

    def error_could_not_unset_socket_handler(self, socket_handler):
        log.error('Something went wrong. Could not unset socket handler {}.'.format(socket_handler))
        return False

    def error_could_not_set_socket_handler(self, socket_handler):
        log.error('Something went wrong. Could not set socket handler {}.'.format(socket_handler))
        return False

    def error_no_system_action_start_target_specified(self, **kwargs):
        log.error('No system action start target specified.')
        return False

    def error_no_command_chain_reply_socket_handler_thread_found(self, thread_map):
        log.error(
                'No command chain reply socket handler thread found in thread map : {}'\
                    .format(thread_map)
                )
        return False

    def error_could_not_set_reply_thread_to_socket_handler_map(self, reply_thread):
        log.error(
                'Something went wrong. Could not set reply thread {} to socket handler thread map.'\
                    .format(reply_thread)
                )
        return False

    def error_could_not_set_listener_thread_to_socket_handler_map(self, listener_thread):
        log.error(
                'Something went wrong. Could not set instruction listener socket handler thread {} to map.'\
                    .format(listener_thread)
                )
        return False

    def error_no_socket_handler_thread_map_found(self):
        log.error('No socket handler thread map found.')
        return False

    def error_no_instruction_set_socket_handler_thread_found(self, thread_map):
        log.error(
                'No instruction set listening socket handler thread found in thread map : {}'\
                    .format(str(thread_map))
                )
        return False

    def error_no_instruction_set_listener_socket_handler_found(self):
        log.error('No instruction set listener socket handler found for session manager.')
        return False

    def error_no_command_chain_reply_socket_handler_found(self):
        log.error('No command chain reply socket handler found for session manager.')
        return False

    def error_invalid_listener_socket_handler(self, socket_handler):
        log.error(
                'Invalid listener socket handler {} type {}.'.format(
                    str(socket_handler), type(socket_handler)
                    )
                )
        return False

    def error_invalid_reply_socket_handler(self, socket_handler):
        log.error(
                'Invalid reply socket handler {} type {}.'.format(
                    str(socket_handler), type(socket_handler)
                    )
                )
        return False

    def error_invalid_socket_port(self, socket_port):
        log.error(
                'Invalid socket port {} type {}.'.format(
                    str(socket_port), type(socket_port)
                    )
                )
        return False

    def error_no_worker_pool_found(self):
        log.error('No worker pool found.')
        return False

    def error_no_client_pool_found(self):
        log.error('No client pool found.')
        return False

    def error_invalid_worker_pool(self, worker_pool):
        log.error(
                'Invalid worker pool {} type {}.'.format(
                    str(worker_pool), type(worker_pool)
                    )
                )
        return False

    def error_client_worker_map_not_found(self):
        log.error('No client worker map found.')
        return False

    def error_invalid_client_pool(self, client_pool):
        log.error(
                'Invalid client pool {} type {}.'.format(
                    str(client_pool), type(client_pool)
                    )
                )
        return False

    def error_invalid_client_worker_map(self, cw_map):
        log.error(
                'Invalid client worker map {} type {}.'.format(
                    str(cw_map), type(cw_map),
                    )
                )
        return False

    def error_could_not_update_worker_pool(self, worker):
        log.error(
                'Something went wrong. Could not update worker pool with new worker {}.'\
                .format(worker)
                )


    def error_could_not_update_client_pool(self, client):
        log.error(
                'Something went wrong. Could not update client pool with new client {}.'\
                .format(client)
                )
        return False

    def error_could_not_update_client_worker_session_map(self, values):
        log.error(
                'Something went wrong. Could not update client worker '
                'session map with values {}'.format(values)
                )
        return False

    def error_could_not_set_client_worker_map(self, cw_map):
        log.error('Something went wrong. Could not set client worker manp : {}'.format(cw_map))
        return False

    def error_no_system_action_open_target_specified(self):
        log.error('No system action open target specified.')
        return False

    def error_no_system_action_close_target_specified(self):
        log.error('No system action close target specified.')
        return False

    def error_no_system_action_new_specified(self):
        log.error('No system action new specified.')
        return False

    def error_no_client_request_specified(self):
        log.error('No client request specified.')
        return False

    def error_no_system_event_client_timeout_target_specified(self):
        log.error('No system event client timeout target specified.')
        return False

    def error_no_system_event_expire_specified(self):
        log.error('No system event expire specified.')
        return False

    def error_no_system_event_timeout_specified(self):
        log.error('No system event timeout specified.')
        return False

    def error_no_system_session_manager_event_specified(self):
        log.error('No system session manager event specified.')
        return False

    def error_no_client_session_manager_action_specified(self):
        log.error('No client session manager action specified.')
        return False

    def error_no_system_session_manager_action_specified(self):
        log.error('No system session manager action specified.')
        return False

    def error_no_client_session_manager_controller_specified(self):
        log.error('No client session manager controller specified.')
        return False

    def error_no_system_session_manager_controller_specified(self):
        log.error('No system session manager controller specified.')
        return False

    # DEBUG

    def debug_worker_unlocked(self, lock):
        log.debug(
            'Worker unlocked {} - PID: {} - '.format(lock.value, os.getpid())
        )

    def debug_worker_locked(self, lock):
        log.debug(
            'Worker locked {} - PID: {} - '.format(lock.value, os.getpid())
        )

    def debug_delegating_instruction_set(self, lock_value, instruction_set):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Delegating instruction set {}.'.format(
                lock_value, os.getpid(), instruction_set
            )
        )

    def debug_waiting_for_unlock_to_delegate_instruction_set(self, lock_value, instruction_set):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Waiting for unlock event to delegate instruction set {}.'
            .format(
                lock_value, os.getpid(), instruction_set
            )
        )

    def debug_waiting_for_worker_unlock_to_read_response(self, lock_value):
        log.debug(
            'Worker locked - {} - PID: {} - '
            'Waiting for unlock event to read instruction set response.'.format(
                lock_value, os.getpid(),
            )
        )

    def debug_received_instruction_set_response(self, lock_value, response):
        log.debug(
            'Worker unlocked - {} - PID: {} - '
            'Received instruction set response {}.'.format(
                lock_value, os.getpid(), response
            )
        )

# CODE DUMP

    def action_stop_credit_clock_timer(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        stop_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='stop',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_stop_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not stop_timer or isinstance(stop_timer, dict) and \
            stop_timer.get('failed') else stop_timer

    def action_logout_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        logout_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='logout',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_logout_user_account(
            ewallet_session, instruction_set
        ) if not logout_account or logout_account.get('failed') \
            else logout_account

    def action_view_logout_records(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        user_logout_records = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='logout',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_user_logout_records(
            ewallet_session, instruction_set
        ) if not user_logout_records or user_logout_records.get('failed') \
            else user_logout_records

    def action_view_login_records(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        user_login_records = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='login',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_user_login_records(
            ewallet_session, instruction_set
        ) if not user_login_records or user_login_records.get('failed') \
            else user_login_records

    def action_unlink_credit_clock(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'credit'
        )
        unlink_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='credit_clock',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_credit_clock(
            ewallet_session, instruction_set
        ) if not unlink_credit_clock or unlink_credit_clock.get('failed') \
            else unlink_credit_clock

    def action_unlink_credit_ewallet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'credit'
        )
        unlink_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='credit_wallet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_credit_ewallet(
            ewallet_session, instruction_set
        ) if not unlink_credit_ewallet or unlink_credit_ewallet.get('failed') \
            else unlink_credit_ewallet

    def action_unlink_contact_list(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'contact'
        )
        unlink_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='contact',
            contact='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_contact_list(
            ewallet_session, instruction_set
        ) if not unlink_contact_list or unlink_contact_list.get('failed') \
            else unlink_contact_list

    def action_unlink_time_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'time'
        )
        unlink_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='time',
            time='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_time_sheet(
            ewallet_session, instruction_set
        ) if not unlink_time_sheet or unlink_time_sheet.get('failed') \
            else unlink_time_sheet

    def action_unlink_conversion_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'conversion'
        )
        unlink_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='conversion',
            conversion='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_conversion_sheet(
            ewallet_session, instruction_set
        ) if not unlink_conversion_sheet or unlink_conversion_sheet.get('failed') \
            else unlink_conversion_sheet

    def action_unlink_invoice_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'invoice'
        )
        unlink_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='invoice',
            invoice='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_invoice_sheet(
            ewallet_session, instruction_set
        ) if not unlink_invoice_sheet or unlink_invoice_sheet.get('failed') \
            else unlink_invoice_sheet

    def action_unlink_transfer_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'transfer'
        )
        unlink_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='transfer',
            transfer='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_transfer_sheet(
            ewallet_session, instruction_set
        ) if not unlink_transfer_sheet or unlink_transfer_sheet.get('failed') \
            else unlink_transfer_sheet

#   @pysnooper.snoop()
    def action_unlink_contact_list_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'contact'
        )
        unlink_contact_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='contact',
            contact='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_contact_list_record(
            ewallet_session, instruction_set
        ) if not unlink_contact_record or unlink_contact_record.get('failed') \
            else unlink_contact_record

    def action_unlink_time_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'time'
        )
        unlink_time_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='time',
            time='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_time_sheet_record(
            ewallet_session, instruction_set
        ) if not unlink_time_record or unlink_time_record.get('failed') \
            else unlink_time_record

    def action_unlink_conversion_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'conversion'
        )
        unlink_conversion_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='conversion',
            conversion='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_conversion_sheet_record(
            ewallet_session, instruction_set
        ) if not unlink_conversion_record or unlink_conversion_record.get('failed') \
            else unlink_conversion_record

    def action_unlink_invoice_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'invoice'
        )
        unlink_invoice_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='invoice',
            invoice='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_invoice_sheet_record(
            ewallet_session, instruction_set
        ) if not unlink_invoice_record or unlink_invoice_record.get('failed') \
            else unlink_invoice_record

    def action_unlink_transfer_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink', 'transfer'
        )
        unlink_transfer_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='transfer',
            transfer='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_transfer_sheet_record(
            ewallet_session, instruction_set
        ) if not unlink_transfer_record or unlink_transfer_record.get('failed') \
            else unlink_transfer_record

    def action_switch_contact_list(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch'
        )
        switch_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='contact_list',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_contact_list(
            ewallet_session, instruction_set
        ) if not switch_contact_list or switch_contact_list.get('failed') \
            else switch_contact_list

    def action_switch_time_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch'
        )
        switch_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='time_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_time_sheet(
            ewallet_session, instruction_set
        ) if not switch_time_sheet or switch_time_sheet.get('failed') else \
        switch_time_sheet

    def action_switch_conversion_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch'
        )
        switch_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='conversion_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_conversion_sheet(
            ewallet_session, instruction_set
        ) if not switch_conversion_sheet or switch_conversion_sheet.get('failed') \
        else switch_conversion_sheet

    def action_switch_invoice_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch'
        )
        switch_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='invoice_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_invoice_sheet(
            ewallet_session, instruction_set
        ) if not switch_invoice_sheet or switch_invoice_sheet.get('failed') \
        else switch_invoice_sheet

    def action_switch_transfer_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch'
        )
        switch_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='transfer_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_transfer_sheet(
            ewallet_session, instruction_set
        ) if not switch_transfer_sheet or switch_transfer_sheet.get('failed') \
        else switch_transfer_sheet

    def action_switch_credit_clock(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch', 'credit'
        )
        switch_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='credit_clock',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_credit_clock(
            ewallet_session, instruction_set
        ) if not switch_credit_clock or switch_credit_clock.get('failed') \
        else switch_credit_clock

    def action_switch_credit_ewallet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch', 'credit'
        )
        switch_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='credit_ewallet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_credit_ewallet(
            ewallet_session, instruction_set
        ) if not switch_credit_ewallet or switch_credit_ewallet.get('failed') \
        else switch_credit_ewallet

    def action_new_invoice_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'invoice'
        )
        new_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='invoice_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_invoice_sheet(
            ewallet_session, instruction_set
        ) if new_invoice_sheet.get('failed') else new_invoice_sheet

    # TODO - Deprecated
    def action_recover_user_account(self, ewallet_session, instruction_set):
        log.debug('TODO - Deprecated')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'recover',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        recover_user_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='recover', recover='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_recover_user_account(
            ewallet_session, instruction_set
        ) if not recover_user_account or recover_user_account.get('failed') \
            else recover_user_account

    # TODO - Deprecated
#   @pysnooper.snoop('logs/ewallet.log')
    def action_unlink_user_account(self, ewallet_session, instruction_set):
        log.debug('TODO - Deprecated')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'unlink',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        unlink_user_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='unlink', unlink='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_unlink_user_account(
            ewallet_session, instruction_set
        ) if not unlink_user_account or unlink_user_account.get('failed') \
            else unlink_user_account

    def action_switch_active_session_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'switch',
        )
        active_session_user = ewallet_session.fetch_active_session_user()
        switch_user_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='switch', switch='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_switch_active_session_user_account(
            ewallet_session, instruction_set
        ) if not switch_user_account or switch_user_account.get('failed') \
            else switch_user_account

    def action_new_time_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'time'
        )
        new_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='time_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_time_sheet(
            ewallet_session, instruction_set
        ) if new_time_sheet.get('failed') else new_time_sheet

    def action_new_conversion_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'conversion'
        )
        new_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='conversion_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_conversion_sheet(
            ewallet_session, instruction_set
        ) if new_conversion_sheet.get('failed') else new_conversion_sheet

    def action_new_transfer_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'transfer'
        )
        new_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='transfer_sheet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_transfer_sheet(
            ewallet_session, instruction_set
        ) if new_transfer_sheet.get('failed') else new_transfer_sheet

    def action_new_credit_clock(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'credit'
        )
        new_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='credit_clock',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_credit_clock(
            ewallet_session, instruction_set
        ) if new_credit_clock.get('failed') else new_credit_clock

    def action_new_credit_ewallet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'credit'
        )
        new_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='credit_wallet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_credit_ewallet(
            ewallet_session, instruction_set
        ) if new_credit_ewallet.get('failed') else new_credit_ewallet

    def action_view_invoice_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'invoice'
        )
        view_invoice_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='invoice',
            invoice='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_invoice_sheet_record(
            ewallet_session, instruction_set
        ) if view_invoice_record.get('failed') else view_invoice_record

    def action_view_invoice_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'invoice'
        )
        view_invoice_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='invoice',
            invoice='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_invoice_sheet(
            ewallet_session, instruction_set
        ) if view_invoice_sheet.get('failed') else view_invoice_sheet

    def action_view_credit_clock(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'credit'
        )
        view_credit_clock = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='credit_clock',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_credit_clock(
            ewallet_session, instruction_set
        ) if view_credit_clock.get('failed') else view_credit_clock

    def action_view_credit_ewallet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'credit'
        )
        view_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='credit_wallet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_credit_ewallet(
            ewallet_session, instruction_set
        ) if view_credit_ewallet.get('failed') else view_credit_ewallet

    def action_view_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view',
        )
        view_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_user_account(
            ewallet_session, instruction_set
        ) if view_account.get('failed') else view_account

    def action_view_conversion_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'conversion',
        )
        view_conversion_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='conversion',
            conversion='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_conversion_sheet_record(
            ewallet_session, instruction_set
        ) if not view_conversion_record or \
        isinstance(view_conversion_record, dict) and \
        view_conversion_record.get('failed') else view_conversion_record

    def action_view_conversion_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'conversion',
        )
        view_conversion_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='conversion',
            conversion='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_conversion_sheet(
            ewallet_session, instruction_set
        ) if view_conversion_sheet.get('failed') else view_conversion_sheet

    def action_view_time_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'time',
        )
        view_time_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='time',
            time='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_time_sheet_record(
            ewallet_session, instruction_set
        ) if view_time_record.get('failed') else view_time_record

    def action_view_time_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'time',
        )
        view_time_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='time',
            time='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_time_sheet(
            ewallet_session, instruction_set
        ) if view_time_sheet.get('failed') else view_time_sheet

    def action_view_transfer_sheet_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'transfer',
        )
        view_transfer_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='transfer',
            transfer='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_transfer_sheet_record(
            ewallet_session, instruction_set
        ) if view_transfer_record.get('failed') else view_transfer_record

    def action_view_transfer_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'transfer',
        )
        view_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='transfer',
            transfer='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_transfer_sheet(
            ewallet_session, instruction_set
        ) if view_transfer_sheet.get('failed') else view_transfer_sheet


