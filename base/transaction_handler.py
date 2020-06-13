from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
#from .res_user import ResUser
from .res_utils import ResUtils, Base
from .config import Config
import time
import datetime
import random
import logging
import pysnooper

log_config = Config().log_config
res_utils = ResUtils()
log = logging.getLogger(log_config['log_name'])


class EWalletTransactionHandler():
    '''
    [ NOTE ]: Responsible for wallet transactions and journaling.
    [ NOTE ]: Currently supports (Credit Payment)
    [ TODO ]: Add support for (Credit Supply, Credit Transfer)
    '''

    transaction_type = None
    source_credit_wallet = None
    target_credit_wallet = None
    source_user_account = None
    target_user_account = None
    active_session = None

    def __init__(self, *args, **kwargs):
        log.debug('')
        self.transaction_type = kwargs.get('transaction_type')
        self.source_credit_wallet = kwargs.get('source_credit_wallet')
        self.target_credit_wallet = kwargs.get('target_credit_wallet')
        self.source_user_account = kwargs.get('source_user_account')
        self.target_user_account = kwargs.get('target_user_account')
        self.active_session = kwargs.get('active_session')

    # FETCHERS

    def fetch_credit_wallet_pair_from_user_accounts(self, source_account, target_account):
        log.debug('')
        return {
            'source': source_account.fetch_user_credit_wallet() or \
                self.error_could_not_fetch_user_credit_wallet(source_account),
            'target': target_account.fetch_user_credit_wallet() or \
                self.error_could_not_fetch_user_credit_wallet(target_account),
        }

    def fetch_credit_wallet_pair_invoice_sheets(self, source_wallet, target_wallet):
        log.debug('')
        return {
            'source': source_wallet.fetch_credit_ewallet_invoice_sheet() or \
                self.error_could_not_fetch_wallet_invoice_sheet(source_wallet),
            'target': target_wallet.fetch_credit_ewallet_invoice_sheet() or \
                self.error_could_not_fetch_wallet_invoice_sheet(target_wallet),
        }

    def fetch_credit_wallet_pair_transfer_sheets(self, source_wallet, target_wallet):
        log.debug('')
        return {
            'source': source_wallet.fetch_credit_ewallet_transfer_sheet() or \
                self.error_could_not_fetch_wallet_transfer_sheet(source_wallet),
            'target': target_wallet.fetch_credit_ewallet_transfer_sheet() or \
                self.error_could_not_fetch_wallet_transfer_sheet(target_wallet),
        }

    def fetch_transaction_handler_value_set(self):
        log.debug('')
        return {
            'transaction_type': self.transaction_type,
            'source_user_account': self.source_user_account,
            'target_user_account': self.target_user_account,
            'source_credit_wallet': self.source_credit_wallet,
            'target_credit_wallet': self.target_credit_wallet,
            'active_session': self.active_session,
        }

    def fetch_credit_wallet_from_user_account(self, user_account):
        log.debug('')
        credit_wallet = user_account.fetch_user_credit_wallet()
        return self.error_no_credit_wallet_found(user_account) if not credit_wallet \
            else credit_wallet

    # SETTERS

    def set_source_credit_wallet(self, source_wallet):
        log.debug('')
        try:
            self.source_credit_wallet = source_wallet
        except:
            return self.error_could_not_set_source_credit_wallet(source_wallet)
        return True

    def set_target_credit_wallet(self, target_wallet):
        log.debug('')
        try:
            self.target_credit_wallet = target_wallet
        except:
            return self.error_could_not_set_target_credit_wallet(target_wallet)
        return True

    # UPDATERS

    def update_transaction_handler_credit_wallets(self, source_wallet, target_wallet):
        log.debug('')
        return {
            'source_credit_wallet': self.set_source_credit_wallet(source_wallet),
            'target_credit_wallet': self.set_target_credit_wallet(target_wallet),
        }

    # VALIDATORS

    def validate_transaction_handler_value_set(self, value_set):
        log.debug('')
        for item in value_set:
            if value_set[item] in [None, False]:
                return self.error_invalid_transaction_handler_value_set(value_set)
        return True

    # COMPUTERS

#   @pysnooper.snoop()
    def compute_transaction_type_supply(self, **kwargs):
        '''
        [ NOTE ]: Command Chain Details
            - seller - Supplier user account
            - source_credit_wallet - Supplier credit wallet
            - target_credit_wallet - Supplied credit wallet
        '''
        log.debug('')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action'
        )
        extract_credits_from_source = kwargs['source_credit_wallet'].main_controller(
            controller='system', action='extract', **sanitized_command_chain
        )
        supply_credits_to_target = kwargs['target_credit_wallet'].main_controller(
            controller='system', action='supply', **sanitized_command_chain
        )
        return {
            'extract': extract_credits_from_source,
            'supply': supply_credits_to_target
        }

    def compute_transaction_type_pay(self, **kwargs):
        log.debug('')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action'
        )
        extract_credits_from_source = kwargs['source_credit_wallet'].main_controller(
            controller='system', action='extract', **sanitized_command_chain
        )
        supply_credits_to_target = kwargs['target_credit_wallet'].main_controller(
            controller='system', action='supply', **sanitized_command_chain
        )
        return {
            'extract': extract_credits_from_source,
            'supply': supply_credits_to_target
        }

    # GENERAL

    def share_partner_transaction_supply_journal_records(self, journal_records, **kwargs):
        log.debug('')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        share_transfer_record = journal_records['transfer_sheets']['target'].credit_transfer_sheet_controller(
            action='add', transfer_type='incoming', **sanitized_command_chain
        )
        share_invoice_record = journal_records['invoice_sheets']['target'].credit_invoice_sheet_controller(
            action='add', seller=kwargs['source_user_account'], transfer_record=share_transfer_record,
            **sanitized_command_chain
        )
        if not share_transfer_record or not share_invoice_record:
            return self.warning_credit_transaction_record_share_failure(
                share_transfer_record=share_transfer_record,
                share_invoice_record=share_invoice_record,
                command_chain=sanitized_command_chain
            )
        return {
            'transfer_record': share_transfer_record,
            'invoice_record': share_invoice_record,
        }

    def share_partner_transaction_pay_journal_records(self, journal_records, **kwargs):
        log.debug('')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        share_transfer_record = journal_records['transfer_sheets']['target'].credit_transfer_sheet_controller(
            action='add', transfer_type='incoming', **sanitized_command_chain
        )
        share_invoice_record = journal_records['invoice_sheets']['target'].credit_invoice_sheet_controller(
            action='add', seller=kwargs['pay'], transfer_record=share_transfer_record,
            **sanitized_command_chain
        )
        if not share_transfer_record or not share_invoice_record:
            return self.warning_credit_transaction_record_share_failure(
                share_transfer_record=share_transfer_record,
                share_invoice_record=share_invoice_record,
                command_chain=sanitized_command_chain
            )
        return {
            'transfer_record': share_transfer_record,
            'invoice_record': share_invoice_record,
        }

    # JOURNALS

    def journal_transaction_type_supply(self, **kwargs):
        log.debug('')
        invoice_sheets = self.fetch_credit_wallet_pair_invoice_sheets(
            kwargs['source_credit_wallet'], kwargs['target_credit_wallet'],
        )
        transfer_sheets = self.fetch_credit_wallet_pair_transfer_sheets(
            kwargs['source_credit_wallet'], kwargs['target_credit_wallet'],
        )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        invoice_record = invoice_sheets['source'].credit_invoice_sheet_controller(
            action='add', seller=kwargs['source_user_account'], **sanitized_command_chain
        )
        transfer_record = transfer_sheets['source'].credit_transfer_sheet_controller(
            action='add', reference=kwargs.get('reference'),
            credits=kwargs['credits'], transfer_type='supply',
            transfer_from=kwargs['source_user_account'].fetch_user_id(),
            transfer_to=kwargs['target_user_account'].fetch_user_id(),
        )
        return {
            'transfer_sheets': transfer_sheets,
            'invoice_sheets': invoice_sheets,
            'transfer_record': transfer_record,
            'invoice_record': invoice_record,
        }

    def journal_transaction_type_pay(self, **kwargs):
        log.debug('')
        invoice_sheets = self.fetch_credit_wallet_pair_invoice_sheets(
            kwargs['source_credit_wallet'], kwargs['target_credit_wallet']
        )
        transfer_sheets = self.fetch_credit_wallet_pair_transfer_sheets(
            kwargs['source_credit_wallet'], kwargs['target_credit_wallet']
        )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        invoice_record = invoice_sheets['source'].credit_invoice_sheet_controller(
            action='add', seller=kwargs['pay'], **sanitized_command_chain
        )
        transfer_record = transfer_sheets['source'].credit_transfer_sheet_controller(
            action='add', reference=kwargs.get('reference'),
            credits=kwargs['credits'], transfer_type='payment',
            transfer_from=kwargs['source_user_account'].fetch_user_id(),
            transfer_to=kwargs['pay'].fetch_user_id(),
        )
        return {
            'transfer_sheets': transfer_sheets,
            'invoice_sheets': invoice_sheets,
            'transfer_record': transfer_record,
            'invoice_record': invoice_record,
        }

    # HANDLERS

#   @pysnooper.snoop()
    def handle_action_start_transaction_type_supply(self, **kwargs):
        log.debug('')
        compute = self.compute_transaction_type_supply(**kwargs)
        journal = self.journal_transaction_type_supply(**kwargs)
        share = self.share_partner_transaction_supply_journal_records(journal, **kwargs)
        kwargs['active_session'].add(
            share['transfer_record'], share['invoice_record']
        )
        return {
            'ewallet_credits': kwargs['source_credit_wallet'].fetch_credit_ewallet_credits(),
            'supplied_credits': compute['supply'],
            'transfer_record': journal['transfer_record'],
            'invoice_record': journal['invoice_record'],
        }

#   @pysnooper.snoop()
    def handle_action_start_transaction_type_pay(self, **kwargs):
        log.debug('')
        compute = self.compute_transaction_type_pay(**kwargs)
        journal = self.journal_transaction_type_pay(**kwargs)
        share = self.share_partner_transaction_pay_journal_records(journal, **kwargs)
        kwargs['active_session'].add(
            share['transfer_record'], share['invoice_record']
        )
        return {
            'ewallet_credits': kwargs['source_credit_wallet'].fetch_credit_ewallet_credits(),
            'spent_credits': compute['extract'],
            'transfer_record': journal['transfer_record'],
            'invoice_record': journal['invoice_record'],
        }

    # TODO
    def handle_action_start_transaction_type_transfer(self, **kwargs):
        log.debug('UNIMPLEMENTED')

    def handle_action_start_transaction(self, **kwargs):
        log.debug('')
        handlers = {
            'pay': self.handle_action_start_transaction_type_pay,
            'transfer': self.handle_action_start_transaction_type_transfer,
            'supply': self.handle_action_start_transaction_type_supply,
        }
        return self.error_invalid_transaction_type(kwargs['transaction_type']) \
            if not kwargs['transaction_type'] in handlers.keys() else \
            handlers[kwargs['transaction_type']](**kwargs)

    # ACTIONS

    def action_setup_transaction_handler(self):
        log.debug('')
        value_set = self.fetch_transaction_handler_value_set()
        update_credit_wallets = self.update_transaction_handler_credit_wallets(
            self.fetch_credit_wallet_from_user_account(
                value_set['source_user_account']
            ),
            self.fetch_credit_wallet_from_user_account(
                value_set['target_user_account']
            )
        )
        return True

    def action_start_transaction(self, **kwargs):
        log.debug('')
        validation_checks = self.validate_transaction_handler_value_set(kwargs)
        return self.error_invalid_transaction_handler_value_set() \
            if not validation_checks else self.handle_action_start_transaction(
                **kwargs
            )

    def action_init_transaction(self, **kwargs):
        log.debug('')
        setup = self.action_setup_transaction_handler()
        value_set = self.fetch_transaction_handler_value_set()
        value_set.update(kwargs)
        start = self.action_start_transaction(**value_set)
        return start

    # CLEANERS

    # WARNINGS

    def warning_credit_transaction_record_share_failure(self, **kwargs):
        log.warning(
            'Credit transaction failure of transfer sheet {} or invoice sheet {}. Details : {}'\
            .format(
                kwargs.get('share_transfer_record'),
                kwargs.get('share_invoice_record'),
                kwargs.get('command_chain'),
            )
        )
        return False

    # ERRORS

    def error_could_not_fetch_wallet_invoice_sheet(self, credit_wallet):
        log.error('Could not fetch invoice sheet from credit wallet {}.'.format(credit_wallet))
        return False

    def error_coult_not_fetch_wallet_transfer_sheet(self, credit_wallet):
        log.error('Could not fetch transfer sheet from credit wallet {}.'.format(credit_wallet))
        return False

    def error_invalid_transaction_type(self, transaction_type):
        log.error('Invalid transaction type {}.'.format(transaction_type))
        return False

    def error_could_not_fetch_user_credit_wallet(self, user_account):
        log.error(
            'Could not credit wallet from user account {}.'.format(
                user_account.fetch_user_name()
            )
        )
        return False

    def error_no_credit_wallet_found(self, user_account):
        log.error(
            'No credit wallet found for user account {}.'.format(
                user_account.fetch_user_name()
            )
        )
        return False

    def error_could_not_set_source_credit_wallet(self, source_wallet):
        log.error(
            'Something went wrong. Could not set source credit wallet {}.'.format(
                source_wallet
            )
        )
        return False

    def error_could_not_set_target_credit_wallet(self, target_wallet):
        log.error(
            'Something went wrong. Could not set target credit wallet {}.'.format(
                target_wallet
            )
        )
        return False


# CODE DUMP

