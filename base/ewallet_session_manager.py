import time
import datetime
import logging
import pysnooper

from .ewallet import EWallet
from .config import Config
from .res_utils import ResUtils
from .ewallet_worker import EWalletWorker
from .socket_handler import EWalletSocketHandler

config, res_utils = Config(), ResUtils()
log = logging.getLogger(Config().log_config['log_name'])


class EWalletSessionManager():

    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config') or config
        self.res_utils = kwargs.get('res_utils') or res_utils
        self.socket_handler = kwargs.get('socket_handler') or None # self.open_ewallet_session_manager_sockets()
        self.worker_pool = kwargs.get('worker_pool') or \
            [self.spawn_ewallet_session_worker()]
        self.client_pool = kwargs.get('client_pool') or []
        self.client_worker_map = kwargs.get('client_worker_map') or {}

        self.primary_session = kwargs.get('primary_session') or \
            self.create_new_ewallet_session(
                reference='S:CorePrimary',
                expiration_date=None,
            )
        check_score = self.check_system_core_account_exists()
        if not check_score:
            res_utils.create_system_user(self.primary_session)

    # FETCHERS

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

    def fetch_ewallet_session_manager_worker_pool(self):
        log.debug('')
        return self.error_ewallet_session_manager_worker_pool_empty() if not \
            self.worker_pool else self.worker_pool

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

    def fetch_ewallet_session_for_system_action_using_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_session_id_found(kwargs)
        ewallet_session = self.fetch_ewallet_session_by_id(kwargs['session_id'])
        return self.warning_no_ewallet_session_found_by_id(kwargs) if not \
            ewallet_session else ewallet_session

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

    def fetch_client_id_mapped_session_worker(self, client_id):
        log.debug('')
        if not self.client_worker_map.get(client_id):
            return self.error_no_mapped_session_worker_found_for_client_id(client_id)
        return self.client_worker_map[client_id]

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

#   @pysnooper.snoop()
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
        return EWalletWorker()

    def spawn_ewallet_session(self, orm_session, **kwargs):
        log.debug('')
        return EWallet(
            name=kwargs.get('reference'), session=orm_session,
            expiration_date=kwargs.get('expiration_date')
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

#   @pysnooper.snoop('logs/ewallet.log')
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

#   @pysnooper.snoop()
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

#   @pysnooper.snoop()
    def create_ewallet_user_account_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Uses EWallet Session object to carry out command chain user action Create Account.
        '''
        log.debug('')
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return ewallet_session
        orm_session = ewallet_session.fetch_active_session()
        new_account = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='account',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_create_new_user_account(
             ewallet_session, instruction_set
        ) if not new_account else new_account

#   @pysnooper.snoop()
    def create_new_ewallet_session(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        ewallet_session = self.spawn_ewallet_session(orm_session, **kwargs)
        orm_session.add(ewallet_session)
        orm_session.commit()
        return ewallet_session

    # GENERAL

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

    def login_ewallet_user_account_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Sets user state to LoggedIn (state code 1), and updates given
                    EWallet Session with user data.
        '''
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        account_login = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='login',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_login_user_account(
            ewallet_session, instruction_set
        ) if not account_login else account_login

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
        user_id = prefix + ':' + uid_code + ':' + timestamp
        return user_id

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

#   @pysnooper.snoop('logs/ewallet.log')
    def action_unlink_user_account(self, ewallet_session, instruction_set):
        log.debug('')
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

    def action_edit_user_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
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

    def action_view_contact_list(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        view_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='view',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_view_contact_list(
            ewallet_session, instruction_set
        ) if not view_contact_list or isinstance(view_contact_list, dict) and \
        view_contact_list.get('failed') else view_contact_list

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

    def action_pay_partner_account(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        pay_partner = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='transfer',
            ttype='pay', **instruction_set
        )
        return self.warning_could_not_pay_partner_account(
            ewallet_session, instruction_set
        ) if not pay_partner or isinstance(pay_partner, dict) and \
            pay_partner.get('failed') else pay_partner

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

#   @pysnooper.snoop()
    def action_resume_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Resumes active credit clock consumption timer if clock is in
                    appropriate state.
        '''
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        resume_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='resume',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_resume_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not resume_timer or isinstance(resume_timer, dict) and \
            resume_timer.get('failed') else resume_timer

#   @pysnooper.snoop()
    def action_pause_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Pauses active credit clock consumption timer if clock is in
                    appropriate state.
        '''
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        pause_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='pause',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_pause_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not pause_timer or isinstance(pause_timer, dict) and \
            pause_timer.get('failed') else pause_timer

#   @pysnooper.snoop()
    def action_start_credit_clock_timer(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Starts active credit clock consumption timer if clock is in
                    appropriate state.
        '''
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        start_timer = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='time', timer='start',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_start_credit_clock_timer(
            ewallet_session, instruction_set
        ) if not start_timer or isinstance(start_timer, dict) and \
            start_timer.get('failed') else start_timer

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

    def action_new_contact_list(self, ewallet_session, instruction_set):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            instruction_set, 'controller', 'ctype', 'action', 'new', 'contact'
        )
        new_contact_list = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create', create='contact',
            contact='list', active_session=orm_session, **sanitized_instruction_set
        )
        return self.warning_could_not_create_new_contact_list(
            ewallet_session, instruction_set
        ) if new_contact_list.get('failed') else new_contact_list

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

#   @pysnooper.snoop()
    def action_supply_user_credit_ewallet_in_session(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Sends a User action Supply command chain to given ewallet session
                    with the SystemCore account as beeing the partner, which creates
                    a credit transaction between two wallets resulting in S:Core having
                    a decreased credit count and the active user having an equivalent
                    increase in credits.
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

#   @pysnooper.snoop('logs/ewallet.log')
    def action_convert_credits_to_credit_clock(self, ewallet_session, instruction_set):
        '''
        [ NOTE   ]: Executes credits to credit clock conversion and returns
                    curent active credit ewallet credits and credit clock time left.
        '''
        log.debug('')
        if not instruction_set.get('credits'):
            return self.error_no_conversion_credit_count_specified(
                ewallet_session, instruction_set
            )
        orm_session = ewallet_session.fetch_active_session()
        conversion = ewallet_session.ewallet_controller(
            controller='user', ctype='action', action='create',
            create='conversion', conversion='credits2clock',
            active_session=orm_session, **instruction_set
        )
        return self.warning_could_not_convert_credits_to_credit_clock(
            instruction_set
        ) if not conversion else conversion

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

    def action_new_session(self, **kwargs):
        log.debug('')
        session = self.spawn_ewallet_session(**kwargs)
        return session

    def action_request_client_id(self):
        log.debug('')
        client_id = self.generate_client_id()
        set_to_pool = self.set_new_client_id_to_pool(client_id)
        if not client_id or not set_to_pool or isinstance(set_to_pool, dict) \
                and set_to_pool.get('failed'):
            return self.warning_could_not_fulfill_client_id_request()
        instruction_set_response = {
            'failed': False,
            'client_id': client_id,
        }
        return instruction_set_response

#   @pysnooper.snoop()
    def action_request_session_token(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session object, assigns it an existing
                    available worker or creates a new worker if none found,
                    generates a new session token and maps it to the Client ID.
        '''
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found(kwargs)
        client_id = kwargs['client_id']
        sanitized_instruction_set = self.res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'new'
        )
        new_session = self.session_manager_controller(
            controller='system', ctype='action', action='new', new='session',
            **sanitized_instruction_set
        )
        if not new_session or isinstance(new_session, dict) and \
                new_session.get('failed'):
            return self.error_could_not_spawn_new_ewallet_session(kwargs)
        ewallet_session = new_session['ewallet_session']
        assigned_worker = self.fetch_ewallet_session_assigned_worker(ewallet_session) or \
            self.assign_new_ewallet_session_to_worker(ewallet_session)
        if not assigned_worker:
            return self.error_could_not_assign_worker_to_new_ewallet_session(ewallet_session)
        session_token = self.generate_ewallet_session_token()
        if not session_token:
            return self.error_could_not_generate_ewallet_session_token(ewallet_session)
        mapping = self.map_client_id_to_ewallet_session(
            client_id, session_token, assigned_worker, ewallet_session
        )
        if not mapping or isinstance(mapping, dict) and mapping.get('failed'):
            return self.error_could_not_map_client_id_to_session_token(
                client_id, session_token
            )
        instruction_set_response = {
            'failed': False,
            'session_token': session_token,
#           'ewallet_session': ewallet_session,
        }
        return instruction_set_response

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

    def handle_system_action_new_worker(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session Manager Worker object and sets
                    it to worker pool.
        '''
        log.debug('')
        worker = self.action_new_worker()
        set_to_pool = self.set_worker_to_pool(worker)
        instruction_set_response = {
            'failed': False,
            'worker': worker,
        }
        return instruction_set_response

    def handle_system_action_interogate_ewallet_workers(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_workers(**kwargs)

#   @pysnooper.snoop()
    def handle_client_action_login(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        user_login = self.login_ewallet_user_account_in_session(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return user_login

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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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

    def handle_client_action_new_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_contact_list = self.action_new_contact_list(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return new_contact_list

    def handle_client_action_new_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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

    def handle_client_action_edit_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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
        if not instruction_set_validation:
            return False
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

    def handle_client_action_view_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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

    def handle_client_action_new_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_contact_record = self.action_new_contact_record(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set'],
        )
        return new_contact_record

    def handle_client_action_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_new_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_contact_list,
            'record': self.handle_client_action_new_contact_record,
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
            'login': self.handle_client_action_view_login_records,
            'logout': self.handle_client_action_view_logout_records,
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet.get('ewallet_session') or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        conversion = self.action_convert_credit_clock_to_credits(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return conversion

#   #@pysnooper.snoop()
    def handle_client_action_supply_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
                kwargs
                )
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
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
        if not ewallet or not ewallet['ewallet_session'] or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        start_timer = self.action_start_credit_clock_timer(
                ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
                )
        return start_timer

    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        return self.action_request_client_id()

#   @pysnooper.snoop()
    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('')
        return self.action_request_session_token(**kwargs)

    def handle_client_action_new_account(self, **kwargs):
        '''
        [ NOTE   ]: Validates received instruction set, searches for worker and session
                    and proceeds to create new User Account in said session. Requiers
                    valid Client ID and Session Token.
        '''
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation:
            return False
        ewallet = self.fetch_ewallet_session_for_client_action_using_instruction_set(
            kwargs
        )
        if not ewallet or not ewallet.get('ewallet_session') or \
                isinstance(ewallet['ewallet_session'], dict) and \
                ewallet['ewallet_session'].get('failed'):
            return self.error_no_ewallet_session_found(kwargs)
        new_account = self.create_ewallet_user_account_in_session(
            ewallet['ewallet_session'], ewallet['sanitized_instruction_set']
        )
        return new_account

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

    def warning_could_not_pay_partner_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not pay partner account in session {}. '
                       'Details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_create_new_user_account(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not create new user account in EWallet Session {}. '
                       'Details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_resume_credit_clock_timer(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not resume credit clock timer in session {}. '\
                       'Details : {}'.format(ewallet_session, instruction_set)
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

    def warning_could_not_start_credit_clock_timer(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not start credit clock timer in session {}. '\
                       'Details : {}'.format(ewallet_session, instruction_set)
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_stop_credit_clock_timer(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not stop credit clock timer in session {}. '\
                       'Details : {}'.format(ewallet_session, instruction_set),
        }
        log.warning(instruction_set_response['warning'])
        return instruction_set_response

    def warning_could_not_convert_credits_to_credit_clock(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not convert ewallet credits to credit clock. '\
                       'Instruction set details : {}'.format(instruction_set),
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

    def warning_could_not_create_new_contact_list(self, ewallet_session, instruction_set):
        instruction_set_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new contact list in ewallet session {}. '\
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
            'warning': 'Could not convert credit clock time to credits. '\
                       'Command Chain Details : {}'.format(kwargs)
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

    # ERRORS

    def error_no_client_id_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No client id found. '\
                     'Instruction set details : {}.'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_session_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No EWallet session found. '\
                     'Instruction set details : {}.'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_session_manager_worker_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No EWallet session manager worker found. '\
                     'Instruction set details : {}.'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_mapped_session_worker_found_for_client_id(self, client_id):
        instruction_set_response = {
            'failed': True,
            'error': 'No mapped session worker found for client id {}.'\
                     .format(client_id),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_invalid_instruction_set_required_data(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid EWallet session manager instruction set required data. '\
                     'Instruction set details : {}'.format(instruction_set),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_session_manager_controller_specified(self):
        instruction_set_response = {
            'failed': True,
            'error': 'Invalid EWallet controller.'
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_fetch_session_worker_pool(self, **kwargs):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch session worker pool. '\
                     'Instruction set details : {}'.format(kwargs),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_could_not_scrape_ewallet_session(self, ewallet_session):
        instruction_set_response = {
            'failed': True,
            'error': 'Something went wrong. Could not scrape ewallet session {}.'\
                     .format(ewallet_session),
        }
        log.error(instruction_set_response['error'])
        return instruction_set_response

    def error_no_ewallet_sessions_found(self, instruction_set):
        instruction_set_response = {
            'failed': True,
            'error': 'No ewallet sessions found. Instruction set details : {}'\
                     .format(instruction_set),
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

    def error_ewallet_session_manager_worker_pool_empty(self):
        instruction_set_response = {
            'failed': True,
            'error': 'EWallet session manager worker pool empty.',
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

    def error_could_not_set_worker_pool(self, worker_pool):
        log.error('Something went wrong. Could not set worker pool : {}'.format(worker_pool))
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

# CODE DUMP
# import random
# import string
# import hashlib
# import datetime
# import threading
# import pprint
