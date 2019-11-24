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

    def fetch_conversion_sheet_id(self):
        return self.conversion_sheet_id

    def fetch_reference(self):
        return self.reference

    def fetch_create_date(self):
        return self.create_date

    def fetch_write_date(self):
        return self.write_date

    def fetch_conversion_type(self):
        return self.conversion_type

    def fetch_minutes(self):
        return self.minutes

    def fetch_credits(self):
        return self.credits

    def fetch_record_data(self):
        _values = {
                'id': self.record_id,
                'conversion_sheet_id': self.conversion_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'conversion_type': self.conversion_type,
                'minutes': self.minutes,
                'credits': self.credits,
                }
        return _values

    def set_conversion_sheet_id(self, **kwargs):
        global conversion_sheet_id
        if not kwargs.get('conversion_sheet_id'):
            return False
        self.conversion_sheet_id = kwargs['conversion_sheet_id']
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

    def set_conversion_type(self, **kwargs):
        global conversion_type
        if not kwargs.get('conversion_type'):
            return False
        self.conversion_type = kwargs['conversion_type']
        return True

    def set_minutes(self, **kwargs):
        global minutes
        if not kwargs.get('minutes'):
            return False
        self.minutes = kwargs['minutes']
        return True

    def set_credits(self, **kwargs):
        global credits
        if not kwargs.get('credits'):
            return False
        self.credits = kwargs['credits']
        return True

    def update_write_date(self):
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)


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

    def fetch_conversion_sheet_clock_id(self):
        return self.clock_id

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

    def fetch_conversion_sheet_record_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.records.get(kwargs['code'])

    def fetch_conversion_sheet_record_by_ref(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.records:
            if self.records[item].fetch_record_reference() == kwargs['code']:
                return self.records[item]
        return False

    def fetch_conversion_sheet_records_by_date(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_create_date() == kwargs['code']
                ]
        return _records or False

    def fetch_conversion_sheet_records_by_credits(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_credits() == kwargs['code']
                ]
        return _records or False

    def fetch_conversion_sheet_records_by_minutes(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_minutes() == kwargs['code']
                ]
        return _records or False

    def fetch_conversion_sheet_records_by_type(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_conversion_type() == kwargs['code']
                ]
        return _records or False

    def fetch_conversion_sheet_records(self, **kwargs):
        return self.records.values()

    def fetch_conversion_sheet_record(self, **kwargs):
        if not self.records or not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_conversion_sheet_record_by_id,
                'reference': self.fetch_conversion_sheet_record_by_ref,
                'date': self.fetch_conversion_sheet_records_by_date,
                'credits': self.fetch_conversion_sheet_records_by_credits,
                'minutes': self.fetch_conversion_sheet_records_by_minutes,
                'conversion_type': self.fetch_conversion_sheet_records_by_type,
                'all': self.fetch_conversion_sheet_records,
                }
        return _handlers[kwargs['identifier']](**kwargs)

    def set_clock_id(self, **kwargs):
        global clock_id
        if not kwargs.get('clock_id'):
            return False
        self.clock_id = kwargs['clock_id']
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

    def set_records(self, **kwargs):
        global records
        if not kwargs.get('records'):
            return False
        self.records = kwargs['records']
        return True

    def update_write_date(self):
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)

    def update_conversion_sheet_records(self, **kwargs):
        global records
        if not kwargs.get('record'):
            return False
        self.records.update({
            kwargs['record'].fetch_record_id(), kwargs['record']
            })
        return self.records

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

    def action_add_conversion_sheet_record(self, **kwargs):
        _record = CreditClockConversionSheetRecord(
                conversion_sheet_id=self.conversion_sheet_id,
                reference=kwargs.get('reference'),
                conversion_type=kwargs.get('conversion_type'),
                minutes=kwargs.get('minutes'),
                credits=kwargs.get('credits'),
                )
        self.update_conversion_sheet_records(record=_record)
        return _record

    def action_remove_conversion_sheet_record(self, **kwargs):
        global records
        if not kwargs.get('record_id'):
            return False
        _record = self.fetch_conversion_sheet_record(
                identifier='id', code=kwargs['record_id']
                )
        return False if not _record \
                else self.records.pop(kwargs['record_id'])

    def interogate_conversion_sheet_records_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _record = self.fetch_conversion_sheet_record(
                identifier='id', code=kwargs['code'],
                )
        return _record or False

    def interogate_conversion_sheet_records_by_ref(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = self.fetch_conversion_sheet_record(
                identifier='reference', code=kwargs['code']
                )
        return _records or False

    def search_conversion_sheet_records_by_date(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = self.fetch_conversion_sheet_record(
                identifier='date', code=kwargs['code']
                )
        return _records or False

    # TODO
    def search_conversion_sheet_records_before_date(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_after_date(self, **kwargs):
        pass


    def search_conversion_sheet_records_by_minutes(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = self.fetch_conversion_sheet_record(
                identifier='minutes', code=kwargs['code']
                )
        return _records or False

    # TODO
    def search_conversion_sheet_records_lesser_minutes(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_greater_minutes(self, **kwargs):
        pass

    def search_conversion_sheet_records_by_credits(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = self.fetch_conversion_sheet_record(
                identifier='credits', code=kwargs['code']
                )
        return _records or False

    # TODO
    def search_conversion_sheet_records_lesser_credits(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_greater_credits(self, **kwargs):
        pass

    def interogate_conversion_sheet_records_by_date(self, **kwargs):
        if not kwargs.get('date'):
            return False
        _handlers = {
                'date': self.search_conversion_sheet_records_by_date,
                'before': self.search_conversion_sheet_records_before_date,
                'after': self.search_conversion_sheet_records_after_date,
                }
        return _handlers[kwargs['date']](**kwargs)

    def interogate_conversion_sheet_records_by_minutes(self, **kwargs):
        if not kwargs.get('minutes'):
            return False
        _handlers = {
                'minutes': self.search_conversion_sheet_records_by_minutes,
                'less': self.search_conversion_sheet_records_lesser_minutes,
                'more': self.search_conversion_sheet_records_greater_minutes,
                }
        return _handlers[kwargs['minutes']](**kwargs)

    def interogate_conversion_sheet_records_by_credits(self, **kwargs):
        if not kwargs.get('credits'):
            return False
        _handlers = {
                'credits': self.search_conversion_sheet_records_by_credits,
                'less': self.search_conversion_sheet_records_lesser_credits,
                'more': self.search_conversion_sheet_records_greater_credits,
                }
        return _handlers[kwargs['credits']](**kwargs)

    def interogate_conversion_sheet_records_by_type(self, **kwargs):
        if not kwargs.get('conversion_type'):
            return False
        _records = self.fetch_conversion_sheet_records(
                identifier='conversion_type', code=kwargs['conversion_type']
                )
        return _records or False

    def interogate_conversion_sheet_records(self, **kwargs):
        return self.fetch_conversion_sheet_record(identifier='all')

    def action_interogate_conversion_sheet_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _handlers = {
                'id': self.interogate_conversion_sheet_records_by_id,
                'reference': self.interogate_conversion_sheet_records_by_ref,
                'date': self.interogate_conversion_sheet_records_by_date,
                'minutes': self.interogate_conversion_sheet_records_by_minutes,
                'credits': self.interogate_conversion_sheet_records_by_credits,
                'conversion_type': self.interogate_conversion_sheet_records_by_type,
                'all': self.interogate_conversion_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def action_clear_conversion_sheet_records(self, **kwargs):
        return self.set_conversion_sheet_records(records={})

    def credit_clock_conversion_sheet_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'add': self.action_add_conversion_sheet_record,
                'remove': self.action_remove_conversion_sheet_record,
                'interogate': self.action_interogate_conversion_sheet_records,
                'clear': self.action_clear_conversion_sheet_records,
                }
        return _handlers[kwargs['action']](**kwargs)

