from ewallet import EWallet
from base.config import Config
from base.res_utils import ResUtils
from base.ewallet_worker import EWalletWorker
from base.socket_handler import EWalletSocketHandler

import time
import datetime
import random
import string
import hashlib
import logging
import datetime
import pysnooper
import threading

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletSessionManager():

    socket_handler = None
    worker_pool = []
    client_pool = []
    client_worker_map = {}

    def __init__(self, *args, **kwargs):
        self.socket_handler = kwargs.get('socket_handler') or self.open_ewallet_session_manager_sockets()
        self.worker_pool = kwargs.get('worker_pool') or []
        self.client_pool = kwargs.get('client_pool') or []
        self.client_worker_map = kwargs.get('client_worker_map') or {}

    # FETCHERS

    # TODO - Fetch configuration values for config file
    def fetch_session_token_default_prefix(self):
        log.debug('')
        return 'ewsm-st'

    # TODO - Fetch configuration values for config file
    def fetch_session_token_default_length(self):
        log.debug('')
        return 20

    def fetch_ewallet_session_assigned_worker(self, ewallet_session):
        log.debug('')
        worker_pool = self.worker_pool
        if not worker_pool:
            return self.error_worker_pool_empty()
        worker_set = [item for item in worker_pool if ewallet_session in item.session_pool]
        return self.error_no_worker_found_assigned_to_session(ewallet_session)\
                if not worker_set else worker_set[0]

    def fetch_first_available_worker(self):
        log.debug('')
        pool = self.worker_pool
        for item in pool:
            if item.session_worker_state_code in [0, 1]:
                return item
        return False

    def fetch_ewallet_session_manager_socket_handler(self):
        log.debug('')
        return self.socket_handler

    # TODO - Fetch configuration values for config file
    def fetch_socket_handler_default_address(self):
        log.debug('')
        return '127.0.0.1'

    # TODO - Fetch configuration values for config file
    def fetch_client_id_default_length(self):
        log.debug('')
        return 20

    # TODO - fetch data from configurations file
    def fetch_client_id_default_prefix(self):
        log.debug('')
        return 'ewsm-uid'

    # TODO : Fetch port number from configurations file
    def fetch_default_ewallet_command_chain_reply_port(self):
        log.debug('')
        return 8081

    # TODO : Fetch port number from configurations file
    def fetch_default_ewallet_command_chain_instruction_port(self):
        log.debug('')
        return 8080

    def fetch_worker_pool(self):
        log.debug('')
        return self.worker_pool

    def fetch_client_pool(self):
        log.debug('')
        return self.client_pool

    def fetch_client_session_map(self):
        log.debug('')
        return self.client_worker_map

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

    def set_worker_to_pool(self, worker):
        log.debug('')
        try:
            self.worker_pool.append(worker)
        except:
            return self.error_could_not_set_worker_pool(worker)
        return True

    '''
    [ NOTE   ]: Overrides socket_handler attribute with a None value.
    [ RETURN ]: (True | False)
    '''
    def unset_socket_handler(self):
        log.debug('')
        if self.socket_handler in (None, False):
            return False
        try:
            self.socket_handler = None
        except:
            return self.error_could_not_unset_socket_handler(self.socket_handler)
        return True

    '''
    [ NOTE   ]: Overrides socket_handler attribute with new EWalletSocketHandler object.
    [ RETURN ]: (True | False)
    '''
    def set_socket_handler(self, socket_handler):
        log.debug('')
        try:
            self.socket_handler = socket_handler
        except:
            return self.error_could_not_set_socket_handler(socket_handler) #
        return True

    '''
    [ NOTE   ]: Overrides entire worker pool.
    [ INPUT  ]: [worker1, worker2, ...]
    [ RETURN ]: (True | False)
    '''
    def set_worker_pool(self, worker_pool, **kwargs):
        log.debug('')
        try:
            self.worker_pool = worker_pool
        except:
            return self.error_could_not_set_worker_pool(worker_pool)
        return True

    '''
    [ NOTE   ]: Overrides entire client pool.
    [ INPUT  ]: [user_id1, user_id2, ...]
    [ RETURN ]: (True | False)
    '''
    def set_client_pool(self, client_pool, **kwargs):
        log.debug('')
        try:
            self.client_pool = client_pool
        except:
            return self.error_coult_not_set_client_pool(client_pool)
        return True

    '''
    [ NOTE   ]: Overrides entire client/worker map.
    [ INPUT  ]: {user_id: worker, user_id: worker, ...}
    [ RETURN ]: (True | False)
    '''
    def set_client_worker_session_map(self, cw_map):
        log.debug('')
        try:
            self.client_worker_map = cw_map
        except:
            return self.error_could_not_set_client_worker_map(cw_map)
        return True

    '''
    [ NOTE   ]: Adds new work to worker pool stack.
    [ INPUT  ]: EwalletWorker object.
    [ RETURN ]: (True | False)
    '''
    def set_to_worker_pool(self, worker, **kwargs):
        log.debug('')
        try:
            self.worker_pool.append(worker)
        except:
            return self.error_could_not_update_worker_pool(worker)
        return True

    '''
    [ NOTE   ]: Adds new client user id to client pool stack.
    [ INPUT  ]: User ID
    [ RETURN ]: (True | False)
    '''
    def set_to_client_pool(self, client, **kwargs):
        log.debug('')
        try:
            self.client_pool.append(client)
        except:
            return self.error_could_not_update_client_pool(client)
        return True

    '''
    [ NOTE   ]: Adds new entry to client/worker map including entry in workers user_id/session token map.
    [ INPUT  ]: User ID, Session Token, EwalletWorker object.
    [ RETURN ]: (True | False)
    '''
    def set_to_client_worker_session_map(self, user_id, session_token, worker):
        log.debug('')
        values = {
                'session_manager': {user_id: worker},
                'worker': {user_id: session_token},
                }
        try:
            self.client_worker_map.update(values['session_manager'])
            worker.token_session_map.update(values['worker'])
        except:
            return self.error_could_not_update_client_worker_session_map(values)
        return True

    # UPDATERS

#   def update_client_worker_map(self, client_id, assigned_worker):
#       log.debug('')
#       try:
#           self.client_worker_map.update({client_id: assigned_worker})
#       except:
#           return self.error_could_not_update_client_worker_map(client_id, assigned_worker)
#       return True

    '''
    [ NOTE   ]: Overrides Session Manager Worker Pool and checks for type errors.
    [ INPUT  ]: [worker1, worker2, ...]
    [ RETURN ]: (True | False)
    '''
    def update_worker_pool(self, worker_pool):
        if not worker_pool:
            return self.error_no_worker_pool_found()
        return self.error_invalid_worker_pool(worker_pool) \
                if not isinstance(worker_pool, list) else \
                self.set_worker_pool(worker_pool)

    '''
    [ NOTE   ]: Overrides Session Manager Client Pool and checks for type errors.
    [ INPUT  ]: [user_id1, user_id2, ...]
    [ RETURN ]: (True | False)
    '''
    def update_client_pool(self, client_pool):
        if not client_pool:
            return self.error_client_pool_not_found()
        return self.error_invalid_client_pool(client_pool) \
                if not isinstance(client_pool, list) else \
                self.set_client_pool(client_pool)

    '''
    [ NOTE   ]: Overrides Session Manager Client Worker map and checks for type errors.
    [ INPUT  ]: {user_id: session_token, ...}
    [ RETURN ]: (True | False)
    '''
    def update_client_worker_map(self, cw_map):
        if not cw_map:
            return self.error_client_worker_map_not_found()
        return self.error_invalid_client_worker_map(cw_map) \
                if not isinstance(cw_map, dict) else \
                self.set_client_worker_session_map(cw_map)

    # CHECKERS

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

    '''
    [ NOTE   ]: Perform port number validity checks and creates a EWallet Socket Handler object.
    [ INPUT  ]: In port number, Out port number
    [ RETURN ]: EWalletSocketHandler object.
    '''
    def spawn_ewallet_session_manager_socket_handler(self, in_port, out_port):
        log.debug('')
        if not isinstance(in_port, int) or not isinstance(out_port, int):
            return self.error_invalid_socket_port(in_port, out_port)
        return EWalletSocketHandler(
                session_manager=self, in_port=in_port, out_port=out_port,
                host=self.fetch_socket_handler_default_address()
                )

    def spawn_ewallet_session_worker(self):
        log.debug('')
        new_worker = EWalletWorker()
        return new_worker

    # TODO
    def spawn_ewallet_session(self):
        pass

    # SCRAPERS

    # TODO
    def scrape_ewallet_session_worker(self):
        pass
    def scrape_ewallet_session(self):
        pass

    # MAPPERS

    def map_client_id_to_worker(self, client_id, assigned_worker):
        log.debug('')
        update_map = self.update_client_worker_map({client_id: assigned_worker})
        return update_map or False

    def map_client_id_to_session_token(self, client_id, session_token, assigned_worker, ewallet_session):
        log.debug('')
        update_map = assigned_worker.main_controller(
                controller='system', ctype='action', action='add', add='session_map',
                client_id=client_id, session_token=session_token, session=ewallet_session
                )
        return update_map or False

    def map_client_id_to_ewallet_session(self, client_id, session_token, assigned_worker, ewallet_session):
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

    # VALIDATORS

    def validate_client_id_prefix(self, client_id):
        log.debug('')
        default_prefix = self.fetch_client_id_default_prefix()
        return False if client_id[0] != default_prefix else True

    def validate_client_id_length(self, client_id):
        log.debug('')
        default_length = self.fetch_client_if_default_length()
        return False if len(client_id[1]) is not default_length else True

    # TODO
    def validate_client_id_timestamp(self, client_id):
        log.debug('')
        time_stamp = client_id[2]
        return True

    def validate_client_id(self, client_id):
        log.debug('')
        client_id_segmented = client_id.split(':')
        if len(client_id_segmented) != 3:
            return self.error_invalid_client_id(client_id)
        checks = {
                'prefix': self.validate_client_id_prefix(segmented_client_id),
                'length': self.validate_client_id_length(segmented_client_id),
                'timestamp': self.validate_client_id_timestamp(segmented_client_id),
                }
        return False if False in checks.values() else True

    # CREATORS

    def create_new_ewallet_session(self):
        log.debug('')
        return EWallet()

    # GENERAL

    def assign_new_ewallet_session_to_worker(self, new_session):
        log.debug('')
        worker = self.fetch_first_available_worker()
        if not worker:
            self.session_manager_controller(
                controller='system', ctype='action', action='new', new='worker'
            )
            worker = self.fetch_first_available_worker()
        assign_worker = worker.main_controller(
            controller='system', ctype='action', action='add', add='session',
            session=new_session
            )
        return False if not assign_worker else worker

    '''
    [ NOTE   ]: Starts socket based command chain instruction set listener.
    [ NOTE   ]: Programs hangs here untill interrupt.
    [ RETURN ]: (True | False)
    '''
    def start_instruction_set_listener(self):
        log.debug('')
        socket_handler = self.fetch_ewallet_session_manager_socket_handler()
        if not socket_handler:
            return self.error_could_not_fetch_socket_handler()
        log.info(
                'Starting instruction set listener using socket handler values : {}.'\
                .format(
                    socket_handler.view_handler_values()
                    )
                )
        socket_handler.start_listener()
        return True

    '''
    [ NOTE   ]: Creates new EWalletSocketHandler object using default configuration values.
    [ RETURN ]: (EWalletSocketHandler object | False)
    '''
    def open_ewallet_session_manager_sockets(self, **kwargs):
        log.debug('')
        in_port = kwargs.get('in_port') or self.fetch_default_ewallet_command_chain_instruction_port()
        out_port = kwargs.get('out_port') or self.fetch_default_ewallet_command_chain_reply_port()
        if not in_port or not out_port:
            return self.error_could_not_fetch_socket_handler_required_values()
        _socket = self.spawn_ewallet_session_manager_socket_handler(in_port, out_port)
        return self.error_could_not_spawn_socket_handler() if not _socket else _socket

    '''
    [ NOTE   ]: Generates a new unique client id using default format and prefix.
    [ NOTE   ]: User ID follows the following format <prefix-string>:<code>:<timestamp>
    [ RETURN ]: User ID
    '''
    def generate_client_id(self):
        log.debug('')
        prefix = self.fetch_client_id_default_prefix()
        length = self.fetch_client_id_default_length()
        timestamp = str(time.time())
        uid_code = res_utils.generate_random_alpha_numeric_string(string_length=length)
        user_id = prefix + ':' + uid_code + ':' + timestamp
        return user_id

    def generate_ewallet_session_token(self):
        log.debug('')
        prefix = self.fetch_session_token_default_prefix()
        length = self.fetch_session_token_default_length()
        timestamp = str(time.time())
        st_code = res_utils.generate_random_alpha_numeric_string(string_length=length)
        session_token = prefix + ':' + st_code + ':' + timestamp
        return session_token

    # TODO
    def map_client_id_ewallet_session_token(self):
        pass
    def map_client_id_ewallet_sessions(self):
        pass

    # ACTIONS

    # TODO - Perform new worker checks
    def action_new_worker(self):
        log.debug('')
        _worker = self.spawn_ewallet_session_worker()
        return _worker

    # TODO
    def action_new_session(self):
        log.debug('')
        _session = self.spawn_ewallet_session()
        return _session

    # TODO
    def action_request_client_id(self):
        log.debug('')
        _client_id = self.generate_client_id()
        return _client_id

    def action_request_session_token(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found()
        client_id = kwargs['client_id']
        new_session = self.session_manager_controller(
            controller='system', ctype='action', action='new', new='session'
        )
        assigned_worker = self.fetch_ewallet_session_assigned_worker(new_session) or \
            self.assign_new_ewallet_session_to_worker(new_session)
        if not assigned_worker:
            return self.error_could_not_assign_worker_to_new_ewallet_session(new_session)
        session_token = self.generate_ewallet_session_token()
        if not session_token:
            return self.error_could_not_generate_ewallet_session_token(new_session)
        mapping = self.map_client_id_to_ewallet_session(
                client_id, session_token, assigned_worker, new_session
                )
        return self.error_could_not_map_client_id_to_session_token(client_id, session_token) \
                if not mapping else session_token

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

    # HANDLERS

    @pysnooper.snoop()
    def handle_system_action_new_session(self, **kwargs):
        log.debug('')
        new_session = self.create_new_ewallet_session()
        assign_worker = self.assign_new_ewallet_session_to_worker(new_session)
        return new_session or False

    '''
    [ NOTE   ]: Turn Session Manager into server listenning for socket based instructions.
    [ NOTE   ]: System hangs here until interrupt.
    [ RETURN ]: True
    '''
    def handle_system_action_start_instruction_listener(self, **kwargs):
        log.debug('')
        return self.start_instruction_set_listener()

    '''
    [ NOTE   ]: Create and setups Session Manager Socket Handler.
    [ RETURN ]: EWalletSocketHandler object.
    '''
    def handle_system_action_open_sockets(self, **kwargs):
        log.debug('')
        socket_handler = self.open_ewallet_session_manager_sockets(**kwargs)
        set_socket_handler = self.set_socket_handler(socket_handler)
        return socket_handler

    '''
    [ NOTE   ]: Desociates Ewallet Socket Handler from Session Manager.
    [ RETURN ]: True
    '''
    def handle_system_action_close_sockets(self, **kwargs):
        log.debug('')
        return self.unset_socket_handler()

    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        _client_id = self.action_request_client_id()
        return _client_id

    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('')
        _session_token = self.action_request_session_token(**kwargs)
        return _session_token

    def handle_system_action_new_worker(self, **kwargs):
        log.debug('')
        worker = self.action_new_worker()
        set_to_pool = self.set_worker_to_pool(worker)
        return worker or False

    # TODO
    def handle_system_event_session_timeout(self, **kwargs):
        _timeout = self.event_session_timeout()
    def handle_system_event_worker_timeout(self, **kwargs):
        _timeout = self.event_worker_timeout()
    def handle_system_event_client_ack_timeout(self, **kwargs):
        _timeout = self.event_client_ack_timeout()
    def handle_system_event_client_id_expire(self, **kwargs):
        _expire = self.event_client_id_expire()
    def handle_system_event_session_token_expire(self, **kwargs):
        _expire = self.event_session_token_expire()

    # TODO
    def handle_client_action_new(self, **kwargs):
        pass
    def handle_client_action_scrape(self, **kwargs):
        pass
    def handle_client_action_search(self, **kwargs):
        pass
    def handle_client_action_view(self, **kwargs):
        pass

    '''
    [ NOTE   ]: Client action handler for request type actions.
    [ INPUT  ]: request=('client_id' | 'session_token')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_client_action_request(self, **kwargs):
        log.debug('')
        if not kwargs.get('request'):
            return self.error_no_client_request_specified()
        _handlers = {
                'client_id': self.handle_client_action_request_client_id,
                'session_token': self.handle_client_action_request_session_token,
                }
        return _handlers[kwargs['request']](**kwargs)

    '''
    [ NOTE   ]: System action handler for new type actions.
    [ INPUT  ]: new='worker'
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_new(self, **kwargs):
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_system_action_new_specified()
        _handlers = {
                'worker': self.handle_system_action_new_worker,
                'session': self.handle_system_action_new_session,
                }
        return _handlers[kwargs['new']](**kwargs)

    def handle_system_action_scrape(self, **kwargs):
        pass
    def handle_system_action_search(self, **kwargs):
        pass
    def handle_system_action_view(self, **kwargs):
        pass
    def handle_system_action_request(self, **kwargs):
        pass

    '''
    [ NOTE   ]: System action handler for start type actions.
    [ INPUT  ]: start=('instruction_listener')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_system_action_start_target_specified() #
        _handlers = {
                'instruction_listener': self.handle_system_action_start_instruction_listener,
                }
        return _handlers[kwargs['start']](**kwargs)

    '''
    [ NOTE   ]: System action handler for open type actions.
    [ INPUT  ]: opening=('sockets')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_open(self, **kwargs):
        log.debug('')
        if not kwargs.get('opening'):
            return self.error_no_system_action_open_target_specified()
        _handlers = {
                'sockets': self.handle_system_action_open_sockets,
                }
        return _handlers[kwargs['opening']](**kwargs)

    '''
    [ NOTE   ]: System action handler for close type actions.
    [ INPUT  ]: closing=('sockets')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_close(self, **kwargs):
        log.debug('')
        if not kwargs.get('closing'):
            return self.error_no_system_action_close_target_specified()
        _handlers = {
                'sockets': self.handle_system_action_close_sockets,
                }
        return _handlers[kwargs['closing']](**kwargs)

    '''
    [ NOTE   ]: System event handler for client timeout events.
    [ INPUT  ]: target='client_ack'
    [ RETURN ]: Event variable correspondent.
    '''
    def handle_system_event_client_timeout(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_event_client_timeout_target_specified()
        _handlers = {
                'client_ack': self.handle_system_event_client_ack_timeout,
                }
        return _handlers[kwargs['target']](**kwargs)

    '''
    [ NOTE   ]: System event handler for expire type events.
    [ INPUT  ]: expire=('client_id' | 'session_token')+
    [ RETURN ]: Event variable correspondent.
    '''
    def handle_system_event_expire(self, **kwargs):
        log.debug('')
        if not kwargs.get('expire'):
            return self.error_no_system_event_expire_specified()
        _handlers = {
                'client_id': self.handle_system_event_client_id_expire,
                'session_token': self.handle_system_event_session_token_expire,
                }
        return _handlers[kwargs['expire']](**kwargs)

    '''
    [ NOTE   ]: System event handler for timeout type events.
    [ INPUT  ]: timeout=('session' | 'worker' | 'client')+
    [ RETURN ]: Event variable correspondent.
    '''
    def handle_system_event_timeout(self, **kwargs):
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

    '''
    [ NOTE   ]: Client action controller for the EWallet Session Manager, accessible
                to regular user api calls.
    [ INPUT  ]: action=('new' | 'scrape' | 'search' | 'view' | 'request')+
    [ RETURN ]: Action variable correspondent.
    '''
    def client_session_manager_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_client_session_manager_action_specified()
        _handlers = {
                'new': self.handle_client_action_new,
                'scrape': self.handle_client_action_scrape,
                'search': self.handle_client_action_search,
                'view': self.handle_client_action_view,
                'request': self.handle_client_action_request,
                }
        return _handlers[kwargs['action']](**kwargs)

    '''
    [ NOTE   ]: System action controller for the EWallet Session Manager, not accessible
                to regular user api calls.
    [ INPUT  ]: action=('new' | 'scrape' | 'search' | 'view' | 'request' | 'open' | 'close')+
    [ RETURN ]: Action variable correspondent.
    '''
    def system_session_manager_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_action_specified()
        _handlers = {
                'new': self.handle_system_action_new,
                'start': self.handle_system_action_start,
                'scrape': self.handle_system_action_scrape,
                'search': self.handle_system_action_search,
                'view': self.handle_system_action_view,
                'request': self.handle_system_action_request,
                'open': self.handle_system_action_open,
                'close': self.handle_system_action_close,
                }
        return _handlers[kwargs['action']](**kwargs)

    # TODO
    '''
    [ NOTE   ]: Client event controller for the EWallet Session Manager, accessible
                to regular user api calls.
    [ INPUT  ]: event=('timeout' | 'expire')+
    [ RETURN ]: Event variable correspondent.
    '''
    def client_session_manager_event_controller(self, **kwargs):
        pass

    '''
    [ NOTE   ]: System event controller for the EWallet Session Manager, not accessible
                to regular user api calls.
    [ INPUT  ]: event=('timeout' | 'expire')+
    [ RETURN ]: Event variable correspondent.
    '''
    def system_session_manager_event_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_system_session_manager_event_specified()
        _handlers = {
                'timeout': self.handle_system_event_timout,
                'expire': self.handle_system_event_expire,
                }
        return _handlers[kwargs['event']](**kwargs)

    '''
    [ NOTE   ]: Main client controller for the EWallet Session Manager, accessible
                to regular user api calls.
    [ INPUT  ]: ctype=('action' | 'event')+
    [ RETURN ]: Action variable correspondent.
    '''
    def client_session_manager_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_client_session_manager_controller_specified()
        _handlers = {
                'action': self.client_session_manager_action_controller,
                'event': self.client_session_manager_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    '''
    [ NOTE   ]: Main system controller for the EWallet Session Manager, not accessible
                to regular user api calls.
    [ INPUT  ]: ctype=('action' | 'event')+
    [ RETURN ]: Action variable correspondent.
    '''
    def system_session_manager_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_controller_specified()
        _handlers = {
                'action': self.system_session_manager_action_controller,
                'event': self.system_session_manager_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    '''
    [ NOTE   ]: Main controller for the EWallet Session Manager.
    [ INPUT  ]: controller=('client' | 'system' | 'test')+
    [ RETURN ]: Action variable correspondent.
    '''
    def session_manager_controller(self, *args, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_controller_specified()
        _handlers = {
                'client': self.client_session_manager_controller,
                'system': self.system_session_manager_controller,
                'test': self.test_session_manager_controller,
                }
        return _handlers[kwargs['controller']](**kwargs)

    # ERRORS

    def error_worker_pool_empty(self):
        log.error('Session manager worker pool empty.')
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

    def error_no_client_id_found(self):
        log.error('No client id found.')
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

    def error_could_not_set_worker_to_pool(self, worker):
        log.error(
                'Something went wrong. Could not set worker {} to session manager worker pool.'\
                    .format(worker)
                )
        return False

    def error_invalid_client_id(self, client_id):
        log.error('Invalid client identifier {}.'.format(client_id))
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

    def error_could_not_unset_socket_handler(self, socket_hadler):
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

    def error_could_not_set_worker_pool(self, worker_pool):
        log.error('Something went wrong. Could not set worker pool : {}'.format(worker_pool))
        return False

    def error_could_not_set_client_pool(self, client_pool):
        log.error('Something went wrong. Could not set client pool : {}'.format(client_pool))
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

    def error_no_session_manager_controller_specified(self):
        log.error('No session manager controller specified.')
        return False

    # TESTS

    def test_request_session_token(self, client_id):
        log.debug('')
        print('[ * ]: User action Request Session Token')
        session_token = self.session_manager_controller(
                controller='client', ctype='action', action='request', request='session_token',
                client_id=client_id
                )
        print(str(session_token) + '\n')
        return session_token

    def test_new_session(self):
        log.debug('')
        print('[ * ]: Action New Session')
        session = self.session_manager_controller(
                controller='system', ctype='action', action='new', new='session'
                )
        print(str(session) + '\n')
        return session

    def test_instruction_set_listener(self):
        log.debug('')
        print('[ * ]: Action start instruction set listener')
        listen = self.session_manager_controller(
                controller='system', ctype='action', action='start',
                start='instruction_listener'
                )
        print(str(listen) + '\n')
        return listen

    def test_open_instruction_listener_port(self):
        log.debug('')
        print('[ * ] Action Open Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='open',
                opening='sockets', in_port=8080, out_port=8081
                )
        print(str(_in_port) + '\n')
        return _in_port

    def test_close_instruction_listener_port(self):
        log.debug('')
        print('[ * ] Action Close Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='close',
                closing='sockets',
                )
        print(str(_in_port) + '\n')
        return _in_port


    def test_request_client_id(self):
        log.debug('')
        print('[ * ] Action Request Client ID')
        _client_id = self.session_manager_controller(
                controller='client', ctype='action', action='request',
                request='client_id'
                )
        print(str(_client_id) + '\n')
        return _client_id

    def test_new_worker(self):
        log.debug('')
        print('[ * ] Action New Worker')
        _worker = self.session_manager_controller(
                controller='system', ctype='action', action='new',
                new='worker'
                )
        print(str(_worker) + '\n')
        return False

    def test_session_manager_controller(self, **kwargs):
        print('[ TEST ] Session Manager')
#       _open_in_port = self.test_open_instruction_listener_port()
#       _listen = self.test_instruction_set_listener()
        _client_id = self.test_request_client_id()
        _worker = self.test_new_worker()
        _session = self.test_new_session()
        _session_token = self.test_request_session_token(_client_id)
#       _close_in_port = self.test_close_instruction_listener_port()

session_manager = EWalletSessionManager()
session_manager.session_manager_controller(controller='test')


# CODE DUMP
