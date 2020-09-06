import datetime
import logging
import pysnooper

from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


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
        self.reference = kwargs.get(
            'reference',
            config.invoice_sheet_config['invoice_record_reference']
        )
        self.credits = kwargs.get('credits', 0)
        self.currency = kwargs.get('currency', 'RON')
        self.cost = kwargs.get('cost', 1)
        self.seller_id = kwargs.get('seller_id', int())
        self.notes = kwargs.get('notes', str())

    # FETCHERS (RECORD)

    def fetch_record_write_date(self):
        log.debg('')
        return self.write_date

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

    # SETTERS (RECORD)

    def set_transfer_record_id(self, record_id):
        log.debug('')
        try:
            self.transfer_record_id = record_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_transfer_record_id(
                record_id, self.transfer_record_id, e
            )
        log.info('Successfully set invoice record transfer record id.')
        return True

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_record_create_date(
                create_date, self.create_date, e
            )
        log.info('Successfully set invoice record create date.')
        return True

    def set_record_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_record_id_found(kwargs)
        try:
            self.record_id = kwargs['record_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_record_id(
                kwargs, self.record_id, e
            )
        log.info('Successfully set invoice record id.')
        return True

    def set_invoice_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_id'):
            return self.error_no_invoice_sheet_id_found(kwargs)
        try:
            self.invoice_sheet_id = kwargs['invoice_sheet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_id(
                kwargs, self.invoice_sheet_id, e
            )
        log.info('Successfully set invoice record sheet id.')
        return False

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_record_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set invoice record reference.')
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found(kwargs)
        try:
            self.credits = kwargs['credits']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credits(
                kwargs, self.credits, e
            )
        log.info('Successfully set invoice record credits.')
        return True

    def set_currency(self, **kwargs):
        log.debug('')
        if not kwargs.get('currency'):
            return self.error_no_currency_found(kwargs)
        try:
            self.currency = kwargs['currency']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_currency(
                kwargs, self.currency, e
            )
        log.info('Successfully set invoice record currency.')
        return False

    def set_cost(self, **kwargs):
        log.debug('')
        if not kwargs.get('cost'):
            return self.error_no_cost_found(kwargs)
        try:
            self.cost = kwargs['cost']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_cost(
                kwargs, self.cost, e
            )
        log.info('Successfully set invoice record cost.')
        return True

    def set_seller_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('seller_id'):
            return self.error_no_seller_id_found(kwargs)
        try:
            self.seller_id = kwargs['seller_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_seller_id(
                kwargs, self.seller_id, e
            )
        log.info('Successfully set invoice record seller id.')
        return True

    def set_notes(self, **kwargs):
        log.debug('')
        if not kwargs.get('notes'):
            return self.error_no_notes_found(kwargs)
        try:
            self.notes = kwargs['notes']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_record_notes(
                kwargs, self.notes, e
            )
        log.info('Successfully set invoice record notes.')
        return True

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_invoice_record_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set invoice record write date.')
        return True

    # UPDATERS (RECORD)

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_record_write_date()

    # ERRORS (RECORD)

    def error_could_not_set_invoice_record_create_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record create date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_transfer_record_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record linked transfer record id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_record_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_record_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record sheet id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_record_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credits(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record credits. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_currency(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record currency. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_cost(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record cost. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_seller_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record seller id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_record_notes(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice record notes. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No record id found. Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet id found. Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice record reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credits found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_currency_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No currency found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_cost_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No cost found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_seller_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No seller id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_notes_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No notes found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response


class CreditInvoiceSheet(Base):
    __tablename__ = 'credit_invoice_sheet'

    invoice_sheet_id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('credit_ewallet.wallet_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    wallet = relationship('CreditEWallet', back_populates='invoice_sheet')
    records = relationship('CreditInvoiceSheetRecord')

    def __init__(self, **kwargs):
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.wallet_id = kwargs.get('wallet_id', int())
        self.wallet = kwargs.get('wallet')
        self.reference = kwargs.get('reference') or \
            config.invoice_sheet_config['invoice_sheet_reference']
        self.records = kwargs.get('records', [])

    # FETCHERS (LIST)

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
        check = self.check_record_in_invoice_sheet(record)
        if not check:
            return self.warning_record_not_in_invoice_sheet(
                kwargs, record
            )
        log.info('Successfully fetched invoice record by id.')
        return record

    def fetch_credit_invoice_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_invoice_record_search_identifier_specified()
        handlers = {
            'id': self.fetch_credit_invoice_record_by_id,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def fetch_invoice_sheet_id(self):
        log.debug('')
        return self.invoice_sheet_id

    def fetch_invoice_sheet_reference(self):
        log.debug('')
        return self.reference

    def fetch_invoice_sheet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_invoice_sheet_write_date(self):
        log.debug('')
        return self.write_date

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
            'reference': kwargs.get('reference') or
                config.invoice_sheet_config['invoice_record_reference'],
            'invoice_sheet_id': self.invoice_sheet_id,
            'credits': kwargs.get('credits'),
            'cost': kwargs.get('cost') or 0,
            'currency': kwargs.get('currency') or 'RON',
            'seller_id': kwargs.get('seller_id'),
            'notes': kwargs.get('notes'),
        }
        return values

    # SETTERS (LIST)

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_create_date(
                create_date, self.create_date, e
            )
        log.info('Successfully set invoice sheet credit ewallet.')
        return True

    def set_ewallet(self, credit_ewallet):
        log.debug('')
        try:
            self.wallet = credit_ewallet
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_ewallet(
                credit_ewallet, self.wallet, e
            )
        log.info('Successfully set invoice sheet credit ewallet.')
        return True

    def set_invoice_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_id'):
            return self.error_no_invoice_sheet_id_found(kwargs)
        try:
            self.invoice_sheet_id = kwargs['invoice_sheet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_id(
                kwargs, self.invoice_sheet_id, e
            )
        log.info('Successfully set invoice sheet id.')
        return True

    def set_wallet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found(kwargs)
        try:
            self.wallet_id = kwargs['wallet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_ewallet_id(
                kwargs, self.wallet_id, e
            )
        log.info('Successfully set invoice sheet ewallet id.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set invoice sheet reference.')
        return True

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found(kwargs)
        try:
            self.records = kwargs['records']
            self.update_write_date()
        except Exception as e:
            return self.error_no_invoice_records_found(
                kwargs, self.records, e
            )
        log.info('Successfully set invoice sheet records.')
        return False

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set invoice sheet write date.')
        return True

    # UPDATERS (LIST)

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_invoice_sheet_write_date()

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

    # CHECKERS

    def check_record_in_invoice_sheet(self, record):
        log.debug('')
        return False if record not in self.records else True

    # INTEROGATORS (LIST)

    def interogate_credit_invoice_record_by_id(self, **kwargs):
        log.debug('')
        record = self.fetch_credit_invoice_records(**kwargs)
        display = self.display_credit_invoice_sheet_records(records=[record])
        return record if display else False

    # ACTIONS (LIST)

    def action_remove_credit_invoice_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_invoice_record_id_found(kwargs)
        record = self.fetch_credit_invoice_record_by_id(
            code=kwargs['record_id'],
            active_session=kwargs['active_session'],
        )
        check = self.check_record_in_invoice_sheet(record)
        if not check:
            return self.warning_record_not_in_invoice_sheet(
                kwargs, record, check
            )
        try:
            kwargs['active_session'].query(
                CreditInvoiceSheetRecord
            ).filter_by(
                record_id=kwargs['record_id']
            ).delete()
        except:
            return self.error_could_not_remove_credit_invoice_sheet_record(kwargs)
        return True

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

    def action_interogate_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_invoice_record_interogation_identifier_specified()
        handlers = {
            'id': self.interogate_credit_invoice_record_by_id,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def action_clear_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        set_record = self.set_record(records=[])
        return set_record if isinstance(set_record, dict) and \
            set_record.get('failed') else self.fetch_invoice_sheet_records()

    # CONTROLLERS (LIST)

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
        return handlers[kwargs['action']](**kwargs)

    # ERROR HANDLERS (LIST)

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

    # WARNINGS (LIST)

    def warning_record_not_in_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Record not in invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_invoice_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch invoice sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS (LIST)

    def error_could_not_set_invoice_sheet_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet credit ewallet. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_create_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet create date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_ewallet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet ewallet id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet records found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invoice_record_already_in_sheet_record_set(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Duplicated invoice record. '
                     'Could not update invoice sheet records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_invoice_sheet_records(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not update invoice sheet records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credits found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_seller_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No seller id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_credit_invoice_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove invoice sheet record. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet record id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet sheet id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_wallet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No wallet id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet records found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_interogation_identifier_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice record interogation identifier specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_controller_action_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet controller action specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credits found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_search_identifier_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice record search identifier specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_new_invoice_record_values_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No new invoice record values found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No active session found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response


###############################################################################
# CODE DUMP
###############################################################################

