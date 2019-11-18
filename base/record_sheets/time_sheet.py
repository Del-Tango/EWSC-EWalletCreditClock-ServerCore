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
        self.credit_clock = kwargs.get('credit_clock')
        self.time_spent = kwargs.get('time_spent')

    def fetch_record_id(self):
        return self.record_id

    def fetch_create_date(self):
        return self.create_date

    def fetch_reference(self):
        return self.reference

    def fetch_record_data(self):
        _values = {
                'id': self.record_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'credit_clock': self.credit_clock,
                'time_spent': self.time_spent,
                }
        return _values

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date


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

    def fetch_time_sheet_reference(self):
        return self.reference

    def fetch_time_sheet_create_date(self):
        return self.create_date

    def fetch_time_sheet_write_date(self):
        return self.write_date

    def fetch_time_sheet_values(self):
        _values = {
                'id': self.time_sheet_id,
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

    def add_time_sheet_record(self, values):
        global records
        _record = TimeSheetRecord(
            time_sheet_id = self.time_sheet_id,
            reference=values.get('reference'),
            credit_clock=values.get('credit_clock'),
            time_spent=values.get('time_spent')
        )
        _record_id = _record.fetch_record_id()
        self.records.update({_record_id: _record})
        return _record

    def display_time_sheet_records(self):
        print('Time Sheet {} Records:'.format(self.reference))
        for k, v in self.records.items():
            print('{}: {} - {}'.format(
                v.fetch_create_date(), k, v.fetch_reference())
                )
        return self.records


