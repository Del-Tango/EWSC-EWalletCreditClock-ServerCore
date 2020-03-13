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


class CreditClockConversionSheetRecord(Base):
    __tablename__ = 'conversion_sheet_record'

    record_id = Column(Integer, primary_key=True)
    conversion_sheet_id = Column(
       Integer, ForeignKey('credit_clock_conversion_sheet.conversion_sheet_id')
       )
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    conversion_type = Column(String)
    minutes = Column(Float)
    credits = Column(Integer)

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.conversion_sheet_id = kwargs.get('conversion_sheet_id')
        self.reference = kwargs.get('reference') or 'Conversion Sheet Record'
        self.conversion_type = kwargs.get('conversion_type')
        self.minutes = kwargs.get('minutes')
        self.credits = kwargs.get('credits')

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_conversion_sheet_id(self):
        log.debug('')
        return self.conversion_sheet_id

    def fetch_reference(self):
        log.debug('')
        return self.reference

    def fetch_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_conversion_type(self):
        log.debug('')
        return self.conversion_type

    def fetch_minutes(self):
        log.debug('')
        return self.minutes

    def fetch_credits(self):
        log.debug('')
        return self.credits

    def fetch_record_data(self):
        log.debug('')
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
        log.debug('')
        if not kwargs.get('conversion_sheet_id'):
            return self.error_no_conversion_sheet_id_found()
        self.conversion_sheet_id = kwargs['conversion_sheet_id']
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

    def set_conversion_type(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_type'):
            return self.error_no_conversion_type_found()
        self.conversion_type = kwargs['conversion_type']
        return True

    def set_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        self.minutes = kwargs['minutes']
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits = kwargs['credits']
        return True

    def update_write_date(self):
        log.debug('')
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_conversion_sheet_id_found(self):
        log.error('No conversion sheet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_write_date_found(self):
        log.error('No write date found.')
        return False

    def error_no_conversion_type_found(self):
        log.error('No conversion type found.')
        return False

    def error_no_minutes_found(self):
        log.error('No minutes found.')
        return False


class CreditClockConversionSheet(Base):
    __tablename__ = 'credit_clock_conversion_sheet'

    conversion_sheet_id = Column(Integer, primary_key=True)
    clock_id = Column(Integer, ForeignKey('credit_clock.clock_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    # O2O
    clock = relationship('CreditClock', back_populates='conversion_sheet')
    # O2M
    records = relationship('CreditClockConversionSheetRecord')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.clock_id = kwargs.get('clock_id')
        self.reference = kwargs.get('reference') or 'Conversion Sheet'
        self.records = kwargs.get('records') or []

    def fetch_conversion_sheet_id(self):
        log.debug('')
        return self.conversion_sheet_id

    def fetch_conversion_sheet_clock_id(self):
        log.debug('')
        return self.clock_id

    def fetch_conversion_sheet_reference(self):
        log.debug('')
        return self.reference

    def fetch_conversion_sheet_records(self):
        log.debug('')
        return self.records

    def fetch_conversion_sheet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_conversion_sheet_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_conversion_sheet_values(self):
        log.debug('')
        _values = {
                'id': self.conversion_sheet_id,
                'clock_id': self.clock_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    def fetch_conversion_record_creation_values(self, **kwargs):
        log.debug('')
        _values = {
                'conversion_sheet_id': self.conversion_sheet_id,
                'reference': kwargs.get('reference'),
                'conversion_type': kwargs.get('conversion_type'),
                'minutes': kwargs.get('minutes'),
                'credits': kwargs.get('credits'),
                }
        return _values

    def fetch_conversion_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_id_found()
        if kwargs.get('active_session'):
            _match = list(kwargs['active_session'].query(
                CreditClockConversionSheetRecord
                ).filter_by(record_id=kwargs['code']))
        else:
            _match = [
                    item for item in self.records
                    if item.fetch_record_id() is kwargs['code']
                    ]
        _record = False if not _match else _match[0]
        if not _record:
            return self.warning_could_not_fetch_conversion_record(
                    'id', kwargs['code']
                    )
        log.info('Successfully fetched conversion record by id.')
        return _record

    def fetch_conversion_sheet_record_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_reference_found()
        for item in self.records:
            if self.records[item].fetch_record_reference() == kwargs['code']:
                log.info('Successfully fetched conversion records by reference.')
                return self.records[item]
        return self.warning_could_not_fetch_conversion_record(
                'reference', kwargs['code']
                )

    def fetch_conversion_sheet_records_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_date_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_create_date() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_conversion_record(
                    'date', kwargs['code']
                    )
        log.info('Successfully fetched conversion records by date.')
        return _records

    def fetch_conversion_sheet_records_by_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_credits_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_credits() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_conversion_records(
                    'credits'. kwargs['code']
                    )
        log.info('Successfully fetched conversion records by credits.')
        return _records

    def fetch_conversion_sheet_records_by_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_minutes_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_minutes() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_conversion_records(
                    'minutes', kwargs['code']
                    )
        log.info('Successfully fetched conversion records by minutes.')
        return _records

    def fetch_conversion_sheet_records_by_type(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_type_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_conversion_type() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_conversion_records(
                    'type', kwargs['code']
                    )
        log.info('Successfully fetched conversion records by type.')
        return _records

    def fetch_conversion_sheet_records(self, **kwargs):
        log.debug('')
        return self.records.values()

    def fetch_conversion_sheet_record(self, **kwargs):
        log.debug('')
        if not self.records or not kwargs.get('search_by'):
            return self.error_no_conversion_sheet_record_identifier_specified()
        _handlers = {
                'id': self.fetch_conversion_sheet_record_by_id,
                'reference': self.fetch_conversion_sheet_record_by_ref,
                'date': self.fetch_conversion_sheet_records_by_date,
                'credits': self.fetch_conversion_sheet_records_by_credits,
                'minutes': self.fetch_conversion_sheet_records_by_minutes,
                'conversion_type': self.fetch_conversion_sheet_records_by_type,
                'all': self.fetch_conversion_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def set_clock_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_clock_id_found()
        self.clock_id = kwargs['clock_id']
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

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found()
        self.records = kwargs['records']
        return True

    def update_write_date(self):
        log.debug('')
        _write_date = datetime.datetime.now()
        return self.set_write_date(write_date=_write_date)

    def update_conversion_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('record'):
            return self.error_no_conversion_record_found()
        self.records.append(kwargs['record'])
        log.info('Successfully updated conversion sheet records.')
        return self.records

    def add_conversion_sheet_record(self, **kwargs):
        log.debug('')
        _values = self.fetch_conversion_record_creation_values(**kwargs)
        _record = CreditClockConversionSheetRecord(**_values)
        self.update_conversion_sheet_records(record=_record)
        log.info('Successfully added conversion record to sheet.')
        return _record

    # TODO - Refactor
    def display_conversion_sheet_records(self):
        log.debug('')
        print('Conversion Sheet {} Records:'.format(self.reference))
        for k, v in self.records.items():
            print('{}: {} - {}'.format(
                v.fetch_create_date(), k, v.fetch_reference())
                )
        return self.records

    def action_add_conversion_sheet_record(self, **kwargs):
        log.debug('')
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
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_record_id_found()
        _record = self.fetch_conversion_sheet_record(
                identifier='id', code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_conversion_record(
                    'id', kwargs['record_id']
                    )
        log.info('Successfully removed conversion record.')
        return self.records.pop(kwargs['record_id'])

    def interogate_conversion_sheet_records_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_id_found()
        _record = self.fetch_conversion_sheet_record(
                identifier='id', code=kwargs['code'],
                )
        if not _record:
            return self.warning_could_not_fetch_conversion_record(
                    'id', kwargs['code']
                    )
        return _record or False

    def interogate_conversion_sheet_records_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_reference_found()
        _records = self.fetch_conversion_sheet_record(
                identifier='reference', code=kwargs['code']
                )
        if not _record:
            return self.warning_could_not_fetch_conversion_record(
                    'reference', kwargs['code']
                    )
        return _records

    def search_conversion_sheet_records_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_date_found()
        _records = self.fetch_conversion_sheet_record(
                identifier='date', code=kwargs['code']
                )
        if not _records:
            return self.warning_could_not_fetch_conversion_record(
                    'date', kwargs['code']
                    )
        return _records or False

    # TODO
    def search_conversion_sheet_records_before_date(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_after_date(self, **kwargs):
        pass

    def search_conversion_sheet_records_by_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_minutes_found()
        _records = self.fetch_conversion_sheet_record(
                identifier='minutes', code=kwargs['code']
                )
        if not _records:
            return self.warning_could_not_fetch_conversion_record(
                    'minutes', kwargs['code']
                    )
        return _records

    # TODO
    def search_conversion_sheet_records_lesser_minutes(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_greater_minutes(self, **kwargs):
        pass

    def search_conversion_sheet_records_by_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_credits_found()
        _records = self.fetch_conversion_sheet_record(
                identifier='credits', code=kwargs['code']
                )
        if not _records:
            return self.warning_could_not_fetch_conversion_record(
                    'credits', kwargs['code']
                    )
        return _records
    # TODO
    def search_conversion_sheet_records_lesser_credits(self, **kwargs):
        pass

    # TODO
    def search_conversion_sheet_records_greater_credits(self, **kwargs):
        pass

    def interogate_conversion_sheet_records_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('date'):
            return self.error_no_conversion_record_date_found()
        _handlers = {
                'date': self.search_conversion_sheet_records_by_date,
                'before': self.search_conversion_sheet_records_before_date,
                'after': self.search_conversion_sheet_records_after_date,
                }
        return _handlers[kwargs['date']](**kwargs)

    def interogate_conversion_sheet_records_by_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_conversion_record_minutes_found()
        _handlers = {
                'minutes': self.search_conversion_sheet_records_by_minutes,
                'less': self.search_conversion_sheet_records_lesser_minutes,
                'more': self.search_conversion_sheet_records_greater_minutes,
                }
        return _handlers[kwargs['minutes']](**kwargs)

    def interogate_conversion_sheet_records_by_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_conversion_record_credits_found()
        _handlers = {
                'credits': self.search_conversion_sheet_records_by_credits,
                'less': self.search_conversion_sheet_records_lesser_credits,
                'more': self.search_conversion_sheet_records_greater_credits,
                }
        return _handlers[kwargs['credits']](**kwargs)

    def interogate_conversion_sheet_records_by_type(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_type'):
            return self.error_no_conversion_record_conversion_type_found()
        _records = self.fetch_conversion_sheet_records(
                identifier='conversion_type', code=kwargs['conversion_type']
                )
        if not _records:
            return self.warning_could_not_fetch_conversion_record(
                    'conversion_type', kwargs['code']
                    )
        return _records or False

    def action_interogate_conversion_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_conversion_reecords_interogation_target_specified()
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
        log.debug('')
        return self.set_conversion_sheet_records(records={})

    def credit_clock_conversion_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_conversion_sheet_controller_action_specified()
        _handlers = {
                'add': self.action_add_conversion_sheet_record,
                'remove': self.action_remove_conversion_sheet_record,
                'interogate': self.action_interogate_conversion_sheet_records,
                'clear': self.action_clear_conversion_sheet_records,
                }
        return _handlers[kwargs['action']](**kwargs)

    def error_no_conversion_record_conversion_type_found(self):
        log.error('No conversion record conversion type found.')
        return False

    def error_no_conversion_records_interogation_target_specified(self):
        log.error('No conversion records interogation target specified.')
        return False

    def error_no_conversion_sheet_controller_action_specified(self):
        log.error('No conversion sheet controller action specified.')
        return False

    def interogate_conversion_sheet_records(self, **kwargs):
        return self.fetch_conversion_sheet_record(identifier='all')

    def error_no_records_found(self):
        log.error('No records found.')
        return False

    def error_no_conversion_record_found(self):
        log.error('No conversion record found.')
        return False

    def error_no_clock_id_found(self):
        log.error('No clock id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_write_date_found(self):
        log.error('No write date found.')
        return False

    def error_no_conversion_record_type_found(self):
        log.error('No conversion record type found.')
        return False

    def error_no_conversion_sheet_record_identifier_specified(self):
        log.error('No conversion sheet record identified specified.')
        return False

    def error_no_conversion_record_credits_found(self):
        log.error('No conversion record credits found.')
        return False

    def error_no_conversion_record_minutes_found(self):
        log.error('No conversion record minutes found.')
        return False

    def error_no_conversion_record_id_found(self):
        log.error('No conversion record id found.')
        return False

    def error_no_conversion_record_reference_found(self):
        log.error('No conversion record reference found.')
        return False

    def error_no_conversion_record_date_found(self):
        log.error('No conversion record date found.')
        return False

    def warning_could_not_fetch_conversion_record(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch conversion record by %s %s.', search_code, code
                )
        return False

###############################################################################
# CODE DUMP
###############################################################################

    # M2O
#   conversion_sheet = relationship('CreditClockConversionSheet')
