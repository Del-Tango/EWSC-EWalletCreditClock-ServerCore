import time
import datetime
import random
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
res_utils = ResUtils()
log = logging.getLogger(log_config['log_name'])


class CreditInvoiceSheetRecord(Base):
    __tablename__ = 'invoice_sheet_record'

    record_id = Column(Integer, primary_key=True)
    invoice_sheet_id = Column(
        Integer, ForeignKey('credit_invoice_sheet.invoice_sheet_id')
        )
    transfer_record_id = Column(
        Integer, ForeignKey('transfer_sheet_record.record_id')
        )
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    credits = Column(Integer)
    currency = Column(String)
    cost = Column(Float)
    seller_id = Column(Integer, ForeignKey('res_user.user_id'))
    notes = Column(String)

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.invoice_sheet_id = kwargs.get('invoice_sheet_id')
        self.transfer_record_id = kwargs.get('transfer_record_id')
        self.reference = kwargs.get('reference') or 'Invoice Sheet Record'
        self.credits = kwargs.get('credits') or 0
        self.currency = kwargs.get('currency') or 'RON'
        self.cost = kwargs.get('cost') or 1
        self.seller_id = kwargs.get('seller_id')
        self.notes = kwargs.get('notes')

    # FETCHERS

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_record_reference(self):
        log.debug('')
        return self.reference

    def fetch_record_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_record_seller_id(self):
        log.debug('')
        return self.seller_id

    def fetch_record_values(self):
        log.debug('')
        values = {
            'id': self.record_id,
            'invoice_sheet': self.invoice_sheet_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'credits': self.credits,
            'currency': self.currency,
            'cost': self.cost,
            'seller': self.seller_id,
            'notes': self.notes,
        }
        return values

    # SETTERS

    def set_record_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_record_id_found()
        self.record_id = kwargs['record_id']
        return True

    def set_invoice_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_id'):
            return self.error_no_invoice_sheet_id_found()
        self.invoice_sheet_id = kwargs['invoice_sheet_id']
        return False

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits = kwargs['credits']
        return True

    def set_currency(self, **kwargs):
        log.debug('')
        if not kwargs.get('currency'):
            return self.error_no_currency_found()
        self.currency = kwargs['currency']
        return False

    def set_cost(self, **kwargs):
        log.debug('')
        if not kwargs.get('cost'):
            return self.error_no_cost_found()
        self.cost = kwargs['cost']
        return True

    def set_seller_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('seller_id'):
            return self.error_no_seller_id_found()
        self.seller_id = kwargs['seller_id']
        return True

    def set_notes(self, **kwargs):
        log.debug('')
        if not kwargs.get('notes'):
            return self.error_no_notes_found()
        self.notes = kwargs['notes']
        return True

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    # ERRORS

    def error_no_record_id_found(self):
        log.error('No record id found.')
        return False

    def error_no_invoice_sheet_id_found(self):
        log.error('No invoice sheet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_currency_found(self):
        log.error('No currency found')
        return False

    def error_no_cost_found(self):
        log.error('No cost found.')
        return False

    def error_no_seller_id_found(self):
        log.error('No seller id found.')
        return False

    def error_no_notes_found(self):
        log.error('No notes found.')
        return False


class CreditInvoiceSheet(Base):
    __tablename__ = 'credit_invoice_sheet'

    invoice_sheet_id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('credit_ewallet.wallet_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    # O2O
    wallet = relationship('CreditEWallet', back_populates='invoice_sheet')
    # O2M
    records = relationship('CreditInvoiceSheetRecord')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference') or 'Invoice Sheet'
        self.records = kwargs.get('records') or []

    # FETCHERS

    def fetch_credit_invoice_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_invoice_record_search_identifier_specified()
        handlers = {
            'id': self.fetch_credit_invoice_record_by_id,
            'reference': self.fetch_credit_invoice_records_by_ref,
            'date': self.fetch_credit_invoice_records_by_date,
            'seller': self.fetch_credit_invoice_records_by_seller,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def fetch_credit_invoice_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_invoice_record_id_found(kwargs)
        if kwargs.get('active_session'):
            match = list(
                kwargs['active_session'].query(
                    CreditInvoiceSheetRecord
                ).filter_by(
                    record_id=kwargs['code']
                )
            )
        else:
            match = [
                item for item in self.records
                if item.fetch_record_id() is kwargs['code']
            ]
        record = False if not match else match[0]
        if not record:
            return self.warning_could_not_fetch_invoice_record(kwargs)
        log.info('Successfully fetched invoice record by id.')
        return record

    def fetch_invoice_sheet_id(self):
        log.debug('')
        return self.invoice_sheet_id

    def fetch_invoice_sheet_reference(self):
        log.debug('')
        return self.reference

    def fetch_invoice_sheet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_invoice_sheet_records(self):
        log.debug('')
        return self.records

    def fetch_invoice_sheet_values(self):
        log.debug('')
        values = {
            'id': self.invoice_sheet_id,
            'ewallet': self.wallet_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'records': {
                item.fetch_record_id(): item.fetch_record_reference() \
                for item in self.records
            },
        }
        return values

    def fetch_invoice_record_creation_values(self, **kwargs):
        log.debug('')
        values = {
            'reference': kwargs.get('reference'),
            'invoice_sheet_id': self.invoice_sheet_id,
            'credits': kwargs.get('credits'),
            'cost': kwargs.get('cost') or 0,
            'currency': kwargs.get('currency') or 'RON',
            'seller_id': kwargs.get('seller_id'),
            'notes': kwargs.get('notes'),
        }
        return values

    def fetch_credit_invoice_records_by_ref(self, code):
        log.debug('')
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_reference() == code:
                _records.append(v)
        if not _records:
            return self.warning_could_not_fetch_invoice_record(
                    'reference', code
                    )
        log.info('Successfully fetched invoice records by reference.')
        return _records

    def fetch_credit_invoice_records_by_date(self, code):
        log.debug('')
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_create_date() == code:
                _records.append(v)
        if not _records:
            return self.warning_could_not_fetch_invoice_record('date', code)
        log.info('Successfully fetched invoice records by date.')
        return _records

    def fetch_credit_invoice_records_by_seller(self, code):
        log.debug('')
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_seller_id() == code:
                _records.append(v)
        if not _records:
            return self.warning_could_not_fetch_invoice_record('seller', code)
        log.info('Successfully fetched invoice records by seller.')
        return _records

    # SETTERS

    def set_invoice_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_id'):
            return self.error_no_invoice_sheet_id_found()
        self.invoice_sheet_id = kwargs['invoice_sheet_id']
        return True

    def set_wallet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        self.wallet_id = kwargs['wallet_id']
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found()
        self.records = kwargs['records']
        return False

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def update_records(self, record):
        log.debug('')
        if record in self.records:
            return self.error_invoice_record_already_in_sheet_record_set(record)
        try:
            self.records.append(record)
        except:
            return self.error_could_not_update_invoice_sheet_records(record)
        log.info('Successfully updated invoice sheet records.')
        return self.records

    # INTEROGATORS

    def interogate_credit_invoice_record_by_id(self, **kwargs):
        log.debug('')
        record = self.fetch_credit_invoice_records(**kwargs)
        display = self.display_credit_invoice_sheet_records(records=[record])
        return record if display else False

    def interogate_credit_invoice_records_by_ref(self, **kwargs):
        log.debug('')
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_sheet_records(records=_records)
        return _records if _display else False

    def interogate_credit_invoice_records_by_date(self, **kwargs):
        log.debug('')
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    def interogate_credit_invoice_records_by_seller(self, **kwargs):
        log.debug('')
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    def interogate_all_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        _records = [item for item in self.records.values()]
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    # ACTIONS

#   @pysnooper.snoop()
    def action_add_credit_invoice_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found(kwargs)
        if not kwargs.get('seller_id'):
            return self.error_no_seller_id_found(kwargs)
        values = self.fetch_invoice_record_creation_values(**kwargs)
        record = CreditInvoiceSheetRecord(**values)
        kwargs['active_session'].add(record)
        update = self.update_records(record)
        log.info('Successfully added new invoice record.')
        kwargs['active_session'].commit()
        return record

    def action_remove_credit_invoice_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_invoice_record_id_found(kwargs)
        try:
            kwargs['active_session'].query(
                CreditInvoiceSheetRecord
            ).filter_by(
                record_id=kwargs['record_id']
            ).delete()
        except:
            return self.error_could_not_remove_credit_invoice_sheet_record(kwargs)
        return True

    def action_interogate_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_invoice_record_interogation_identifier_specified()
        handlers = {
            'id': self.interogate_credit_invoice_record_by_id,
            'reference': self.interogate_credit_invoice_records_by_ref,
            'date': self.interogate_credit_invoice_records_by_date,
            'seller': self.interogate_credit_invoice_records_by_seller,
            'all': self.interogate_all_credit_invoice_sheet_records,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def action_clear_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        self.records = []
        return self.records

    # CONTROLLERS

    def credit_invoice_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_invoice_sheet_controller_action_specified()
        handlers = {
            'add': self.action_add_credit_invoice_sheet_record,
            'remove': self.action_remove_credit_invoice_sheet_record,
            'interogate': self.action_interogate_credit_invoice_sheet_records,
            'clear': self.action_clear_credit_invoice_sheet_records,
        }
        handle = handlers[kwargs['action']](**kwargs)
        if handle:
            self.update_write_date()
        return handle

    # ERROR HANDLERS

    def error_handler_add_credit_invoice_sheet_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credits': kwargs.get('credits'),
                    'seller_id': kwargs.get('seller_id'),
                    },
                'handlers': {
                    'credits': self.error_no_credits_found,
                    'seller_id': self.error_no_seller_id,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    # WARNINGS

    def warning_could_not_fetch_invoice_record(self, command_chain, *args, **kwargs):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch invoice sheet record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS

    def error_invoice_record_already_in_sheet_record_set(self, record):
        command_chain_response = {
            'failed': True,
            'error': 'Duplicated invoice record. Could not update invoice sheet records '\
                     'with {}.'.format(record),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_invoice_sheet_records(self, record):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not update invoice sheet records '\
                     'with {}.'.format(record),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credits found. Command chain details : {}',
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_seller_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No seller id found. Command chain details : {}',
        }
        log.error(command_chain_response['error'])
        return command_chain_response


    def error_could_not_remove_credit_invoice_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not remove credit invoice sheet record. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_id_found(self):
        log.error('No invoice sheet id found.')
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_records_found(self):
        log.error('No records found.')
        return False

    def error_no_invoice_record_interogation_identifier_specified(self):
        log.error('No invoice record interogation identifier specified.')
        return False

    def error_no_invoice_sheet_controller_action_specified(self):
        log.error('No invoice sheet controller action specified.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_invoice_record_search_identifier_specified(self):
        log.error('No invoice record search identifier specified.')
        return False

    def error_no_new_invoice_record_values_found(self):
        log.error('No new invoice record values found.')
        return False

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

###############################################################################
# CODE DUMP
###############################################################################

