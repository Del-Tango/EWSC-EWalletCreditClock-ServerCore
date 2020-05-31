from ewallet import EWallet
from base.config import Config
from base.res_utils import ResUtils
from base.ewallet_worker import EWalletWorker

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


class EWalletSessionManager():

    worker_pool = []
    client_pool = []
    client_worker_map = {}

    def __init__(self, *args, **kwargs):
        pass

    # FETCHERS

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
    def fetch_ewallet_worker_sessions(self):
        pass
    def fetch_from_ewallet_worker_session(self):
        pass

    # SETTERS

    def set_worker_pool(self, worker_pool, **kwargs):
        log.debug('')
        self.worker_pool = worker_pool
        return True

    def set_client_pool(self, client_pool, **kwargs):
        log.debug('')
        self.client_pool = client_pool
        return True

    def set_token_session_map(self, token_session_map, **kwargs):
        log.debug('')
        self.token_session_map = token_session_map
        return True

    def set_client_session_map(self, client_session_map, **kwargs):
        log.debug('')
        self.client_session_map = client_session_map
        return True

    def set_to_worker_pool(self, worker, **kwargs):
        log.debug('')
        self.worker_pool.append(worker)
        return True

    def set_to_client_pool(self, client, **kwargs):
        log.debug('')
        self.client_pool.append(client)

    # TODO
    def set_to_token_session_map(self, token_map, **kwargs):
        log.debug('')
    def set_to_client_session_map(self, client_map, **kwargs):
        log.debug('')

    # UPDATERS

    # TODO
    def update_worker_pool(self):
        pass
    def update_client_pool(self):
        pass
    def update_token_session_map(self):
        pass
    def update_client_session_map(self):
        pass

    # CHECKERS

    # TODO
    def check_command_chain_client_id(self):
        pass
    def check_command_chain_session_token(self):
        pass
    def check_command_chain_instruction_set(self):
        pass

    # SPAWNERS

    # TODO
    def spawn_ewallet_session_worker(self):
        pass
    def spawn_ewallet_session(self):
        pass
    def spawn_ewallet_session_manager_socket(self):
        pass

    # SCRAPERS

    # TODO
    def scrape_ewallet_session_worker(self):
        pass
    def scrape_ewallet_session(self):
        pass

    # GENERAL

    # TODO
    def open_ewallet_session_manager_command_chain_instruction_socket(self, **kwargs):
        log.debug('')
        _socket = self.spawn_ewallet_session_manager_socket()
        return _socket

    # TODO
    def open_ewallet_session_manager_command_chain_reply_socket(self, **kwargs):
        log.debug('')
        _socket = self.spawn_ewallet_session_manager_socket()
        return _socket

    # TODO
    def generate_ewallet_session_token(self):
        pass
    def generate_client_id(self):
        pass
    def map_ewallet_session_token(self):
        pass
    def map_client_id_ewallet_sessions(self):
        pass

    # ACTIONS

    # TODO
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

    # TODO
    def action_request_session_token(self):
        log.debug('')
        _session_token = self.generate_ewallet_session_token()
        return _session_token

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

    # TODO
    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        _client_id = self.action_request_client_id()
        return _client_id

    # TODO
    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('')
        _session_token = self.action_request_session_token()
        return _session_token

    # TODO
    def handle_system_action_open_instruction_listener_port(self, **kwargs):
        log.debug('')
        _in_port = self.open_ewallet_session_manager_command_chain_instruction_socket()
        return _in_port

    # TODO
    def handle_system_action_open_command_chain_reply_port(self, **kwargs):
        log.debug('')
        _out_port = self.open_ewallet_session_manager_command_chain_reply_socket()
        return _out_port

    def handle_system_action_close_instruction_listener_port(self, **kwargs):
        log.debug('')
    def handle_system_action_close_command_chain_reply_port(self, **kwargs):
        log.debug('')

	# TODO
    def handle_system_action_new_worker(self, **kwargs):
        log.debug('')
        _worker = self.action_new_worker()
        return _worker

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
    [ NOTE   ]: System action handler for open type actions.
    [ INPUT  ]: open=('in_port' | 'out_port')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_open(self, **kwargs):
        log.debug('')
        if not kwargs.get('open'):
            return self.error_no_system_action_open_target_specified()
        _handlers = {
                'in_port': self.handle_system_action_open_instruction_listener_port,
                'out_port': self.handle_system_action_open_command_chain_reply_port,
                }
        return _handlers[kwargs['open']](**kwargs)

    '''
    [ NOTE   ]: System action handler for close type actions.
    [ INPUT  ]: close=('in_port' | 'out_port')
    [ RETURN ]: Action variable correspondent.
    '''
    def handle_system_action_close(self, **kwargs):
        log.debug('')
        if not kwargs.get('close'):
            return self.error_no_system_action_close_target_specified()
        _handlers = {
                'in_port': self.handle_system_action_close_instruction_listener_port,
                'out_port': self.handle_system_action_close_command_chain_reply_port,
                }
        return _handlers[kwargs['close']](**kwargs)

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
    def session_manager_controller(self, **kwargs):
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

    def test_open_instruction_listener_port(self):
        log.debug('')
        print('[ * ] Action Open Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='open',
                opening='in_port', in_port=8080
                )
        print(str(_in_port) + '\n')
        return _in_port

    def test_open_command_chain_reply_port(self):
        log.debug('')
        print('[ * ] Action Open Command Chain Reply Port')
        _out_port = self.session_manager_controller(
                controller='system', ctype='action', action='open',
                opening='out_port', out_port=8081,
                )
        print(str(_out_port) + '\n')
        return _out_port

    def test_close_instruction_listener_port(self):
        log.debug('')
        print('[ * ] Action Close Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='close',
                closing='in_port', in_port=8080,
                )
        print(str(_in_port) + '\n')
        return _in_port

    def test_close_command_chain_reply_port(self):
        log.debug('')
        print('[ * ] Action Close Command Chain Reply Port')
        _out_port = self.session_manager_controller(
                controller='system', ctype='action', action='close',
                closing='out_port', out_port=8081,
                )
        print(str(_out_port) + '\n')
        return _out_port


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
        _open_in_port = self.test_open_instruction_listener_port()
        _open_out_port = self.test_open_command_chain_reply_port()
        _client_id = self.test_request_client_id()
        _worker = self.test_new_worker()
        _close_in_port = self.test_close_instruction_listener_port()
        _close_out_port = self.test_close_command_chain_reply_port()

session_manager = EWalletSessionManager()
session_manager.session_manager_controller(controller='test')


