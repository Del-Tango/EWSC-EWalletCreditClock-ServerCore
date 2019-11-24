import time
import random
import datetime
import pysnooper

class TimeSheetRecord():

    def __init__(self, **kwargs):
        self.record_id = random.randint(10, 20)
        self.time_sheet_id = kwargs.get('time_sheet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.time_spent = kwargs.get('time_spent')

    def fetch_record_id(self):
        return self.record_id

    def fetch_time_sheet_id(self):
        return self.time_sheet_id

    def fetch_create_date(self):
        return self.create_date

    def fetch_write_date(self):
        return self.write_date

    def fetch_reference(self):
        return self.reference

    def fetch_time_spent(self):
        return self.time_spent

    def fetch_record_data(self):
        _values = {
                'id': self.record_id,
                'time_sheet_id': self.time_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,,
                'time_spent': self.time_spent,
                }
        return _values

    def set_time_sheet_id(self, **kwargs):
        global time_sheet_id
        if not kwargs.get('time_sheet_id'):
            return False
        self.time_sheet_id = kwargs['time_sheet_id']
        return True

    def set_reference(self, **kwargs):
        global reference
        if not kwargs.get('reference'):
            return False
        self.reference = kwargs['reference']
        return True

    def set_write_date(self, **kwargs):
        global write_date
        if not kwargs.get('write_date'):
            return False
        self.write_date = kwargs['write_date']
        return True

    def set_time_spent(self, **kwargs):
        global time_spent
        if not kwargs.get('time_spent'):
            return False
        self.time_spent = kwargs['time_spent']
        return True

    def update_write_date(self):
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)


class CreditClockTimeSheet():

    def __init__(self, **kwargs):
        self.time_sheet_id = random.randint(10, 20)
        self.clock_id = kwargs.get('clock_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = {}

    def fetch_time_sheet_id(self):
        return self.time_sheet_id

    def fetch_time_sheet_clock_id(self):
        return self.clock_id

    def fetch_time_sheet_reference(self):
        return self.reference

    def fetch_time_sheet_create_date(self):
        return self.create_date

    def fetch_time_sheet_write_date(self):
        return self.write_date

    def fetch_time_sheet_records(self):
        return self.records

    def fetch_time_sheet_values(self):
        _values = {
                'id': self.time_sheet_id,
                'clock_id': self.clock_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def fetch_time_sheet_record_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.records.get(kwargs['code'])

    def fetch_time_sheet_record_by_ref(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.records:
            if self.records[item].fetch_record_reference() == kwargs['code']:
                return self.records[item]
        return False

    def fetch_time_sheet_record_by_date(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.records:
            if self.records[item].fetch_record_create_date() == kwargs['code']:
                return self.records[item]
        return False

    def fetch_time_sheet_record_by_time(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.records:
            if self.record[item].fetch_record_time_spent() == kwargs['code']:
                return self.records[item]
        return False

    def fetch_time_sheet_records(self, **kwargs):
        return self.records.values()

    def fetch_time_sheet_record(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_time_sheet_record_by_id,
                'reference': self.fetch_time_sheet_record_by_ref,
                'date': self.fetch_time_sheet_record_by_date,
                'time': self.fetch_time_sheet_record_by_time,
                'all': self.fetch_time_sheet_records,
                }
        return _handlers[kwargs['identifier']](**kwargs)

    def set_time_sheet_id(self, **kwargs):
        global time_sheet_id
        if not kwargs.get('sheet_id'):
            return False
        self.time_sheet_id = kwargs['sheet_id']
        return True

    def set_time_sheet_clock_id(self, **kwargs):
        global clock_id
        if not kwargs.get('clock_id'):
            return False
        self.clock_id = kwargs['clock_id']
        return True

    def set_time_sheet_reference(self, **kwargs):
        global reference
        if not kwargs.get('reference'):
            return False
        self.reference = kwargs['reference']
        return True

    def set_time_sheet_records(self, **kwargs):
        global records
        if not kwargs.get('records'):
            return False
        self.records = kwargs['records']
        return True

    def update_time_sheet_records(self, **kwargs):
        global records
        if not kwargs.get('record'):
            return False
        self.records.update({
            kwargs['record'].fetch_record_id(), kwargs['record']
            })
        return self.records

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date

    def display_time_sheet_records(self):
        print('Time Sheet {} Records:'.format(self.reference))
        for k, v in self.records.items():
            print('{}: {} - {}'.format(
                v.fetch_create_date(), k, v.fetch_reference())
                )
        return self.records

    def action_add_time_sheet_record(self, **kwargs):
        _record = TimeSheetRecord(
            time_sheet_id = self.time_sheet_id,
            reference=kwargs.get('reference'),
            time_spent=kwargs.get('time_spent')
        )
        self.update_time_sheet_records(record=_record)
        return _record

    def action_remove_time_sheet_record(self, **kwargs):
        global records
        if not kwargs.get('record_id'):
            return False
        _record = self.fetch_time_sheet_record(
                identifier='id', code=kwargs['record_id']
                )
        return False if not _record \
                else self.records.pop(kwargs['record_id'])

    def action_interogate_time_sheet_records_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.records.get(kwargs['code'])

    def action_interogate_time_sheet_records_by_reference(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.fetch_time_sheet_record(
                identifier='reference', code=kwargs['code']
                )

    def search_time_sheet_record_by_date(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.fetch_time_sheet_record(
                identifier='date', code=kwargs['code']
                )

    # TODO
    def search_time_sheet_record_before_date(self, **kwargs):
        pass

    # TODO
    def search_time_sheet_record_after_date(self, **kwargs):
        pass

    def search_time_sheet_record_by_time(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.fetch_time_sheet_record(
                identifier='time', code=kwargs['code']
                )

    # TODO
    def search_time_sheet_record_greater_time(self, **kwargs):
        pass

    # TODO
    def search_time_sheet_record_lesser_time(self, **kwargs):
        pass

    def action_interogate_time_sheet_records_by_date(self, **kwargs):
        if not kwargs.get('date'):
            return False
        _handlers = {
                'date': self.search_time_sheet_record_by_date,
                'before': self.search_time_sheet_record_before_date,
                'after': self.search_time_sheet_record_after_date,
                }
        return _handlers[kwargs['date']](**kwargs)

    def action_interogate_time_sheet_records_by_time_spent(self, **kwargs):
        if not kwargs.get('time'):
            return False
        _handlers = {
                'time': self.search_time_sheet_record_by_time,
                'more': self.search_time_sheet_record_greater_time,
                'less': self.search_time_sheet_record_lesser_time,
                }
        return _handlers[kwargs['time']](**kwargs)

    def action_interogate_all_time_sheet_records(self, **kwargs):
        return self.fetch_time_sheet_records(identifier='all')

    def action_interogate_time_sheet_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _handlers = {
                'id': self.action_interogate_time_sheet_records_by_id,
                'reference': self.action_interogate_time_sheet_records_by_reference,
                'date': self.action_interogate_time_sheet_records_by_date,
                'time_spent': self.action_interogate_time_sheet_records_by_time_spent,
                'all': self.action_interogate_all_time_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def action_clear_time_sheet_records(self, **kwargs):
        return self.set_time_sheet_records(records={})

    def credit_clock_time_sheet_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'add': self.action_add_time_sheet_record,
                'remove': self.action_remove_time_sheet_record,
                'interogate': self.action_interogate_time_sheet_records,
                'clear': self.action_clear_time_sheet_records,
                }
        return _handlers[kwargs['action']](**kwargs)
