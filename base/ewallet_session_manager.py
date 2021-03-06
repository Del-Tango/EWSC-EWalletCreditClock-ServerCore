import time
import os
import datetime
import logging
import pysnooper
import ast
import multiprocessing as mp
import json
import schedule
import threading

from multiprocessing import Process, Queue, Lock, Value

from .ewallet import EWallet
from .config import Config
from .res_utils import ResUtils
from .res_user import ResUser
from .res_master import ResMaster
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
    create_date = None
    write_date = None
    worker_pool = dict() # {<worker id>: {process: <Proc>, instruction: <Queue>, response: <Queue>, lock: <Value type-bool>}}
    ctoken_pool = dict() # {<label>: <ClientToken>}
    stoken_pool = dict() # {<label>: <SessionToken>}
    cron_pool = dict() # {<label>: {command: <list>, lock: <Lock>, state: <bool>}}
    cleaner_thread = None
    primary_session = None

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now()
        self.config = kwargs.get('config') or config
        self.res_utils = kwargs.get('res_utils') or res_utils
        self.socket_handler = kwargs.get('socket_handler') or \
            self.open_ewallet_session_manager_sockets()
        self.create_date = kwargs.get('create_date') or now,
        self.write_date = kwargs.get('write_date') or now,
        self.worker_pool = kwargs.get('worker_pool') or {}
        if not self.worker_pool:
            self.session_manager_controller(
                controller='system', ctype='action', action='new', new='worker'
            )
        self.ctoken_pool = kwargs.get('ctoken_pool') or {}
        self.stoken_pool = kwargs.get('stoken_pool') or {}
        self.cron_pool = kwargs.get('cron_pool') or {}
        self.primary_session = kwargs.get('primary_session') or \
            self.create_new_ewallet_session(
                reference='S:CorePrimary',
                expiration_date=None,
                master_id='system',
            )
        self.cleaner_thread = kwargs.get('cleaner_thread')
        check_score = self.check_system_core_account_exists()
        if not check_score:
            res_utils.create_system_user(self.primary_session)
        # Start cleaner crons on seperate thread
        self.session_manager_controller(**{
            'controller': 'system', 'ctype': 'action', 'action': 'start',
            'start': 'cleaner', 'clean': 'all'
        })

    # FETCHERS

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_master_accounts_by_id_set(self, master_account_ids, **kwargs):
        log.debug('')
        if not master_account_ids or not isinstance(master_account_ids, list):
            return self.error_invalid_master_account_id_set(master_account_ids)
        try:
            orm_session = kwargs.get('active_session') or \
                self.res_utils.session_factory()
            master_query = orm_session.query(ResMaster).filter(
                ResMaster.user_id.in_(master_account_ids)
            ).all()
            master_accounts = [
                next(
                    master for master in master_query
                    if master.user_id == user_id
                ) for user_id in master_account_ids
            ]
        except Exception as e:
            return self.error_could_not_fetch_master_accounts_by_id_set(
                master_account_ids, e
            )
        return self.warning_no_master_accounts_found_by_id_set(master_account_ids) \
            if not master_accounts else master_accounts

    # TODO
    def fetch_from_worker_pool(self):
        log.debug('TODO - UNIMPLEMENTED')
    def fetch_from_client_pool(self):
        log.debug('TODO - UNIMPLEMENTED')
    def fetch_from_client_session_map(self):
        log.debug('TODO - UNIMPLEMENTED')
    def fetch_ewallet_worker_sessions(self, ewallet_worker):
        log.debug('TODO - UNIMPLEMENTED')
    def fetch_from_ewallet_worker_session(self):
        log.debug('TODO - UNIMPLEMENTED')

    def fetch_default_session_worker_pool_size_limit(self):
        log.debug('')
        return int(config.worker_config['worker_limit'])

    def fetch_system_clear_session_worker_instruction(self, **kwargs):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'clear',
            'clear': 'session',
            'client_id': kwargs.get('client_id', ''),
            'session_token': kwargs.get('session_token', ''),
        }

    def fetch_master_remove_ctoken_worker_instruction(self, **kwargs):
        log.debug('')
        return {
            'controller': 'master',
            'ctype': 'action',
            'action': 'remove',
            'remove': 'ctoken',
            'ctoken': 'acquired',
            'client_id': kwargs.get('client_id', ''),
            'session_token': kwargs.get('session_token', ''),
            'master_id': kwargs.get('master_id'),
            'key': kwargs.get('key'),
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_master_account_by_email(self, master_account_email, **kwargs):
        log.debug('')
        if not master_account_email or not isinstance(master_account_email, str):
            return self.error_invalid_master_account_email(
                master_account_email, kwargs
            )
        try:
            orm_session = kwargs.get('active_session') or \
                self.res_utils.session_factory()
            master_account = list(orm_session.query(
               ResMaster
            ).filter_by(user_email=master_account_email))
        except Exception as e:
            return self.error_could_not_fetch_master_account_by_email_address(
                master_account_email, e
            )
        return self.warning_no_master_account_found_by_email(
            master_account_email
        ) if not master_account else master_account[0]

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_master_account_by_id(self, master_account_id, **kwargs):
        log.debug('')
        if not master_account_id or not isinstance(master_account_id, int):
            return self.error_invalid_master_account_id(master_account_id)
        try:
            orm_session = kwargs.get('active_session') or \
                self.res_utils.session_factory()
            master_account = list(orm_session.query(
               ResMaster
            ).filter_by(user_id=master_account_id))
        except Exception as e:
            return self.error_could_not_fetch_master_account_by_id(
                master_account_id, e
            )
        return self.warning_no_master_account_found_by_id(master_account_id) \
            if not master_account else master_account[0]

    def fetch_master_account_acquired_ctokens(self, master_id, **kwargs):
        log.debug('')
        ctoken_pool = self.fetch_ctoken_pool()
        if not ctoken_pool:
            return self.error_ctoken_pool_empty(master_id, kwargs, ctoken_pool)
        acquired_ctokens = {
            client_id: ctoken for client_id, ctoken in ctoken_pool.items() if
            ctoken.fetch_master() == master_id
        }
        return self.error_no_acquired_ctokens_found_for_master_account(
            master_id, kwargs, ctoken_pool, acquired_ctokens
        ) if not acquired_ctokens else acquired_ctokens

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_worker_identifier_by_client_id(self, client_id):
        log.debug('')
        client_pool = self.fetch_ctoken_pool()
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

    def fetch_default_master_account_subordonate_pool_size_limit(self):
        log.debug('')
        return int(config.master_config['subordonate_pool_size'])

    def fetch_master_accounts_marked_for_unlink(self, **kwargs):
        log.debug('')
        try:
            orm_session = kwargs.get('active_session') or \
                self.res_utils.session_factory()
            master_accounts = list(orm_session.query(
               ResMaster
            ).filter_by(to_unlink=True).all())
        except Exception as e:
            return self.error_could_not_fetch_master_accounts_marked_for_unlink(
                kwargs, e
            )
        return self.warning_no_master_accounts_marked_for_unlink_found(kwargs)\
            if not master_accounts else master_accounts

    def fetch_master_account_unlink_freeze_interval(self):
        log.debug('')
        return int(config.master_config['master_unlink_freeze_interval'])

    def fetch_subordonate_accounts_from_masters(self, master_accounts):
        log.debug('')
        if not master_accounts or not isinstance(master_accounts, list):
            return self.error_invalid_master_account_set(master_accounts)
        subordonates, masters = [], []
        try:
            for master in master_accounts:
                subpool = master.fetch_subordonate_account_pool()
                if not subpool or isinstance(subpool, dict) and \
                        subpool.get('failed'):
                    continue
                subordonates += subpool
                masters.append(master.fetch_user_id())
        except Exception as e:
            return self.error_could_not_fetch_subordonate_accounts_for_masters(
                master_accounts, subordonates, masters, e
            )
        return self.warning_no_subordonate_accounts_found_for_masters(
            master_accounts, subordonates, masters
        ) if not subordonates else subordonates

    def fetch_master_add_ctoken_worker_instruction(self, **kwargs):
        log.debug('')
        return {
            'controller': 'master',
            'ctype': 'action',
            'action': 'add',
            'add': 'ctoken',
            'ctoken': 'acquired',
            'client_id': kwargs.get('client_id', ''),
            'session_token': kwargs.get('session_token', ''),
            'master_id': kwargs.get('master_id'),
            'key': kwargs.get('key'),
        }

    # TODO - Refactor
#   @pysnooper.snoop()
    def fetch_ewallet_session_by_id(self, ewallet_session_id, **kwargs):
        log.debug('TODO - Refactor')
        if not ewallet_session_id or not isinstance(ewallet_session_id, int):
            return self.error_invalid_ewallet_session_id(ewallet_session_id)
        try:
            orm_session = kwargs.get('active_session') or \
                self.res_utils.session_factory()
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
        log.debug('TODO - Refactor')
        if not kwargs.get('session_id'):
            return self.error_no_session_id_found(kwargs)
        ewallet_session = self.fetch_ewallet_session_by_id(
            kwargs['session_id'], **kwargs
        )
        return self.warning_no_ewallet_session_found_by_id(kwargs) if not \
            ewallet_session else ewallet_session

    # TODO - Refactor
#   @pysnooper.snoop()
    def fetch_ewallet_session_for_client_action_using_instruction_set(self, instruction_set):
        log.debug('TODO - Refactor')
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

    def fetch_acquired_masters_from_client_token_set(self, client_token_set):
        '''
        [ NOTE ]: Fetches acquired master accounts for each ctoken in client token set,
                  assures unique item values and filters out None items.
        '''
        log.debug('')
        acquired_masters = []
        try:
            for client_id in client_token_set:
                ctoken = self.fetch_client_token_by_label(client_id)
                if not ctoken or isinstance(ctoken, dict) and \
                        ctoken.get('failed'):
                    self.warning_invalid_client_token_label(
                        client_id, client_token_set, acquired_masters, client_id
                    )
                    continue
                master_id = ctoken.fetch_master()
                if not master_id:
                    continue
                acquired_masters.append(master_id)
        except Exception as e:
            return self.error_could_not_fetch_acquired_masters_from_client_token_set(
                client_token_set, acquired_masters, e
            )
        return self.warning_no_acquired_master_accounts_found_by_ctokens(
            client_token_set, acquired_masters
        ) if not acquired_masters else acquired_masters

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_ewallet_session_ids_by_session_tokens(self, session_token_labels):
        log.debug('')
        worker_pool, session_worker_map = self.fetch_worker_pool(), {}
        instruction = self.fetch_ewallet_worker_session_search_by_stoken_instruction()
        for session_token in session_token_labels:
            instruction.update({'session_token': session_token})
            for worker_id in worker_pool:
                search = self.action_execute_system_instruction_set(
                    worker_id=worker_id, **instruction
                )
                if not search or isinstance(search, dict) and \
                        search.get('failed'):
                    continue
                try:
                    session_worker_map[worker_id].append(search['session'])
                except KeyError:
                    session_worker_map.update({worker_id: [search['session']]})
        return self.warning_no_ewallet_sessions_found_by_stokens(
            session_token_labels, worker_pool, instruction
        ) if not session_worker_map else session_worker_map

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_stokens_from_client_token_set(self, client_token_set):
        '''
        [ NOTE ]: Fetches stoken for each ctoken in client token set,
                  assures unique item values and filters out None items.
        '''
        log.debug('')
        session_tokens = []
        try:
            for client_id in client_token_set:
                ctoken = self.fetch_client_token_by_label(client_id)
                if not ctoken or isinstance(ctoken, dict) and \
                        ctoken.get('failed'):
                    self.warning_invalid_client_token_label(
                        client_id, client_token_set, session_tokens, client_id
                    )
                    continue
                session_token = ctoken.fetch_stoken()
                if not session_token:
                    continue
                session_tokens.append(session_token)
        except Exception as e:
            return self.error_could_not_fetch_stokens_from_client_token_set(
                client_token_set, session_tokens, e
            )
        return session_tokens

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_worker_pool_entry_by_id(self, worker_id, **kwargs):
        log.debug('')
        if not isinstance(worker_id, int):
            return self.error_invalid_worker_id(worker_id)
        wp_map = kwargs.get('worker_pool') or self.fetch_worker_pool()
        return wp_map.get(worker_id) or {}

    def fetch_ewallet_worker_session_search_by_stoken_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'search',
            'search': 'session',
            'session_token': str(),
        }

    def fetch_session_worker_interogate_session_pool_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session_pool',
        }

    def fetch_session_worker_has_empty_session_check_instruction(self):
        log.debug('')
        instruction = self.fetch_session_worker_interogate_session_pool_instruction()
        instruction.update({'pool': 'has_empty'})
        return instruction

    def fetch_session_worker_empty_session_check_instruction(self):
        log.debug('')
        instruction = self.fetch_session_worker_interogate_session_pool_instruction()
        instruction.update({'pool': 'empty'})
        return instruction

    def fetch_empty_ewallet_session_map(self, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or \
            self.fetch_ewallet_session_manager_worker_pool()
        if not worker_pool or isinstance(worker_pool, dict) and \
                worker_pool.get('failed'):
            return self.error_could_not_fetch_session_worker_pool(
                kwargs, worker_pool
            )
        workers_with_abandoned_sessions, now = {}, datetime.datetime.now()
        instruction = self.fetch_session_worker_empty_session_check_instruction()
        for worker_id in worker_pool:
            try:
                worker_interogation = self.action_execute_system_instruction_set(
                    worker_id=worker_id, **instruction
                )
                if not worker_interogation or \
                        isinstance(worker_interogation, dict) and \
                        worker_interogation.get('failed'):
                    self.warning_could_not_interogate_worker_session_pool(
                        kwargs, worker_pool, worker_id,
                        instruction, worker_interogation
                    )
                    continue
                if not worker_interogation['empty_sessions']:
                    continue
                workers_with_abandoned_sessions.update({
                    worker_id: worker_interogation['empty_sessions']
                })
            except Exception as e:
                self.warning_could_not_fetch_empty_ewallet_sessions_from_worker(
                    worker_id, worker_pool, instruction, e
                )
                continue
        return self.warning_no_empty_ewallet_sessions_found(
            kwargs, worker_pool, instruction
        ) if not workers_with_abandoned_sessions \
            else workers_with_abandoned_sessions

#   @pysnooper.snoop()
    def fetch_ewallet_sessions_past_expiration_date(self, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or \
            self.fetch_ewallet_session_manager_worker_pool()
        if not worker_pool or isinstance(worker_pool, dict) and \
                worker_pool.get('failed'):
            return self.error_could_not_fetch_session_worker_pool(
                kwargs, worker_pool
            )
        now, expired_sessions = datetime.datetime.now(), {}
        instruction = self.fetch_session_worker_expired_session_check_instruction()
        for worker_id in worker_pool:
            try:
                worker_interogation = self.action_execute_system_instruction_set(
                    worker_id=worker_id, **instruction
                )
                if not worker_interogation or \
                        isinstance(worker_interogation, dict) and \
                        worker_interogation.get('failed'):
                    self.warning_could_not_interogate_worker_session_pool(
                        kwargs, worker_pool, worker_id,
                        instruction, worker_interogation
                    )
                    continue
                if not worker_interogation['expired_sessions']:
                    continue
                expired_sessions.update({
                    worker_id: worker_interogation['expired_sessions']
                })
            except Exception as e:
                self.warning_could_not_fetch_expired_ewallet_sessions_from_worker(
                    worker_id, e
                )
                continue
        return self.warning_no_expired_ewallet_sessions_found(kwargs) \
            if not expired_sessions else expired_sessions

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_vacant_session_workers(self, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        sorted_worker_pool = self.sort_session_worker_pool_by_state_code(worker_pool)
        vacant_workers = list(sorted_worker_pool[0].keys())
        return self.warning_no_vacant_session_workers_found(
            worker_pool, vacant_workers
        ) if not vacant_workers else vacant_workers

    def fetch_stoken_pool(self):
        log.debug('')
        return self.stoken_pool

    def fetch_ctoken_pool(self):
        log.debug('')
        return self.ctoken_pool

    def fetch_client_token_cleaner_cron_function(self):
        log.debug('')
        return self.action_sweep_cleanup_client_tokens

    def fetch_client_token_cleaner_cron_default_interval(self):
        log.debug('')
        hours = self.config.cron_config['ctoken_cleaner_cron_interval']
        return int(hours)

    def fetch_client_token_cleaner_cron_default_label(self):
        log.debug('')
        return self.config.cron_config['ctoken_cleaner_cron_label']

    def fetch_ewallet_session_cleaner_cron_function(self):
        log.debug('')
        return self.action_sweep_cleanup_ewallet_sessions

    def fetch_ewallet_session_cleaner_cron_default_interval(self):
        log.debug('')
        hours = self.config.cron_config['session_cleaner_cron_interval']
        return int(hours)

    def fetch_ewallet_session_cleaner_cron_default_label(self):
        log.debug('')
        return self.config.cron_config['session_cleaner_cron_label']

    def fetch_session_worker_cleaner_cron_function(self):
        log.debug('')
        return self.action_sweep_cleanup_session_workers

    def fetch_session_worker_cleaner_cron_default_interval(self):
        log.debug('')
        hours = self.config.cron_config['worker_cleaner_cron_interval']
        return int(hours)

    def fetch_session_worker_cleaner_cron_default_label(self):
        log.debug('')
        return self.config.cron_config['worker_cleaner_cron_label']

    def fetch_user_account_cleaner_cron_default_label(self):
        log.debug('')
        return self.config.cron_config['account_cleaner_cron_label']

    def fetch_worker_state_interogation_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'state',
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_worker_state_code_interogation_instruction(self):
        log.debug('')
        instruction = self.fetch_worker_state_interogation_instruction()
        instruction.update({'state': 'code'})
        return instruction

    def fetch_worker_state_info_interogation_instruction(self):
        log.debug('')
        instruction = self.fetch_worker_state_interogation_instruction()
        instruction.update({'state': 'info'})
        return instruction

    def fetch_cron_pool(self):
        log.debug('')
        return self.cron_pool

    def fetch_cleaner_thread(self):
        log.debug('')
        cleaner_thread = self.cleaner_thread
        return self.error_no_cleaner_thread_found(self.cleaner_thread) \
            if not cleaner_thread else cleaner_thread

    def fetch_account_unlink_freeze_interval(self):
        log.debug('')
        days = self.config.client_config['account_unlink_freeze_interval']
        return int(days)

    def fetch_cron_pool_entry_by_label(self, label=str()):
        log.debug('')
        cron_pool = self.fetch_session_manager_cron_pool()
        if not cron_pool or isinstance(cron_pool, dict) and \
                cron_pool.get('failed'):
            return self.error_could_not_fetch_cron_pool(label, cron_pool)
        pool_entry = cron_pool.get(label)
        return self.warning_could_not_fetch_cron_pool_entry_by_label(
            label, cron_pool, pool_entry
        ) if not pool_entry else pool_entry

    def fetch_account_cleaner_cron_state(self):
        cron_pool = self.fetch_session_manager_cron_pool()
        if not cron_pool or isinstance(cron_pool, dict) and \
                cron_pool.get('failed'):
            return self.error_could_not_fetch_cron_pool(cron_pool)
        pool_entry = cron_pool.get(
            self.fetch_account_cleaner_cron_default_label()
        )
        return self.error_could_not_fetch_cleaner_cron_state(
            cron_pool, pool_entry
        ) if not pool_entry else pool_entry.get('state')

    def fetch_account_cleaner_cron_lock(self):
        log.debug('')
        cron_pool = self.fetch_session_manager_cron_pool()
        if not cron_pool or isinstance(cron_pool, dict) and \
                cron_pool.get('failed'):
            return self.error_could_not_fetch_cron_pool(cron_pool)
        pool_entry = cron_pool.get(
            self.fetch_account_cleaner_cron_default_label()
        )
        return self.error_could_not_fetch_cleaner_cron_lock(
            cron_pool, pool_entry
        ) if not pool_entry else pool_entry.get('lock')

    def fetch_account_cleaner_cron_default_label(self):
        log.debug('')
        return self.config.cron_config['account_cleaner_cron_label']

    def fetch_session_manager_cron_pool(self):
        log.debug('')
        return self.cron_pool

    def fetch_account_cleaner_cron_command_interface(self):
        log.debug('')
        cron_pool = self.fetch_session_manager_cron_pool()
        if not cron_pool or isinstance(cron_pool, dict) and \
                cron_pool.get('failed'):
            return self.error_could_not_fetch_cron_pool(cron_pool)
        pool_entry = cron_pool.get(
            self.fetch_account_cleaner_cron_default_label()
        )
        return self.error_could_not_fetch_cleaner_cron_command_interface(
            cron_pool, pool_entry
        ) if not pool_entry else pool_entry.get('command')

    def fetch_user_account_cleaner_cron_function(self):
        log.debug('')
        return self.cleanup_user_accounts

    def fetch_user_account_cleaner_cron_default_interval(self):
        log.debug('')
        hours = self.config.cron_config['account_cleaner_cron_interval']
        return int(hours)

    def fetch_session_worker_cleanup_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'cleanup',
            'cleanup': 'worker',
        }

    def fetch_ewallet_session_interogation_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session',
            'session': 'state',
        }

    def fetch_worker_new_system_session_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'add',
            'add': 'system_session'
        }

    def fetch_ewallet_system_session_expiration_date(self):
        log.debug('')
        validity_interval = self.fetch_default_ewallet_system_session_validity_in_hours()
        now = datetime.datetime.now()
        return now + datetime.timedelta(hours=validity_interval)

    def fetch_default_ewallet_system_session_validity_in_hours(self):
        log.debug('TODO - Fetch data from config file.')
        return 24

    def fetch_session_worker_state_code_check_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'state',
            'state': 'code',
        }

    def fetch_worker_session_target_cleanup_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'remove',
            'remove': 'session',
        }

    def fetch_session_worker_session_exists_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session',
            'session': 'exists',
        }

#   @pysnooper.snoop()
    def fetch_ewallet_session_assigned_worker(self, ewallet_session_id):
        log.debug('')
        worker_pool = self.fetch_worker_pool()
        instruction = self.fetch_session_worker_session_exists_instruction()
        instruction.update({'session_id': ewallet_session_id})
        for worker_id in worker_pool:
            check = self.action_execute_system_instruction_set(
                worker_id=worker_id, **instruction
            )
            if isinstance(check, dict) and check.get('failed'):
                return self.error_could_not_check_if_ewallet_session_is_assigned_to_worker(
                    ewallet_session_id, worker_pool, worker_id,
                    instruction, check
                )
            if not check.get('exists'):
                continue
            return worker_id
        return self.warning_no_worker_found_assigned_to_session(
            ewallet_session_id, worker_pool, instruction
        )

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_ewallet_session_manager_worker_pool(self):
        log.debug('')
        return self.worker_pool or \
            self.error_ewallet_session_manager_worker_pool_empty(
                self.worker_pool
            )

    def fetch_session_worker_expired_session_check_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'interogate',
            'interogate': 'session_pool',
            'pool': 'expired',
        }

    def fetch_session_worker_remove_session_set_instruction(self):
        log.debug('')
        return {
            'controller': 'system',
            'ctype': 'action',
            'action': 'remove',
            'remove': 'sessions',
            'sessions': list(),
        }

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

    def fetch_client_token_by_label(self, client_id):
        log.debug('')
        client_pool = self.fetch_ctoken_pool()
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
        if isinstance(worker_set, dict) and worker_set.get('failed'):
            return worker_set
        return list(worker_set.keys())

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
            self.config.client_config['session_token_validity']
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

    # SETTERS
    '''
    [ NOTE ]: Write date updates are done here.
    '''

    def remove_session_token_from_pool(self, stoken_label, **kwargs):
        log.debug('')
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        try:
            del stoken_pool[stoken_label]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_remove_session_token_from_pool(
                stoken_label, stoken_pool, kwargs, e
            )
        log.info(
            'Successfully removed session token '
            '{} from pool'.format(stoken_label)
        )
        return True

    def remove_client_token_from_pool(self, client_id, **kwargs):
        log.debug('')
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        try:
            del ctoken_pool[client_id]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_remove_client_token_from_pool(
                client_id, ctoken_pool, kwargs, e
            )
        log.info(
            'Successfully removed client token '
            '{} from pool'.format(client_id)
        )
        return True

    def remove_session_worker_from_pool(self, session_worker_id, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        try:
            del worker_pool[session_worker_id]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_remove_ewallet_session_worker_from_pool(
                session_worker_id, worker_pool, e
            )
        log.info(
            'Successfully removed ewallet session worker '
            '{} from pool.'.format(session_worker_id)
        )
        return True

    def set_cleaner_cron_states(self, flag=None):
        log.debug('')
        cron_pool = self.fetch_cron_pool()
        if not cron_pool or isinstance(cron_pool, dict) and \
                cron_pool.get('failed'):
            return self.error_could_not_fetch_cron_pool(flag, cron_pool)
        updated, update_count = [], 0
        for item in cron_pool:
            try:
                cron_pool[item]['active'] = flag
                self.update_write_date()
            except Exception as e:
                self.warning_could_not_set_cron_state_flag(
                    flag, cron_pool, item, e
                )
            updated.append(item)
            update_count += 1
        log.info(
            'Successfully updated {} session manager '
            'cron pool entry states - {}'.format(update_count, updated)
        )
        return True

    def set_cleaner_thread(self, cleaner_thread):
        log.debug('')
        try:
            self.cleaner_thread = cleaner_thread
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_cleaner_thread(
                cleaner_thread, self.cleaner_thread, e
            )
        return True

    def set_user_account_cleaner_cron_state(self, flag=None):
        log.debug('')
        pool_entry = self.fetch_cron_pool_entry_by_label(
            label=self.fetch_account_cleaner_cron_default_label()
        )
        try:
            pool_entry['active'] = flag
        except Exception as e:
            return self.error_cold_not_set_cleaner_cron_state(
                flag, pool_entry, e
            )
        log.info('Succesfully set AccountCleaner cron state.')
        return True

    def set_cron_job_pool_entry(self, **kwargs):
        log.debug('')
        try:
            self.cron_pool.update({
                kwargs.get('label'): {
                    'active': kwargs.get('active') or False,
                }
            })
            self.update_write_date()
        except Exception as e:
            return self.error_could_no_set_cron_job_pool_entry(
                kwargs, self.cron_pool, e
            )
        return True

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully updated session manager write date.')
        return True

    def set_new_session_token_to_pool(self, session_token_map):
        log.debug('')
        try:
            self.stoken_pool.update(session_token_map)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_stoken_pool(
                session_token_map, self.stoken_pool, e
            )
        log.info('Successfully updated session token pool.')
        return True

#   @pysnooper.snoop()
    def set_new_client_id_to_pool(self, client_id_map):
        log.debug('')
        try:
            self.ctoken_pool.update(client_id_map)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_client_pool(
                client_id_map, self.ctoken_pool, e
            )
        log.info('Successfully updated client id pool.')
        return True

#   @pysnooper.snoop()
    def set_worker_to_pool(self, worker_pool_record):
        log.debug('')
        try:
            self.worker_pool.update(worker_pool_record)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_pool(
                worker_pool_record, self.worker_pool, e
            )
        log.info('Successfully updated ewallet session worker pool.')
        return True

    def unset_socket_handler(self):
        '''
        [ NOTE   ]: Overrides socket_handler attribute with a None value.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if self.socket_handler in (None, False):
            return self.warning_session_manager_socket_handler_not_set(
                self.socket_handler
            )
        try:
            self.socket_handler = None
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_unset_socket_handler(
                self.socket_handler, e
            )
        log.info('Successfully unset session manager socket handler.')
        return True

    def set_socket_handler(self, socket_handler):
        '''
        [ NOTE   ]: Overrides socket_handler attribute with
                    new EWalletSocketHandler object.
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            if self.socket_handler:
                del self.socket_handler
            self.socket_handler = socket_handler
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_socket_handler(
                socket_handler, self.socket_handler, e
            )
        log.info('Successfully set session manager socket handler.')
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
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_worker_pool(
                worker_pool, self.worker_pool, e
            )
        log.info('Successfully set ewallet session worker pool')
        return True

    def set_client_pool(self, client_pool, **kwargs):
        '''
        [ NOTE   ]: Overrides entire client pool.
        [ INPUT  ]: [user_id1, user_id2, ...]
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.ctoken_pool = client_pool
            self.update_write_date()
        except Exception as e:
            return self.error_coult_not_set_client_pool(
                client_pool, self.ctoken_pool, e
            )
        log.info('Successfully set session manager client pool.')
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
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_update_worker_pool(
                worker, self.worker_pool, e
            )
        log.info('Successfully set ewallet session worker pool.')
        return True

    def set_to_client_pool(self, client, **kwargs):
        '''
        [ NOTE   ]: Adds new client user id to client pool stack.
        [ INPUT  ]: User ID
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        try:
            self.ctoken_pool.append(client)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_update_client_pool(
                client, self.ctoken_pool, e
            )
        log.info('Successfully set session manager client pool.')
        return True

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        return self.set_write_date(datetime.datetime.now())

    def update_worker_pool(self, worker_pool):
        '''
        [ NOTE   ]: Overrides Session Manager Worker Pool
                    and checks for type errors.
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
        [ NOTE   ]: Overrides Session Manager Client Pool
                    and checks for type errors.
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
        [ NOTE   ]: Overrides Session Manager Client Worker map
                    and checks for type errors.
        [ INPUT  ]: {user_id: session_token, ...}
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not cw_map:
            return self.error_client_worker_map_not_found()
        return self.error_invalid_client_worker_map(cw_map) \
            if not isinstance(cw_map, dict) else \
            self.set_client_worker_session_map(cw_map)

    # VERIFIERS

    def verify_stoken_linked_ctoken(self, stoken):
        log.debug('')
        ctoken = stoken.fetch_ctoken()
        if isinstance(ctoken, dict) and ctoken.get('failed'):
            return self.warning_could_not_fetch_stoken_linked_ctoken(
                stoken, ctoken
            )
        instruction_set_response = {
            'failed': False,
            'ctoken': ctoken,
            'valid': False if not ctoken else True,
        }
        if not ctoken:
            instruction_set_response.update({
                'reason': 'Unlinked',
                'details': 'No linked CToken found.',
            })
        return instruction_set_response

    def verify_ctoken_linked_stoken(self, ctoken):
        log.debug('')
        stoken = ctoken.fetch_stoken()
        if isinstance(stoken, dict) and stoken.get('failed'):
            return self.warning_could_not_fetch_ctoken_linked_stoken(
                ctoken, stoken
            )
        instruction_set_response = {
            'failed': False,
            'stoken': stoken,
            'valid': False if not stoken else True,
        }
        if not stoken:
            instruction_set_response.update({
                'reason': 'Unlinked',
                'details': 'No linked SToken found.',
            })
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def verify_ctoken_in_pool(self, ctoken):
        log.debug('')
        in_pool = self.check_ctoken_in_pool(ctoken)
        if isinstance(in_pool, dict) and in_pool.get('failed'):
            return self.warning_could_not_verify_ctoken_in_pool(ctoken, in_pool)
        instruction_set_response = {
            'failed': False,
            'ctoken': ctoken,
            'valid': in_pool,
        }
        if not in_pool:
            instruction_set_response.update({
                'reason': 'Unregistered',
                'details': 'Token not found in pool.',
            })
        return instruction_set_response

    def verify_stoken_in_pool(self, stoken):
        log.debug('')
        in_pool = self.check_stoken_in_pool(stoken)
        if isinstance(in_pool, dict) and in_pool.get('failed'):
            return self.warning_could_not_verify_stoken_in_pool(stoken, in_pool)
        instruction_set_response = {
            'failed': False,
            'stoken': stoken,
            'valid': in_pool,
        }
        if not in_pool:
            instruction_set_response.update({
                'reason': 'Unregistered',
                'details': 'Token not found in pool.',
            })
        return instruction_set_response

    def verify_stoken_expired(self, stoken):
        log.debug('')
        stoken_expired = self.check_session_token_expired(stoken.fetch_label())
        instruction_set_response = {
            'failed': False,
            'stoken': stoken,
            'valid': True if not stoken_expired else False,
        }
        if stoken_expired:
            instruction_set_response.update({
                'reason': 'Expired',
                'details': 'Expiration date: {}'.format(
                    res_utils.format_datetime(
                    stoken.fetch_token_expiration_date()
                    )
                ),
            })
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def verify_ctoken_expired(self, ctoken):
        log.debug('')
        ctoken_expired = self.check_client_token_expired(ctoken.fetch_label())
        instruction_set_response = {
            'failed': False,
            'ctoken': ctoken,
            'valid': True if not ctoken_expired else False,
        }
        if ctoken_expired:
            instruction_set_response.update({
                'reason': 'Expired',
                'details': 'Expiration date: {}'.format(
                    res_utils.format_datetime(
                    ctoken.fetch_token_expiration_date()
                    )
                ),
            })
        return instruction_set_response

    # CHECKERS

    # TODO
    def check_command_chain_session_token(self):
        log.debug('TODO - UNIMPLEMENTED')
    def check_command_chain_instruction_set(self):
        log.debug('TODO - UNIMPLEMENTED')

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def check_worker_is_available(self, worker_id, **kwargs):
        log.debug('TODO - Refactor, sync processes with Semaphore objects.')
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
            time.sleep(0.1)
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

    def check_ctoken_acquired_master_account(self, client_id):
        log.debug('')
        ctoken = self.fetch_client_token_by_label(client_id)
        has_master = ctoken.fetch_master()
        return False if not has_master else True

    def check_stoken_in_pool(self, stoken):
        log.debug('')
        stoken_pool = self.fetch_stoken_pool()
        if not isinstance(stoken_pool, dict):
            return self.error_invalid_stoken_pool(stoken, stoken_pool)
        return False if stoken not in stoken_pool.values() else True

    def check_ctoken_in_pool(self, ctoken):
        log.debug('')
        ctoken_pool = self.fetch_ctoken_pool()
        if not isinstance(ctoken_pool, dict):
            return self.error_invalid_ctoken_pool(ctoken, ctoken_pool)
        return False if ctoken not in ctoken_pool.values() else True

    def check_session_token_expired(self, session_token):
        log.debug('')
        stoken = self.fetch_session_token_by_label(session_token)
        if isinstance(stoken, dict) and stoken.get('failed'):
            return self.error_could_not_fetch_client_token(
                session_token, stoken
            )
        return stoken.check_token_expired()

    def check_client_token_expired(self, client_id):
        log.debug('')
        ctoken = self.fetch_client_token_by_label(client_id)
        if isinstance(ctoken, dict) and ctoken.get('failed'):
            return self.error_could_not_fetch_client_token(
                client_id, ctoken
            )
        return ctoken.check_token_expired()

    def check_cleaner_thread_active(self):
        log.debug('')
        cleaner_thread = self.fetch_cleaner_thread()
        if isinstance(cleaner_thread, dict) and \
                cleaner_thread.get('failed'):
            return self.error_could_not_fetch_cleaner_thread(cleaner_thread)
        return False if not cleaner_thread.is_alive() else True

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

    # FILTERS

#   @pysnooper.snoop('logs/ewallet.log')
    def filter_unlinked_master_accounts_past_freeze_inteval(self, master_accounts, freeze_interval):
        log.debug('')
        if not master_accounts or not isinstance(master_accounts, list):
            return self.error_no_master_accounts_found(
                master_accounts, freeze_interval
            )
        unlink_overdue, not_to_unlink, unlink_pending = [], [], []
        for master in master_accounts:
            to_unlink = master.fetch_user_to_unlink()
            if not to_unlink:
                not_to_unlink.append(master)
                continue
            unlink_timestamp = master.fetch_user_to_unlink_timestamp()
            check_days_passed = res_utils.check_days_since_timestamp(
                unlink_timestamp, freeze_interval
            )
            if not check_days_passed:
                unlink_pending.append(master)
                continue
            unlink_overdue.append(master)
        instruction_set_response = {
            'failed': False,
            'unlink_overdue': unlink_overdue,
            'not_to_unlink': not_to_unlink,
            'unlink_pending': unlink_pending
        }
        return instruction_set_response

    # SPAWNERS

    def spawn_ewallet_session(self, orm_session, **kwargs):
        log.debug('')
        return EWallet(
            name=kwargs.get('reference'), session=orm_session,
            expiration_date=kwargs.get('expiration_date')
        )

#   @pysnooper.snoop('logs/ewallet.log')
    def spawn_ewallet_session_worker(self, **kwargs):
        log.debug('')
        existing_worker_ids = self.fetch_ewallet_session_worker_ids()
        if not existing_worker_ids or isinstance(existing_worker_ids, dict) and\
                existing_worker_ids.get('failed'):
            existing_worker_ids = list()

        worker_limit = self.fetch_default_session_worker_pool_size_limit()
        if len(existing_worker_ids) >= worker_limit:
            return self.warning_session_worker_limit_reached(
                kwargs, worker_limit
            )
        worker_id = kwargs.get('worker_id') or \
            self.generate_id_for_entity_set(existing_worker_ids)
        if not worker_id or isinstance(worker_id, dict) and\
                worker_id.get('failed'):
            return self.error_could_not_generate_session_worker_identifier(
                kwargs, worker_id, existing_worker_ids
            )
        termination_signal = self.fetch_default_session_worker_termination_signal()
        return EWalletWorker(
            id=worker_id, sigterm=termination_signal, **kwargs
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

    # SETUPS

    def setup_client_token_cleaner_cron(self):
        log.debug('')
        interval = res_utils.compute_number_of_minutes_from_hours(
            self.fetch_client_token_cleaner_cron_default_interval()
        )
        label = self.fetch_client_token_cleaner_cron_default_label()
        try:
            schedule.every(interval).hours.do(
                self.fetch_client_token_cleaner_cron_function(),
                ctoken_pool=self.fetch_ctoken_pool(),
                from_cron=True,
            ).tag(label, 'Cron')
        except Exception as e:
            return self.error_could_not_setup_client_token_cleaner_cron(
                label, interval, e
            )
        active_state = False if not self.check_cleaner_thread_active() else True
        set_pool_entry = self.set_cron_job_pool_entry(
            label=label, active=active_state
        )
        instruction_set_response = {
            'failed': False,
            'interval': interval,
            'active': active_state,
        }
        return instruction_set_response

    def setup_ewallet_session_cleaner_cron(self):
        log.debug('')
        interval = res_utils.compute_number_of_minutes_from_hours(
            self.fetch_ewallet_session_cleaner_cron_default_interval()
        )
        label = self.fetch_ewallet_session_cleaner_cron_default_label()
        try:
            schedule.every(interval).hours.do(
                self.fetch_ewallet_session_cleaner_cron_function(),
                worker_pool=self.fetch_worker_pool(),
                from_cron=True,
            ).tag(label, 'Cron')
        except Exception as e:
            return self.error_could_not_setup_ewallet_session_cleaner_cron(
                label, interval, e
            )
        active_state = False if not self.check_cleaner_thread_active() else True
        set_pool_entry = self.set_cron_job_pool_entry(
            label=label, active=active_state
        )
        instruction_set_response = {
            'failed': False,
            'interval': interval,
            'active': active_state,
        }
        return instruction_set_response

    def setup_session_worker_cleaner_cron(self):
        log.debug('')
        interval = res_utils.compute_number_of_minutes_from_hours(
            self.fetch_session_worker_cleaner_cron_default_interval()
        )
        label = self.fetch_session_worker_cleaner_cron_default_label()
        try:
            schedule.every(interval).minutes.do(
                self.fetch_session_worker_cleaner_cron_function(),
                worker_pool=self.fetch_worker_pool(),
                from_cron=True,
            ).tag(label, 'Cron')
        except Exception as e:
            return self.error_could_not_setup_session_worker_cleaner_cron(
                label, interval, e
            )
        active_state = False if not self.check_cleaner_thread_active() else True
        set_pool_entry = self.set_cron_job_pool_entry(
            label=label, active=active_state
        )
        instruction_set_response = {
            'failed': False,
            'interval': interval,
            'active': active_state,
        }
        return instruction_set_response

    def setup_user_account_cleaner_cron(self):
        log.debug('')
        interval = res_utils.compute_number_of_minutes_from_hours(
            self.fetch_user_account_cleaner_cron_default_interval()
        )
        try:
            schedule.every(interval).minutes.do(
                self.fetch_user_account_cleaner_cron_function(),
                from_cron=True,
            ).tag(self.fetch_account_cleaner_cron_default_label(), 'Cron')
        except Exception as e:
            return self.error_could_not_setup_account_cleaner_cron(interval, e)
        active_state = False if not self.check_cleaner_thread_active() else True
        set_pool_entry = self.set_cron_job_pool_entry(
            label=self.fetch_account_cleaner_cron_default_label(),
            active=active_state
        )
        instruction_set_response = {
            'failed': False,
            'interval': interval,
            'active': active_state,
        }
        return instruction_set_response

    # SCRAPERS

    # MAPPERS

    def map_worker_id_to_session_token(self, stoken, worker):
        log.debug('')
        if not isinstance(stoken, object) or not isinstance(worker, object):
            return self.error_invalid_stoken_worker_pair(stoken, worker)
        try:
            stoken.set_worker_id(worker.fetch_worker_id())
        except Exception as e:
            return self.error_could_not_map_worker_id_to_session_token(
                stoken, worker, e
            )
        return {
            'failed': False,
            'stoken': stoken,
            'worker': worker,
        }

    def map_client_session_tokens(self, ctoken, stoken):
        log.debug('')
        if not isinstance(ctoken, object) or not isinstance(stoken, object):
            return self.error_invalid_client_session_token_pair(ctoken, stoken)
        try:
            ctoken.set_stoken(stoken)
            stoken.set_ctoken(ctoken)
        except Exception as e:
            return self.error_could_not_map_client_session_tokens(
                ctoken, stoken, e
            )
        return {
            'failed': False,
            'ctoken': ctoken,
            'stoken': stoken,
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def map_client_id_to_worker(self, client_id, assigned_worker_id):
        log.debug('')
        update_map = self.update_client_worker_map(
            {client_id: assigned_worker_id}
        )
        return update_map or False

    def map_client_id_to_ewallet_session(
        self, client_id, session_token, assigned_worker, ewallet_session):
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
            'worker_to_stoken': self.map_worker_id_to_session_token(
                session_token, assigned_worker
            ),
        }
        return False if False in mappers.values() else True

    def map_client_id_to_session_token(
        self, client_id, session_token, assigned_worker, ewallet_session):
        log.debug('')
        update_map = assigned_worker.main_controller(
            controller='system', ctype='action', action='add', add='session_map',
            client_id=client_id, session_token=session_token,
            session=ewallet_session
        )
        return update_map or False

    # VALIDATORS

    # TODO
    def validate_client_id_timestamp(self, client_id):
        log.debug('TODO - Refactor')
        time_stamp = client_id[2]
        return True

    # TODO
    def validate_session_token_timestamp(self, session_token):
        log.debug('TODO - Refactor')
        timestamp = session_token[2]
        return True

    def validate_client_token_in_pool(self, client_token):
        log.debug('')
        return False if client_token not in self.ctoken_pool.values() else True

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

#   @pysnooper.snoop('logs/ewallet.log')
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

#   @pysnooper.snoop('logs/ewallet.log')
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
        session_token = self.generate_ewallet_session_token(**kwargs)
        if not session_token or isinstance(session_token, dict) and \
                session_token.get('failed'):
            return self.error_could_not_generate_ewallet_session_token(
                session_token, kwargs
            )
        # Map tokens
        return self.map_client_session_tokens(client_token, session_token)

    def create_new_system_session(self, **kwargs):
        log.debug('')
        worker_id = kwargs.get('worker_id') or \
            self.fetch_available_worker_id()
        instruction = self.fetch_worker_new_system_session_instruction()
        return self.action_execute_system_instruction_set(
            worker_id=worker_id, **instruction
        )

#   @pysnooper.snoop('logs/ewallet.log')
    def create_new_ewallet_session(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        ewallet_session = self.spawn_ewallet_session(orm_session, **kwargs)
        orm_session.add(ewallet_session)
        orm_session.commit()
        return ewallet_session

    # SORTERS

#   @pysnooper.snoop('logs/ewallet.log')
    def sort_session_worker_pool_by_state_code(self, worker_pool):
        log.debug('')
        worker_instruction = self.fetch_worker_state_code_interogation_instruction()
        sorted_workers = {0: {}, 1: {}, 2: {}}
        for worker_id in worker_pool:
            interogation = self.action_execute_system_instruction_set(
                worker_id=worker_id, **worker_instruction
            )
            if isinstance(interogation, dict) and interogation.get('failed'):
                self.warning_session_worker_interogation_failure(
                    worker_id, worker_instruction, interogation, worker_pool
                )
                continue
            state_code = interogation.get('state')
            if state_code not in sorted_workers:
                self.warning_invalid_session_worker_state_code(
                    worker_id, state_code, worker_instruction,
                    interogation, worker_pool
                )
                continue
            sorted_workers[state_code].update(
                {worker_id: worker_pool[worker_id]}
            )
        return sorted_workers or \
            self.warning_could_not_sort_worker_pool_by_state_code(
                worker_pool, worker_instruction, sorted_workers
            )

    # CLEANERS

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_user_accounts(self, **kwargs):
        log.debug(
            'TODO - Refactor '
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_account_cleaner_cron_default_label()
            )
        )
        freeze_interval = self.fetch_account_unlink_freeze_interval()
        orm_session = res_utils.session_factory()
        accounts_removed = []
        user_query = list(
            orm_session.query(ResUser).filter_by(to_unlink=True)
        )
        if not user_query:
            log.info('No user accounts marked for unlink found.')
            return False
        accounts_to_unlink = len(user_query)
        try:
            sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
                kwargs, 'action', 'cleanup', 'account'
            )
            for account in user_query:
                user_id = account.fetch_user_id()
                check = res_utils.check_days_since_timestamp(
                    account.to_unlink_timestamp, freeze_interval
                )
                log.info('Checking unlink timestamp...')
                if not check:
                    log.info('Account {} not ready for unlink.'.format(user_id))
                    continue
                log.info('Cleaning up user account {}.'.format(user_id))
                account.user_controller(
                    ctype='action', action='cleanup', cleanup='account',
                    **sanitized_instruction_set
                )
                try:
                    orm_session.query(ResUser).filter_by(user_id=user_id).delete()
                    orm_session.commit()
                except Exception as e:
                    self.warning_could_not_cleanup_user_account(
                        freeze_interval, orm_session, accounts_removed, user_query,
                        accounts_to_unlink, account, check, user_id, e
                    )
                    continue
                accounts_removed.append(user_id)
        finally:
            orm_session.close()

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_master_user_accounts(self, master_ids):
        log.debug('TODO - Refactor')
        orm_session = res_utils.session_factory()
        accounts_removed, cleanup_failures = [], 0
        try:
            user_query = list(
                orm_session.query(ResMaster).filter(
                    ResMaster.user_id.in_(master_ids)
                )
            )
            if not user_query:
                log.info('No master user accounts found by ID set.')
                return False
        except Exception as e:
            return self.error_could_not_fetch_master_accounts_by_identifier_set(
                master_ids, orm_session, e
            )
        accounts_to_unlink = len(user_query)
        try:
            for account in user_query:
                user_id = account.fetch_user_id()
                log.info('Cleaning up master user account {}.'.format(user_id))
                try:
                    orm_session.query(ResMaster)\
                        .filter_by(user_id=user_id).delete()
                    orm_session.commit()
                except Exception as e:
                    self.warning_could_not_cleanup_user_account(
                        orm_session, accounts_removed, user_query,
                        accounts_to_unlink, account, user_id,
                        cleanup_failures, e
                    )
                    cleanup_failures += 1
                    continue
                accounts_removed.append(user_id)
        finally:
            orm_session.close()
        instruction_set_response = {
            'failed': False,
            'masters': accounts_removed,
            'cleanup_failures': cleanup_failures,
            'masters_cleaned': len(accounts_removed),
        }
        return instruction_set_response

    def cleanup_subordonate_user_accounts(self, user_account_ids, **kwargs):
        log.debug('')
        orm_session = kwargs.get('orm_session') or res_utils.session_factory()
        try:
            delete_users = orm_session.query(ResUser).filter(
                ResUser.user_id.in_(user_account_ids)
            ).delete()
        except Exception as e:
            return self.error_could_not_delete_subordonate_user_accounts(
                user_account_ids, kwargs, orm_session, e
            )
        instruction_set_response = {
            'failed': False,
            'subordonates': user_account_ids,
            'subordonates_cleaned': len(user_account_ids),
        }
        return instruction_set_response

    # TODO
    def cleanup_master_account_subordonate_pool(self, master_id):
        log.debug('TODO - Refactor')
        orm_session = res_utils.session_factory()
        master_account = self.fetch_master_account_by_id(master_id)
        accounts_removed, cleanup_failures = [], 0
        user_query = list(
            orm_session.query(ResMaster).filter_by(user_id=master_id)
        )
        if not user_query:
            log.info('No master user account found by ID.')
            return False
        accounts_to_unlink = len(user_query)
        try:
            account = user_query[0]
            subpool = account.fetch_subordonate_account_pool()
            sub_ids = [account.fetch_user_id() for account in subpool]
            subpool_cleanup = self.cleanup_subordonate_user_accounts(
                sub_ids, orm_session=orm_session
            )
            if not subpool_cleanup or isinstance(subpool_cleanup, dict) and \
                    subpool_cleanup.get('failed'):
                return self.error_could_not_cleanup_master_account_subpool(
                    master_id, orm_session, master_account, accounts_removed,
                    cleanup_failures, user_query, accounts_to_unlink, account,
                    subpool, sub_ids, subpool_cleanup
                )
            accounts_removed += sub_ids
        except Exception as e:
            return self.error_could_not_cleanup_master_account_subpool(
                master_id, orm_session, master_account, accounts_removed,
                cleanup_failures, user_query, e
            )
        instruction_set_response = {
            'failed': False,
            'masters': [master_id],
            'subordonates': accounts_removed,
            'cleanup_failures': cleanup_failures,
            'masters_cleaned': 1,
            'subordonates_cleaned': len(accounts_removed),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_worker_map'):
            return self.error_no_ewallet_session_worker_map_found(kwargs)
        instruction = self.fetch_session_worker_remove_session_set_instruction()
        session_tokens_to_remove, session_workers, ewallet_sessions = [], [], []
        orphaned_stokens, cleanup_failures = [], 0
        for worker_id in kwargs['session_worker_map']:
            instruction.update({
                'sessions': kwargs['session_worker_map'][worker_id]
            })
            clean = self.action_execute_system_instruction_set(
                worker_id=worker_id, **instruction
            )
            if not clean or isinstance(clean, dict) and \
                    clean.get('failed'):
                cleanup_failures += 1
                self.warning_could_not_clean_worker_sessions(
                    kwargs, instruction, worker_id, clean
                )
                continue
            orphaned_stokens = clean['orphaned_stokens']
            ewallet_sessions += clean['sessions']
            session_workers.append(worker_id)
        if not ewallet_sessions:
            return self.warning_could_not_cleanup_ewallet_sessions(
                kwargs, instruction, session_tokens_to_remove, session_workers,
                ewallet_sessions, orphaned_stokens, cleanup_failures,
            )
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': len(ewallet_sessions),
            'cleanup_failures': cleanup_failures,
            'worker_count': len(session_workers),
            'workers': session_workers,
            'sessions': ewallet_sessions,
            'orphaned_stokens': orphaned_stokens,
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def sweep_cleanup_client_tokens(self, **kwargs):
        log.debug('TODO - Refactor')
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        ctokens_to_remove = [
            client_id for client_id in ctoken_pool
            if self.check_client_token_expired(client_id)
        ]
        if not ctokens_to_remove:
            return self.warning_no_client_tokens_to_remove(
                kwargs, ctoken_pool, ctokens_to_remove
            )
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctoken_pool'
        )
        stokens_to_remove = self.fetch_stokens_from_client_token_set(
            ctokens_to_remove
        )
        sessions_to_remove = self.fetch_ewallet_session_ids_by_session_tokens(
            stokens_to_remove
        )
        session_cleanup = self.cleanup_ewallet_sessions(
            session_worker_map=sessions_to_remove
        )
        stoken_cleanup = self.cleanup_session_tokens(
            stokens_to_remove, ctoken_pool=ctoken_pool
        )
        if isinstance(stoken_cleanup, dict) and stoken_cleanup.get('failed'):
            self.warning_could_not_cleanup_ctoken_linked_stokens(
                kwargs, ctoken_pool, ctokens_to_remove,
                stokens_to_remove, stoken_cleanup, session_cleanup
            )
        ctoken_cleanup = self.cleanup_client_tokens(
            ctokens_to_remove, ctoken_pool=ctoken_pool,
            **sanitized_instruction_set
        )
        if isinstance(ctoken_cleanup, dict) and ctoken_cleanup.get('failed'):
            return self.error_could_not_cleanup_client_tokens(
                kwargs, ctoken_pool, ctokens_to_remove, ctoken_cleanup,
                session_cleanup
            )
        instruction_set_response = {
            'failed': False,
            'ctokens_cleaned': ctoken_cleanup['ctokens_cleaned'],
            'cleanup_failures': ctoken_cleanup['cleanup_failures'] \
                + session_cleanup.get('cleanup_failures', 0) \
                + stoken_cleanup.get('cleanup_failures', 0),
            'ctokens': ctoken_cleanup['ctokens'],
            'stokens_cleaned': stoken_cleanup.get('stokens_cleaned', 0),
            'stokens': stoken_cleanup.get('stokens', []),
            'sessions_cleaned': session_cleanup.get('sessions_cleaned', 0),
            'worker_count': session_cleanup.get('worker_count', 0),
            'workers': session_cleanup.get('workers', []),
            'sessions': session_cleanup.get('sessions', []),
        }
        return instruction_set_response

    def cleanup_client_token(self, client_id, **kwargs):
        log.debug('')
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        if client_id not in ctoken_pool:
            return self.error_client_id_not_found_in_ctoken_pool(
                client_id, ctoken_pool, kwargs
            )
        remove = self.remove_client_token_from_pool(client_id, **kwargs)
        if not remove or isinstance(remove, dict) and \
                remove.get('failed'):
            return self.error_could_not_remove_client_token_from_pool(
                client_id, remove
            )
        return {
            'failed': False,
            'ctokens_cleaned': 1,
            'ctokens': [client_id],
        }

    def cleanup_client_tokens(self, client_ids, **kwargs):
        log.debug('')
        ctoken_pool = kwargs.get('ctoken_pool') or \
            self.fetch_ctoken_pool()
        cleaned_tokens, cleaning_failures = [], 0
        for client_id in client_ids:
            clean = self.cleanup_client_token(
                client_id, **kwargs
            )
            if isinstance(clean, dict) and clean.get('failed'):
                self.warning_could_not_clean_client_token(
                    client_id, client_ids, clean
                )
                cleaning_failures += 1
                continue
            cleaned_tokens.append(client_id)
        return self.warning_no_client_tokens_cleaned(client_ids) \
            if not cleaned_tokens else {
                'failed': False,
                'ctokens_cleaned': len(cleaned_tokens),
                'cleanup_failures': cleaning_failures,
                'ctokens': cleaned_tokens
            }

#   @pysnooper.snoop('logs/ewallet.log')
    def sweep_cleanup_session_tokens(self, **kwargs):
        log.debug('')
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        tokens_to_remove = [
            session_token for session_token in stoken_pool
            if self.check_session_token_expired(session_token)
        ]
        sessions_to_remove = self.fetch_ewallet_session_ids_by_session_tokens(
            tokens_to_remove
        )
        if not tokens_to_remove:
            return self.warning_no_session_tokens_to_remove(
                kwargs, stoken_pool, tokens_to_remove
            )
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'stoken_pool'
        )
        cleanup_sessions = self.cleanup_ewallet_sessions(
            session_worker_map=sessions_to_remove
        )
        cleanup_stokens = self.cleanup_session_tokens(
            tokens_to_remove, stoken_pool=stoken_pool,
            **sanitized_instruction_set
        )
        cleanup = False if not (cleanup_sessions and cleanup_stokens) \
            or (isinstance(cleanup_sessions, dict) and cleanup_sessions.get('failed')) \
            or (isinstance(cleanup_stokens, dict) and cleanup_stokens.get('failed')) \
            else True
        if not cleanup:
            return self.error_could_not_cleanup_session_tokens(
                kwargs, stoken_pool, tokens_to_remove, cleanup_sessions,
                cleanup_stokens, cleanup
            )
        instruction_set_response = {
            'failed': False,
            'stokens_cleaned': cleanup_stokens.get('stokens_cleaned', 0),
            'cleanup_failures': cleanup_stokens.get('cleanup_failures', 0)
                + cleanup_sessions.get('cleanup_failures', 0),
            'stokens': cleanup_stokens.get('stokens', []),
            'sessions_cleaned': cleanup_sessions.get('sessions_cleaned', 0),
            'sessions': cleanup_sessions.get('sessions', []),
            'worker_count': cleanup_sessions.get('worker_count', 0),
            'workers': cleanup_sessions.get('workers', []),
        }
        return instruction_set_response

    def cleanup_session_tokens(self, stoken_labels, **kwargs):
        log.debug('')
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        cleaned_tokens, cleaning_failures = [], 0
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'stoken_pool'
        )
        for stoken_label in stoken_labels:
            clean = self.cleanup_session_token(
                stoken_label, stoken_pool=stoken_pool,
                **sanitized_instruction_set
            )
            if isinstance(clean, dict) and clean.get('failed'):
                self.warning_could_not_clean_session_token(
                    stoken_label, stoken_labels, stoken_pool, clean
                )
                cleaning_failures += 1
                continue
            cleaned_tokens.append(stoken_label)
        return self.warning_no_session_tokens_cleaned(stoken_labels) \
            if not cleaned_tokens else {
                'failed': False,
                'stokens_cleaned': len(cleaned_tokens),
                'cleanup_failures': cleaning_failures,
                'stokens': cleaned_tokens
            }

#   @pysnooper.snoop('logs/ewallet.log')
    def sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_worker_map'):
            return self.error_no_ewallet_session_worker_map_found(kwargs)
        instruction = self.fetch_session_worker_remove_session_set_instruction()
        session_tokens_to_remove, session_workers = [], []
        cleanup_failures, session_count = 0, 0
        for worker_id in kwargs['session_worker_map']:
            instruction.update({
                'sessions': kwargs['session_worker_map'][worker_id]
            })
            clean = self.action_execute_system_instruction_set(
                worker_id=worker_id, **instruction
            )
            if not clean or isinstance(clean, dict) and \
                    clean.get('failed'):
                cleanup_failures += 1
                self.warning_could_not_clean_expired_worker_sessions(
                    kwargs, instruction, worker_id, clean
                )
                continue
            session_tokens_to_remove += clean['orphaned_stokens']
            session_count += len(kwargs['session_worker_map'][worker_id])
            session_workers.append(worker_id)
        cleanup_stokens = self.cleanup_session_tokens(
            session_tokens_to_remove, **kwargs
        )
        if not cleanup_stokens or isinstance(cleanup_stokens, dict) and \
                cleanup_stokens.get('failed'):
            return self.warning_could_not_cleanup_orphaned_session_tokens(
                kwargs, cleanup_stokens
            )
        elif not session_count:
            return self.warning_could_not_cleanup_ewallet_sessions(
                kwargs, instruction, session_tokens_to_remove, session_workers,
                cleanup_failures, session_count, cleanup_stokens
            )
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': session_count,
            'cleanup_failures': cleanup_failures
                + cleanup_stokens['cleanup_failures'],
            'orphaned_stokens': session_tokens_to_remove,
            'stoken_count': len(session_tokens_to_remove),
            'stokens_cleaned': cleanup_stokens['stokens'],
            'worker_count': len(session_workers),
            'workers': session_workers,
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_session_worker(self, worker_id, **kwargs):
        log.debug('')
        instruction = self.fetch_session_worker_cleanup_instruction()
        cleanup = self.action_execute_system_instruction_set(
            worker_id=worker_id, **instruction
        )
        if not cleanup or isinstance(cleanup, dict) and \
                cleanup.get('failed'):
            return self.error_could_not_clean_session_worker(
                worker_id, cleanup
            )
        remove = self.remove_session_worker_from_pool(worker_id, **kwargs)
        if not remove or isinstance(remove, dict) and \
                remove.get('failed'):
            return self.error_could_not_remove_session_worker_from_pool(
                worker_id, remove
            )
        return {
            'failed': False,
            'workers_cleaned': 1,
            'workers': [worker_id],
        }

    def cleanup_session_workers(self, worker_ids, **kwargs):
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_session_worker_cleaner_cron_default_label()
            )
        )
        orphaned_stokens, cleaned_workers, cleaning_failures = [], [], 0
        for worker_id in worker_ids:
            clean = self.cleanup_session_worker(
                worker_id, **kwargs
            )
            if isinstance(clean, dict) and clean.get('failed'):
                self.warning_could_not_clean_session_worker(
                    worker_id, worker_ids, clean
                )
                cleaning_failures += 1
                continue
            if clean.get('orphaned_stokens'):
                orphaned_stokens += clean['orphaned_stokens']
            cleaned_workers.append(worker_id)
        return self.warning_no_session_workers_cleaned(worker_ids) \
            if not cleaned_workers else {
                'failed': False,
                'workers_cleaned': len(cleaned_workers),
                'cleanup_failures': cleaning_failures,
                'workers': cleaned_workers,
                'orphaned_stokens': orphaned_stokens,
            }

    def clear_ctoken_linked_stoken(self, stoken_label, **kwargs):
        log.debug('')
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        for client_id in ctoken_pool:
            ctoken = ctoken_pool[client_id]
            check = ctoken.check_has_stoken(stoken_label)
            if not check:
                continue
            return ctoken.clear_stoken()
        return False

    def cleanup_session_token(self, stoken_label, **kwargs):
        log.debug('')
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        if stoken_label not in stoken_pool:
            return self.error_stoken_label_not_found_in_stoken_pool(
                stoken_label, stoken_pool, ctoken_pool, kwargs
            )
        break_cstoken_link = self.clear_ctoken_linked_stoken(
            stoken_label, ctoken_pool=ctoken_pool
        )
        remove = self.remove_session_token_from_pool(
            stoken_label, stoken_pool=stoken_pool
        )
        if not remove or isinstance(remove, dict) and \
                remove.get('failed'):
            return self.error_could_not_remove_session_token_from_pool(
                stoken_label, kwargs, ctoken_pool, stoken_pool,
                break_cstoken_link, remove
            )
        return {
            'failed': False,
            'stokens_cleaned': 1,
            'stokens': [stoken_label],
        }

    # INIT

#   @pysnooper.snoop('logs/ewallet.log')
    def init_cleaner_thread(self, **kwargs):
        log.debug('')
        try:
            t = threading.Thread(
                target=self.cron_session_manager_cleaners,
                daemon=True,
                name='CleanerThread',
            )
            set_thread = self.set_cleaner_thread(t)
            t.start()
        except Exception as e:
            return self.error_could_not_init_user_account_cleaner_cron(
                kwargs, e
            )
        self.set_cleaner_cron_states(flag=True)
        return True

    # GENERAL

    def write_issue_report_to_disk(self, issue_report):
        log.debug('')
        formatted_content = '================================================================================\n'\
            '(EWSC) - ISSUE REPORT - {}\n'\
            '================================================================================\n\n'\
            'Issue: {}\n\n'\
            'IP Address: {}\n\n'\
            'Email: {}\n\n'\
            'Timestamp: {}\n\n'\
            'Details: {}\n\n'\
            'Client Log Scrape:\n\n{}\n'.format(
                issue_report['issue_id'], issue_report['name'],
                issue_report['remote_address'], issue_report['user_email'],
                issue_report['timestamp'], issue_report['details'],
                issue_report['log_content']
            )
        write_to_file = res_utils.write_to_file(
            issue_report['report_file'], formatted_content
        )
        return {
            'failed': False,
            'issue_id': issue_report['issue_id'],
            'file_path': issue_report['report_file'],
        }

    def decrease_master_account_subordonate_account_pool_size(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        decrease_by = kwargs.get('decrease_by') or \
            self.fetch_default_master_account_subordonate_pool_size_limit()
        master_account = kwargs.get('master_account') or \
            self.fetch_master_account_by_id(kwargs['master_id'])
        decrease_size = master_account.decrease_subordonate_account_pool_size_limit(
            decrease_by
        )
        if not decrease_size or isinstance(decrease_size, dict) and \
                decrease_size.get('failed'):
            return self.warning_could_not_decrease_subordonate_account_pool_size_limit(
                kwargs, decrease_by, master_account, decrease_size
            )
        instruction_set_response = {
            'failed': False,
            'master': kwargs['master_id'],
            'subpool_size': decrease_size.get('subpool_size', 0),
            'decreased_by': decrease_size.get('decreased_by', 0),
            'master_data': decrease_size.get('master_data', {}),
        }
        return instruction_set_response

    def increase_master_account_subordonate_account_pool_size(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        increase_by = kwargs.get('increase_by') or \
            self.fetch_default_master_account_subordonate_pool_size_limit()
        master_account = kwargs.get('master_account') or \
            self.fetch_master_account_by_id(kwargs['master_id'])
        increase_size = master_account.increase_subordonate_account_pool_size_limit(
            increase_by
        )
        if not increase_size or isinstance(increase_size, dict) and \
                increase_size.get('failed'):
            return self.warning_could_not_increase_subordonate_account_pool_size_limit(
                kwargs, increase_by, master_account, increase_size
            )
        instruction_set_response = {
            'failed': False,
            'master': kwargs['master_id'],
            'subpool_size': increase_size.get('subpool_size', 0),
            'increased_by': increase_size.get('increased_by', 0),
            'master_data': increase_size.get('master_data', {}),
        }
        return instruction_set_response

    def unfreeze_subordonate_user_accounts(self, user_account_ids, **kwargs):
        log.debug('')
        orm_session = kwargs.get('orm_session') or res_utils.session_factory()
        subordonates_activated, activation_failures = [], 0
        try:
            user_accounts = list(
                orm_session.query(ResUser)\
                    .filter(ResUser.user_id.in_(user_account_ids))
            )
            for account in user_accounts:
                unfreeze_account = account.unfreeze_user_account()
                if not unfreeze_account or isinstance(unfreeze_account, dict) and \
                        unfreeze_account.get('failed'):
                    self.warning_could_not_unfreeze_subordonate_user_account(
                        user_account_ids, kwargs, orm_session,
                        subordonates_activated, activation_failures,
                        user_accounts, account, unfreeze_account
                    )
                    activation_failures += 1
                    continue
                subordonates_activated.append(account.fetch_user_id())
        except Exception as e:
            return self.error_could_not_unfreeze_subordonate_user_accounts(
                user_account_ids, kwargs, orm_session, e
            )
        instruction_set_response = {
            'failed': False,
            'subordonates': subordonates_activated,
            'subordonates_activated': len(subordonates_activated),
            'activation_failures': activation_failures,
        }
        return instruction_set_response

    def unfreeze_master_account_subordonate_pool(self, master_id):
        log.debug('')
        orm_session = res_utils.session_factory()
        master_account = self.fetch_master_account_by_id(master_id)
        accounts_activated = []
        user_query = list(
            orm_session.query(ResMaster).filter_by(user_id=master_id)
        )
        if not user_query:
            log.info('No Master user account found by ID.')
            return False
        try:
            account = user_query[0]
            subpool = account.fetch_subordonate_account_pool()
            sub_ids = [account.fetch_user_id() for account in subpool]
            subpool_unfreeze = self.unfreeze_subordonate_user_accounts(
                sub_ids, orm_session=orm_session
            )
            if not subpool_unfreeze or isinstance(subpool_unfreeze, dict) and \
                    subpool_unfreeze.get('failed'):
                return self.error_could_not_unfreeze_master_account_subpool(
                    master_id, orm_session, master_account, accounts_activated,
                    user_query, account, subpool, sub_ids, subpool_unfreeze
                )
            accounts_activated += subpool_unfreeze.get('subordonates', [])
        except Exception as e:
            return self.error_could_not_unfreeze_master_account_subpool(
                master_id, orm_session, master_account, accounts_activated,
                user_query, e
            )
        instruction_set_response = {
            'failed': False,
            'masters': [master_id],
            'subordonates': accounts_activated,
            'activation_failures': subpool_unfreeze.get('activation_failures', 0),
            'subordonates_activated': len(accounts_activated),
        }
        return instruction_set_response

    def unfreeze_master_user_accounts(self, master_ids):
        log.debug('TODO - Refactor')
        orm_session = res_utils.session_factory()
        accounts_activated, activation_failures = [], 0
        try:
            user_query = list(
                orm_session.query(ResMaster).filter(
                    ResMaster.user_id.in_(master_ids)
                )
            )
            if not user_query:
                log.info('No Master user accounts found by ID set.')
                return False
        except Exception as e:
            return self.error_could_not_fetch_master_accounts_by_identifier_set(
                master_ids, orm_session, e
            )
        accounts_to_unfreeze = len(user_query)
        try:
            for account in user_query:
                user_id = account.fetch_user_id()
                log.info('Unfreezing Master user account {}.'.format(user_id))
                unfreeze_account = account.unfreeze_user_account()
                if not unfreeze_account or isinstance(unfreeze_account, dict) and \
                    unfreeze_account.get('failed'):
                    self.warning_could_not_unfreeze_user_account(
                        orm_session, accounts_activated, user_query,
                        accounts_to_unfreeze, account, user_id,
                        activation_failures
                    )
                    activation_failures += 1
                    continue
                accounts_activated.append(user_id)
        finally:
            orm_session.commit()
            orm_session.close()
        instruction_set_response = {
            'failed': False,
            'masters': accounts_activated,
            'activation_failures': activation_failures,
            'masters_activated': len(accounts_activated),
        }
        return instruction_set_response

    def freeze_subordonate_user_accounts(self, user_account_ids, **kwargs):
        log.debug('')
        orm_session = kwargs.get('orm_session') or res_utils.session_factory()
        subordonates_frozen, freeze_failures = [], 0
        try:
            user_accounts = list(
                orm_session.query(ResUser)\
                    .filter(ResUser.user_id.in_(user_account_ids))
            )
            for account in user_accounts:
                freeze_account = account.freeze_user_account()
                if not freeze_account or isinstance(freeze_account, dict) and \
                        freeze_account.get('failed'):
                    self.warning_could_not_freeze_subordonate_user_account(
                        user_account_ids, kwargs, orm_session,
                        subordonates_frozen, freeze_failures, user_accounts,
                        account, freeze_account
                    )
                    freeze_failures += 1
                    continue
                subordonates_frozen.append(account.fetch_user_id())
        except Exception as e:
            return self.error_could_not_freeze_subordonate_user_accounts(
                user_account_ids, kwargs, orm_session, e
            )
        instruction_set_response = {
            'failed': False,
            'subordonates': subordonates_frozen,
            'subordonates_frozen': len(subordonates_frozen),
            'frozen_failures': freeze_failures,
        }
        return instruction_set_response

    def freeze_master_user_accounts(self, master_ids):
        log.debug('TODO - Refactor')
        orm_session = res_utils.session_factory()
        accounts_frozen, freeze_failures = [], 0
        try:
            user_query = list(
                orm_session.query(ResMaster).filter(
                    ResMaster.user_id.in_(master_ids)
                )
            )
            if not user_query:
                log.info('No master user accounts found by ID set.')
                return False
        except Exception as e:
            return self.error_could_not_fetch_master_accounts_by_identifier_set(
                master_ids, orm_session, e
            )
        accounts_to_freeze = len(user_query)
        try:
            for account in user_query:
                user_id = account.fetch_user_id()
                log.info('Freezing up Master user account {}.'.format(user_id))
                freeze_account = account.freeze_user_account()
                if not freeze_account or isinstance(freeze_account, dict) and \
                    freeze_account.get('failed'):
                    self.warning_could_not_freeze_user_account(
                        orm_session, accounts_frozen, user_query,
                        accounts_to_freeze, account, user_id,
                        freeze_failures
                    )
                    freeze_failures += 1
                    continue
                accounts_frozen.append(user_id)
        finally:
            orm_session.commit()
            orm_session.close()
        instruction_set_response = {
            'failed': False,
            'masters': accounts_frozen,
            'frozen_failures': freeze_failures,
            'masters_frozen': len(accounts_frozen),
        }
        return instruction_set_response

    def freeze_master_account_subordonate_pool(self, master_id):
        log.debug('')
        orm_session = res_utils.session_factory()
        master_account = self.fetch_master_account_by_id(master_id)
        accounts_frozen = []
        user_query = list(
            orm_session.query(ResMaster).filter_by(user_id=master_id)
        )
        if not user_query:
            log.info('No master user account found by ID.')
            return False
        try:
            account = user_query[0]
            subpool = account.fetch_subordonate_account_pool()
            sub_ids = [account.fetch_user_id() for account in subpool]
            subpool_freeze = self.freeze_subordonate_user_accounts(
                sub_ids, orm_session=orm_session
            )
            if not subpool_freeze or isinstance(subpool_freeze, dict) and \
                    subpool_freeze.get('failed'):
                return self.error_could_not_freeze_master_account_subpool(
                    master_id, orm_session, master_account, accounts_frozen,
                    user_query, account, subpool, sub_ids, subpool_freeze
                )
            accounts_frozen += subpool_freeze.get('subordonates', [])
        except Exception as e:
            return self.error_could_not_freeze_master_account_subpool(
                master_id, orm_session, master_account, accounts_frozen,
                user_query, e
            )
        instruction_set_response = {
            'failed': False,
            'masters': [master_id],
            'subordonates': accounts_frozen,
            'frozen_failures': subpool_freeze.get('frozen_failures', 0),
            'subordonates_frozen': len(accounts_frozen),
        }
        return instruction_set_response

    def log_error(self, **kwargs):
        log.warning(
            '{} - [ DETAILS ] - {}'.format(
                kwargs.get('error'), kwargs.get('details'),
            )
        )

    def log_warning(self, **kwargs):
        log.warning(
            '{} - [ DETAILS ] - {}'.format(
                kwargs.get('warning'), kwargs.get('details'),
            )
        )

    def execute_worker_instruction(self, worker_id, instruction, **kwargs):
        log.debug('')
        worker_pool = kwargs.get('worker_pool') or \
            self.fetch_worker_pool()
        # Fetch worker pool entry by worker id
        pool_entry = self.fetch_worker_pool_entry_by_id(
            worker_id, worker_pool=worker_pool
        )
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
                time.sleep(0.1)
                continue
        self.debug_worker_unlocked(lock)
        return True

    def ensure_worker_locked(self, lock):
        log.debug('')
        if not lock.value:
            while not lock.value:
                time.sleep(0.1)
                continue
        self.debug_worker_locked(lock)
        return True

    def interogate_session_pool_workers(self, **kwargs):
        log.debug('')
        worker_pool = self.fetch_worker_pool()
        if not worker_pool or isinstance(worker_pool, dict) and \
                worker_pool.get('failed'):
            return self.warning_could_not_fetch_session_worker_pool(kwargs)
        if kwargs.get('limit') and isinstance(kwargs['limit'], int):
            worker_ids = list(worker_pool.keys())[:kwargs['limit']]
            workers = {
                worker_id: worker_pool[worker_id] for worker_id in worker_ids
            }
            worker_pool = workers
        instruction = self.fetch_worker_state_info_interogation_instruction()
        worker_states = {
            worker_id: self.action_execute_system_instruction_set(
                worker_id=worker_id, **instruction
            ) for worker_id in worker_pool
        }
        instruction_set_response = {
            'failed': False,
            'workers': worker_states,
        }
        return instruction_set_response

#   @pysnooper.snoop()
    def send_session_worker_instruction(self, worker_id, instruction_set):
        log.debug('')
        pool_entry = self.fetch_worker_pool_entry_by_id(worker_id)
        if not pool_entry or isinstance(pool_entry, dict) and \
                pool_entry.get('failed'):
            return pool_entry
        pool_entry['instruction'].put(instruction_set)
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
            'Starting instruction set listener using socket handler '
            'values: {}.'.format(socket_handler.view_handler_values())
        )
        socket_handler.start_listener()
        return True

    def open_ewallet_session_manager_sockets(self, **kwargs):
        '''
        [ NOTE ]: Creates new EWalletSocketHandler object using
                  default configuration values.
        '''
        log.debug('')
        in_port = kwargs.get('in_port') or \
            self.fetch_default_ewallet_command_chain_instruction_port()
        out_port = kwargs.get('out_port') or \
            self.fetch_default_ewallet_command_chain_reply_port()
        if not in_port or not out_port:
            return self.error_could_not_fetch_socket_handler_required_values()
        socket = self.spawn_ewallet_session_manager_socket_handler(
            in_port, out_port
        )
        return self.error_could_not_spawn_socket_handler() \
            if not socket else socket

    # GENERATORS

    def generate_id_for_entity_set(self, entity_set):
        '''
        [ NOTE   ]: Entity identifier generator, for session workers and
                    ewallet sessions.
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

    def generate_ewallet_session_token(self, **kwargs):
        '''
        [ NOTE ]: Generates a new unique session token using
                  default format and prefix.
        [ NOTE ]: Session Token follows the following format
                  <prefix-string>:<code>:<timestamp>
        '''
        log.debug('')
        prefix = self.fetch_session_token_default_prefix()
        length = self.fetch_session_token_default_length()
        timestamp = str(time.time())
        st_code = self.res_utils.generate_random_alpha_numeric_string(
            string_length=length
        )
        label = prefix + ':' + st_code + ':' + timestamp

        now = datetime.datetime.now()
        interval = self.fetch_default_session_token_validity_interval_in_minutes()
        default_expiration_date = now + datetime.timedelta(minutes=interval)
        specific_expiration_date = kwargs.get('expires_on')

        expiration_datetime = default_expiration_date if \
            not specific_expiration_date \
            or specific_expiration_date > default_expiration_date \
            else specific_expiration_date

        session_token = self.spawn_session_token(
            session_token=label,
            expires_on=expiration_datetime,
        )
        return session_token

#   @pysnooper.snoop()
    def generate_client_id(self, **kwargs):
        '''
        [ NOTE   ]: Generates a new unique client id using default
                    format and prefix.
        [ NOTE   ]: User ID follows the following format
                    <prefix-string>:<code>:<timestamp>
        '''
        log.debug('')
        prefix = self.fetch_client_id_default_prefix()
        length = self.fetch_client_id_default_length()
        timestamp = str(time.time())
        uid_code = self.res_utils.generate_random_alpha_numeric_string(
            string_length=length
        )
        label = prefix + ':' + uid_code + ':' + timestamp

        now = datetime.datetime.now()
        interval = self.fetch_default_client_id_validity_interval_in_minutes()
        default_expiration_date = now + datetime.timedelta(minutes=interval)
        specific_expiration_date = kwargs.get('expires_on')

        expiration_datetime = default_expiration_date if \
            not specific_expiration_date \
            or specific_expiration_date > default_expiration_date \
            else specific_expiration_date

        client_id_token = self.spawn_client_id(
            client_id=label,
            expires_on=expiration_datetime,
        )
        return client_id_token

    # CRONJOBS

#   @pysnooper.snoop('logs/ewallet.log')
    def cron_session_manager_cleaners(self):
        log.debug('CRON')
        while True:
            schedule.run_pending()
            time.sleep(1)

    # ACTIONS
    '''
    [ NOTE ]: Instruction set responses are formulated here.
    '''

    # TODO
    def action_stop_user_account_cleaner_cron(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_stop_session_worker_cleaner_cron(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_stop_ewallet_session_cleaner_cron(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_stop_client_token_cleaner_cron(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')

#   @pysnooper.snoop('logs/ewallet.log')
    def action_sweep_cleanup_master_accounts_by_id(self, master_ids, **kwargs):
        log.debug('')
        master_accounts = self.fetch_master_accounts_by_id_set(
            master_ids, **kwargs
        )
        if not master_accounts or isinstance(master_accounts, dict) and \
                master_accounts.get('failed'):
            return self.warning_could_not_fetch_master_accounts_by_ids(
                master_ids, kwargs, master_accounts
            )
        subordonate_accounts = self.fetch_subordonate_accounts_from_masters(
            master_accounts
        )
        subordonate_ids = [] if not isinstance(subordonate_accounts, list) \
            else [
                account.fetch_user_id() for account in subordonate_accounts
            ]
        clean_subordonates = False if not subordonate_ids \
            else self.cleanup_subordonate_user_accounts(
                subordonate_ids
            )
        clean_master = self.cleanup_master_user_accounts(
            master_ids
        )
        if not clean_master or isinstance(clean_master, dict) and \
                clean_master.get('failed'):
            return self.warning_could_not_clean_master_accounts(
                master_ids, kwargs, master_accounts, subordonate_accounts,
                clean_subordonates, clean_master,
            )
        instruction_set_response = {
            'failed': False,
            'masters_cleaned': len(master_ids),
            'cleanup_failures': clean_master.get('cleanup_failures', 0),
            'subordonates_cleaned': len(subordonate_ids),
            'cleanup_failures': 0,
            'masters': master_ids,
            'subordonates': subordonate_ids,
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_sweep_cleanup_master_accounts(self, **kwargs):
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_session_worker_cleaner_cron_default_label()
            )
        )
        master_freeze_interval = self.fetch_master_account_unlink_freeze_interval()
        masters = self.fetch_master_accounts_by_id_set(
            kwargs.get('master_ids'), **kwargs
        ) if kwargs.get('master_ids') else \
            self.fetch_master_accounts_marked_for_unlink(**kwargs)
        try:
            master_ids = [item.fetch_user_id() for item in masters]
        except Exception as e:
            return self.error_could_not_fetch_master_account_ids(
                kwargs, masters, master_freeze_interval, e
            )
        if not master_ids or isinstance(master_ids, dict) and \
                master_ids.get('failed'):
            return self.warning_no_master_account_ids_found(
                kwargs, master_freeze_interval, masters, master_ids
            )
        cleanup_masters = self.action_sweep_cleanup_master_accounts_by_id(
            master_ids
            if kwargs.get('master_ids')
            else [
                item.fetch_user_id() for item in
                self.filter_unlinked_master_accounts_past_freeze_inteval(
                    masters, master_freeze_interval
                ).get('unlink_overdue', [])
            ]
        )
        if not cleanup_masters or isinstance(cleanup_masters, dict) and \
                cleanup_masters.get('failed'):
            return self.warning_could_not_clean_master_accounts(
                kwargs, master_freeze_interval, master_ids,
                cleanup_masters
            )
        instruction_set_response = {
            'failed': False,
            'masters_cleaned': cleanup_masters['masters_cleaned'],
            'subordonates_cleaned': cleanup_masters['subordonates_cleaned'],
            'cleanup_failures': cleanup_masters['cleanup_failures'],
            'masters': cleanup_masters['masters'],
            'subordonates': cleanup_masters['subordonates'],
            'cleanup_count': cleanup_masters['subordonates_cleaned'] \
                + cleanup_masters['masters_cleaned']
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
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
        set_stoken_worker_id = cst_map['stoken'].set_worker_id(worker_id)
        if not set_stoken_worker_id or isinstance(set_stoken_worker_id, dict) \
                and set_stoken_worker_id.get('failed'):
            return self.warning_could_not_map_worker_id_to_session_token(
                worker_id, cst_map, kwargs, sanitized_instruction_set,
                new_session, set_stoken_worker_id
            )
        return new_session

#   @pysnooper.snoop('logs/ewallet.log')
    def action_acquire_master_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id') or not kwargs.get('master_id'):
            return self.error_invalid_acquire_master_action_data_set(kwargs)
        ctoken = self.fetch_client_token_by_label(kwargs['client_id'])
        if isinstance(ctoken, dict) and ctoken.get('failed'):
            return self.warning_could_not_fetch_client_token(kwargs, ctoken)
        instruction_set = self.fetch_master_add_ctoken_worker_instruction(**kwargs)
        add_acquired_ctoken = self.action_execute_user_instruction_set(**instruction_set)
        if not add_acquired_ctoken or isinstance(add_acquired_ctoken, dict) and \
                add_acquired_ctoken.get('failed'):
            return self.warning_could_not_add_acquired_ctoken_to_master_pool(
                kwargs, ctoken, instruction_set, add_acquired_ctoken
            )
        set_master = ctoken.set_master(kwargs['master_id'])
        if isinstance(set_master, dict) and set_master.get('failed'):
            return self.error_could_not_set_master_user_account_to_ctoken(
                kwargs, ctoken, set_master
            )
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'master_id': kwargs['master_id'],
            'ctoken': ctoken,
            'ctoken_data': ctoken.fetch_token_values(),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_inspect_master_acquired_ctokens(self, **kwargs):
        log.debug('')
        # Fetch Master account data from EWallet Session
        active_master = self.action_execute_user_instruction_set(**kwargs)
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master_id(
                kwargs, active_master
            )
        instruction_set_response = {
            'failed': False,
            'account': active_master['master'],
            'account_data': active_master['master_data'],
            'ctokens': list(),
        }
        ctokens = self.fetch_master_account_acquired_ctokens(
            active_master['master_id'], **kwargs
        )
        if not ctokens or isinstance(ctokens, dict) and \
                ctokens.get('failed'):
            return instruction_set_response
        instruction_set_response.update({'ctokens': list(ctokens.keys())})
        return instruction_set_response

    def action_inspect_master_acquired_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctoken'):
            return self.error_no_ctoken_found(kwargs)
        # Fetch Master account data from EWallet Session
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'inspect'
        )
        active_master = self.action_execute_user_instruction_set(
            inspect='ctokens', **sanitized_instruction_set
        )
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master_id(
                kwargs, active_master
            )
        ctoken = self.fetch_client_token_by_label(kwargs['ctoken'])
        if not ctoken or isinstance(ctoken, dict) and \
                ctoken.get('failed'):
            return self.warning_could_not_fetch_client_token(
                kwargs, active_master, ctoken
            )
        check = ctoken.check_has_master(active_master['master_id'])
        if not check:
            return self.warning_ctoken_has_not_acquired_current_master_account(
                kwargs, active_master, ctoken, check
            )
        instruction_set_response = {
            'failed': False,
            'account': active_master['master'],
            'ctoken': kwargs['ctoken'],
            'ctoken_data': ctoken.fetch_token_values(),
        }
        return instruction_set_response

    def action_release_master_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_invalid_release_master_action_data_set(kwargs)
        ctoken = self.fetch_client_token_by_label(kwargs['client_id'])
        if isinstance(ctoken, dict) and ctoken.get('failed'):
            return self.warning_could_not_fetch_client_token(kwargs, ctoken)
        kwargs.update({'master_id': ctoken.fetch_master()})
        instruction_set = self.fetch_master_remove_ctoken_worker_instruction(**kwargs)
        remove_ctoken = self.action_execute_user_instruction_set(**instruction_set)
        if not remove_ctoken or isinstance(remove_ctoken, dict) and \
                remove_ctoken.get('failed'):
            return self.warning_could_not_remove_released_ctoken_from_master_pool(
                kwargs, ctoken, instruction_set, remove_ctoken
            )
        unset_master = ctoken.set_master(None)
        if isinstance(unset_master, dict) and unset_master.get('failed'):
            return self.error_could_not_unset_master_user_account_from_ctoken(
                kwargs, ctoken, unset_master
            )
        worker_id = self.fetch_worker_identifier_by_client_id(kwargs['client_id'])
        if not worker_id or isinstance(worker_id, dict) and \
                worker_id.get('failed'):
            return worker_id
        instruction_set = self.fetch_system_clear_session_worker_instruction(**kwargs)
        clear_session = self.action_execute_system_instruction_set(
            worker_id=worker_id, **instruction_set
        )
        if not clear_session or isinstance(clear_session, dict) and \
                clear_session.get('failed'):
            self.warning_could_not_clear_ewallet_session(
                kwargs, ctoken, remove_ctoken, unset_master, worker_id,
                instruction_set, clear_session
            )
        master = self.fetch_master_account_by_id(kwargs['master_id'], **kwargs)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'released': str(kwargs['master_id']) if not master or
                isinstance(master, dict) and master.get('failed')
                else master.fetch_user_email(),
            'ctoken': ctoken,
            'ctoken_data': ctoken.fetch_token_values(),
        }
        return instruction_set_response

    def action_report_issue(self, **kwargs):
        log.debug('')
        if not kwargs.get('issue'):
            return self.error_no_issue_to_report_found(kwargs)
        formatted_issue = self.format_issue_report_data(**kwargs)
        if not formatted_issue or isinstance(formatted_issue, dict) and \
                formatted_issue.get('failed'):
            return self.error_could_not_format_issue_report(
                kwargs, formatted_issue
            )
        write_to_disk = self.write_issue_report_to_disk(formatted_issue)
        if not write_to_disk or isinstance(write_to_disk, dict) and \
                write_to_disk.get('failed'):
            return self.warning_could_not_write_issue_report_to_disk(
                kwargs, formatted_issue, write_to_disk
            )
        instruction_set_response = {
            'failed': False,
            'issue': write_to_disk['issue_id'],
            'timestamp': formatted_issue['timestamp'],
            'source': formatted_issue['remote_address'],
            'contact': formatted_issue['user_email'],
        }
        return instruction_set_response

    def action_ctoken_keep_alive(self, **kwargs):
        log.debug('')
        ctoken = self.fetch_client_token_by_label(kwargs['client_id'])
        if not ctoken or isinstance(ctoken, dict) and \
                ctoken.get('failed'):
            return self.warning_could_not_fetch_client_token(kwargs, ctoken)
        ctoken_keep_alive = ctoken.keep_alive(**kwargs)
        if not ctoken_keep_alive or isinstance(ctoken_keep_alive, dict) and \
                ctoken_keep_alive.get('failed'):
            return self.warning_could_not_keep_alive_client_token(
                kwargs, ctoken, ctoken_keep_alive
            )
        instruction_set_response = {
            'failed': False,
            'ctoken': kwargs['client_id'],
            'extended': self.fetch_default_client_id_validity_interval_in_minutes(),
            'time_unit': 'minutes',
            'ctoken_data': ctoken.fetch_token_values(),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_stoken_keep_alive(self, **kwargs):
        log.debug('')
        stoken = self.fetch_session_token_by_label(kwargs['session_token'])
        if not stoken or isinstance(stoken, dict) and \
                stoken.get('failed'):
            return self.warning_could_not_fetch_session_token(kwargs, stoken)
        stoken_keep_alive = stoken.keep_alive(**kwargs)
        if not stoken_keep_alive or isinstance(stoken_keep_alive, dict) and \
                stoken_keep_alive.get('failed'):
            return self.warning_could_not_keep_alive_session_token(
                kwargs, stoken, stoken_keep_alive
            )
        instruction_set_response = {
            'failed': False,
            'stoken': kwargs['session_token'],
            'extended': self.fetch_default_session_token_validity_interval_in_minutes(),
            'time_unit': 'minutes',
            'stoken_data': stoken.fetch_token_values(),
        }
        session_token_map = self.fetch_ewallet_session_ids_by_session_tokens(
            [kwargs['session_token']]
        )
        if not session_token_map or isinstance(session_token_map, dict) and \
                session_token_map.get('failed'):
            return instruction_set_response
        try:
            session_id = list(session_token_map.values())[0][0]
            session = self.fetch_ewallet_session_by_id(session_id, **kwargs)
        except Exception as e:
            return self.error_could_not_fetch_stoken_linked_session_by_id(
                kwargs, stoken, stoken_keep_alive, session_token_map, e
            )
        session_keep_alive = session.keep_alive(**kwargs)
        if not session_keep_alive or isinstance(session_keep_alive, dict) and \
                session_keep_alive.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_keep_alive_ewallet_session(
                kwargs, stoken, stoken_keep_alive, session,
                session_keep_alive
            )
        return instruction_set_response

    def action_decrease_master_subordonate_account_pool_size(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        master_account = self.fetch_master_account_by_id(kwargs['master_id'])
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_user_account_found_by_id(
                kwargs, master_account
            )
        decrease_subpool_size = self.decrease_master_account_subordonate_account_pool_size(
            master_account=master_account, **kwargs
        )
        if not decrease_subpool_size or isinstance(decrease_subpool_size, dict) and \
            decrease_subpool_size.get('failed'):
            return self.warning_could_not_decrease_subordonate_account_pool_size_limit(
                kwargs, master_account, decrease_subpool_size
            )
        instruction_set_response = {
            'failed': False,
            'master': decrease_subpool_size.get('master', None),
            'subpool_size': decrease_subpool_size.get('subpool_size', 0),
            'decreased_by': decrease_subpool_size.get('decreased_by', 0),
            'master_data': decrease_subpool_size.get('master_data', {}),
        }
        return instruction_set_response

    def action_increase_master_subordonate_account_pool_size(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        master_account = self.fetch_master_account_by_id(kwargs['master_id'])
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_user_account_found_by_id(
                kwargs, master_account
            )
        increase_subpool_size = self.increase_master_account_subordonate_account_pool_size(
            master_account=master_account, **kwargs
        )
        if not increase_subpool_size or isinstance(increase_subpool_size, dict) and \
            increase_subpool_size.get('failed'):
            return self.warning_could_not_increase_subordonate_account_pool_size_limit(
                kwargs, master_account, increase_subpool_size
            )
        instruction_set_response = {
            'failed': False,
            'master': increase_subpool_size.get('master', None),
            'subpool_size': increase_subpool_size.get('subpool_size', 0),
            'increased_by': increase_subpool_size.get('increased_by', 0),
            'master_data': increase_subpool_size.get('master_data', {}),
        }
        return instruction_set_response

    def action_unfreeze_master_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        master_account = self.fetch_master_account_by_id(kwargs['master_id'])
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_user_account_found_by_id(
                kwargs, master_account
            )
        unfreeze_subordonates = self.unfreeze_master_account_subordonate_pool(
            kwargs['master_id']
        )
        unfreeze_master = self.unfreeze_master_user_accounts(
            [kwargs['master_id']]
        )
        if not unfreeze_master or isinstance(unfreeze_master, dict) and \
                unfreeze_master.get('failed'):
            return self.warning_could_not_unfreeze_master_account(
                kwargs, master_account, unfreeze_subordonates,
                unfreeze_master,
            )
        instruction_set_response = {
            'failed': False,
            'masters_activated': unfreeze_master.get('masters_activated', 0),
            'subordonates_activated': unfreeze_subordonates.get('subordonates_activated', 0),
            'activation_failures': unfreeze_subordonates.get('activation_failures', 0)
                + unfreeze_master.get('activation_failures', 0),
            'masters': unfreeze_master.get('masters', []),
            'subordonates': unfreeze_subordonates.get('subordonates', []),
            'activation_count': unfreeze_master.get('masters_activated', 0)
                + unfreeze_subordonates.get('subordonates_activated', 0),
        }
        return instruction_set_response

    def action_freeze_master_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        master_account = self.fetch_master_account_by_id(kwargs['master_id'])
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_user_account_found_by_id(
                kwargs, master_account
            )
        freeze_subordonates = self.freeze_master_account_subordonate_pool(
            kwargs['master_id']
        )
        freeze_master = self.freeze_master_user_accounts(
            [kwargs['master_id']]
        )
        if not freeze_master or isinstance(freeze_master, dict) and \
                freeze_master.get('failed'):
            return self.warning_could_not_freeze_master_account(
                kwargs, master_account, freeze_subordonates,
                freeze_master,
            )
        instruction_set_response = {
            'failed': False,
            'masters_frozen': freeze_master.get('masters_frozen', 0),
            'subordonates_frozen': freeze_subordonates.get('subordonates_frozen', 0),
            'frozen_failures': freeze_subordonates.get('frozen_failures', 0)
                + freeze_master.get('frozen_failures', 0),
            'masters': freeze_master.get('masters', []),
            'subordonates': freeze_subordonates.get('subordonates', []),
            'frozen_count': freeze_master.get('masters_frozen', 0)
                + freeze_subordonates.get('subordonates_frozen', 0),
        }
        return instruction_set_response

    def action_cleanup_target_master_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        master_account = self.fetch_master_account_by_id(kwargs['master_id'])
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_user_account_found_by_id(
                kwargs, master_account
            )
        clean_subordonates = self.cleanup_master_account_subordonate_pool(
            kwargs['master_id']
        )
        clean_master = self.cleanup_master_user_accounts(
            [kwargs['master_id']]
        )
        if not clean_master or isinstance(clean_master, dict) and \
                clean_master.get('failed'):
            return self.warning_could_not_clean_master_account(
                kwargs, master_account, clean_subordonates,
                clean_master,
            )
        instruction_set_response = {
            'failed': False,
            'masters_cleaned': clean_master.get('masters_cleaned', 0),
            'subordonates_cleaned': clean_subordonates.get('subordonates_cleaned', 0),
            'cleanup_failures': clean_subordonates.get('cleanup_failures', 0)
                + clean_master.get('cleanup_failures', 0),
            'masters': clean_master.get('masters', []),
            'subordonates': clean_subordonates.get('subordonates', []),
            'cleanup_count': clean_master.get('masters_cleaned', 0)
                + clean_subordonates.get('subordonates_cleaned', 0),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_verify_client_id_master_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
        }
        master = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master, dict) and master.get('failed'):
            instruction_set_response.update({
                'master': False,
                'reason': 'Unlinked',
            })
            return instruction_set_response
        master_account = self.fetch_master_account_by_id(master[0])
        instruction_set_response.update({
            'master': True,
            'acquired_master': master_account.fetch_user_email(),
        })
        return instruction_set_response

    def action_verify_client_id_status(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
        }
        validity = self.action_verify_client_id_validity(**kwargs)
        linked = self.action_verify_client_id_linked_stoken(**kwargs)
        plugged = self.action_verify_client_id_ewallet_session(**kwargs)
        master = self.action_verify_client_id_master_account(**kwargs)
        instruction_set_response.update({
            'valid': validity['valid'],
            'linked': linked['linked'],
            'plugged': plugged['plugged'],
            'master': master['master'],
            'session_token': linked.get('session_token'),
            'session': plugged.get('session'),
            'acquired': master.get('acquired_master'),
        })
        return instruction_set_response

    def action_execute_system_instruction_set(self, **kwargs):
        log.debug('')
        if not kwargs.get('worker_id'):
            return self.error_no_worker_id_found(kwargs)
        return self.execute_worker_instruction(kwargs['worker_id'], kwargs)

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

    def action_verify_session_token_status(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'session_token': kwargs['session_token'],
        }
        validity = self.action_verify_session_token_validity(**kwargs)
        linked = self.action_verify_session_token_linked_ctoken(**kwargs)
        plugged = self.action_verify_session_token_ewallet_session(**kwargs)
        instruction_set_response.update({
            'valid': validity['valid'],
            'linked': linked['linked'],
            'plugged': plugged['plugged'],
            'client_id': linked.get('client_id'),
            'session': plugged.get('session'),
        })
        return instruction_set_response

    def action_verify_session_token_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'session_token': kwargs['session_token'],
        }
        stoken = self.fetch_session_token_by_label(kwargs['session_token'])
        if isinstance(stoken, dict) and stoken.get('failed'):
            instruction_set_response.update({
                'valid': False,
                'reason': 'Unregistered',
            })
            return instruction_set_response
        session = self.fetch_ewallet_session_ids_by_session_tokens(
            [kwargs['session_token']]
        )
        if isinstance(session, dict) and session.get('failed'):
            instruction_set_response.update({
                'plugged': False,
                'reason': 'Unplugged',
            })
            return instruction_set_response
        instruction_set_response.update({
            'plugged': True,
            'session': list(session.values())[0][0]
        })
        return instruction_set_response

    def action_verify_session_token_linked_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'session_token': kwargs['session_token'],
        }
        stoken = self.fetch_session_token_by_label(kwargs['session_token'])
        if isinstance(stoken, dict) and stoken.get('failed'):
            self.warning_could_not_fetch_session_token(kwargs, stoken)
            instruction_set_response.update({
                'valid': False,
                'reason': 'Unregistered',
            })
            return instruction_set_response
        verify_ctoken = self.verify_stoken_linked_ctoken(stoken)
        instruction_set_response.update({
            'linked': True if verify_ctoken.get('valid') else False,
        })
        if verify_ctoken.get('valid'):
            instruction_set_response.update({
                'client_id': verify_ctoken['ctoken'].fetch_label(),
            })
        return instruction_set_response

    def action_verify_session_token_validity(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_specified(kwargs)
        stoken = self.fetch_session_token_by_label(kwargs['session_token'])
        verify_registered = self.verify_stoken_in_pool(stoken)
        verify_expired = self.verify_stoken_expired(stoken)
        instruction_set_response = {
            'failed': False,
            'session_token': kwargs['session_token'],
            'valid': False if (
                verify_registered.get('failed') or
                verify_expired.get('failed')
            ) else True,
            'registered': verify_registered.get('valid'),
            'expired': True if not verify_expired.get('failed') and \
                not verify_expired.get('valid') else False,
        }
        if not verify_registered.get('valid') or \
                not verify_expired.get('valid'):
            instruction_set_response.update({
                'reasons': verify_registered.get('reason') or
                    verify_expired.get('reason'),
                'details': verify_registered.get('details') or
                    verify_expired.get('details'),
            })
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_verify_client_id_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
        }
        stoken = self.fetch_stokens_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(stoken, dict) and stoken.get('failed'):
            instruction_set_response.update({
                'plugged': False,
                'reason': 'Unlinked',
            })
            return instruction_set_response
        session_token = stoken[0].fetch_label()
        session = self.fetch_ewallet_session_ids_by_session_tokens(
            [session_token]
        )
        if isinstance(session, dict) and session.get('failed'):
            instruction_set_response.update({
                'plugged': False,
                'reason': 'Unplugged',
            })
            return instruction_set_response
        instruction_set_response.update({
            'plugged': True,
            'session': list(session.values())[0][0]
        })
        return instruction_set_response

    def action_verify_client_id_linked_stoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
        }
        ctoken = self.fetch_client_token_by_label(kwargs['client_id'])
        if isinstance(ctoken, dict) and ctoken.get('failed'):
            self.warning_could_not_fetch_client_token(kwargs, ctoken)
            instruction_set_response.update({
                'valid': False,
                'reason': 'Unregistered',
            })
            return instruction_set_response
        verify_stoken = self.verify_ctoken_linked_stoken(ctoken)
        instruction_set_response.update({
            'linked': True if verify_stoken.get('valid') else False,
        })
        if verify_stoken.get('valid'):
            instruction_set_response.update({
                'session_token': verify_stoken['stoken'].fetch_label(),
            })
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_verify_client_id_validity(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        ctoken = self.fetch_client_token_by_label(kwargs['client_id'])
        verify_registered = self.verify_ctoken_in_pool(ctoken)
        verify_expired = self.verify_ctoken_expired(ctoken)
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'valid': False if (
                verify_registered.get('failed') or
                verify_expired.get('failed')
            ) else True,
            'registered': verify_registered.get('valid'),
            'expired': True if not verify_expired.get('failed') and \
                not verify_expired.get('valid') else False,
        }
        if not verify_registered.get('valid') or \
                not verify_expired.get('valid'):
            instruction_set_response.update({
                'reasons': verify_registered.get('reason') or
                    verify_expired.get('reason'),
                'details': verify_registered.get('details') or
                    verify_expired.get('details'),
            })
        return instruction_set_response

    def action_target_cleanup_session_worker(self, **kwargs):
        log.debug('')
        if not kwargs.get('worker_id'):
            return self.error_no_session_worker_id_specified(kwargs)
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        clean_workers = self.cleanup_session_workers(
            [kwargs['worker_id']], worker_pool=worker_pool
        )
        if not clean_workers or isinstance(clean_workers, dict) and \
                clean_workers.get('failed'):
            return self.warning_could_not_cleanup_ewallet_session_workers(
                kwargs, worker_pool, clean_workers,
            )
        stokens_to_remove = clean_workers.get('orphaned_stokens', [])
        clean_stokens = self.cleanup_session_tokens(stokens_to_remove)
        instruction_set_response = {
            'failed': False,
            'worker_pool': self.fetch_worker_pool(),
            'workers_cleaned': clean_workers.get('workers_cleaned', 0),
            'cleanup_failures': clean_workers.get('cleanup_failures', 0)
                + clean_stokens.get('cleanup_failures', 0),
            'workers': clean_workers.get('workers', []),
            'stokens_cleaned': clean_stokens.get('stokens_cleaned', 0),
            'stokens': clean_stokens.get('stokens', [])
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_target_cleanup_client_token(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_specified(kwargs)
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        if kwargs['client_id'] not in ctoken_pool:
            return self.error_client_token_not_found_in_pool(
                kwargs, ctoken_pool
            )
        stokens_to_remove = self.fetch_stokens_from_client_token_set(
            [kwargs['client_id']]
        )
        sessions_to_remove = self.fetch_ewallet_session_ids_by_session_tokens(
            stokens_to_remove
        )
        clean_sessions = self.cleanup_ewallet_sessions(
            session_worker_map=sessions_to_remove
        )
        clean_stokens = self.cleanup_session_tokens(
            stokens_to_remove
        )
        clean_ctokens = self.cleanup_client_tokens(
            [kwargs['client_id']]
        )
        if not clean_ctokens or isinstance(clean_ctokens, dict) and \
                clean_ctokens.get('failed'):
            return self.warning_could_not_clean_client_token(
                kwargs, ctoken_pool, stokens_to_remove, sessions_to_remove,
                clean_sessions, clean_stokens, clean_ctokens
            )
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': clean_sessions.get('sessions_cleaned', 0),
            'cleanup_failures': clean_sessions.get('cleanup_failures', 0)
                + clean_stokens.get('cleanup_failures', 0)
                + clean_ctokens.get('cleanup_failures', 0),
            'worker_count': clean_sessions.get('worker_count', 0),
            'workers': clean_sessions.get('workers', []),
            'sessions': clean_sessions.get('sessions', []),
            'stokens_cleaned': clean_stokens.get('stokens_cleaned', 0),
            'stokens': clean_stokens.get('stokens', []),
            'ctokens_cleaned': clean_ctokens.get('ctokens_cleaned', 0),
            'ctokens': clean_ctokens.get('ctokens', []),
        }
        return instruction_set_response

    def action_target_cleanup_session_token(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_token'):
            return self.error_no_session_token_specified(kwargs)
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        if kwargs['session_token'] not in stoken_pool:
            return self.error_session_token_not_found_in_pool(
                kwargs, stoken_pool
            )
        sessions_to_remove = self.fetch_ewallet_session_ids_by_session_tokens(
            [kwargs['session_token']]
        )
        clean_sessions = self.cleanup_ewallet_sessions(
            session_worker_map=sessions_to_remove
        )
        clean_stokens = self.cleanup_session_tokens(
            [kwargs['session_token']], stoken_pool=stoken_pool
        )
        if not clean_stokens or isinstance(clean_stokens, dict) and \
                clean_stokens.get('failed'):
            return self.warning_could_not_clean_session_token(
                kwargs, stoken_pool, sessions_to_remove,
                clean_sessions, clean_stokens,
            )
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': clean_sessions.get('sessions_cleaned', 0),
            'cleanup_failures': clean_sessions.get('cleanup_failures', 0)
                + clean_stokens.get('cleanup_failures', 0),
            'worker_count': clean_sessions.get('worker_count', 0),
            'workers': clean_sessions.get('workers', []),
            'sessions': clean_sessions.get('sessions', []),
            'stokens_cleaned': clean_stokens.get('stokens_cleaned', 0),
            'stokens': clean_stokens.get('stokens', []),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_sweep_cleanup_session_workers(self, **kwargs):
        '''
        [ NOTE ]: Saves one vacant worker to reduce client execution time in
                  case all other workers are full.
        '''
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_session_worker_cleaner_cron_default_label()
            )
        )
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        vacant_workers = self.fetch_vacant_session_workers(
            worker_pool=worker_pool
        )
        if not vacant_workers or isinstance(vacant_workers, dict) and \
                vacant_workers.get('failed'):
            return self.warning_could_not_fetch_vacant_session_workers(
                kwargs, vacant_workers
            )
        reserved = vacant_workers.pop(0)
        clean = self.cleanup_session_workers(
            vacant_workers, worker_pool=worker_pool
        )
        if not clean or isinstance(clean, dict) and \
                clean.get('failed'):
            return self.warning_could_not_cleanup_vacant_ewallet_session_workers(
                kwargs, vacant_workers, clean,
            )
        clean.update({
            'worker_reserved': reserved,
            'worker_pool': self.fetch_worker_pool(),
        })
        return clean

#   @pysnooper.snoop('logs/ewallet.log')
    def action_cleanup_ewallet_session_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_action_cleanup_ewallet_session_id_found(kwargs)
        worker_id = self.fetch_ewallet_session_assigned_worker(
            kwargs['session_id']
        )
        if not worker_id or isinstance(worker_id, dict) and \
                worker_id.get('failed'):
            return self.warning_could_not_fetch_assigned_session_worker_id(
                kwargs, worker_id
            )
        instruction = self.fetch_worker_session_target_cleanup_instruction()
        instruction.update({'session_id': kwargs['session_id']})

        clean_sessions = self.cleanup_ewallet_sessions(
            session_worker_map={worker_id: [kwargs['session_id']]}
        )
        clean_stokens = self.cleanup_session_tokens(
            clean_sessions.get('orphaned_stokens', [])
        )
        if not clean_sessions or isinstance(clean_sessions, dict) and \
                clean_sessions.get('failed'):
            return self.warning_could_not_cleanup_target_ewallet_session(
                kwargs, worker_id, instruction, clean_sessions, clean_stokens
            )
        instruction_set_response = {
            'failed': False,
            'sessions_cleaned': clean_sessions.get('sessions_cleaned', 0),
            'cleanup_failures': clean_sessions.get('cleanup_failures', 0) \
                + clean_stokens.get('cleanup_failures', 0),
            'worker_count': clean_sessions.get('worker_count', 0),
            'workers': clean_sessions.get('workers', []),
            'sessions': clean_sessions.get('sessions', []),
            'stokens_cleaned': clean_stokens.get('stokens_cleaned', 0),
            'stokens': clean_stokens.get('stokens', []),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_ewallet_session_cleaner_cron_default_label()
            )
        )
        worker_pool = kwargs.get('worker_pool') or self.fetch_worker_pool()
        workers_with_expired_sessions = self.fetch_ewallet_sessions_past_expiration_date(
            worker_pool=worker_pool
        )
        workers_with_empty_sessions = self.fetch_empty_ewallet_session_map(
            worker_pool=worker_pool
        )
        worker_ids = set(
            list(workers_with_expired_sessions.keys())
            + list(workers_with_empty_sessions.keys())
        )
        to_remove = dict.fromkeys(worker_ids, [])
        for worker_id in worker_ids:
            if worker_id in workers_with_expired_sessions:
                to_remove[worker_id] += workers_with_expired_sessions[worker_id]
            if worker_id in workers_with_empty_sessions:
                to_remove[worker_id] += workers_with_empty_sessions[worker_id]
            to_remove[worker_id] = set(to_remove[worker_id])
        if not workers_with_expired_sessions or \
                isinstance(workers_with_expired_sessions, dict) and \
                workers_with_expired_sessions.get('failed'):
            return self.warning_could_not_fetch_workers_with_expired_sessions(
                kwargs, workers_with_expired_sessions,
            )
        sweep = self.sweep_cleanup_ewallet_sessions(
            session_worker_map=to_remove,
        )
        instruction_set_response = self.warning_could_not_sweep_cleanup_ewallet_sessions(
            kwargs, workers_with_expired_sessions, sweep
        ) if not sweep or isinstance(sweep, dict) and \
            sweep.get('failed') else sweep
        return instruction_set_response

    def action_new_worker(self, **kwargs):
        log.debug('')
        worker = self.spawn_ewallet_session_worker(**kwargs)
        instruction_queue, response_queue = Queue(), Queue()
        worker.set_instruction_queue(instruction_queue)
        worker.set_response_queue(response_queue)
        worker.set_lock(Value('i', 0))
        return worker

    def action_sweep_cleanup_session_tokens(self, **kwargs):
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_client_token_cleaner_cron_default_label()
            )
        )
        stoken_pool = kwargs.get('stoken_pool') or self.fetch_stoken_pool()
        sweep = self.sweep_cleanup_session_tokens(stoken_pool=stoken_pool)
        return self.warning_could_not_sweep_cleanup_session_tokens(
            kwargs, stoken_pool, sweep
        ) if isinstance(sweep, dict) and sweep.get('failed') else sweep

    def action_sweep_cleanup_client_tokens(self, **kwargs):
        log.debug(
            '' if not kwargs.get('from_cron') else \
            '- Automated Action: {} -'.format(
                self.fetch_client_token_cleaner_cron_default_label()
            )
        )
        ctoken_pool = kwargs.get('ctoken_pool') or self.fetch_ctoken_pool()
        sweep = self.sweep_cleanup_client_tokens(ctoken_pool=ctoken_pool)
        return self.warning_could_not_sweep_cleanup_client_tokens(
            kwargs, ctoken_pool, sweep
        ) if isinstance(sweep, dict) and sweep.get('failed') else sweep

    def action_start_client_token_cleaner_cron(self, **kwargs):
        log.debug('')
        label = self.fetch_client_token_cleaner_cron_default_label()
        setup = self.setup_client_token_cleaner_cron()
        check = self.check_cleaner_thread_active()
        if not check or isinstance(check, dict) and check.get('failed'):
            init = self.init_cleaner_thread()
        log.info('Successfully started {} cron job thread.'.format(label))
        instruction_set_response = {
            'failed': False,
            'cron': label,
            'pool_entry': self.fetch_cron_pool_entry_by_label(label=label),
        }
        return instruction_set_response

    def action_start_ewallet_session_cleaner_cron(self, **kwargs):
        log.debug('')
        label = self.fetch_ewallet_session_cleaner_cron_default_label()
        setup = self.setup_ewallet_session_cleaner_cron()
        check = self.check_cleaner_thread_active()
        if not check or isinstance(check, dict) and check.get('failed'):
            init = self.init_cleaner_thread()
        log.info('Successfully started {} cron job thread.'.format(label))
        instruction_set_response = {
            'failed': False,
            'cron': label,
            'pool_entry': self.fetch_cron_pool_entry_by_label(label=label),
        }
        return instruction_set_response

    def action_start_session_worker_cleaner_cron(self, **kwargs):
        log.debug('')
        label = self.fetch_session_worker_cleaner_cron_default_label()
        setup = self.setup_session_worker_cleaner_cron()
        check = self.check_cleaner_thread_active()
        if not check or isinstance(check, dict) and check.get('failed'):
            init = self.init_cleaner_thread()
        log.info('Successfully started {} cron job.'.format(label))
        instruction_set_response = {
            'failed': False,
            'cron': label,
            'pool_entry': self.fetch_cron_pool_entry_by_label(label=label),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_start_user_account_cleaner_cron(self, **kwargs):
        log.debug('')
        label = self.fetch_account_cleaner_cron_default_label()
        setup = self.setup_user_account_cleaner_cron()
        check = self.check_cleaner_thread_active()
        if not check or isinstance(check, dict) and check.get('failed'):
            init = self.init_cleaner_thread()
        log.info('Successfully started {} cron job.'.format(label))
        instruction_set_response = {
            'failed': False,
            'cron': label,
            'pool_entry': self.fetch_cron_pool_entry_by_label(label=label),
        }
        return instruction_set_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_interogate_ewallet_session_workers(self, **kwargs):
        log.debug('')
        interogate_workers = self.interogate_session_pool_workers(**kwargs)
        if isinstance(interogate_workers, dict) and \
                interogate_workers.get('failed'):
            return self.warning_could_not_interogate_session_workers(
                kwargs, interogate_workers
            )
        return interogate_workers

#   @pysnooper.snoop('logs/ewallet.log')
    def action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_id'):
            return self.error_no_ewallet_session_id_found(kwargs)
        worker_id = self.fetch_ewallet_session_assigned_worker(
            kwargs['session_id']
        )
        if isinstance(worker_id, dict) and worker_id.get('failed'):
            return self.warning_could_not_fetch_worker_id(kwargs, worker_id)
        instruction = self.fetch_ewallet_session_interogation_instruction()
        instruction.update({'session_id': kwargs['session_id']})
        session_state = self.action_execute_system_instruction_set(
            worker_id=worker_id, **instruction
        )
        if isinstance(session_state, dict) and session_state.get('failed'):
            return self.warning_could_not_interogate_ewallet_session(
                kwargs, worker_id, instruction, session_state
            )
        session_state.update({'worker': worker_id})
        return session_state

#   @pysnooper.snoop()
    def action_new_ewallet_session(self, **kwargs):
        log.debug('')
        worker_id = self.fetch_available_worker_id()
        ewallet_session = self.create_new_system_session(
            worker_id=worker_id,
        )
        if not ewallet_session or isinstance(ewallet_session, dict) and \
                ewallet_session.get('failed'):
            return self.warning_could_not_create_new_ewallet_session(
                kwargs, worker_id, ewallet_session
            )
        instruction_set_response = {
            'failed': False,
            'worker': worker_id,
            'ewallet_session': ewallet_session['ewallet_session'],
        }
        return instruction_set_response

    def action_new_session(self, **kwargs):
        log.debug('')
        session = self.create_new_ewallet_session(**kwargs)
        return session

    def action_request_client_id(self, **kwargs):
        log.debug('')
        client_id = self.generate_client_id(**kwargs)
        set_to_pool = self.set_new_client_id_to_pool({client_id.label: client_id})
        if not client_id or not set_to_pool or isinstance(set_to_pool, dict) \
                and set_to_pool.get('failed'):
            return self.warning_could_not_fulfill_client_id_request()
        instruction_set_response = {
            'failed': False,
            'client_id': client_id.label,
        }
        return instruction_set_response

    # EVENTS

    # FORMATTERS

#   @pysnooper.snoop()
    def format_issue_report_data(self, **kwargs):
        log.debug('')
        report_file_data = res_utils.new_issue_report_file(**kwargs)
        if not report_file_data or isinstance(report_file_data, dict) and \
                report_file_data.get('failed'):
            return self.error_could_not_create_new_issue_report_file(
                kwargs, report_file_data
            )
        formatted_issue_report = {
            'name': kwargs['issue'].get('name'),
            'details': kwargs['issue'].get('details'),
            'remote_address': kwargs.get('remote_addr'),
            'user_email': kwargs['issue'].get('email'),
            'log_content': res_utils.decode_message_base64(
                kwargs['issue'].get('log')
            ),
            'report_file': report_file_data['file_path'],
            'issue_id': report_file_data['issue_id'],
            'timestamp': res_utils.format_datetime(datetime.datetime.now()),
        }
        return formatted_issue_report

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

    # ACTION HANDLERS
    '''
    [ NOTE ]: Instruction set validation and sanitizations are performed here.

    [ NOTE ]: First generation instruction set mutations happen here on user
              actions, fetching the acquired Master ID from CToken and passing
              it to the EWSession Worker along with the original instruction.

    [ TODO ]: Consider sacrificing atomic Action Handlers and move generic
              action handler verifications to Jumptable Handlers for
              reduced redundancy.
    '''

    # TODO
    def handle_system_action_close_sockets(self, **kwargs):
        '''
        [ NOTE   ]: Desociates Ewallet Socket Handler from Session Manager.
        '''
        log.debug('TODO - [ RESOURCE-WARNING ]: Kill process')
        return self.unset_socket_handler()

    def handle_master_action_unlink_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        unlink_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_master_account(
            kwargs, unlink_account
        ) if not unlink_account or isinstance(unlink_account, dict) and \
            unlink_account.get('failed') else unlink_account

    def handle_client_action_unlink_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_user_account(
            kwargs, unlink_account
        ) if not unlink_account or isinstance(unlink_account, dict) and \
            unlink_account.get('failed') else unlink_account

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def handle_client_action_request_session_token(self, **kwargs):
        log.debug('TODO')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found(kwargs)
        client_id = kwargs['client_id']
        sanitized_instruction_set = res_utils.remove_tags_from_command_chain(
            kwargs, 'client_id'
        )
        # Map tokens
        cst_map = self.create_client_session_token_map(
            client_id, **sanitized_instruction_set
        )
        if not cst_map or isinstance(cst_map, dict) and cst_map.get('failed'):
            return self.error_could_not_create_client_session_token_map(
                kwargs, cst_map
            )
        # Fetch worker id by client id
        worker_id = self.fetch_available_worker_id(client_id=kwargs['client_id'])
        if not worker_id or isinstance(worker_id, dict) and \
                worker_id.get('failed'):
            self.warning_could_not_fetch_worker_id(
                worker_id, cst_map['ctoken'].label, cst_map['stoken'].label
            )
            worker = self.handle_system_action_new_worker(**kwargs)
            worker_id = worker.get('worker')
            if not worker_id:
                return self.error_could_not_create_new_session_worker(
                    kwargs, client_id, cst_map, worker_id, worker
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

#   @pysnooper.snoop('logs/ewallet.log')
    def handle_client_action_release_master(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        check_acquired = self.check_ctoken_acquired_master_account(
            kwargs['client_id']
        )
        if not check_acquired or isinstance(check_acquired, dict) and \
                check_acquired.get('failed'):
            return self.warning_ctoken_has_no_acquired_master_account(
                kwargs, check_acquired
            )
        release_account = self.action_release_master_user_account(**kwargs)
        if not release_account or isinstance(release_account, dict) and \
                release_account.get('failed'):
            return self.warning_could_not_release_master_user_account(
                kwargs, instruction_set_validation, release_account
            )
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'released': release_account['released'],
            'ctoken_data': release_account['ctoken_data'],
        }
        return instruction_set_response

    def handle_client_action_report_issue(self, **kwargs):
        log.debug('')
        issue_report = self.action_report_issue(**kwargs)
        return self.warning_could_not_report_issue(
            kwargs, issue_report
        ) if not issue_report or isinstance(issue_report, dict) and \
            issue_report.get('failed') else issue_report

    def handle_client_action_ctoken_keep_alive(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        ctoken_keep_alive = self.action_ctoken_keep_alive(**kwargs)
        return self.warning_could_not_pushback_ctoken_expiration_datetime(
            kwargs, ctoken_keep_alive
        ) if not ctoken_keep_alive or isinstance(ctoken_keep_alive, dict) and \
            ctoken_keep_alive.get('failed') else ctoken_keep_alive

    def handle_client_action_stoken_keep_alive(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        stoken_keep_alive = self.action_stoken_keep_alive(**kwargs)
        return self.warning_could_not_pushback_stoken_expiration_datetime(
            kwargs, stoken_keep_alive
        ) if not stoken_keep_alive or isinstance(stoken_keep_alive, dict) and \
            stoken_keep_alive.get('failed') else stoken_keep_alive

    def handle_master_action_view_logout_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_logout = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_master_account_logout_records(
            kwargs, view_logout
        ) if not view_logout or isinstance(view_logout, dict) and \
            view_logout.get('failed') else view_logout

    def handle_master_action_view_login_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_login = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_master_account_login_records(
            kwargs, view_login
        ) if not view_login or isinstance(view_login, dict) and \
            view_login.get('failed') else view_login

    def handle_master_action_inspect_subordonate(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        inspect_sub = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_inspect_subordonate_account(
            kwargs, inspect_sub
        ) if not inspect_sub or isinstance(inspect_sub, dict) and \
            inspect_sub.get('failed') else inspect_sub

    def handle_master_action_inspect_subpool(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        inspect_subpool = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_inspect_subpool(
            kwargs, inspect_subpool
        ) if not inspect_subpool or isinstance(inspect_subpool, dict) and \
            inspect_subpool.get('failed') else inspect_subpool

    def handle_master_action_login(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account = self.fetch_master_account_by_email(
            kwargs.get('user_email'), **kwargs
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_could_not_fetch_master_account_by_email(
                kwargs, instruction_set_validation, master_account
            )
        account_login = self.action_execute_user_instruction_set(
            master_id=master_account.fetch_user_id(), **kwargs
        )
        return self.warning_could_not_login_master_account(
            kwargs, account_login
        ) if not account_login or isinstance(account_login, dict) and \
            account_login.get('failed') else account_login

    def handle_master_action_inspect_ctoken(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        inspect_ctoken = self.action_inspect_master_acquired_ctoken(**kwargs)
        return self.warning_could_not_inspect_ctoken(
            kwargs, inspect_ctoken
        ) if not inspect_ctoken or isinstance(inspect_ctoken, dict) and \
            inspect_ctoken.get('failed') else inspect_ctoken

    def handle_master_action_inspect_ctokens(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        inspect_ctokens = self.action_inspect_master_acquired_ctokens(**kwargs)
        return self.warning_could_not_inspect_ctokens(
            kwargs, inspect_ctokens
        ) if not inspect_ctokens or isinstance(inspect_ctokens, dict) and \
            inspect_ctokens.get('failed') else inspect_ctokens

    def handle_master_action_recover_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        recover_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_recover_master_account(
            kwargs, recover_account
        ) if not recover_account or isinstance(recover_account, dict) and \
            recover_account.get('failed') else recover_account

    def handle_master_action_edit_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        edit_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_edit_master_account(
            kwargs, edit_account
        ) if not edit_account or isinstance(edit_account, dict) and \
            edit_account.get('failed') else edit_account

    def handle_master_action_view_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        view_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_master_account(
            kwargs, view_account
        ) if not view_account or isinstance(view_account, dict) and \
            view_account.get('failed') else view_account

    def handle_master_action_logout(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        account_logout = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_logout_master_account(
            kwargs, account_logout
        ) if not account_logout or isinstance(account_logout, dict) and \
            account_logout.get('failed') else account_logout

    def handle_client_action_view_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_account(
            kwargs, view_account
        ) if not view_account or isinstance(view_account, dict) and \
            view_account.get('failed') else view_account

    def handle_client_action_logout(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        account_logout = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_logout_user_account(
            kwargs, account_logout
        ) if not account_logout or isinstance(account_logout, dict) and \
            account_logout.get('failed') else account_logout

    def handle_client_action_new_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        account_login = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_login_user_account(
            kwargs, account_login
        ) if not account_login or isinstance(account_login, dict) and \
            account_login.get('failed') else account_login

#   @pysnooper.snoop('logs/ewallet.log')
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
        master_account = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account, dict) and master_account.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account
            )
        kwargs.update({'master_id': master_account[0]})
        new_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_user_account(
            kwargs, new_account
        ) if not new_account or isinstance(new_account, dict) and \
            new_account.get('failed') else new_account

    def handle_system_action_decrease_master_subpool_size(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_decrease_master_subordonate_account_pool_size(
                **kwargs
            )
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_system_action_increase_master_subpool_size(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_increase_master_subordonate_account_pool_size(
                **kwargs
            )
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_system_action_unfreeze_master_account(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_unfreeze_master_user_account(**kwargs)
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_system_action_freeze_master_account(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_freeze_master_user_account(**kwargs)
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_system_action_cleanup_target_master_account(self, **kwargs):
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_cleanup_target_master_account(**kwargs)
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_system_action_sweep_cleanup_master_accounts(self, **kwargs):
        '''
        [ NOTE ]: First generation instruction set mutation,
                  SqlAlchemy ORM session inserted.
        '''
        log.debug('')
        orm_session = self.res_utils.session_factory()
        try:
            kwargs.update({'active_session': orm_session})
            return self.action_sweep_cleanup_master_accounts(**kwargs)
        finally:
            orm_session.close()
            log.info('SqlAlchemy ORM session closed.')

    def handle_client_action_acquire_master(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        search_master = self.action_execute_user_instruction_set(**kwargs)
        if not search_master or isinstance(search_master, dict) and \
                search_master.get('failed'):
            return self.warning_master_user_account_search_failure(
                kwargs, search_master
            )
        acquire_account = self.action_acquire_master_user_account(
            master_id=search_master['master_data']['id'],
            **kwargs
        )
        if not acquire_account or isinstance(acquire_account, dict) and \
                acquire_account.get('failed'):
            return self.warning_could_not_acquire_master_user_account(
                kwargs, instruction_set_validation, search_master,
                acquire_account
            )
        instruction_set_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'master': kwargs['master'],
        }
        return instruction_set_response

    def handle_client_action_new_master_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        check_ctoken_master = self.check_ctoken_acquired_master_account(
            kwargs['client_id']
        )
        if check_ctoken_master:
            return self.warning_ctoken_has_acquired_master_account(
                kwargs, instruction_set_validation, check_ctoken_master
            )
        new_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_user_account(
            kwargs, new_account
        ) if not new_account or isinstance(new_account, dict) and \
            new_account.get('failed') else new_account

    def handle_client_action_verify_session_token_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_verify_session_token_ewallet_session(**kwargs)

    def handle_client_action_verify_session_token_status(self, **kwargs):
        log.debug('')
        return self.action_verify_session_token_status(**kwargs)

    def handle_client_action_verify_session_token_linked_ctoken(self, **kwargs):
        log.debug('')
        return self.action_verify_session_token_linked_ctoken(**kwargs)

    def handle_client_action_verify_session_token_validity(self, **kwargs):
        log.debug('')
        return self.action_verify_session_token_validity(**kwargs)

    def handle_client_action_verify_client_id_status(self, **kwargs):
        log.debug('')
        return self.action_verify_client_id_status(**kwargs)

    def handle_client_action_verify_client_id_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_verify_client_id_ewallet_session(**kwargs)

    def handle_client_action_verify_client_id_linked_stoken(self, **kwargs):
        log.debug('')
        return self.action_verify_client_id_linked_stoken(**kwargs)

    def handle_client_action_verify_client_id_validity(self, **kwargs):
        log.debug('')
        return self.action_verify_client_id_validity(**kwargs)

    def handle_system_action_start_all_cleaner_crons(self, **kwargs):
        log.debug('')
        cleaner_crons = {
            'accounts': self.handle_system_action_start_user_account_cleaner_cron(**kwargs),
            'workers': self.handle_system_action_start_session_worker_cleaner_cron(**kwargs),
            'sessions': self.handle_system_action_start_ewallet_session_cleaner_cron(**kwargs),
            'ctokens': self.handle_system_action_start_client_token_cleaner_cron(**kwargs),
        }
        return {
            'failed': False,
            'cleaners': cleaner_crons,
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def handle_system_action_new_worker(self, **kwargs):
        '''
        [ NOTE   ]: Creates new EWallet Session Manager Worker object and sets
                    it to worker pool.
        '''
        log.debug('')
        worker = self.action_new_worker(**kwargs)
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

    def handle_system_action_cleanup_target_session_worker(self, **kwargs):
        log.debug('')
        return self.action_target_cleanup_session_worker(**kwargs)

    def handle_system_action_sweep_cleanup_session_worker(self, **kwargs):
        log.debug('')
        return self.action_sweep_cleanup_session_workers(**kwargs)

    def handle_system_action_cleanup_target_client_token(self, **kwargs):
        log.debug('')
        return self.action_target_cleanup_client_token(**kwargs)

    def handle_system_action_cleanup_target_session_token(self, **kwargs):
        log.debug('')
        return self.action_target_cleanup_session_token(**kwargs)

    def handle_system_action_sweep_cleanup_client_tokens(self, **kwargs):
        log.debug('')
        return self.action_sweep_cleanup_client_tokens(**kwargs)

    def handle_system_action_sweep_cleanup_session_tokens(self, **kwargs):
        log.debug('')
        return self.action_sweep_cleanup_session_tokens(**kwargs)

    def handle_system_action_start_client_token_cleaner_cron(self, **kwargs):
        log.debug('')
        return self.action_start_client_token_cleaner_cron(**kwargs)

    def handle_system_action_start_ewallet_session_cleaner_cron(self, **kwargs):
        log.debug('')
        return self.action_start_ewallet_session_cleaner_cron(**kwargs)

    def handle_system_action_start_user_account_cleaner_cron(self, **kwargs):
        log.debug('')
        return self.action_start_user_account_cleaner_cron(**kwargs)

    def handle_system_action_start_session_worker_cleaner_cron(self, **kwargs):
        log.debug('')
        return self.action_start_session_worker_cleaner_cron(**kwargs)

    def handle_system_action_interogate_ewallet_workers(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_workers(**kwargs)

    def handle_system_action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session(**kwargs)

    def handle_system_action_sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        return self.action_sweep_cleanup_ewallet_sessions(**kwargs)

    def handle_system_action_cleanup_target_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_cleanup_ewallet_session_by_id(**kwargs)

    def handle_client_action_unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_invoice_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_invoice_sheet(
            kwargs, unlink_invoice_sheet
        ) if not unlink_invoice_sheet or isinstance(unlink_invoice_sheet, dict) and \
            unlink_invoice_sheet.get('failed') else unlink_invoice_sheet

    def handle_client_action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_invoice_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_invoice_sheet_record(
            kwargs, unlink_invoice_record
        ) if not unlink_invoice_record or isinstance(unlink_invoice_record, dict) and \
            unlink_invoice_record.get('failed') else unlink_invoice_record

    def handle_client_action_recover_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        recover_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_recover_user_account(
            kwargs, recover_account
        ) if not recover_account or isinstance(recover_account, dict) and \
            recover_account.get('failed') else recover_account

    def handle_client_action_switch_user_account(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_user_account(
            kwargs, switch_account
        ) if not switch_account or isinstance(switch_account, dict) and \
            switch_account.get('failed') else switch_account

    def handle_client_action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_credit_clock = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_credit_clock(
            kwargs, unlink_credit_clock
        ) if not unlink_credit_clock or isinstance(unlink_credit_clock, dict) and \
            unlink_credit_clock.get('failed') else unlink_credit_clock

    def handle_client_action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_credit_ewallet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_credit_ewallet(
            kwargs, unlink_credit_ewallet
        ) if not unlink_credit_ewallet or isinstance(unlink_credit_ewallet, dict) and \
            unlink_credit_ewallet.get('failed') else unlink_credit_ewallet

    def handle_client_action_unlink_time_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_time_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_time_record(
            kwargs, unlink_time_record
        ) if not unlink_time_record or isinstance(unlink_time_record, dict) and \
            unlink_time_record.get('failed') else unlink_time_record

    def handle_client_action_unlink_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_time_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_time_sheet(
            kwargs, unlink_time_sheet
        ) if not unlink_time_sheet or isinstance(unlink_time_sheet, dict) and \
            unlink_time_sheet.get('failed') else unlink_time_sheet

    def handle_client_action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_transfer_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_transfer_record(
            kwargs, unlink_transfer_record
        ) if not unlink_transfer_record or isinstance(unlink_transfer_record, dict) and \
            unlink_transfer_record.get('failed') else unlink_transfer_record

    def handle_client_action_unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_transfer_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_transfer_sheet(
            kwargs, unlink_transfer_sheet
        ) if not unlink_transfer_sheet or isinstance(unlink_transfer_sheet, dict) and \
            unlink_transfer_sheet.get('failed') else unlink_transfer_sheet

    def handle_client_action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_conversion_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_conversion_sheet_record(
            kwargs, unlink_conversion_record
        ) if not unlink_conversion_record or isinstance(unlink_conversion_record, dict) and \
            unlink_conversion_record.get('failed') else unlink_conversion_record

    def handle_client_action_unlink_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_conversion_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_conversion_sheet(
            kwargs, unlink_conversion_sheet
        ) if not unlink_conversion_sheet or isinstance(unlink_conversion_sheet, dict) and \
            unlink_conversion_sheet.get('failed') else unlink_conversion_sheet

    def handle_client_action_unlink_contact_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_contact_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_contact_record(
            kwargs, unlink_contact_record
        ) if not unlink_contact_record or isinstance(unlink_contact_record, dict) and \
            unlink_contact_record.get('failed') else unlink_contact_record

    def handle_client_action_unlink_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        unlink_contact_list = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_unlink_contact_list(
            kwargs, unlink_contact_list
        ) if not unlink_contact_list or isinstance(unlink_contact_list, dict) and \
            unlink_contact_list.get('failed') else unlink_contact_list

    def handle_client_action_switch_contact_list(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_contact_list = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_contact_list(
            kwargs, switch_contact_list
        ) if not switch_contact_list or isinstance(switch_contact_list, dict) and \
            switch_contact_list.get('failed') else switch_contact_list

    def handle_client_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_time_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_time_sheet(
            kwargs, switch_time_sheet
        ) if not switch_time_sheet or isinstance(switch_time_sheet, dict) and \
            switch_time_sheet.get('failed') else switch_time_sheet

    def handle_client_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_conversion_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_conversion_sheet(
            kwargs, switch_conversion_sheet
        ) if not switch_conversion_sheet or isinstance(switch_conversion_sheet, dict) and \
            switch_conversion_sheet.get('failed') else switch_conversion_sheet

    def handle_client_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_invoice_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_invoice_sheet(
            kwargs, switch_invoice_sheet
        ) if not switch_invoice_sheet or isinstance(switch_invoice_sheet, dict) and \
            switch_invoice_sheet.get('failed') else switch_invoice_sheet

    def handle_client_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_transfer_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_transfer_sheet(
            kwargs, switch_transfer_sheet
        ) if not switch_transfer_sheet or isinstance(switch_transfer_sheet, dict) and \
            switch_transfer_sheet.get('failed') else switch_transfer_sheet

    def handle_client_action_request_client_id(self, **kwargs):
        log.debug('')
        return self.action_request_client_id(**kwargs)

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

    def handle_client_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_credit_ewallet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_credit_ewallet(
            kwargs, switch_credit_ewallet
        ) if not switch_credit_ewallet or isinstance(switch_credit_ewallet, dict) and \
            switch_credit_ewallet.get('failed') else switch_credit_ewallet

    def handle_client_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        switch_credit_clock = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_switch_credit_clock(
            kwargs, switch_credit_clock
        ) if not switch_credit_clock or isinstance(switch_credit_clock, dict) and \
            switch_credit_clock.get('failed') else switch_credit_clock

    def handle_client_action_new_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_conversion_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_conversion_sheet(
            kwargs, new_conversion_sheet
        ) if not new_conversion_sheet or isinstance(new_conversion_sheet, dict) and \
            new_conversion_sheet.get('failed') else new_conversion_sheet

    def handle_client_action_new_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_time_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_time_sheet(
            kwargs, new_time_sheet
        ) if not new_time_sheet or isinstance(new_time_sheet, dict) and \
            new_time_sheet.get('failed') else new_time_sheet

    def handle_client_action_new_transfer_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_transfer_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_transfer_sheet(
            kwargs, new_transfer_sheet
        ) if not new_transfer_sheet or isinstance(new_transfer_sheet, dict) and \
            new_transfer_sheet.get('failed') else new_transfer_sheet

    def handle_client_action_new_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_invoice_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_invoice_sheet(
            kwargs, new_invoice_sheet
        ) if not new_invoice_sheet or isinstance(new_invoice_sheet, dict) and \
            new_invoice_sheet.get('failed') else new_invoice_sheet

    def handle_client_action_new_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_clock = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_credit_clock(
            kwargs, new_clock
        ) if not new_clock or isinstance(new_clock, dict) and \
            new_clock.get('failed') else new_clock

    def handle_client_action_new_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        new_ewallet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_create_new_credit_ewallet(
            kwargs, new_ewallet
        ) if not new_ewallet or isinstance(new_ewallet, dict) and \
            new_ewallet.get('failed') else new_ewallet

    def handle_client_action_view_logout_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_logout_records = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_logout_records(
            kwargs, view_logout_records
        ) if not view_logout_records or isinstance(view_logout_records, dict) and \
            view_logout_records.get('failed') else view_logout_records

    def handle_client_action_view_login_records(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_login_records = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_login_records(
            kwargs, view_login_records
        ) if not view_login_records or isinstance(view_login_records, dict) and \
            view_login_records.get('failed') else view_login_records

    def handle_client_action_view_invoice_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_invoice_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_invoice_record(
            kwargs, view_invoice_record
        ) if not view_invoice_record or isinstance(view_invoice_record, dict) and \
            view_invoice_record.get('failed') else view_invoice_record

    def handle_client_action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_invoice_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_invoice_sheet(
            kwargs, view_invoice_sheet
        ) if not view_invoice_sheet or isinstance(view_invoice_sheet, dict) and \
            view_invoice_sheet.get('failed') else view_invoice_sheet

    def handle_client_action_view_credit_clock(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_clock = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_credit_clock(
            kwargs, view_clock
        ) if not view_clock or isinstance(view_clock, dict) and \
            view_clock.get('failed') else view_clock

    def handle_client_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_ewallet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_credit_ewallet(
            kwargs, view_ewallet
        ) if not view_ewallet or isinstance(view_ewallet, dict) and \
            view_ewallet.get('failed') else view_ewallet

    def handle_client_action_view_conversion_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_conversion_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_conversion_record(
            kwargs, view_conversion_record
        ) if not view_conversion_record or isinstance(view_conversion_record, dict) and \
            view_conversion_record.get('failed') else view_conversion_record

    def handle_client_action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_conversion_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_conversion_sheet(
            kwargs, view_conversion_sheet
        ) if not view_conversion_sheet or isinstance(view_conversion_sheet, dict) and \
            view_conversion_sheet.get('failed') else view_conversion_sheet

    def handle_client_action_view_time_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_time_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_time_record(
            kwargs, view_time_record
        ) if not view_time_record or isinstance(view_time_record, dict) and \
            view_time_record.get('failed') else view_time_record

    def handle_client_action_view_time_sheet(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_time_sheet = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_time_sheet(
            kwargs, view_time_sheet
        ) if not view_time_sheet or isinstance(view_time_sheet, dict) and \
            view_time_sheet.get('failed') else view_time_sheet

    def handle_client_action_view_transfer_record(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        view_transfer_record = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_view_transfer_sheet_record(
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
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
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        edit_account = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_edit_user_account(
            kwargs, edit_account
        ) if not edit_account or isinstance(edit_account, dict) and \
            edit_account.get('failed') else edit_account

    def handle_client_action_transfer_credits(self, **kwargs):
        log.debug('')
        instruction_set_validation = self.validate_instruction_set(kwargs)
        if not instruction_set_validation \
                or isinstance(instruction_set_validation, dict) \
                and instruction_set_validation.get('failed'):
            return instruction_set_validation
        master_account_id = self.fetch_acquired_masters_from_client_token_set(
            [kwargs['client_id']]
        )
        if isinstance(master_account_id, dict) and master_account_id.get('failed'):
            return self.warning_no_master_account_acquired_by_ctoken(
                kwargs, instruction_set_validation, master_account_id
            )
        kwargs.update({'master_id': master_account_id[0]})
        transfer_credits = self.action_execute_user_instruction_set(**kwargs)
        return self.warning_could_not_transfer_credits_to_partner(
            kwargs, transfer_credits
        ) if not transfer_credits or isinstance(transfer_credits, dict) and \
            transfer_credits.get('failed') else transfer_credits

    def handle_system_action_new_session(self, **kwargs):
        log.debug('')
        return self.action_new_ewallet_session(**kwargs)

    # JUMPTABLE HANDLERS

    # TODO
    def handle_client_action_transfer(self, **kwargs):
        log.debug('TODO - Add support for client action transfer time')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_transfer_target_specified(kwargs)
        handlers = {
            'credits': self.handle_client_action_transfer_credits,
#           'time': self.handle_client_action_transfer_time,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_release(self, **kwargs):
        log.debug('')
        if not kwargs.get('release'):
            return self.error_no_client_action_release_target_specified(kwargs)
        handlers = {
            'master': self.handle_client_action_release_master,
        }
        return handlers[kwargs['release']](**kwargs)

    def handle_client_action_report(self, **kwargs):
        log.debug('')
        if not kwargs.get('report'):
            return self.error_no_client_action_report_target_specified(kwargs)
        handlers = {
            'issue': self.handle_client_action_report_issue,
        }
        return handlers[kwargs['report']](**kwargs)

    def handle_client_action_alive(self, **kwargs):
        log.debug('')
        if not kwargs.get('alive'):
            return self.error_no_client_action_alive_target_specified(kwargs)
        handlers = {
            'stoken': self.handle_client_action_stoken_keep_alive,
            'ctoken': self.handle_client_action_ctoken_keep_alive,
        }
        return handlers[kwargs['alive']](**kwargs)

    def handle_master_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_master_action_view_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_view_account,
            'login': self.handle_master_action_view_login_records,
            'logout': self.handle_master_action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_master_action_inspect(self, **kwargs):
        log.debug('')
        if not kwargs.get('inspect'):
            return self.error_no_master_action_inspect_target_specified(kwargs)
        handlers = {
            'ctokens': self.handle_master_action_inspect_ctokens,
            'ctoken': self.handle_master_action_inspect_ctoken,
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

    def handle_system_action_decrease_master(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_system_action_decrease_master_target_specified(kwargs)
        handlers = {
            'subpool': self.handle_system_action_decrease_master_subpool_size,
        }
        return handlers[kwargs['master']](**kwargs)

    def handle_system_action_decrease(self, **kwargs):
        log.debug('')
        if not kwargs.get('decrease'):
            return self.error_no_system_action_decrease_target_specified(kwargs)
        handlers = {
            'master': self.handle_system_action_decrease_master,
        }
        return handlers[kwargs['decrease']](**kwargs)

    def handle_system_action_increase_master(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_system_action_increase_master_target_specified(kwargs)
        handlers = {
            'subpool': self.handle_system_action_increase_master_subpool_size,
        }
        return handlers[kwargs['master']](**kwargs)

    def handle_system_action_increase(self, **kwargs):
        log.debug('')
        if not kwargs.get('increase'):
            return self.error_no_system_action_increase_target_specified(kwargs)
        handlers = {
            'master': self.handle_system_action_increase_master,
        }
        return handlers[kwargs['increase']](**kwargs)

    def handle_system_action_unfreeze(self, **kwargs):
        log.debug('')
        if not kwargs.get('unfreeze'):
            return self.error_no_system_action_unfreeze_target_specified(kwargs)
        handlers = {
            'master': self.handle_system_action_unfreeze_master_account,
        }
        return handlers[kwargs['unfreeze']](**kwargs)

    def handle_system_action_freeze(self, **kwargs):
        log.debug('')
        if not kwargs.get('freeze'):
            return self.error_no_system_action_freeze_target_specified(kwargs)
        handlers = {
            'master': self.handle_system_action_freeze_master_account,
        }
        return handlers[kwargs['freeze']](**kwargs)

    def handle_system_action_cleanup_master_accounts(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('master_id') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_master_account,
            'sweep': self.handle_system_action_sweep_cleanup_master_accounts,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_client_action_acquire(self, **kwargs):
        log.debug('')
        if not kwargs.get('acquire'):
            return self.error_no_client_action_acquire_target_specified(kwargs)
        handlers = {
            'master': self.handle_client_action_acquire_master,
        }
        return handlers[kwargs['acquire']](**kwargs)

    def handle_client_action_new(self, **kwargs):
        log.debug('')
        if not kwargs.get('new'):
            return self.error_no_client_action_new_target_specified()
        handlers = {
            'master': self.handle_client_action_new_master,
            'account': self.handle_client_action_new_account,
            'contact': self.handle_client_action_new_contact,
            'credit': self.handle_client_action_new_credit,
            'transfer': self.handle_client_action_new_transfer,
            'invoice': self.handle_client_action_new_invoice,
            'conversion': self.handle_client_action_new_conversion,
            'time': self.handle_client_action_new_time,
        }
        return handlers[kwargs['new']](**kwargs)

    def handle_client_action_new_master(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_client_action_new_master_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_new_master_account,
        }
        return handlers[kwargs['master']](**kwargs)

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

    def handle_client_action_verify_client_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctoken'):
            return self.error_no_client_action_verify_ctoken_target_specified(kwargs)
        handlers = {
            'validity': self.handle_client_action_verify_client_id_validity,
            'linked': self.handle_client_action_verify_client_id_linked_stoken,
            'session': self.handle_client_action_verify_client_id_ewallet_session,
            'status': self.handle_client_action_verify_client_id_status,
        }
        return handlers[kwargs['ctoken']](**kwargs)

    def handle_client_action_verify_session_token(self, **kwargs):
        log.debug('')
        if not kwargs.get('stoken'):
            return self.error_no_client_action_verify_stoken_target_specified(kwargs)
        handlers = {
            'validity': self.handle_client_action_verify_session_token_validity,
            'linked': self.handle_client_action_verify_session_token_linked_ctoken,
            'session': self.handle_client_action_verify_session_token_ewallet_session,
            'status': self.handle_client_action_verify_session_token_status,
        }
        return handlers[kwargs['stoken']](**kwargs)

    def handle_client_action_verify(self, **kwargs):
        log.debug('')
        if not kwargs.get('verify'):
            return self.error_no_client_action_verify_target_specified(kwargs)
        handlers = {
            'ctoken': self.handle_client_action_verify_client_id,
            'stoken': self.handle_client_action_verify_session_token,
        }
        return handlers[kwargs['verify']](**kwargs)

    def handle_system_action_start_cleaner_cron(self, **kwargs):
        log.debug('')
        if not kwargs.get('clean'):
            return self.error_no_system_cleaner_cron_target_specified(kwargs)
        handlers = {
            'accounts': self.handle_system_action_start_user_account_cleaner_cron,
            'workers': self.handle_system_action_start_session_worker_cleaner_cron,
            'sessions': self.handle_system_action_start_ewallet_session_cleaner_cron,
            'ctokens': self.handle_system_action_start_client_token_cleaner_cron,
            'all': self.handle_system_action_start_all_cleaner_crons,
        }
        return handlers[kwargs['clean']](**kwargs)

    def handle_system_action_cleanup_session_workers(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('worker_id') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_session_worker,
            'sweep': self.handle_system_action_sweep_cleanup_session_worker,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_system_action_cleanup_client_tokens(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('client_id') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_client_token,
            'sweep': self.handle_system_action_sweep_cleanup_client_tokens,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_system_action_cleanup_session_tokens(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('session_token') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_session_token,
            'sweep': self.handle_system_action_sweep_cleanup_session_tokens,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_system_action_cleanup(self, **kwargs):
        log.debug('')
        if not kwargs.get('cleanup'):
            return self.error_no_system_action_cleanup_target_specified(kwargs)
        handlers = {
            'masters': self.handle_system_action_cleanup_master_accounts,
            'workers': self.handle_system_action_cleanup_session_workers,
            'sessions': self.handle_system_action_cleanup_ewallet_sessions,
            'ctokens': self.handle_system_action_cleanup_client_tokens,
            'stokens': self.handle_system_action_cleanup_session_tokens,
        }
        return handlers[kwargs['cleanup']](**kwargs)

#   @pysnooper.snoop('logs/ewallet.log')
    def handle_system_action_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('start'):
            return self.error_no_system_action_start_target_specified()
        handlers = {
            'listener': self.handle_system_action_start_instruction_listener,
            'cleaner': self.handle_system_action_start_cleaner_cron,
        }
        return handlers[kwargs['start']](**kwargs)

    def handle_system_action_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        cleanup_mode = 'target' if kwargs.get('session_id') else 'sweep'
        handlers = {
            'target': self.handle_system_action_cleanup_target_ewallet_session,
            'sweep': self.handle_system_action_sweep_cleanup_ewallet_sessions,
        }
        return handlers[cleanup_mode](**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_system_action_interogate_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_interogate_ewallet_session,
            'workers': self.handle_system_action_interogate_ewallet_workers,
        }
        return handlers[kwargs['interogate']](**kwargs)

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

    def handle_client_action_switch_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_switch_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_switch_contact_list,
        }
        return handlers[kwargs['contact']](**kwargs)

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
            'account': self.handle_client_action_switch_user_account,
        }
        return handlers[kwargs['switch']](**kwargs)

    def handle_client_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_client_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_client_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_client_action_unlink_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_unlink_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_unlink_credit_ewallet,
            'clock': self.handle_client_action_unlink_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

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

    def handle_client_action_unlink_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_client_action_unlink_contact_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_contact_list,
            'record': self.handle_client_action_unlink_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_client_action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_unlink_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_time_sheet,
            'record': self.handle_client_action_unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_unlink_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_conversion_sheet,
            'record': self.handle_client_action_unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_unlink_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_unlink_invoice_sheet,
            'record': self.handle_client_action_unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

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

    def handle_client_action_switch_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_switch_credit_target_specified(kwargs)
        handlers = {
            'ewallet': self.handle_client_action_switch_credit_ewallet,
            'clock': self.handle_client_action_switch_credit_clock,
        }
        return handlers[kwargs['credit']](**kwargs)

    def handle_client_action_new_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_client_action_new_time_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_time_sheet,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_client_action_new_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_client_action_new_conversion_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_conversion_sheet,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_client_action_new_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_client_action_new_invoice_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_client_action_new_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_client_action_new_transfer_target_specified(kwargs)
        handlers = {
            'list': self.handle_client_action_new_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_client_action_new_credit(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit'):
            return self.error_no_client_action_target_new_credit_target_specified(kwargs)
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

    def handle_client_action_request(self, **kwargs):
        '''
        [ NOTE   ]: Client action handler for request type actions.
        '''
        log.debug('')
        if not kwargs.get('request'):
            return self.error_no_client_request_specified()
        handlers = {
            'client_id': self.handle_client_action_request_client_id,
            'session_token': self.handle_client_action_request_session_token,
        }
        return handlers[kwargs['request']](**kwargs)

    def handle_system_action_open(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for open type actions.
        '''
        log.debug('')
        if not kwargs.get('opening'):
            return self.error_no_system_action_open_target_specified()
        handlers = {
            'sockets': self.handle_system_action_open_sockets,
        }
        return handlers[kwargs['opening']](**kwargs)

    def handle_system_action_close(self, **kwargs):
        '''
        [ NOTE   ]: System action handler for close type actions.
        '''
        log.debug('')
        if not kwargs.get('closing'):
            return self.error_no_system_action_close_target_specified()
        handlers = {
            'sockets': self.handle_system_action_close_sockets,
        }
        return handlers[kwargs['closing']](**kwargs)

    def handle_system_event_client_timeout(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for client timeout events.
        '''
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_event_client_timeout_target_specified()
        handlers = {
            'client_ack': self.handle_system_event_client_ack_timeout,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_system_event_expire(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for expire type events.
        '''
        log.debug('')
        if not kwargs.get('expire'):
            return self.error_no_system_event_expire_specified()
        handlers = {
            'client_id': self.handle_system_event_client_id_expire,
            'session_token': self.handle_system_event_session_token_expire,
        }
        return handlers[kwargs['expire']](**kwargs)

    def handle_system_event_timeout(self, **kwargs):
        '''
        [ NOTE   ]: System event handler for timeout type events.
        '''
        log.debug('')
        if not kwargs.get('timeout'):
            return self.error_no_system_event_timeout_specified()
        handlers = {
            'session': self.handle_system_event_session_timeout,
            'worker': self.handle_system_event_worker_timeout,
            'client': self.handle_system_event_client_timeout,
        }
        return handlers[kwargs['timeout']](**kwargs)

    # CONTROLLERS

    def master_session_manager_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_master_session_manager_action_specified(kwargs)
        handlers = {
            'login': self.handle_master_action_login,
            'logout': self.handle_master_action_logout,
            'view': self.handle_master_action_view,
            'edit': self.handle_master_action_edit,
            'unlink': self.handle_master_action_unlink,
            'recover': self.handle_master_action_recover,
            'inspect': self.handle_master_action_inspect,
        }
        return handlers[kwargs['action']](**kwargs)

    def master_session_manager_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_master_session_manager_controller_specified()
        handlers = {
            'action': self.master_session_manager_action_controller,
#           'event': self.master_session_manager_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def session_manager_controller(self, *args, **kwargs):
        '''
        [ NOTE   ]: Main controller for the EWallet Session Manager.
        '''
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_session_manager_controller_specified(kwargs)
        handlers = {
            'client': self.client_session_manager_controller,
            'master': self.master_session_manager_controller,
            'system': self.system_session_manager_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    def client_session_manager_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_client_session_manager_action_specified(kwargs)
        handlers = {
            'new': self.handle_client_action_new,
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
            'verify': self.handle_client_action_verify,
            'acquire': self.handle_client_action_acquire,
            'alive': self.handle_client_action_alive,
            'report': self.handle_client_action_report,
            'release': self.handle_client_action_release,
        }
        return handlers[kwargs['action']](**kwargs)

    def system_session_manager_action_controller(self, **kwargs):
        '''
        [ NOTE ]: Not accessible to regular user api calls.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_session_manager_action_specified(kwargs)
        handlers = {
            'new': self.handle_system_action_new,
            'start': self.handle_system_action_start,
            'open': self.handle_system_action_open,
            'close': self.handle_system_action_close,
            'interogate': self.handle_system_action_interogate,
            'cleanup': self.handle_system_action_cleanup,
            'freeze': self.handle_system_action_freeze,
            'unfreeze': self.handle_system_action_unfreeze,
            'increase': self.handle_system_action_increase,
            'decrease': self.handle_system_action_decrease,
        }
        return handlers[kwargs['action']](**kwargs)

    def client_session_manager_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_client_session_manager_controller_specified()
        handlers = {
            'action': self.client_session_manager_action_controller,
#           'event': self.client_session_manager_event_controller,
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
#           'event': self.system_session_manager_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    # WARNINGS
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_could_not_fetch_master_accounts_by_ids(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch master accounts by ids.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_session_worker_limit_reached(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Imposed EWallet Session Worker limit reached.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_account_found_by_email(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No Master account found by email address.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_release_master_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not release Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clear_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean EWallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_remove_released_ctoken_from_master_pool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not remove released CToken from '
                       'Master account Subordonate pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_ctoken_has_no_acquired_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'CToken has no acquired Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_write_issue_report_to_disk(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not write IssueReport to disk.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_report_issue(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not report issue.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_client_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch CToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_keep_alive_client_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not process CToken keep alive signal.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_pushback_ctoken_expiration_datetime(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not push back CToken expiration datetime.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_stoken_linked_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch SToken linked EWallet Session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_keep_alive_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not keep EWallet Session alive.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch SToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_keep_alive_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not process SToken keep alive signal.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_pushback_stoken_expiration_datetime(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not push back SToken expiration datetime.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_master_account_logout_records(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view Master account logout records.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_master_account_login_records(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view Master account login records.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_inspect_subordonate_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not inspect Master subordonate account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_inspect_subpool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not inspect Master subordonate account pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_master_account_by_email(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch Master user account by email address.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_ctoken_has_not_acquired_current_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'CToken has not acquired active Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_inspect_ctoken(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not inspect acquired CToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_ewallet_session_active_master_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch ewallet session active Master ID.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_inspect_ctokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not inspect acquired CTokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_recover_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not recover Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_edit_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not edit Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_logout_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not logout Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_login_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not login Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_map_worker_id_to_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not map EWSession Worker ID to SToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_decrease_subordonate_account_pool_size_limit(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not decrease Subordonate user account pool size '
                       'for Master account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_increase_subordonate_account_pool_size_limit(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not increase Subordonate user account pool size '
                       'for Master account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unfreeze_subordonate_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unfreeze Subordonate user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unfreeze_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unfreeze user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unfreeze_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unfreeze Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_freeze_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not freeze user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_freeze_subordonate_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not freeze subordonate user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_freeze_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not freeze Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_accounts_marked_for_unlink_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No Master accounts marked for unlink found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_account_ids_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'No Master account ids found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_master_accounts(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean Master user accounts.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_subordonate_accounts_found_for_masters(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No Subordonate user accounts found associated '
                       'with given Master account set.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_accounts_found_by_id_set(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No Master accounts found by identifier set.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup master user accounts.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_add_acquired_ctoken_to_master_pool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not add acquired CToken to Master account pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_master_user_account_search_failure(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Master user account search has failed.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_acquire_master_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not acquire master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_account_acquired_by_ctoken(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No master account acquired by CToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_acquired_master_accounts_found_by_ctokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No acquired master accounts found by CTokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_master_account_found_by_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No master account found by ID.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_ctoken_has_acquired_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'CToken already has a Master account acquired.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_master_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new Master user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_stoken_linked_ctoken(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch SToken linked CToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch SToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_ctoken_linked_stoken(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch CToken linked SToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_client_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch CToken.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_verify_ctoken_in_pool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not verify if CToken belongs to pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_ewallet_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup ewallet sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_sort_worker_pool_by_state_code(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not sort session worker pool by state code.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_client_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup client token.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_session_tokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup session tokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_session_worker_pool_entry_by_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Could not fetch ewallet session worker '
                       'pool entry by ID.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_worker_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup worker ewallet sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_ewallet_sessions_found_by_stokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No ewallet session found by session tokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_empty_ewallet_sessions_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No empty ewallet sessions found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_empty_ewallet_sessions_from_worker(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch empty ewallet sessions from worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_session_tokens_to_remove(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No session tokens staged for removal.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_invalid_client_token_label(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Invalid client token label.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_sweep_cleanup_session_tokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not sweep cleanup session tokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup session token.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_session_tokens_cleaned(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No session tokens cleaned.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_ctoken_linked_stokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup session tokens '
                       'found associated with client token set.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_sweep_cleanup_client_tokens(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not sweep cleanup client tokens.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_client_tokens_to_remove(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No client tokens staged for removal.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_client_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean client token',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_client_tokens_cleaned(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'No client tokens cleanead.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_invalid_session_worker_state_code(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Invalid session worker state code.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_session_worker_interogation_failure(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not interogate EWallet session worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_set_cron_state_flag(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not set cron state flag.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_cron_pool_entry_by_label(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch cron pool entry by label.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_time_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view time record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_invoice_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view invoice record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_logout_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not logout user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_interogate_session_workers(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not interogate session workers.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_session_worker_pool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch session worker pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_interogate_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not interogate ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_session_workers_cleaned(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No ewallet session workers cleaned.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_session_worker(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean ewallet session worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_vacant_session_workers(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch vacant ewallet session workers.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_vacant_ewallet_session_workers(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup vacant ewallet session workers.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_vacant_session_workers_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No vacant session workers found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_target_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup target ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_assigned_session_worker_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch assigned worker id for ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_worker_found_assigned_to_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No worker found assigned to ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_sweep_cleanup_ewallet_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not sweep clean ewallet sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_expired_worker_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean expired worker sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_workers_with_expired_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch workers with expired sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_interogate_worker_session_pool(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not interogate worker session pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_expired_ewallet_sessions_from_worker(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch expired ewallet sessions from worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_session_manager_socket_handler_not_set(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'EWallet Session Manager socket handler not set.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_invoice_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink invoice sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_invoice_sheet_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink invoice record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_recover_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not recover user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_credit_clock(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink credit clock.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_credit_ewallet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink credit ewallet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_time_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink time sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_time_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink time record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_transfer_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink transfer record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_transfer_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink transfer sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_conversion_sheet_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink conversion record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_conversion_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink conversion sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_contact_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink contact record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_contact_list(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink contact list.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_unlink_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not unlink user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_contact_list(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch contact list.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_time_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch time sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_conversion_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch conversion sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_invoice_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch invoice sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_transfer_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch transfer sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_credit_clock(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch credit clock.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_switch_credit_ewallet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not switch credit ewallet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_conversion_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new conversion sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_time_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new time sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_invoice_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new invoice sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_transfer_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new transfer sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_credit_ewallet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new credit ewallet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_credit_clock(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new credit clock.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_login_records(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view login records.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_logout_records(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view logout records.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_invoice_sheet_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view invoice record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_invoice_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view invoice sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_credit_clock(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view credit clock.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_credit_ewallet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view credit ewallet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_conversion_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view conversion record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_conversion_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view conversion sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_time_sheet_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view time record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_time_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view time sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_transfer_sheet_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_transfer_sheet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view transfer sheet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_contact_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view contact record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_view_contact_list(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not view active contact list.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_stop_credit_clock_timer(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not stop credit clock timer.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_resume_credit_clock_timer(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not resume credit clock timer.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_start_credit_clock_timer(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not start credit clock timer.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_edit_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not edit user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_transfer_credits_to_partner(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not transfer credits to partner.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_contact_list(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new contact list.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_contact_record(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new contact record.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_convert_credit_clock_to_credits(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not convert credit clock time to credits.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_convert_credits_to_credit_clock(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not convert ewallet credits to credit clock.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_pay_partner_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not pay partner account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_supply_user_credit_ewallet(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not supply user credit ewallet.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_login_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not login user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_create_new_user_account(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not create new user account.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_request_session_token(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not request ewallet session token.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_worker_not_found_in_pool_by_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'EWallet session worker not found in pool by id.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_worker_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch session worker id.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_ctoken_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No client token found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_stoken_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No session token found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_worker_id_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No ewallet session worker id found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_available_session_worker_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No available session worker found in pool.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_multiple_session_tokens_found_by_label(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Multiple session tokens found. Fetching first.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_multiple_client_tokens_found_by_label(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Multiple client tokens found. Fetching first.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_pause_credit_clock_timer(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not pause credit clock timer.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_expired_ewallet_sessions_found(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'No expired ewallet sessions found.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_expired_ewallet_sessions(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch expired ewallet sessions.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_clean_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not clean ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_cleanup_ewallet_session_worker(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not cleanup ewallet session worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fulfill_client_id_request(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not honour client ID request.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_interogate_ewallet_session_workers(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not interogate ewallet session workers.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_ewallet_session_manager_worker_pool_empty(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Ewallet session manager worker pool empty.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_no_ewallet_session_found_by_id(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'No ewallet session found by id.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_ewallet_session_worker_assignment_failure(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not assign ewallet session to worker.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    def warning_could_not_fetch_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_warning_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'warning': 'Something went wrong. '
                       'Could not fetch ewallet session.',
        })
        self.log_warning(**instruction_set_response)
        return instruction_set_response

    # ERRORS
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_could_not_fetch_master_account_ids(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master user account ids.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_create_new_session_worker(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not create new EWallet Session Worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_release_master_action_data_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid ReleaseMaster action data set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_unset_master_user_account_from_ctoken(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not unset linked Master user account from CToken.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_release_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action Release target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_format_issue_report(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not format new IssueReport data set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_create_new_issue_report_file(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not create new IssueReport file.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_issue_to_report_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No issue found to report.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_report_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action Report target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_stoken_linked_session_by_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch SToken linked EWallet Session by ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_alive_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action KeepAlive target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_master_account_email(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid Master user account by email address.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_master_account_by_email_address(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master user account by email address.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_ctoken_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No CToken found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_acquired_ctokens_found_for_master_account(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No acquired CTokens found for Master user account.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_ctoken_pool_empty(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Session manager CToken pool empty.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_action_inspect_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master action Inspect target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_action_recover_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master action Recover target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_action_unlink_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master action Unlink target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_action_edit_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master action Edit target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_action_view_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master action View target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_session_manager_action_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No session manager Master controller action specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_session_manager_controller_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No session manager Master controller specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_stoken_worker_pair(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid EWSession Worker - SToken pair.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_map_worker_id_to_session_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not map EWSession Worker ID to SToken.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_decrease_master_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action DecreaseMaster target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_decrease_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action Decrease target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_increase_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action Increase target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_increase_master_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action IncreaseMaster target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_unfreeze_subordonate_user_accounts(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not unfreeze Subordonate user accounts.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_unfreeze_master_account_subpool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not unfreeze Subordonate user account pool '
                     'for given Master account.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_unfreeze_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action Unfreeze target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_freeze_subordonate_user_accounts(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not freeze Subordonate user accounts.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_freeze_master_account_subpool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not freeze Master account subordonate pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_freeze_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action Freeze target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_master_accounts_by_identifier_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master accounts by identifier set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_accounts_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master user accounts found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_master_accounts_marked_for_unlink(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master accounts marked for unlink.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_delete_subordonate_user_accounts(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not delete Subordonate user accounts.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_cleanup_master_account_subpool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not cleanup Master user account '
                     'Subordonate accounts.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_subordonate_accounts_for_masters(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Subordonate user accounts for '
                     'given Master account set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_master_account_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid Master account set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_master_account_id_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid Master account identifier set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_master_accounts_by_id_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master accounts by '
                     'given identifier set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_account_id_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master user account identifier specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_master_user_account_found_by_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No Master user account found by ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_master_user_account_to_ctoken(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set master user account to CToken.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_acquire_master_action_data_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid AcquireMaster action data set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_acquire_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action Acquire target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_master_account_by_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch Master account by ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_master_account_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid Master account identifier.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_acquired_masters_from_client_token_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch acquired Master accounts from '
                     'CToken set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_master_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action NewMaster target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_verify_stoken_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action VerifySToken target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_stoken_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid SToken pool found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_ctoken_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid CToken pool found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_verify_ctoken_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action verify CToken target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_verify_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action verify target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_client_token_not_found_in_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Client token not found in pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_id_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client ID specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_session_token_not_found_in_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Specified session token not found in pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_session_token_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No session token specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_session_worker_id_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session worker ID specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_cleanup_session_tokens(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not cleanup session tokens.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_remove_session_token_from_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not remove session token from SToken pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_stoken_label_not_found_in_stoken_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Session token label not found in SToken pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_remove_session_token_from_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not remove session token from pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_stokens_from_client_token_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session tokens linked to '
                     'client token set items.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_setup_client_token_cleaner_cron(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not setup client token cleaner cron.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_cleanup_client_tokens(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not cleanup client tokens.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_client_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch client token.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_remove_client_token_from_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not remove client token from pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_client_id_not_found_in_ctoken_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Client  ID not found in CToken pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_setup_ewallet_session_cleaner_cron(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not setup ewallet session cleaner cron.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_setup_session_worker_cleaner_cron(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not setup session worker cleaner cron.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cron_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session manager cron pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_cleaner_thread(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set cleaner thread.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cleaner_thread(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch cleaner thread.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_cleaner_thread_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No cleaner thread found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cron_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session manager cron pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_cold_not_set_cleaner_cron_state(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set cleaner cron state.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cleaner_cron_state(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch cleaner cron state.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cleaner_cron_command_interface(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch cleaner cron command interface.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_cleaner_cron_lock(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch account cleaner cron lock.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_no_set_cron_job_pool_entry(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not setup cron job pool entry.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_setup_account_cleaner_cron(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not setup user account cleaner cron.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_init_user_account_cleaner_cron(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not initialise user account cleaner cron.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_cleaner_cron_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system CleanerCron orientation target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_remove_session_worker_from_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not remove session worker from pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_ewallet_session_id_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session id found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_clean_session_worker(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not clean session worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_check_if_session_worker_vacant(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not check if session worker is vacant.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_action_cleanup_ewallet_session_id_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session id found for action cleanup.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_check_if_ewallet_session_is_assigned_to_worker(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not check if ewallet session is assigned to worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_ewallet_session_worker_map_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session worker map found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_worker_id_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No session worker id found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_session_worker_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_write_date(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set ewallet session manager write date.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_contact_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch contact target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_transfer_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch transfer target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_invoice_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch invoice target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_conversion_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch conversion target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_time_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch time target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_session_token_by_label(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session token map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_client_session_token_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch client session token map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_create_client_session_token_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not create client session token map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_values_for_worker_pool_entry(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid values for worker pool entry.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_create_new_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not create new ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_session_token_pair(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client session token pair.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_map_client_session_tokens(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not create client session token map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_session_worker_instruction_response(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Software error. '
                     'Invalid session worker instruction response.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_worker_id_by_client_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session worker ID by given client ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_worker_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid worker id.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client id.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client token.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_worker_pool_entry_by_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch worker pool entry by worker id.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_worker_to_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set worker to session manager worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_worker_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_worker_pool_empty(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Session manager worker pool empty.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_generate_session_worker_identifier(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not generate ewallet session worker identifier.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_generate_id_for_entity_set(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not generate unique identifier for entity set.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_client_token_by_label(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch client token by label.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_stoken_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set session token to pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client id.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_session_token_from_label(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session token from label.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_session_token_validity_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform session token validity check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_session_token_unlink_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform session token unlink check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_session_token_expiration_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform session token validity check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_client_token_validity_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform client token validity check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_client_token_unlink_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform client token unlink check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_perform_client_token_expiration_check(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not perform client token expiration check.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_client_token_from_label(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch client token from pool by client ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_config_handler_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No configuration handler found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_id_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client id found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_ewallet_session_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_session_manager_worker_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session manager worker found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_mapped_session_worker_found_for_client_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No mapped session worker found for client ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_instruction_set_required_data(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid ewallet session manager instruction set data.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_session_manager_controller_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid ewallet controller.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_scrape_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Could not scrape ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_ewallet_sessions_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet sessions found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_session_worker_for_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch session worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_remove_ewallet_session_worker_from_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not remove ewallet session worker '
                     'from session worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_scrape_ewallet_session_worker(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not scrape ewallet session worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_vacant_session_workers_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No vacant session workers found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_cleanup_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action cleanup target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_client_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set client id to pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_spawn_new_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not spawn new ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_assign_worker_to_new_ewallet_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not assign session worker for new ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_ewallet_session_manager_worker_pool_empty(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'EWallet session manager worker pool empty.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_manager_worker_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch ewallet session manager worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_ewallet_session_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid ewallet session ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_ewallet_session_by_id(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch ewallet session by ID.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_session_id_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No ewallet session ID found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response


    def error_no_system_action_interogate_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action interogate target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_unlink_time_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action unlink time target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_unlink_conversion_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action unlink conversion target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_unlink_invoice_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action unlink invoice target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_unlink_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action unlink target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_unlink_transfer_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action unlink transfer target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_switch_credit_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action switch credit target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_time_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new time target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_conversion_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new conversion target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_invoice_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new invoice target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_transfer_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new transfer target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_credit_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new credit target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_invoice_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action view invoice target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_credit_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action view credit target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_edit_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action edit target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_conversion_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action view conversion target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_transfer_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action view transfer target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_conversion_credit_clock_time_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No credit clock time specified for conversion.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_transfer_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action transfer target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_contact_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new contact target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_contact_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action View Contact target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_view_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action View target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_start_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action start target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_conversion_credit_count_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No conversion credit count specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_convert_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action convert target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_supply_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action supply target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_client_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set client ID to session manager client pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_session_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid session token.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_action_new_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client action new target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_worker_found_assigned_to_session(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No worker assigned to ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_update_client_worker_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not update session manager client/worker map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_assign_worker_to_new_ewallet_sesion(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not assign worker to new ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_generate_ewallet_session_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not generate session token for new ewallet session.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_map_client_id_to_session_token(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not map client ID to ewallet session token.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not fetch socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_fetch_socket_handler_required_values(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Could not fetch required values for ewallet socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_spawn_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Could not spawn new ewallet socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_unset_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not unset socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_start_target_specified(self, *args, **kwargs):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action start target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_command_chain_reply_socket_handler_thread_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No command chain reply socket handler thread found '
                     'in thread map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_reply_thread_to_socket_handler_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set reply thread to socket handler thread map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_listener_thread_to_socket_handler_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set instruction '
                     'listener socket handler thread to map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_socket_handler_thread_map_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No socket handler thread map found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_instruction_set_socket_handler_thread_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No instruction set listening socket handler '
                     'thread found in thread map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_instruction_set_listener_socket_handler_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No instruction set listener socket handler found '
                     'for session manager.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_command_chain_reply_socket_handler_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No command chain reply socket handler found '
                     'for session manager.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_listener_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid listener socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_reply_socket_handler(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid reply socket handler.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_socket_port(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid socket port.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_worker_pool_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No worker pool found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_pool_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client pool found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_worker_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid worker pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_client_worker_map_not_found(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client worker map found.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client pool.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_invalid_client_worker_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Invalid client worker map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_update_worker_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not update worker pool with new worker.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_update_client_pool(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not update client pool with new client.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_update_client_worker_session_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not update client/worker/session map with values.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_could_not_set_client_worker_map(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'Something went wrong. '
                     'Could not set client/worker map.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_open_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action open target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_close_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action close target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_action_new_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system action new specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_request_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client request specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_event_client_timeout_target_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system event client timeout target specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_event_expire_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system event expire specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_event_timeout_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system event timeout specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_session_manager_event_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system session manager event specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_session_manager_action_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client session manager action specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_session_manager_action_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system session manager action specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_client_session_manager_controller_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No client session manager controller specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    def error_no_system_session_manager_controller_specified(self, *args):
        instruction_set_response = res_utils.format_error_response(**{
            'failed': True, 'details': args, 'level': 'session-manager',
            'error': 'No system session manager controller specified.',
        })
        self.log_error(**instruction_set_response)
        return instruction_set_response

    # DEBUG

    def debug_worker_unlocked(self, lock):
        log.debug(
            'Worker unlocked - {} - PID: {} - '.format(lock.value, os.getpid())
        )

    def debug_worker_locked(self, lock):
        log.debug(
            'Worker locked - {} - PID: {} - '.format(lock.value, os.getpid())
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

#   def system_session_manager_event_controller(self, **kwargs):
#       '''
#       [ NOTE   ]: System event controller for the EWallet Session Manager, not accessible
#                   to regular user api calls.
#       '''
#       log.debug('')
#       if not kwargs.get('event'):
#           return self.error_no_system_session_manager_event_specified()
#       handlers = {
#           'timeout': self.handle_system_event_timout,
#           'expire': self.handle_system_event_expire,
#       }
#       return handlers[kwargs['event']](**kwargs)

#   def handle_system_action_scrape(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_action_search(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_action_view(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_action_request(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_event_session_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#       timeout = self.event_session_timeout()
#   def handle_system_event_worker_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#       timeout = self.event_worker_timeout()
#   def handle_system_event_client_ack_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#       timeout = self.event_client_ack_timeout()
#   def handle_system_event_client_id_expire(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#       expire = self.event_client_id_expire()
#   def handle_system_event_session_token_expire(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#       expire = self.event_session_token_expire()

#   def event_session_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def event_worker_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def event_client_ack_timeout(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def event_client_id_expire(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def event_session_token_expire(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')

#   def scrape_ewallet_session_worker(self, session_worker):
#       log.debug('TODO - DEPRECATED - Remove')
#       remove_from_pool = self.remove_session_worker_from_pool(session_worker)
#       return self.error_could_not_scrape_ewallet_session_worker(session_worker) \
#           if not remove_from_pool or isinstance(remove_from_pool, dict) and \
#           remove_from_pool.get('failed') else True

#   def cleanup_vacant_session_workers(self, **kwargs):
#       log.debug('TODO - DEPRECATED - Remove')
#       if not kwargs.get('vacant_workers'):
#           return self.error_no_vacant_session_workers_found(kwargs)
#       reserved_buffer_worker = kwargs['vacant_workers'][0]
#       log.info(
#           'Reserved vacant ewallet session worker {}.'.format(
#               reserved_buffer_worker
#           )
#       )
#       kwargs['vacant_workers'].remove(kwargs['vacant_workers'][0])
#       worker_count = len(kwargs['vacant_workers'])
#       for worker in kwargs['vacant_workers']:
#           clean = self.scrape_ewallet_session_worker(worker)
#           if not clean or isinstance(clean, dict) and clean.get('failed'):
#               self.warning_could_not_cleanup_ewallet_session_worker(worker)
#               worker_count -= 1
#               continue
#           log.info('Successfully scraped ewallet session worker.')
#       instruction_set_response = {
#           'failed': False,
#           'workers_cleaned': worker_count,
#           'worker_reserved': reserved_buffer_worker,
#           'worker_pool': self.fetch_ewallet_session_manager_worker_pool(),
#       }
#       return instruction_set_response


