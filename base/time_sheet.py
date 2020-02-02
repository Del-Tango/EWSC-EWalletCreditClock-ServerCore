import time
import random
import datetime
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class TimeSheetRecord(Base):
    __tablename__ = 'time_sheet_record'

    record_id = Column(
       Integer, primary_key=True, nullable=False, autoincrement=True
       )
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    time_spent = Column(Float)
    time_sheet_id = Column(
       Integer, ForeignKey('credit_clock_time_sheet.time_sheet_id')
       )

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_time_sheet_id(self):
        log.debug('')
        return self.time_sheet_id

    def fetch_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_reference(self):
        log.debug('')
        return self.reference

    def fetch_time_spent(self):
        log.debug('')
        return self.time_spent

    def fetch_record_data(self):
        log.debug('')
        _values = {
                'record_id': self.record_id,
                'time_sheet_id': self.time_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'time_spent': self.time_spent,
                }
        return _values

    def set_time_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_sheet_id'):
            return self.error_no_time_sheet_id_found()
        self.time_sheet_id = kwargs['time_sheet_id']
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_write_date_found()
        self.write_date = kwargs['write_date']
        return True

    def set_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_spent'):
            return self.error_no_time_spent_found()
        self.time_spent = kwargs['time_spent']
        return True

    def update_write_date(self):
        log.debug('')
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)

    def error_no_time_sheet_id_found(self):
        log.error('No time sheet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_write_date_found(self):
        log.error('No write date found.')
        return False

    def error_no_time_spent_found(self):
        log.error('No time spent found.')
        return False


class CreditClockTimeSheet(Base):
    __tablename__ = 'credit_clock_time_sheet'

    time_sheet_id = Column(Integer, primary_key=True)
    clock_id = Column(Integer, ForeignKey('credit_clock.clock_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    # O2O
    clock = relationship('CreditClock', back_populates='time_sheet')
    # O2M
    records = relationship('TimeSheetRecord')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_time_sheet_id(self):
        log.debug('')
        return self.time_sheet_id

    def fetch_time_sheet_clock_id(self):
        log.debug('')
        return self.clock_id

    def fetch_time_sheet_reference(self):
        log.debug('')
        return self.reference

    def fetch_time_sheet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_time_sheet_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_time_sheet_records(self):
        log.debug('')
        return self.records

    def fetch_time_sheet_values(self):
        log.debug('')
        _values = {
                'time_sheet_id': self.time_sheet_id,
                'clock_id': self.clock_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def fetch_time_record_creation_values(self, **kwargs):
        log.debug('')
        _values = {
                'record_id': kwargs.get('record_id'),
                'time_sheet_id': self.time_sheet_id,
                'reference': kwargs.get('reference'),
                'credit_clock': kwargs.get('credit_clock'),
                'time_spent': kwargs.get('time_spent'),
                }
        return _values

    # TODO
    def fetch_time_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_id_found()
        _record = self.records.get(kwargs['code'])
        if not _record:
            return self.warning_could_not_fetch_time_record(
                    'id', kwargs['code']
                    )
        log.info('Successfully fetched time record by id.')
        return _record

    # TODO - Refactor for multiple records
    def fetch_time_sheet_record_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_reference_found()
        for item in self.records:
            if self.records[item].fetch_record_reference() == kwargs['code']:
                log.info('Successfully fetched time record by reference.')
                return self.records[item]
        return self.warning_could_not_fetch_time_record(
                'reference', kwargs['code']
                )

    # TODO - Refactor for multiple records
    def fetch_time_sheet_record_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_date_found()
        for item in self.records:
            if self.records[item].fetch_record_create_date() == kwargs['code']:
                log.info('Successfully fetched time record by date.')
                return self.records[item]
        return self.warning_could_not_fetch_time_record(
                'date', kwargs['code']
                )

    # TODO - Refactor for multiple records
    def fetch_time_sheet_record_by_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_time_found()
        for item in self.records:
            if self.record[item].fetch_record_time_spent() == kwargs['code']:
                log.info('Successfully fetched time record by time.')
                return self.records[item]
        return self.warning_could_not_fetch_time_record(
                'time', kwargs['code']
                )

    def fetch_time_sheet_records(self, **kwargs):
        log.debug('')
        return self.records.values()

    def fetch_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_time_record_identifier_specified()
        _handlers = {
                'id': self.fetch_time_sheet_record_by_id,
                'reference': self.fetch_time_sheet_record_by_ref,
                'date': self.fetch_time_sheet_record_by_date,
                'time': self.fetch_time_sheet_record_by_time,
                'all': self.fetch_time_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def set_time_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_time_sheet_id_found()
        self.time_sheet_id = kwargs['sheet_id']
        return True

    def set_time_sheet_clock_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_time_sheet_clock_id_found()
        self.clock_id = kwargs['clock_id']
        return True

    def set_time_sheet_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_time_sheet_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_time_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_time_sheet_records_found()
        self.records = kwargs['records']
        return True

    def update_time_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('record'):
            return self.error_no_time_sheet_records_found()
        self.records.update({
            kwargs['record'].fetch_record_id(), kwargs['record']
            })
        log.info('Successfully update time sheet records.')
        return self.records

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    # TODO - Refactor
    def display_time_sheet_records(self):
        log.debug('')
        print('Time Sheet {} Records:'.format(self.reference))
        for k, v in self.records.items():
            print('{}: {} - {}'.format(
                v.fetch_create_date(), k, v.fetch_reference())
                )
        return self.records

    def action_add_time_sheet_record(self, **kwargs):
        log.debug('')
        _values = self.fetch_time_record_creation_values(**kwargs)
        _record = TimeSheetRecord(**_values)
        self.update_time_sheet_records(record=_record)
        log.info('Successfully added new time record.')
        return _record

    def action_remove_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found()
        log.info('Attempting to fetch time record...')
        _record = self.fetch_time_sheet_record(
                identifier='id', code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_time_record(
                    'id', kwargs['record_id']
                    )
        _unlink = self.records.pop(kwargs['record_id'])
        if _unlink:
            log.info('Successfully removed time record by id.')
        return _unlink

    def action_interogate_time_sheet_records_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_id_found()
        return self.records.get(kwargs['code'])

    def action_interogate_time_sheet_records_by_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_reference_found()
        return self.fetch_time_sheet_record(
                identifier='reference', code=kwargs['code']
                )

    def search_time_sheet_record_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_date_found()
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
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_time_found()
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
        log.debug('')
        if not kwargs.get('date'):
            return self.error_no_time_record_date_found()
        _handlers = {
                'date': self.search_time_sheet_record_by_date,
                'before': self.search_time_sheet_record_before_date,
                'after': self.search_time_sheet_record_after_date,
                }
        return _handlers[kwargs['date']](**kwargs)

    def action_interogate_time_sheet_records_by_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_time_record_time_found()
        _handlers = {
                'time': self.search_time_sheet_record_by_time,
                'more': self.search_time_sheet_record_greater_time,
                'less': self.search_time_sheet_record_lesser_time,
                }
        return _handlers[kwargs['time']](**kwargs)

    def action_interogate_all_time_sheet_records(self, **kwargs):
        log.debug('')
        return self.fetch_time_sheet_records(identifier='all')

    def action_interogate_time_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_time_record_identifier_specified()
        _handlers = {
                'id': self.action_interogate_time_sheet_records_by_id,
                'reference': self.action_interogate_time_sheet_records_by_reference,
                'date': self.action_interogate_time_sheet_records_by_date,
                'time_spent': self.action_interogate_time_sheet_records_by_time_spent,
                'all': self.action_interogate_all_time_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def action_clear_time_sheet_records(self, **kwargs):
        log.debug('')
        _clear = self.set_time_sheet_records(records={})
        log.info('Successfully cleared all time sheet records.')
        return _clear

    def credit_clock_time_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_time_sheet_controller_action_specified()
        _handlers = {
                'add': self.action_add_time_sheet_record,
                'remove': self.action_remove_time_sheet_record,
                'interogate': self.action_interogate_time_sheet_records,
                'clear': self.action_clear_time_sheet_records,
                }
        return _handlers[kwargs['action']](**kwargs)

    def error_no_time_sheet_controller_action_specified(self):
        log.error('No time sheet controller action specified.')
        return False

    def error_no_time_record_identifier_specified(self):
        log.error('No time record identifier specified.')
        return False

    def error_no_time_sheet_id_found(self):
        log.error('No time sheet id found.')
        return False

    def error_no_time_sheet_clock_id_found(self):
        log.error('No time sheet clock id found.')
        return False

    def error_no_time_sheet_reference_found(self):
        log.error('No time sheet reference found.')
        return False

    def error_no_time_sheet_records_found(self):
        log.error('No time sheet records found.')
        return False

    def error_no_time_record_date_found(self):
        log.error('No time record date found.')
        return False

    def error_no_time_record_time_found(self):
        log.error('No time record time found.')
        return False

    def error_no_time_record_id_found(self):
        log.error('No time record id found.')
        return False

    def error_no_time_record_reference_found(self):
        log.error('No time record reference found.')
        return False

    def warning_could_not_fetch_time_record(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch time record by %s %s.', search_code, code
                )
        return False

###############################################################################
# CODE DUMP
###############################################################################

#   # M2O
#   time_sheet = relationship('CreditClockTimeSheet')
