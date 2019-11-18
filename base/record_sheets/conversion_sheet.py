import time
import random
import datetime
import pysnooper


class CreditClockConversionSheetRecord():

    def __init__(self, **kwargs):
        self.record_id = random.randint(10, 20)
        self.conversion_sheet_id = kwargs.get('conversion_sheet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.conversion_type = kwargs.get('conversion_type')
        self.minutes = kwargs.get('minutes')
        self.credits = kwargs.get('credits')

    def fetch_record_id(self):
        return self.record_id

    def fetch_reference(self):
        return self.reference

    def fetch_create_date(self):
        return self.create_date

    def fetch_record_data(self):
        _values = {
                'id': self.record_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'conversion_type': self.conversion_type,
                'minutes': self.minutes,
                'credits': self.credits,
                }
        return _values

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date


class CreditClockConversionSheet():

    def __init__(self, **kwargs):
        self.conversion_sheet_id = random.randint(10,20)
        self.clock_id = kwargs.get('clock_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = {}

    def fetch_conversion_sheet_id(self):
        return self.conversion_sheet_id

    def fetch_conversion_sheet_reference(self):
        return self.reference

    def fetch_conversion_sheet_records(self):
        return self.records

    def fetch_conversion_sheet_create_date(self):
        return self.create_date

    def fetch_conversion_sheet_write_date(self):
        return self.write_date

    def fetch_conversion_sheet_values(self):
        _values = {
                'id': self.conversion_sheet_id,
                'clock_id': self.clock_id,
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

    # TODO - Has dummy data
    def add_conversion_sheet_record(self, values):
        global records
        _record = CreditClockConversionSheetRecord(
                    conversion_sheet_id=self.conversion_sheet_id,
                    reference='First Conversion Sheet Record',
                    conversion_type=values.get('conversion_type'),
                    minutes=values.get('minutes'),
                    credits=values.get('credits'),
                )
        _record_id = _record.fetch_record_id()
        self.records.update({_record_id: _record})
        return _record

    def display_conversion_sheet_records(self):
        print('Conversion Sheet {} Records:'.format(self.reference))
        for k, v in self.records.items():
            print('{}: {} - {}'.format(
                v.fetch_create_date(), k, v.fetch_reference())
                )
        return self.records



