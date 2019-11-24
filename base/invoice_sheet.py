import time
import datetime
import random
import pysnooper


class CreditInvoiceSheetRecord():

    # TODO - Has dummy data
    def __init__(self, **kwargs):
        self.record_id = random.randint(10, 20)
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
        return self.record_id

    def fetch_record_reference(self):
        return self.reference

    def fetch_record_create_date(self):
        return self.create_date

    def fetch_record_seller_id(self):
        return self.seller_id

    def fetch_record_values(self):
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
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date


class CreditInvoiceSheet():

    # TODO - Had dummy data
    def __init__(self, **kwargs):
        self.invoice_sheet_id = random.randint(10, 20)
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = {}

    def fetch_invoice_sheet_id(self):
        return self.invoice_sheet_id

    def fetch_invoice_sheet_reference(self):
        return self.reference

    def fetch_invoice_sheet_create_date(self):
        return self.create_date

    def fetch_invoice_sheet_records(self):
        return self.records

    def fetch_invoice_sheet_values(self):
        _values = {
                'id': self.invoice_sheet_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def fetch_credit_invoice_records_by_id(self, code):
        for k, v in self.records.items():
            if v.fetch_record_id() == code:
                return v
        return False

    def fetch_credit_invoice_records_by_ref(self, code):
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_reference() == code:
                _records.append(v)
        return _records or False

    def fetch_credit_invoice_records_by_date(self, code):
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_create_date() == code:
                _records.append(v)
        return _records or False

    def fetch_credit_invoice_records_by_seller(self, code):
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_seller_id() == code:
                _records.append(v)
        return _records or False

    def fetch_credit_invoice_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _handlers = {
                'id': self.fetch_credit_invoice_records_by_id,
                'reference': self.fetch_credit_invoice_records_by_ref,
                'date': self.fetch_credit_invoice_records_by_date,
                'seller': self.fetch_credit_invoice_records_by_seller,
                }
        _handle = _handlers[kwargs['search_by']](kwargs.get('code'))
        return _handle

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date

    # TODO - Has dummy data
    # TODO - Key record_values = {}
    def add_credit_invoice_sheet_record(self, **kwargs):
        if not kwargs.get('values'):
            return False
        values = kwargs['values']
        if not values.get('credits') or not values.get('seller_id'):
            return False
        global records
        _record = CreditInvoiceSheetRecord(
                invoice_sheet_id=self.invoice_sheet_id,
                reference=values.get('reference'),
                credits=values['credits'],
                cost=values.get('cost'),
                currency=values.get('currency'),
                seller_id=values['seller_id'],
                notes=values.get('notes')
                )
        self.records.update({_record.fetch_record_id(): _record})
        return _record

    def remove_credit_invoice_sheet_record(self, **kwargs):
        global records
        if not kwargs.get('record_id'):
            return False
        for k, v in self.records.items():
            if k == kwargs['record_id']:
                del self.records[k]
                return self.records
        return False

    def interogate_credit_invoice_record_by_id(self, **kwargs):
        _record = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_sheet_records(records=[record])
        return _record if _display else False

    def interogate_credit_invoice_records_by_ref(self, **kwargs):
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_sheet_records(records=_records)
        return _records if _display else False

    def interogate_credit_invoice_records_by_date(self, **kwargs):
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    def interogate_credit_invoice_records_by_seller(self, **kwargs):
        _records = self.fetch_credit_invoice_records(**kwargs)
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    def interogate_all_credit_invoice_sheet_records(self, **kwargs):
        _records = [item for item in self.records.values()]
        _display = self.display_credit_invoice_records(records=_records)
        return _records if _display else False

    def interogate_credit_invoice_sheet_records(self, **kwargs):
        if not kwrags.get('search_by'):
            return False
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
        global records
        self.records = {}
        return self.records

    def credit_invoice_sheet_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
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

    def display_credit_invoice_sheet_records(self, records=[]):
        if not records:
            records = [item for item in self.records.values()]
        for item in records:
            print('{}: {} - {}'.format(
                item.fetch_record_create_date(), item.fetch_record_id(),
                item.fetch_record_reference()
                ))
        return records

    def display_credit_invoice_sheet_record_values(self, records=[]):
        if not records:
            records = [item for item in self.records.values()]
        for item in records:
            print(item.fetch_record_values())
        return records

