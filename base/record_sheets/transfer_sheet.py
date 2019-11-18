import time
import datetime
import random
import pysnooper


class CreditTransferSheetRecord():

    # TODO - Refactor
    def __init__(self, **kwargs):
        self.record_id = random.randint(10, 20)
        self.transfer_sheet_id = kwargs.get('transfer_sheet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.transfer_type = kwargs.get('transfer_type')
        self.transfer_from = kwargs.get('transfer_from')
        self.transfer_to = kwargs.get('transfer_to')
        self.credits = kwargs.get('credits')

    def fetch_record_id(self):
        return self.record_id

    def fetch_record_reference(self):
        return self.reference

    def fetch_record_create_date(self):
        return self.create_date

    def fetch_record_transfer_from(self):
        return self.transfer_from

    def fetch_record_transfer_to(self):
        return self.transfer_to

    def fetch_record_values(self):
        _values = {
                'id': self.record_id,
                'transfer_sheet_id': self.transfer_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'transfer_type': self.transfer_type,
                'transfer_from': self.transfer_from,
                'transfer_to': self.transfer_to,
                'credits': self.credits,
                }
        return _values

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date


class CreditTransferSheet():

    # TODO - Refactor
    def __init__(self, **kwargs):
        self.transfer_sheet_id = random.randint(10, 20)
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = {}

    def fetch_transfer_sheet_id(self):
        return self.transfer_sheet_id

    def fetch_transfer_sheet_reference(self):
        return self.reference

    def fetch_transfer_sheet_create_date(self):
        return self.create_date

    def fetch_transfer_sheet_records(self):
        return self.records

    def fetch_transfer_sheet_values(self):
        _values = {
                'id': self.transfer_sheet_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date

    def fetch_transfer_sheet_record_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _record = [self.records.get(kwargs.get('code'))]
        return _record or False

    def fetch_transfer_sheet_record_by_ref(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_reference() == kwargs['code']
                ]
        return False

    def fetch_transfer_sheet_record_by_date(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_create_date() == kwargs['code']
                ]
        return _records or False

    def fetch_transfer_sheet_record_by_src(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_transfer_from() == kwargs['code']
                ]
        return _records or False

    def fetch_transfer_sheet_record_by_dst(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_transfer_to() == kwargs['code']
                ]
        return _records

    def fetch_all_transfer_sheet_records(self, **kwargs):
        _records = [item for item in self.records.values()]
        return _records

    def fetch_transfer_sheet_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _handlers = {
                'id': self.fetch_transfer_sheet_record_by_id,
                'reference': self.fetch_transfer_sheet_record_by_ref,
                'date': self.fetch_transfer_sheet_record_by_date,
                'transfer_from': self.fetch_transfer_sheet_record_by_src,
                'transfer_to': self.fetch_transfer_sheet_record_by_dst,
                'all': self.fetch_all_transfer_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def add_transfer_sheet_record(self, **kwargs):
        if not kwargs.get('values'):
            return False
        values = kwargs['values']
        if not values.get('transfer_type') or not values.get('credits'):
            return False
        global records
        _record = CreditTransferSheetRecord(
                    transfer_sheet_id=self.transfer_sheet_id,
                    reference=values.get('reference'),
                    transfer_type=values['transfer_type'], #incomming | outgoing | expence
                    transfer_from=values.get('transfer_from'),
                    transfer_to=values.get('transfer_to'),
                    credits=values['credits'],
                )
        _record_id = _record.fetch_record_id()
        self.records.update({_record_id: _record})
        return _record

    def remove_transfer_sheet_record(self, **kwargs):
        if not kwargs.get('search_by'):
            return Flase
        global records
        _records_to_remove = self.fetch_transfer_sheet_records(**kwargs)
        for item in _records_to_remove:
            del self.records[item.fetch_record_id()]
        return self.records

    def append_transfer_sheet_record(self, **kwargs):
        if not kwargs.get('records'):
            return False
        global records
        for item in kwargs['records']:
            self.records.update({item.fetch_record_id(): item})
        return self.records

    def interogate_transfer_sheet_records(self, **kwargs):
        _records = self.fetch_transfer_sheet_records(**kwargs)
        _display = self.display_transfer_sheet_records(records=_records)
        return _records if _display else False

    def clear_transfer_sheet_records(self, **kwargs):
        global records
        self.records = {}
        return self.records

    def credit_transfer_sheet_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'add': self.add_transfer_sheet_record,
                'remove': self.remove_transfer_sheet_record,
                'append': self.append_transfer_sheet_record,
                'interogate': self.interogate_transfer_sheet_records,
                'clear': self.clear_transfer_sheet_records,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return _handle

    def display_transfer_sheet_records(self, records=[]):
        if not records:
            records = [item for item in self.records.values()]
        print('Transfer Sheet {} Records:'.format(self.reference))
        for item in records:
            print('{}: {} - {}'.format(
                item.fetch_record_create_date(), item.fetch_record_id(),
                item.fetch_record_reference()
                ))
        return records







