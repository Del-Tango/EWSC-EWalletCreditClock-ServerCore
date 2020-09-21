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
        if not source_account and not target_account:
            return self.error_no_user_accounts_found({}, source_account, target_account)
        return {
            'source': self.error_could_not_fetch_user_credit_wallet(source_account) \
                if not source_account \
                else source_account.fetch_user_credit_wallet(),
            'target': self.error_could_not_fetch_user_credit_wallet(target_account) \
                if not target_account \
                else target_account.fetch_user_credit_wallet(),
        }

    def fetch_credit_wallet_pair_invoice_sheets(self, source_wallet, target_wallet):
        log.debug('')
        if not source_wallet and not target_wallet:
            return self.error_no_wallets_found({}, source_wallet, target_wallet)
        return {
            'source': self.error_could_not_fetch_wallet_invoice_sheet(
                    source_wallet, target_wallet
                ) if not source_wallet or isinstance(source_wallet, dict) and \
                source_wallet.get('failed') else \
                source_wallet.fetch_credit_ewallet_invoice_sheet(),
            'target': self.error_could_not_fetch_wallet_invoice_sheet(
                    source_wallet, target_wallet
                ) if not target_wallet or isinstance(target_wallet, dict) and \
                target_wallet.get('failed') else \
                target_wallet.fetch_credit_ewallet_invoice_sheet(),
        }

    def fetch_credit_wallet_pair_transfer_sheets(self, source_wallet, target_wallet):
        log.debug('')
        if not source_wallet and not target_wallet:
            return self.error_no_wallets_found({}, source_wallet, target_wallet)
        return {
            'source': self.error_could_not_fetch_wallet_transfer_sheet(
                    source_wallet, target_wallet
                ) if not source_wallet or isinstance(source_wallet, dict) and \
                source_wallet.get('failed') else \
                source_wallet.fetch_credit_ewallet_transfer_sheet(),
            'target': self.error_could_not_fetch_wallet_transfer_sheet(
                    source_wallet, target_wallet
                ) if not target_wallet or isinstance(target_wallet, dict) and \
                target_wallet.get('failed') else \
                target_wallet.fetch_credit_ewallet_transfer_sheet(),
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
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return self.error_no_user_account_found(user_account)
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

#   @pysnooper.snoop()
    def validate_transaction_handler_value_set(self, value_set):
        log.debug('')
        for item in value_set:
            if value_set[item] in [None, False]:
                return self.error_invalid_transaction_handler_value_set(value_set)
        return True

    # COMPUTERS

#   @pysnooper.snoop('logs/ewallet.log')
    def compute_transaction_type_supply(self, **kwargs):
        '''
        [ NOTE ]: Command Chain Details
            - seller - Supplier user account
            - source_credit_wallet - Supplier credit wallet
            - target_credit_wallet - Supplied credit wallet
        '''
        log.debug('')
        if not kwargs.get('source_credit_wallet') or \
                not kwargs.get('target_credit_wallet'):
            if not kwargs.get('source_credit_wallet'):
                return self.error_no_source_credit_wallet_found(kwargs)
            elif not kwargs.get('target_credit_wallet'):
                return self.error_no_target_credit_wallet_found(kwargs)
            return self.error_no_wallets_found(kwargs)
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

    def compute_transaction_type_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('source_credit_wallet') or \
                not kwargs.get('target_credit_wallet'):
            if not kwargs.get('source_credit_wallet'):
                return self.error_no_source_credit_wallet_found(kwargs)
            elif not kwargs.get('target_credit_wallet'):
                return self.error_no_target_credit_wallet_found(kwargs)
            return self.error_no_wallets_found(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action'
        )
        extract_credits_from_source = kwargs['source_credit_wallet'].main_controller(
            controller='system', action='extract', **sanitized_command_chain
        )
        if not extract_credits_from_source or \
                isinstance(extract_credits_from_source, dict) and \
                extract_credits_from_source.get('failed'):
            return self.error_could_not_extract_credits_from_source(
                kwargs, extract_credits_from_source
            )
        supply_credits_to_target = kwargs['target_credit_wallet'].main_controller(
            controller='system', action='supply', **sanitized_command_chain
        )
        if not supply_credits_to_target or \
                isinstance(supply_credits_to_target, dict) and \
                supply_credits_to_target.get('failed'):
            return self.error_could_not_supply_credits_to_target(
                kwargs, extract_credits_from_source, supply_credits_to_target
            )
        return {
            'extract': extract_credits_from_source,
            'supply': supply_credits_to_target
        }

    def compute_transaction_type_pay(self, **kwargs):
        log.debug('')
        if not kwargs.get('target_credit_wallet') or \
                isinstance(kwargs['target_credit_wallet'], dict) and \
                kwargs['target_credit_wallet'].get('failed'):
            return self.error_no_source_credit_wallet_found(kwargs)
        if not kwargs.get('source_credit_wallet') or \
                isinstance(kwargs['source_credit_wallet'], dict) and \
                kwargs['source_credit_wallet'].get('failed'):
            return self.error_no_target_credit_wallet_found(kwargs)
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

#   @pysnooper.snoop('logs/ewallet.log')
    def share_partner_transaction_supply_journal_records(self, journal_records, **kwargs):
        log.debug('')
        if not journal_records.get('transfer_sheets') or \
                not journal_records.get('invoice_sheets'):
            if not journal_records.get('transfer_sheets'):
                return self.error_no_transfer_sheets_found(kwargs, journal_records)
            elif not journal_records.get('invoice_sheets'):
                return self.error_no_invoice_sheets_found(kwargs, journal_records)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        share_transfer_record = journal_records[
            'transfer_sheets'
        ][
            'target'
        ].credit_transfer_sheet_controller(
            action='add', transfer_type='incoming', **sanitized_command_chain
        )
        share_invoice_record = journal_records[
            'invoice_sheets'
        ][
            'target'
        ].credit_invoice_sheet_controller(
            action='add', seller=kwargs['source_user_account'],
            transfer_record=share_transfer_record, **sanitized_command_chain
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

#   @pysnooper.snoop('logs/ewallet.log')
    def share_partner_transaction_transfer_journal_records(self, journal_records, **kwargs):
        log.debug('')
        if not journal_records.get('transfer_sheets'):
            return self.error_no_transfer_sheets_found(kwargs, journal_records)
        transfer_from = kwargs['source_user_account'].fetch_user_id()
        transfer_to = kwargs['transfer_to'].fetch_user_id()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action', 'transfer_from', 'transfer_to'
        )
        share_transfer_record = journal_records['transfer_sheets']['target']\
            .credit_transfer_sheet_controller(
                action='add', transfer_type='incoming',
                transfer_from=transfer_from, transfer_to=transfer_to,
                **sanitized_command_chain
            )
        if not share_transfer_record or isinstance(share_transfer_record, dict) and \
                share_transfer_record.get('failed'):
            return self.warning_credit_transaction_record_share_failure(
                share_transfer_record=share_transfer_record,
                share_invoice_record=None,
                command_chain=sanitized_command_chain
            )
        return {
            'failed': False,
            'transfer_record': share_transfer_record,
        }

    def share_partner_transaction_pay_journal_records(self, journal_records, **kwargs):
        log.debug('')
        if not journal_records.get('transfer_sheets') or \
                not journal_records.get('invoice_sheets'):
            if not journal_records.get('transfer_sheets'):
                return self.error_no_transfer_sheets_found(kwargs, journal_records)
            elif not journal_records.get('invoice_sheets'):
                return self.error_no_invoice_sheets_found(kwargs, journal_records)
        if not journal_records['transfer_sheets'].get('target') or \
                not journal_records['invoice_sheets'].get('target'):
            return self.error_no_journal_records_found(kwargs, journal_records)
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

#   @pysnooper.snoop('logs/ewallet.log')
    def journal_transaction_type_transfer(self, **kwargs):
        log.debug('')
        transfer_sheets = self.fetch_credit_wallet_pair_transfer_sheets(
            kwargs['source_credit_wallet'], kwargs['target_credit_wallet'],
        )
        if not transfer_sheets or isinstance(transfer_sheets, dict) and \
                transfer_sheets.get('failed'):
            return transfer_sheets
        elif not transfer_sheets.get('source'):
            return self.error_no_source_transfer_sheet_found(kwargs, transfer_sheets)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action', 'transfer_to'
        )
        transfer_record = transfer_sheets['source'].credit_transfer_sheet_controller(
            action='add', transfer_type='transfer',
            transfer_from=kwargs['source_user_account'].fetch_user_id(),
            transfer_to=kwargs['target_user_account'].fetch_user_id(),
            **sanitized_command_chain
        )
        kwargs['active_session'].add(transfer_record)
        kwargs['active_session'].commit()
        return {
            'transfer_sheets': transfer_sheets,
            'transfer_record': transfer_record,
        }

#   @pysnooper.snoop('logs/ewallet.log')
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
        if not invoice_sheets.get('source') or not transfer_sheets['source']:
            if not invoice_sheets.get('source'):
                return self.error_no_source_invoice_sheet_found(
                    kwargs, invoice_sheets
                )
            elif not transfer_sheets.get('source'):
                return self.error_no_source_transfer_sheet_found(
                    kwargs, transfer_sheets
                )
            return self.error_no_transaction_supply_journal_source_sheets_found(
                kwargs, invoice_sheets, transfer_sheets
            )
        invoice_record = invoice_sheets['source'].credit_invoice_sheet_controller(
            action='add', seller_id=kwargs['source_user_account'].fetch_user_id(),
            **sanitized_command_chain
        )
        transfer_record = transfer_sheets['source'].credit_transfer_sheet_controller(
            action='add', transfer_type='supply',
            transfer_from=kwargs['source_user_account'].fetch_user_id(),
            transfer_to=kwargs['target_user_account'].fetch_user_id(),
            **sanitized_command_chain
        )
        return {
            'transfer_sheets': transfer_sheets,
            'invoice_sheets': invoice_sheets,
            'transfer_record': transfer_record,
            'invoice_record': invoice_record,
        }

#   @pysnooper.snoop()
    def journal_transaction_type_pay(self, **kwargs):
        '''
        [ NOTE ]: Source user account - Client performing the payment.
        [ NOTE ]: Target user account - Supplier
        '''
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
            action='add', seller=kwargs['pay'],
            seller_id=kwargs['pay'].fetch_user_id(),
            **sanitized_command_chain
        )
        transfer_record = transfer_sheets['source'].credit_transfer_sheet_controller(
            action='add', transfer_type='payment',
            transfer_from=kwargs['source_user_account'].fetch_user_id(),
            transfer_to=kwargs['pay'].fetch_user_id(),
            seller_id=kwargs['pay'].fetch_user_id(),
            **sanitized_command_chain
        )
        return {
            'transfer_sheets': transfer_sheets,
            'invoice_sheets': invoice_sheets,
            'transfer_record': transfer_record,
            'invoice_record': invoice_record,
        }

    # HANDLERS

#   @pysnooper.snoop()
    def handle_action_start_transaction_type_pay(self, **kwargs):
        log.debug('')
        compute = self.compute_transaction_type_pay(**kwargs)
        if not compute or isinstance(compute, dict) and \
                compute.get('failed'):
            return self.error_could_not_compute_transaction_type_pay(
                kwargs, compute
            )
        journal = self.journal_transaction_type_pay(**kwargs)
        share = self.share_partner_transaction_pay_journal_records(journal, **kwargs)
        if not share or isinstance(share, dict) and share.get('failed'):
            return share
        elif not share.get('transfer_record') or not share.get('invoice_record'):
            if not share.get('transfer_record'):
                return self.error_no_transfer_record_found(kwargs)
            elif not share.get('invoice_record'):
                return self.error_no_invoice_record_found(kwargs)
        kwargs['active_session'].add(
            share['transfer_record'], share['invoice_record']
        )
        return {
            'ewallet_credits': kwargs['source_credit_wallet'].fetch_credit_ewallet_credits(),
            'spent_credits': compute['extract'],
            'transfer_record': journal['transfer_record'],
            'invoice_record': journal['invoice_record'],
        }

#   @pysnooper.snoop('logs/ewallet.log')
    def handle_action_start_transaction_type_supply(self, **kwargs):
        log.debug('')
        compute = self.compute_transaction_type_supply(**kwargs)
        journal = self.journal_transaction_type_supply(**kwargs)
        share = self.share_partner_transaction_supply_journal_records(journal, **kwargs)
        if not share or isinstance(share, dict) and share.get('failed'):
            return share
        kwargs['active_session'].add(
            share['transfer_record'], share['invoice_record']
        )
        command_chain_response = {
            'ewallet_credits': kwargs['target_credit_wallet'].fetch_credit_ewallet_credits(),
            'supplied_credits': compute['supply'],
            'transfer_record': journal['transfer_record'],
            'invoice_record': journal['invoice_record'],
        }
        return command_chain_response

#   @pysnooper.snoop()
    def handle_action_start_transaction_type_transfer(self, **kwargs):
        log.debug('')
        compute = self.compute_transaction_type_transfer(**kwargs)
        journal = self.journal_transaction_type_transfer(**kwargs)
        share = self.share_partner_transaction_transfer_journal_records(journal, **kwargs)
        if not share or isinstance(share, dict) and share.get('failed'):
            return share
        if not share.get('transfer_record'):
            return self.error_no_transfer_record_shared(kwargs)
        kwargs['active_session'].add(share['transfer_record'])
        return {
            'ewallet_credits': kwargs['source_credit_wallet'].fetch_credit_ewallet_credits(),
            'transfered_credits': kwargs['credits'],
            'transfer_record': journal['transfer_record'].fetch_record_id(),
        }

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
        return self.error_invalid_transaction_handler_value_set(kwargs) \
            if not validation_checks else self.handle_action_start_transaction(
                **kwargs
            )


#   @pysnooper.snoop()
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
        command_chain_response = {
            'failed': True,
            'warning': 'Credit transaction failure. '
                       'Details: {}'.format(kwargs)
        }
        log.warning(command_chain_response['warnings'])
        return command_chain_response

    # ERRORS

    def error_could_not_extract_credits_from_source(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not extract credits from source ewallet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_supply_credits_to_target(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not supply credits to target ewallet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_compute_transaction_type_pay(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not compute transaction type pay. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_wallet_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch user credit ewallet transfer sheet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_wallet_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch user credit ewallet invoice sheet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No user account found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_source_transfer_sheet_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No source transfer sheet found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_record_shared(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer record shared. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_record_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer record found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice record found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_journal_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No journal records found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_sheets_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer sheet set found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheets_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet set found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_credit_wallet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch user account credit ewallet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_accounts_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No user accounts found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_source_credit_wallet_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No source credit ewallet found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_target_credit_wallet_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No target credit ewallet found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_wallets_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallets found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_source_invoice_sheet_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No source invoice sheet found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_source_transfer_sheet_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No source transfer sheet found. Details: {}, {}'\
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transaction_supply_journal_source_sheets_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No journal source sheets found for transaction type supply. '
                     'Details: {}, {}'.format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_transaction_handler_value_set(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid transaction handler values set. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_wallet_transfer_sheet(self, credit_wallet):
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

