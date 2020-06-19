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

#   #@pysnooper.snoop()
    def fetch_ewallet_session_for_client_action_using_instruction_set(self, instruction_set):
        log.debug('')
        session_manager_worker = self.fetch_client_id_mapped_session_worker(
                instruction_set['client_id']
                )
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
                instruction_set, 'controller', 'ctype', 'action'
                )
        ewallet_session = self.fetch_ewallet_session_from_worker(
                session_manager_worker, sanitized_instruction_set
                )
        value_set = {
                'sanitized_instruction_set': sanitized_instruction_set,
                'ewallet_session': ewallet_session,
                }
        return False if False in value_set.keys() else value_set

    def fetch_ewallet_session_from_worker(self, session_manager_worker, instruction_set):
        log.debug('')
        ewallet_session = session_manager_worker.main_controller(
            controller='system', ctype='action', action='search', search='session',
            **instruction_set
        )
        return ewallet_session

    def fetch_client_id_mapped_session_worker(self, client_id):
        log.debug('')
        if not self.client_worker_map.get(client_id):
            return self.error_no_mapped_session_worker_found_for_client_id(client_id)
        return self.client_worker_map[client_id]

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

    def set_new_client_id_to_pool(self, client_id):
        log.debug('')
        try:
            self.client_pool.append(client_id)
        except:
            return self.error_could_not_set_client_pool(client_id)
        return True

    def set_worker_to_pool(self, worker):
        log.debug('')
        try:
            self.worker_pool.append(worker)
        except:
            return self.error_could_not_set_worker_pool(worker)
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
        except:
            return self.error_could_not_unset_socket_handler(self.socket_handler)
        return True

    def set_socket_handler(self, socket_handler):
        '''
        [ NOTE   ]: Overrides socket_handler attribute with new EWalletSocketHandler object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.socket_handler = socket_handler
        except:
            return self.error_could_not_set_socket_handler(socket_handler) #
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
        except:
            return self.error_could_not_set_worker_pool(worker_pool)
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
        except:
            return self.error_coult_not_set_client_pool(client_pool)
        return True

    def set_client_worker_session_map(self, cw_map):
        '''
        [ NOTE   ]: Overrides entire client/worker map.
        [ INPUT  ]: {user_id: worker, user_id: worker, ...}
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.client_worker_map = cw_map
        except:
            return self.error_could_not_set_client_worker_map(cw_map)
        return True

    def set_to_worker_pool(self, worker, **kwargs):
        '''
        [ NOTE   ]: Adds new work to worker pool stack.
        [ INPUT  ]: EwalletWorker object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.worker_pool.append(worker)
        except:
            return self.error_could_not_update_worker_pool(worker)
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
        except:
            return self.error_could_not_update_client_pool(client)
        return True

    def set_to_client_worker_session_map(self, user_id, session_token, worker):
        '''
        [ NOTE   ]: Adds new entry to client/worker map including entry in workers user_id/session token map.
        [ INPUT  ]: User ID, Session Token, EwalletWorker object.
        [ RETURN ]: (True | False)
        '''
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
        '''
        [ NOTE   ]: Maps Client ID to Worker for Session Manager and Client ID
                    with Session Token and EWallet Session object for Worker.
        [ INPUT  ]: <client-id>, <session-token>, <assigned-worker>, <ewallet-session>
        [ RETURN ]: ([{client_id: assigned_worker},
                      {client_id: {'token': session_token, 'session': EWalletSession}
                    }] | False)
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

    # VALIDATORS

    def validate_session_token_prefix(self, session_token):
        log.debug('')
        default_prefix = self.fetch_session_token_default_prefix()
        return False if session_token[0] != default_prefix else True

    def validate_session_token_length(self, session_token):
        log.debug('')
        default_length = self.fetch_session_token_default_length()
        return False if len(session_token[1]) is not default_length else True

    # TODO
    def validate_session_token_timestamp(self, session_token):
        log.debug('')
        timestamp = session_token[2]
        return True

    def validate_client_id_prefix(self, client_id):
        log.debug('')
        default_prefix = self.fetch_client_id_default_prefix()
        return False if client_id[0] != default_prefix else True

    def validate_client_id_length(self, client_id):
        log.debug('')
        default_length = self.fetch_client_id_default_length()
        return False if len(client_id[1]) is not default_length else True

    def validate_client_id_in_pool(self, client_id):
        log.debug('')
        return False if client_id not in self.client_pool else True

    # TODO
    def validate_client_id_timestamp(self, client_id):
        log.debug('')
        time_stamp = client_id[2]
        return True

#   #@pysnooper.snoop()
    def validate_session_token(self, session_token):
        session_token_segmented = session_token.split(':')
        if len(session_token_segmented) != 3:
            return self.error_invalid_session_token(session_token)
        checks = {
            'prefix': self.validate_session_token_prefix(session_token_segmented),
            'length': self.validate_session_token_length(session_token_segmented),
            'timestamp': self.validate_session_token_timestamp(session_token_segmented),
        }
        return False if False in checks.values() else True

#   @pysnooper.snoop()
    def validate_client_id(self, client_id):
        log.debug('')
        segmented_client_id = client_id.split(':')
        if len(segmented_client_id) != 3:
            return self.error_invalid_client_id(client_id)
        checks = {
            'prefix': self.validate_client_id_prefix(segmented_client_id),
            'length': self.validate_client_id_length(segmented_client_id),
            'timestamp': self.validate_client_id_timestamp(segmented_client_id),
            'pool': self.validate_client_id_in_pool(client_id),
        }
        return False if False in checks.values() else True

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

    def create_ewallet_user_account_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Uses EWallet Session object to carry out command chain user action Create Account.
        [ INPUT  ]: <ewallet-session>, <instruction-set>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        new_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='account',
            **instruction_set
        )
        return self.warning_could_not_create_new_user_account(
             ewallet_session, instruction_set
        ) if not new_account else new_account

    def create_new_ewallet_session(self):
        log.debug('')
        return EWallet()

    # GENERAL

    def login_ewallet_user_account_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Sets user state to LoggedIn (state code 1), and updates given
                    EWallet Session with user data.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        account_login = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='login', **instruction_set
        )
        return self.warning_could_not_login_user_account(
            ewallet_session, instruction_set
        ) if not account_login else account_login

    def assign_new_ewallet_session_to_worker(self, new_session):
        '''
        [ NOTE   ]: Adds new EWallet Session to one of the workers session pool.
                    The worker is simply the neares available worker in pool, and
                    if none is found, one is created.
        [ INPUT  ]: EWallet Session object
        [ RETURN ]: (EWallet Worker object | False)
        '''
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

    def start_instruction_set_listener(self):
        '''
        [ NOTE   ]: Starts socket based command chain instruction set listener.
        [ NOTE   ]: Programs hangs here untill interrupt.
        [ RETURN ]: (True | False)
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
        [ RETURN ]: (EWalletSocketHandler object | False)
        '''
        log.debug('')
        in_port = kwargs.get('in_port') or self.fetch_default_ewallet_command_chain_instruction_port()
        out_port = kwargs.get('out_port') or self.fetch_default_ewallet_command_chain_reply_port()
        if not in_port or not out_port:
            return self.error_could_not_fetch_socket_handler_required_values()
        socket = self.spawn_ewallet_session_manager_socket_handler(in_port, out_port)
        return self.error_could_not_spawn_socket_handler() if not socket else socket

    def generate_client_id(self):
        '''
        [ NOTE   ]: Generates a new unique client id using default format and prefix.
        [ NOTE   ]: User ID follows the following format <prefix-string>:<code>:<timestamp>
        [ RETURN ]: User ID
        '''
        log.debug('')
        prefix = self.fetch_client_id_default_prefix()
        length = self.fetch_client_id_default_length()
        timestamp = str(time.time())
        uid_code = res_utils.generate_random_alpha_numeric_string(string_length=length)
        user_id = prefix + ':' + uid_code + ':' + timestamp
        return user_id

    def generate_ewallet_session_token(self):
        '''
        [ NOTE   ]: Generates a new unique session token using default format and prefix.
        [ NOTE   ]: Session Token follows the following format <prefix-string>:<code>:<timestamp>
        [ RETURN ]: Session Token
        '''
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
    '''
    [ NOTE ]: SqlAlchemy ORM sessions are fetched here.
    '''

    def action_new_credit_clock(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'credit'
        )
        view_credit_ewallet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='credit_wallet',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_credit_ewallet(
            ewallet_session, instruction_set
        ) if view_credit_ewallet.get('failed') else view_credit_ewallet

    def action_edit_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'edit',
        )
        edit_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='edit', edit='account',
            active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_edit_user_account(
            ewallet_session, instruction_set
        ) if edit_account.get('failed') else edit_account

    def action_view_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'conversion',
        )
        view_conversion_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='conversion',
            conversion='record', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_conversion_sheet_record(
            ewallet_session, instruction_set
        ) if view_conversion_record.get('failed') else view_conversion_record

    def action_view_conversion_sheet(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
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
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'view', 'transfer',
        )
        view_transfer_sheet = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view', view='transfer',
            transfer='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_view_transfer_sheet(
            ewallet_session, instruction_set
        ) if view_transfer_sheet.get('failed') else view_transfer_sheet

    def action_transfer_credits(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        transfer_credits = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='transfer',
            ttype='transfer', active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_transfer_credits_to_partner(
            ewallet_session, instruction_set
        ) if not transfer_credits else transfer_credits

    def action_new_contact_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        new_contact_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='contact', active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_create_new_contact_record(
            ewallet_session, instruction_set
        ) if not new_contact_record else new_contact_record

    def action_view_contact_list(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        view_contact_list = ewallet_session.ewallet_controller(
        controller='user', ctype='action', action='view',
        active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_view_contact_list(
            ewallet_session, instruction_set
        ) if not view_contact_list else view_contact_list

    def action_view_contact_record(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        view_contact_record = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_view_contact_record(
            ewallet_session, instruction_set
        ) if not view_contact_record else view_contact_record

    def action_pay_partner_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        pay_partner = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='transfer',
            ttype='pay', **instruction_set
        )
        return self.warning_could_not_pay_partner_account(
            ewallet_session, instruction_set
        ) if not pay_partner else pay_partner

#   @pysnooper.snoop()
    def action_supply_user_credit_ewallet_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Sends a User action Supply command chain to given ewallet session
                    with the SystemCore account as beeing the partner, which creates
                    a credit transaction between two wallets resulting in S:Core having
                    a decreased credit count and the active user having an equivalent
                    increase in credits.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: ({'extract': -<count>, 'supply': <count>} | False)
        '''
        log.debug('')
        score = ewallet_session.fetch_system_core_user_account()
        orm_session = ewallet_session.fetch_active_session()
        credit_supply = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='transfer',
            ttype='supply', active_session=orm_session, partner_account=score,
            **instruction_set
        )
        return self.warning_could_not_supply_user_credit_wallet_with_credits(
            ewallet_session, instruction_set
        ) if not credit_supply else credit_supply

    # TODO - Format command chain response in EWallet Session action
    def action_stop_credit_clock_timer(self, ewallet_session, instruction_set):
        log.debug('TODO - Format command chain response in EWallet Session action.')
        orm_session = ewallet_session.fetch_active_session()
        stop_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='stop',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_stop_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not stop_timer else {'minutes_spent': stop_timer}

    # TODO - Format command chain response in EWallet Session action
#   @pysnooper.snoop()
    def action_resume_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Resumes active credit clock consumption timer if clock is in
                    appropriate state.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: (Legacy elapsed time since user action start | False)
        '''
        log.debug('TODO - Format command chain response in EWallet Session action.')
        orm_session = ewallet_session.fetch_active_session()
        resume_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='resume',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_resume_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not isinstance(resume_timer, float) else {'pending_time': resume_timer}

    # TODO - Format command chain response in EWallet Session action
#   @pysnooper.snoop()
    def action_pause_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Pauses active credit clock consumption timer if clock is in
                    appropriate state.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: (Clock session pause count | False)
        '''
        log.debug('TODO - Format command chain response in EWallet Session action.')
        orm_session = ewallet_session.fetch_active_session()
        pause_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='pause',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_pause_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not isinstance(pause_timer, int) else {'pending_count': pause_timer}

    # TODO - Format command chain response in EWallet Session action
#   @pysnooper.snoop()
    def action_start_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Starts active credit clock consumption timer if clock is in
                    appropriate state.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: (Legacy timestamp | False)
        '''
        log.debug('TODO - Format command chain response in EWallet Session action.')
        orm_session = ewallet_session.fetch_active_session()
        start_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='start',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_start_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not start_timer else {'clock_timestamp': start_timer}

    def action_convert_credits_to_credit_clock(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Executes credits to credit clock conversion and returns
                    curent active credit ewallet credits and credit clock time left.
        [ INPUT  ]: EWallet Session object, Instruction set
        [ RETURN ]: ({'ewallet_credits': <credits>, 'credit_clock': <time>} | False)
        '''
        log.debug('')
        if not instruction_set.get('credits'):
            return self.error_no_conversion_credit_count_specified(
                ewallet_session, instruction_set
            )
        credit_wallet = ewallet_session.fetch_active_session_credit_wallet()
        orm_session = ewallet_session.fetch_active_session()
        conversion = credit_wallet.main_controller(
            controller='system', action='convert', conversion='to_minutes',
            credit_ewallet=credit_wallet, active_session=orm_session,
            credits=instruction_set['credits'],
        )
        post_conversion_value_set = {
            'ewallet_credits': credit_wallet.main_controller(
                controller='user', action='interogate', interogate='credit_wallet',
                target='credits'
            ),
            'credit_clock': credit_wallet.main_controller(
                controller='user', action='interogate', interogate='credit_clock',
                target='credit_clock'
            )
        }
        return self.warning_could_not_convert_credits_to_credit_clock(
            credit_wallet, instruction_set
        ) if not conversion else post_conversion_value_set

    def action_convert_credit_clock_to_credits(self, ewallet_session, instruction_set):
        log.debug('')
        if not instruction_set.get('minutes'):
            return self.error_no_conversion_credit_clock_time_specified(
                ewallet_session, instruction_set
            )
        orm_session = ewallet_session.fetch_active_session()
        conversion = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='conversion', conversion='clock2credits',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_convert_credit_clock_time_to_credits(
            instruction_set) if conversion.get('failed') else conversion

    def action_new_worker(self):
        log.debug('')
        worker = self.spawn_ewallet_session_worker()
        return worker

    def action_new_session(self):
        log.debug('')
        session = self.spawn_ewallet_session()
        return session

    def action_request_client_id(self):
        log.debug('')
        client_id = self.generate_client_id()
        set_to_pool = self.set_new_client_id_to_pool(client_id)
        return {'client_id': client_id}

    def action_request_session_token(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session object, assigns it an existing
                    available worker or creates a new worker if none found,
                    generates a new session token and maps it to the Client ID.
        [ INPUT  ]: client_id=<id>
        [ RETURN ]: ({session_token: <token>} | False)
        '''
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
                if not mapping else {'session_token': session_token}

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
    '''
    [ NOTE ]: Instruction set validation and sanitizations are performed here.
    '''

    def handle_client_action_new_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        new_credit_clock = self.action_new_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_credit_clock

    def handle_client_action_new_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
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
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_invoice_record = self.action_view_invoice_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_invoice_record

    def handle_client_action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
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
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_credit_clock = self.action_view_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_credit_clock

    def handle_client_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
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

    def handle_client_action_edit_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        edit_account = self.action_edit_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return edit_account

    def handle_client_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_client_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_client_action_view_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_account = self.action_view_user_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_account

    def handle_client_action_view_conversion_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_conversion_record = self.action_view_conversion_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_conversion_record

    def handle_client_action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
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
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_time_record = self.action_view_time_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_time_record

    def handle_client_action_view_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
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

    def handle_client_action_view_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_transfer_record = self.action_view_transfer_sheet_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_transfer_record

    def handle_client_action_view_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_transfer_sheet = self.action_view_transfer_sheet(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_transfer_sheet

    def handle_client_action_view_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_view_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_view_transfer_sheet,
            'record': self.handle_client_action_view_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_transfer_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        credit_transfer = self.action_transfer_credits(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return credit_transfer

    def handle_client_action_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_transfer_target_specified(kwargs)
        handlers = {
            'credits': self.handle_client_action_transfer_credits,
#           'time': self.handle_client_action_transfer_time,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_action_new_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        new_contact_record = self.action_new_contact_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_contact_record

    def handle_client_action_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_new_contact_target_specified(kwargs)
        handlers = {
#           'list': self.handle_action_new_contact_list,
            'record': self.handle_action_new_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_view_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_contact_list = self.action_view_contact_list(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_contact_list

    def handle_client_action_view_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        view_contact_record = self.action_view_contact_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return view_contact_record

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
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_client_action_pay(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        pay_partner = self.action_pay_partner_account(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return pay_partner

    def handle_client_action_resume(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        resume_timer = self.action_resume_credit_clock_timer(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return resume_timer

    def handle_client_action_pause(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        pause_timer = self.action_pause_credit_clock_timer(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return pause_timer

    def handle_client_action_stop(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        stop_timer = self.action_stop_credit_clock_timer(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return stop_timer

    def handle_client_action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        conversion = self.action_convert_credits_to_credit_clock(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return conversion

    def handle_client_action_convert_clock_to_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        conversion = self.action_convert_credit_clock_to_credits(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return conversion

    def handle_client_action_login(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
                kwargs
                )
        if not ewallet:
            return False
        user_login = self.login_ewallet_user_account_in_session(
                ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
                )
        return user_login

#   #@pysnooper.snoop()
    def handle_client_action_supply_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
                kwargs
                )
        if not ewallet:
            return False
        credit_supply = self.action_supply_user_credit_ewallet_in_session(
                ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
                )
        return credit_supply

    def handle_client_action_start_clock_timer(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
                kwargs
                )
        if not ewallet:
            return False
        start_timer = self.action_start_credit_clock_timer(
                ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
                )
        return start_timer

    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        _client_id = self.action_request_client_id()
        return _client_id

    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('')
        _session_token = self.action_request_session_token(**kwargs)
        return _session_token

    def handle_client_action_new_account(self, **kwargs):
        '''
        [ NOTE   ]: Validates received instruction set, searches for worker and session
                    and proceeds to create new User Account in said session. Requiers
                    valid Client ID and Session Token.
        [ INPUT  ]: client_id=<id>, session_token=<token>, user_name=<name>
                    user_pass=<pass>, user_email=<email>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet:
            return False
        new_account = self.create_ewallet_user_account_in_session(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return new_account

#   #@pysnooper.snoop()
    def handle_system_action_new_session(self, **kwargs):
        log.debug('')
        new_session = self.create_new_ewallet_session()
        assign_worker = self.assign_new_ewallet_session_to_worker(new_session)
        return new_session or False

    def handle_system_action_start_instruction_listener(self, **kwargs):
        '''
        [ NOTE   ]: Turn Session Manager into server listenning for socket based instructions.
        [ NOTE   ]: System hangs here until interrupt.
        [ RETURN ]: True
        '''
        log.debug('')
        return self.start_instruction_set_listener()

    def handle_system_action_open_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Create and setups Session Manager Socket Handler.
        [ RETURN ]: EWalletSocketHandler object.
        '''
        log.debug('')
        socket_handler = self.open_ewallet_session_manager_sockets(**kwargs)
        set_socket_handler = self.set_socket_handler(socket_handler)
        return socket_handler

    # TODO - Kill process
    def handle_system_action_close_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Desociates Ewallet Socket Handler from Session Manager.
        [ RETURN ]: True
        '''
        log.debug('')
        return self.unset_socket_handler()

    def handle_system_action_new_worker(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session Manager Worker object and sets
                    it to worker pool.
        [ RETURN ]: (EWalletWorker object | False)
        '''
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

    def handle_client_action_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_client_action_start_target_specified()
        _handlers = {
                'clock_timer': self.handle_client_action_start_clock_timer,
                }
        return _handlers[kwargs['start']](**kwargs)

    def handle_client_action_convert(self, **kwargs):
        log.debug('')
        if not kwargs.get('convert'):
            return self.error_no_client_action_convert_target_specified()
        _handlers = {
            'credits2clock': self.handle_client_action_convert_credits_to_clock,
            'clock2credits': self.handle_client_action_convert_clock_to_credits,
        }
        return _handlers[kwargs['convert']](**kwargs)

    def handle_client_action_supply(self, **kwargs):
        log.debug('')
        if not kwargs.get('supply'):
            return self.error_no_client_action_supply_target_specified()
        _handlers = {
                'credits': self.handle_client_action_supply_credits,
                }
        return _handlers[kwargs['supply']](**kwargs)

    def handle_client_action_new(self, **kwargs):
        '''
        [ NOTE   ]: Client action handler for new type actions.
        [ INPUT  ]: new='account'
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_client_action_new_target_specified()
        _handlers = {
                'account': self.handle_client_action_new_account,
                'contact': self.handle_client_action_new_contact,
                'credit': self.handle_client_action_new_credit,
                }
        return _handlers[kwargs['new']](**kwargs)

    def handle_client_action_request(self, **kwargs):
        '''
        [ NOTE   ]: Client action handler for request type actions.
        [ INPUT  ]: request=('client_id' | 'session_token')
        [ RETURN ]: Action variable correspondent.
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
        [ INPUT  ]: new=('worker' | 'session')
        [ RETURN ]: Action variable correspondent.
        '''
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

    def handle_system_action_start(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for start type actions.
        [ INPUT  ]: start=('instruction_listener')
        [ RETURN ]: Action variable correspondent.
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
        [ INPUT  ]: opening=('sockets')
        [ RETURN ]: Action variable correspondent.
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
        [ INPUT  ]: closing=('sockets')
        [ RETURN ]: Action variable correspondent.
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
        [ INPUT  ]: target='client_ack'
        [ RETURN ]: Event variable correspondent.
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
        [ INPUT  ]: expire=('client_id' | 'session_token')+
        [ RETURN ]: Event variable correspondent.
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
        [ INPUT  ]: timeout=('session' | 'worker' | 'client')+
        [ RETURN ]: Event variable correspondent.
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
        [ INPUT  ]: action=(
                    'new' | 'scrape' | 'search' | 'view' | 'request' | 'login' |
                    'supply' | 'convert | start | pause | resume | stop | pay'
                    )+
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_client_session_manager_action_specified()
        _handlers = {
                'new': self.handle_client_action_new,
#               'scrape': self.handle_client_action_scrape,
#               'search': self.handle_client_action_search,
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
                }
        return _handlers[kwargs['action']](**kwargs)

    def system_session_manager_action_controller(self, **kwargs):
        '''
        [ NOTE   ]: System action controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        [ INPUT  ]: action=('new' | 'scrape' | 'search' | 'view' | 'request' |
        [ NOTE   ]: Pauses active credit clock consumption timer.
        [ INPUT  ]: EWallet Session object, Instruction set
                    'open' | 'close')+
        [ RETURN ]: Action variable correspondent.
        '''
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
    def client_session_manager_event_controller(self, **kwargs):
        '''
        [ NOTE   ]: Client event controller for the EWallet Session Manager, accessible
                    to regular user api calls.
        [ INPUT  ]: event=('timeout' | 'expire')+
        [ RETURN ]: Event variable correspondent.
        [ WARNING ]: Unimplemented
        '''
        pass

    def system_session_manager_event_controller(self, **kwargs):
        '''
        [ NOTE   ]: System event controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        [ INPUT  ]: event=('timeout' | 'expire')+
        [ RETURN ]: Event variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_system_session_manager_event_specified()
        _handlers = {
                'timeout': self.handle_system_event_timout,
                'expire': self.handle_system_event_expire,
                }
        return _handlers[kwargs['event']](**kwargs)

    def client_session_manager_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main client controller for the EWallet Session Manager, accessible
                    to regular user api calls.
        [ INPUT  ]: ctype=('action' | 'event')+
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_client_session_manager_controller_specified()
        _handlers = {
                'action': self.client_session_manager_action_controller,
                'event': self.client_session_manager_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    def system_session_manager_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main system controller for the EWallet Session Manager, not accessible
                    to regular user api calls.
        [ INPUT  ]: ctype=('action' | 'event')+
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_session_manager_controller_specified()
        _handlers = {
                'action': self.system_session_manager_action_controller,
                'event': self.system_session_manager_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    def session_manager_controller(self, *args, **kwargs):
        '''
        [ NOTE   ]: Main controller for the EWallet Session Manager.
        [ INPUT  ]: controller=('client' | 'system' | 'test')+
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_controller_specified()
        handlers = {
            'client': self.client_session_manager_controller,
            'system': self.system_session_manager_controller,
            'test': self.test_session_manager_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_could_not_create_new_credit_clock(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new credit clock in ewallet session {}.'\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_invoice_sheet_record(self, ewallet_session, instruction_set):
        log.warning()
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

    def warning_could_not_edit_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit user account in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set)
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

    def warning_could_not_view_transfer_sheet_record(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view transfer sheet record in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_view_transfer_sheet(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view transfer sheet in ewallet session {}. '\
                       'Instruction set details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_convert_credit_clock_time_to_credits(self, conversion_response, **kwargs):
        instruction_set_response = {
            'failed': True,
            'warning': 'Could not convert credit clock time to credits. Got response {}. '\
                       'Command Chain Details : {}'.format(conversion_response, kwargs)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response['warning']

    def warning_could_not_transfer_credits_to_partner(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not transfer credits to partner in ewallet session {}. '\
            'Details : {}'.format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_create_new_contact_record(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not create new contact record for session {}.'\
            'Details : {}'.format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_view_contact_list(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not view active contact list for ewallet session {}.'\
            'Details : {}'.format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_view_contact_record(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not view active contact list record for ewallet session {}.'\
            'Details : {}'.format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_pay_partner_account(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not pay partner account in session {}. Details : {}'\
            .format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_stop_credit_clock_timer(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not stop credit clock timer in session {}. '\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def warning_could_not_resume_credit_clock_timer(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not resume credit clock timer in session {}. '\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def warning_could_not_pause_credit_clock_timer(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not pause credit clock timer in session {}. '\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def warning_could_not_start_credit_clock_timer(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not start credit clock timer in session {}. '\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def warning_could_not_convert_credits_to_credit_clock(self, credit_wallet, instruction_set):
        log.warning(
                'Something went wrong. Could not convert credit wallet {} credits to credit clock. '\
                'Details : {}'.format(credit_wallet, instruction_set)
                )
        return False

    def warning_could_not_supply_user_credit_wallet_with_credits(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not supply user credit wallet with credits in session {}.'\
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    def warning_could_not_login_user_account(self, ewallet_session, instruction_set):
        log.warning(
            'Something went wrong. Could not login user account in session {}.'\
            'Details : {}'.format(ewallet_session, instruction_set)
        )
        return False

    def warning_could_not_create_new_user_account(self, ewallet_session, instruction_set):
        log.warning(
                'Something went wrong. Could not create new user account in EWallet Session {}.'
                'Details : {}'.format(ewallet_session, instruction_set)
                )
        return False

    # ERRORS

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

    def error_no_mapped_session_worker_found_for_client_id(self, client_id):
        log.error('No mapped session worker found for client id {}.'.format(client_id))
        return False

    def error_invalid_session_token(self, session_token):
        log.error('Invalid session token {}.'.format(session_token))
        return False

    def error_invalid_instruction_set_required_data(self, instruction_set):
        log.error(
                'Invalid EWallet session manager instruction set required data. '
                'Instruction set : {}'.format(instruction_set)
                )
        return False

    def error_no_client_action_new_target_specified(self):
        log.error('No aclient action new target specified.')
        return False

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
        print('[ * ]: System Action New Session')
        session = self.session_manager_controller(
                controller='system', ctype='action', action='new', new='session'
                )
        print(str(session) + '\n')
        return session

    def test_instruction_set_listener(self):
        log.debug('')
        print('[ * ]: System Action Start Instruction Set Listener')
        listen = self.session_manager_controller(
                controller='system', ctype='action', action='start',
                start='instruction_listener'
                )
        print(str(listen) + '\n')
        return listen

    def test_open_instruction_listener_port(self):
        log.debug('')
        print('[ * ]: System Action Open Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='open',
                opening='sockets', in_port=8080, out_port=8081
                )
        print(str(_in_port) + '\n')
        return _in_port

    def test_close_instruction_listener_port(self):
        log.debug('')
        print('[ * ]: System Action Close Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='close',
                closing='sockets',
                )
        print(str(_in_port) + '\n')
        return _in_port


    def test_request_client_id(self):
        log.debug('')
        print('[ * ]: User Action Request Client ID')
        _client_id = self.session_manager_controller(
                controller='client', ctype='action', action='request',
                request='client_id'
                )
        print(str(_client_id) + '\n')
        return _client_id

    def test_new_worker(self):
        log.debug('')
        print('[ * ]: System Action New Worker')
        _worker = self.session_manager_controller(
                controller='system', ctype='action', action='new',
                new='worker'
                )
        print(str(_worker) + '\n')
        return _worker

    def test_user_action_create_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Create Account')
        _create_account = self.session_manager_controller(
                controller='client', ctype='action', action='new',
                new='account', client_id=kwargs.get('client_id'),
                session_token=kwargs.get('session_token'), user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'), user_email=kwargs.get('user_email')
                )
        print(str(_create_account) + '\n')
        return _create_account

    def test_user_action_session_login(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Session Login')
        _login = self.session_manager_controller(
                controller='client', ctype='action', action='login',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                user_name=kwargs['user_name'], user_pass=kwargs['user_pass'],
                )
        print(str(_login) + '\n')
        return _login

    def test_user_action_supply_credits(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Supply Credits')
        _supply = self.session_manager_controller(
                controller='client', ctype='action', action='supply', supply='credits',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                currency=kwargs['currency'], credits=kwargs['credits'], cost=kwargs['cost'],
                notes=kwargs['notes']
                )
        print(str(_supply) + '\n')
        return _supply

    def test_user_action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Convert Credits To Clock')
        _convert = self.session_manager_controller(
                controller='client', ctype='action', action='convert', convert='credits2clock',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                credits=kwargs['credits'], notes=kwargs['notes']
                )
        print(str(_convert) + '\n')
        return _convert

    def test_user_action_start_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Start Clock Timer')
        _start = self.session_manager_controller(
            controller='client', ctype='action', action='start', start='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_start) + '\n')
        return _start

    def test_user_action_pause_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Pause Clock Timer')
        _pause = self.session_manager_controller(
            controller='client', ctype='action', action='pause', pause='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_pause) + '\n')
        return _pause

    def test_user_action_resume_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Resume Clock Timer')
        _resume = self.session_manager_controller(
            controller='client', ctype='action', action='resume', resume='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_resume) + '\n')
        return _resume

    def test_user_action_stop_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Stop Clock Timer')
        _stop = self.session_manager_controller(
            controller='client', ctype='action', action='stop', stop='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_stop) + '\n')
        return _stop

    def test_user_action_pay_credits_to_partner(self, **kwargs):
        '''
        [ NOTE ]: Instruction Set Details
            - pay = Target user email address
        '''
        log.debug('')
        print('[ * ]: User Action Pay Credits To Partner')
        _pay = self.session_manager_controller(
            controller='client', ctype='action', action='pay', pay=kwargs['pay'],
            credits=kwargs['credits'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_pay) + '\n')
        return _pay

    def test_user_action_add_contact_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Add Contact List Record')
        _add_record = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact', contact='record',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            contact_list=kwargs['contact_list'],
            user_name=kwargs['user_name'], user_email=kwargs['user_email'],
            user_phone=kwargs['user_phone'], user_reference=kwargs['user_reference'],
            notes=kwargs['notes'],
        )
        print(str(_add_record) + '\n')
        return _add_record

    def test_user_action_view_contact_list(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action View Active Contact List')
        _view_list = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='contact',
            contact='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view_list) + '\n')
        return _view_list

    def test_user_action_view_contact_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action View Active Contact List Record')
        _view_record = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='contact',
            contact='record', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'], record=kwargs['record']
        )
        print(str(_view_record) + '\n')
        return _view_record

    def test_user_action_transfer_credits(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Transfer Credits.')
        _transfer = self.session_manager_controller(
            controller='client', ctype='action', action='transfer',
            transfer='credits', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'], transfer_to=kwargs['transfer_to'],
            credits=kwargs['credits']
        )
        print(str(_transfer) + '\n')
        return _transfer

    def test_user_action_convert_clock_to_credits(self, **kwargs):
        print('[ * ]: User action Convert Clock To Credits')
        _convert = self.session_manager_controller(
            controller='client', ctype='action', action='convert', convert='clock2credits',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            minutes=kwargs['minutes']
        )
        print(str(_convert) + '\n')
        return _convert

    def test_user_action_view_transfer_sheet(self, **kwargs):
        print('[ * ]: User action View Transfer Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='transfer',
            transfer='list', client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_transfer_record(self, **kwargs):
        print('[ * ]: User action View Transfer Sheet Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='transfer',
            transfer='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_time_sheet(self, **kwargs):
        print('[ * ]: User action View Time Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='time',
            time='list', client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_time_record(self, **kwargs):
        print('[ * ]: User action View Time Sheet Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='time',
            time='record', record_id=kwargs['record_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_conversion_sheet(self, **kwargs):
        print('[ * ]: User action View Conversion Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='conversion',
            conversion='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_conversion_record(self, **kwargs):
        print('[ * ]: User action View Conversion Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='conversion',
            conversion='record', record_id=kwargs['record_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_account(self, **kwargs):
        print('[ * ]: User action View Account')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='account',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_edit_account(self, **kwargs):
        print('[ * ]: User action Edit Account')
        _edit = self.session_manager_controller(
            controller='client', ctype='action', action='edit', edit='account',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            user_name=kwargs['user_name'], user_phone=kwargs['user_phone'],
#           user_email=kwargs['user_email'], user_pass=kwargs['user_pass'],
            user_alias=kwargs['user_alias']
        )
        print(str(_edit) + '\n')
        return _edit

    def test_user_action_view_credit_ewallet(self, **kwargs):
        print('[ * ]: User action View Credit EWallet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='credit',
            credit='ewallet', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_credit_clock(self, **kwargs):
        print('[ * ]: User action View Credit Clock')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='credit',
            credit='clock', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_invoice_sheet(self, **kwargs):
        print('[ * ]: User action View Invoice Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='invoice',
            invoice='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_invoice_record(self, **kwargs):
        print('[ * ]: User action View Invoice Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='invoice',
            invoice='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_create_credit_ewallet(self, **kwargs):
        print('[ * ]: User action Create Credit EWallet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='credit',
            credit='ewallet', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_credit_clock(self, **kwargs):
        print('[ * ]: User action Create Credit Clock')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='credit',
            credit='clock', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_session_manager_controller(self, **kwargs):
        print('[ TEST ] Session Manager')
#       open_in_port = self.test_open_instruction_listener_port()
#       listen = self.test_instruction_set_listener()
#       close_in_port = self.test_close_instruction_listener_port()

        client_id = self.test_request_client_id()
        worker = self.test_new_worker()
        session = self.test_new_session()
        session_token = self.test_request_session_token(client_id['client_id'])
        create_account = self.test_user_action_create_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user', user_pass='1234@!xxA', user_email='testuser@mail.com'
        )
        session_login = self.test_user_action_session_login(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user', user_pass='1234@!xxA'
        )
        supply_credits = self.test_user_action_supply_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            currency='RON', credits=15, cost=4.74,
            notes='Test Credit Wallet Supply Notes...'
        )
        convert_credits_2_clock = self.test_user_action_convert_credits_to_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'], credits=5,
            notes='Test Credits To Clock Conversion Notes...'
        )
#       start_clock_timer = self.test_user_action_start_clock_timer(
#           client_id=client_id['client_id'], session_token=session_token['session_token']
#       )
#       time.sleep(3)
#       pause_clock_timer = self.test_user_action_pause_clock_timer(
#           client_id=client_id['client_id'], session_token=session_token['session_token']
#       )
#       time.sleep(3)
#       resume_clock_timer = self.test_user_action_resume_clock_timer(
#           client_id=client_id['client_id'], session_token=session_token['session_token']
#       )
#       time.sleep(3)
#       stop_clock_timer = self.test_user_action_stop_clock_timer(
#           client_id=client_id['client_id'], session_token=session_token['session_token']
#       )
#       time.sleep(3)
        pay_credits = self.test_user_action_pay_credits_to_partner(
            partner_account=1, credits=5, client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            pay='system.core@alvearesolutions.com'
        )
#       view_contact_list = self.test_user_action_view_contact_list(
#           client_id=client_id['client_id'],
#           session_token=session_token['session_token'],
#       )
#       add_contact_record = self.test_user_action_add_contact_record(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#           contact_list=view_contact_list['contact_list'],
#           user_name='This is bob', user_email='example@example.com', user_phone='095551234',
#           user_reference='That weird guy coding wallets.', notes='WOOHO.'
#       )
#       view_contact_record = self.test_user_action_view_contact_record(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#           record=add_contact_record['contact_record']
#       )
        transfer_credits = self.test_user_action_transfer_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            transfer_to='example@example.com', credits=50
        )
        convert_clock_2_credits = self.test_user_action_convert_clock_to_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            minutes=13,
        )
#       view_transfer_sheet = self.test_user_action_view_transfer_sheet(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#       )
        view_transfer_record = self.test_user_action_view_transfer_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
#       view_time_sheet = self.test_user_action_view_time_sheet(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#       )
        view_time_record = self.test_user_action_view_time_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=33
        )
#       view_conversion_sheet = self.test_user_action_view_conversion_sheet(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#       )
        view_conversion_record = self.test_user_action_view_conversion_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
        view_account = self.test_user_action_view_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        # TODO - password and email edits not supported
#       edit_account = self.test_user_action_edit_account(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#           user_name='New Name', user_phone='555555555', user_alias='New Alias',
#           user_pass='1234asscdYEEBOY@!', user_email='new@user.mail'
#       )
        view_credit_ewallet = self.test_user_action_view_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_credit_clock = self.test_user_action_view_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
#       view_invoice_sheet = self.test_user_action_view_invoice_sheet(
#           client_id=client_id['client_id'], session_token=session_token['session_token'],
#       )
        view_invoice_record = self.test_user_action_view_invoice_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
        create_credit_ewallet = self.test_user_action_create_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_credit_clock = self.test_user_action_create_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )

if __name__ == '__main__':
    session_manager = EWalletSessionManager()
    session_manager.session_manager_controller(controller='test')


# CODE DUMP

