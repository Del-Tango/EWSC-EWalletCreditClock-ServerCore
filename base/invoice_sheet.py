import time
import datetime
import random
import logging
import pysnooper
from itertools import count

from .res_utils import ResUtils
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class CreditInvoiceSheetRecord():

    def __init__(self, **kwargs):
        self.seq = count()
        self.record_id = kwargs.get('record_id') or next(self.seq)
        self.invoice_sheet_id = kwargs.get('invoice_sheet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.credits = kwargs.get('credits')
        self.currency = kwargs.get('currency')
        self.cost = kwargs.get('cost')
        self.seller_id = kwargs.get('seller_id')
        self.notes = kwargs.get('notes')

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
        _values = {
                'id': self.record_id,
                'invoice_sheet_id': self.invoice_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'credits': self.credits,
                'currency': self.currency,
                'cost': self.cost,
                'seller_id': self.seller_id,
                'notes': self.notes,
                }
        return _values

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date


class CreditInvoiceSheet():

    def __init__(self, **kwargs):
        self.seq = count()
        self.invoice_sheet_id = kwargs.get('invoice_sheet_id') or next(self.seq)
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = kwargs.get('records') or {}

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
        _values = {
                'id': self.invoice_sheet_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def fetch_invoice_record_creation_values(self, **kwargs):
        log.debug('')
        _values = {
                'reference': kwargs.get('reference'),
                'invoice_sheet_id': self.invoice_sheet_id,
                'credits': kwargs.get('credits'),
                'cost': kwargs.get('cost') or 0,
                'currency': kwargs.get('currency') or 'RON',
                'seller_id': kwargs('seller_id'),
                'notes': kwargs.get('notes'),
                }
        return _values

    def fetch_credit_invoice_record_by_id(self, code):
        log.debug('')
        _record = self.records.get(code)
        if not _records:
            return self.warning_could_not_fetch_invoice_record('id', code)
        return _record

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
        return _records

    def fetch_credit_invoice_records_by_date(self, code):
        log.debug('')
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_create_date() == code:
                _records.append(v)
        if not _records:
            return self.warning_could_not_fetch_invoice_record('date', code)
        return _records

    def fetch_credit_invoice_records_by_seller(self, code):
        log.debug('')
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_seller_id() == code:
                _records.append(v)
        if not _records:
            return self.warning_could_not_fetch_invoice_record('seller', code)
        return _records

    def fetch_credit_invoice_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_invoice_record_search_identifier_specified()
        _handlers = {
                'id': self.fetch_credit_invoice_records_by_id,
                'reference': self.fetch_credit_invoice_records_by_ref,
                'date': self.fetch_credit_invoice_records_by_date,
                'seller': self.fetch_credit_invoice_records_by_seller,
                }
        _handle = _handlers[kwargs['search_by']](kwargs.get('code'))
        return _handle

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def update_records(self, record):
        log.debug('')
        self.records.update({
            record.fetch_record_id():
            record
            })
        return self.records

    def add_credit_invoice_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('seller_id'):
            return self.error_handlers_add_credit_invoice_sheet_record(
                    credits=kwargs.get('credits'),
                    seller_id=kwargs.get('seller_id'),
                    )
        _values = self.fetch_invoice_record_creation_values(**kwargs)
        _record = CreditInvoiceSheetRecord(**_values)
        _update = self.update_records(_record)
        return _record

    def remove_credit_invoice_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_invoice_record_id_found()
        for k, v in self.records.items():
            if k == kwargs['record_id']:
                del self.records[k]
                return self.records
        return self.warning_could_not_fetch_invoice_record(
                'id', kwargs['record_id']
                )

    def interogate_credit_invoice_record_by_id(self, **kwargs):
        log.debug('')
        _record = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_sheet_records(records=[record])
        return _record if _display else False

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

    def interogate_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        if not kwrags.get('search_by'):
            return self.error_no_invoice_record_interogation_identifier_specified()
        _handlers = {
                'id': self.interogate_credit_invoice_record_by_id,
                'reference': self.interogate_credit_invoice_records_by_ref,
                'date': self.interogate_credit_invoice_records_by_date,
                'seller': self.interogate_credit_invoice_records_by_seller,
                'all': self.interogate_all_credit_invoice_sheet_records,
                }
        _handle = _handlers[kwargs['search_by']](**kwargs)
        return _handle

    def clear_credit_invoice_sheet_records(self, **kwargs):
        log.debug('')
        self.records = {}
        return self.records

    # TODO - Refactor
    def credit_invoice_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_invoice_sheet_controller_action_specified()
        _handlers = {
                'add': self.add_credit_invoice_sheet_record,
                'remove': self.remove_credit_invoice_sheet_record,
                'interogate': self.interogate_credit_invoice_sheet_records,
                'clear': self.clear_credit_invoice_sheet_records,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle:
            self.update_write_date()
        return _handle

    # TODO - Refactor
    def display_credit_invoice_sheet_records(self, records=[]):
        log.debug('')
        if not records:
            records = [item for item in self.records.values()]
        for item in records:
            print('{}: {} - {}'.format(
                item.fetch_record_create_date(), item.fetch_record_id(),
                item.fetch_record_reference()
                ))
        return records

    # TODO - Refactor
    def display_credit_invoice_sheet_record_values(self, records=[]):
        log.debug('')
        if not records:
            records = [item for item in self.records.values()]
        for item in records:
            print(item.fetch_record_values())
        return records

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

    def error_no_invoice_record_interogation_identifier_specified(self):
        log.error('No invoice record interogation identifier specified.')
        return False

    def error_no_invoice_sheet_controller_action_specified(self):
        log.error('No invoice sheet controller action specified.')
        return False

    def error_no_invoice_record_id_found(self):
        log.error('No invoice record id found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_seller_id_found(self):
        log.error('No seller id found.')
        return False

    def error_no_invoice_record_search_identifier_specified(self):
        log.error('No invoice record search identifier specified.')
        return False

    def error_no_new_invoice_record_values_found(self):
        log.error('No new invoice record values found.')
        return False

    def warning_could_not_fetch_invoice_record(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch invoice record by %s %s.', search_code, code
                )
        return False

