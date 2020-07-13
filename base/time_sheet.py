import time
import random
import datetime
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime, update
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class TimeSheetRecord(Base):
    __tablename__ = 'time_sheet_record'

    record_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    create_uid = Column(Integer, ForeignKey('res_user.user_id'))
    write_uid = Column(Integer, ForeignKey('res_user.user_id'))
    time_start = Column(Float)
    time_stop = Column(Float)
    time_spent = Column(Float)
    time_pending = Column(Float)
    pending_count = Column(Integer)
    time_sheet_id = Column(
        Integer, ForeignKey('credit_clock_time_sheet.time_sheet_id')
    )
    credit_clock_id = Column(
        Integer, ForeignKey('credit_clock.clock_id')
    )

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.create_uid = kwargs.get('create_uid')
        self.write_uid = kwargs.get('write_uid')
        self.reference = kwargs.get('reference') or \
            config.time_sheet_config['time_record_reference']
        self.time_start = kwargs.get('time_start')
        self.time_stop = kwargs.get('time_stop')
        self.time_spent = kwargs.get('time_spent') or 0.00
        self.time_pending = kwargs.get('time_pending') or 0.00
        self.pending_count = kwargs.get('pending_count') or 0
        self.time_sheet_id = kwargs.get('time_sheet_id')
        self.credit_clock_id = kwargs.get('credit_clock_id')

    # FETCHERS

    def fetch_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_time_record_identifier_specified()
        handlers = {
            'id': self.fetch_time_sheet_record_by_id,
            'reference': self.fetch_time_sheet_record_by_ref,
            'date': self.fetch_time_sheet_record_by_date,
            'time': self.fetch_time_sheet_record_by_time,
            'all': self.fetch_time_sheet_records,
        }
        return handlers[kwargs['identifier']](**kwargs)

    def fetch_create_uid(self):
        log.debug('')
        return self.create_uid

    def fetch_write_uid(self):
        log.debug('')
        return self.write_uid

    def fetch_time_pending(self):
        log.debug('')
        return self.time_pending

    def fetch_pending_count(self):
        log.debug('')
        return self.pending_count

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_time_sheet_id(self):
        log.debug('')
        return self.time_sheet_id

    def fetch_credit_clock_id(self):
        return self.credit_clock_id

    def fetch_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_record_reference(self):
        log.debug('')
        return self.reference

    def fetch_time_start(self):
        log.debug('')
        return self.time_start

    def fetch_time_stop(self):
        log.debug('')
        return self.time_stop

    def fetch_time_spent(self):
        log.debug('')
        return self.time_spent

    def fetch_record_values(self):
        log.debug('')
        values = {
            'id': self.record_id,
            'time_sheet': self.time_sheet_id,
            'reference': self.reference or \
                config.time_sheet_config['time_record_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'time_start': res_utils.format_timestamp(self.time_start),
            'time_stop': res_utils.format_timestamp(self.time_stop),
            'time_spent': self.time_spent,
            'time_pending': self.time_pending,
            'pending_count': self.pending_count,
        }
        return values

    # SETTERS

    def set_create_uid(self, **kwargs):
        log.debug('')
        if not kwargs.get('create_uid'):
            return self.error_no_create_uid_found()
        self.create_uid = kwargs['create_uid']
        return True

    def set_write_uid(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_uid'):
            return self.error_no_write_uid_found()
        self.write_uid = kwargs['write_uid']
        return True

    def set_time_pending(self, **kwargs):
        log.debug('')
        if kwargs.get('time_pending') is None:
            return self.error_no_pending_time_found()
        self.time_pending = kwargs['time_pending']
        return True

    def set_pending_count(self, **kwargs):
        log.debug('')
        if kwargs.get('pending_count') is None:
            return self.error_no_pending_count_found()
        self.pending_count = kwargs['pending_count']
        return True

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

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_start'):
            return self.error_no_start_time_found()
        self.time_start = kwargs['time_start']
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_stop(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_stop'):
            return self.error_no_stop_time_found()
        self.time_stop = kwargs['time_stop']
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_spent'):
            return self.error_no_spent_time_found()
        self.time_spent = kwargs['time_spent']
        return True

    def set_write_uid(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_uid'):
            return self.error_no_write_uid_found()
        try:
            self.write_uid = kwargs['write_uid']
        except:
            return self.error_could_not_set_write_uid()
        return True

    # UPDATES

#   @pysnooper.snoop('logs/ewallet.log')
    def update_record_values(self, values, **kwargs):
        log.debug('')
        _set = {
            'time_start': self.set_time_start,
            'time_stop': self.set_time_stop,
            'time_spent': self.set_time_spent,
            'time_pending': self.set_time_pending,
            'pending_count': self.set_pending_count,
            'write_uid': self.set_write_uid,
        }
        for field_name, field_value in values.items():
            try:
                 _set[field_name](
                    active_session=kwargs['active_session'],
                    **{field_name: field_value}
                )
            except KeyError:
                log.warning(
                    'Invalid field name for action update time sheet record values.'
                )
        self.update_write_date()
        return True

    def update_write_date(self, **kwargs):
        log.debug('')
        write_date = datetime.datetime.now()
        return self.set_write_date(write_date=write_date, **kwargs)

    # WARNINGS

    def warning_could_not_fetch_time_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch credit clock time sheet record. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS

    def error_no_time_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No time record id found. Command chain details : {}'\
                        .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_write_uid(self):
        log.error('Could not set write uid.')
        return False

    def error_no_create_uid_found(self):
        log.error('No create user id found.')
        return False

    def error_no_write_uid_found(self):
        log.error('No write user id found.')
        return False

    def error_no_pending_time_found(self):
        log.error('No pending time found.')
        return False

    def error_no_pending_count_found(self):
        log.error('No pending count found.')
        return False

    def error_no_start_time_found(self):
        log.error('No start time found.')
        return False

    def error_no_stop_time_found(self):
        log.error('No stop time found.')
        return False

    def error_no_spent_time_found(self):
        log.error('No spent time found.')
        return False

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
        self.clock_id = kwargs.get('clock_id')
        self.reference = kwargs.get('reference') or 'Time Sheet'
        self.records = kwargs.get('records') or []

    # FETCHERS

    def fetch_time_record_creation_values(self, **kwargs):
        log.debug('')
        values = {
            'record_id': kwargs.get('record_id'),
            'create_uid': kwargs.get('create_uid'),
            'write_uid': kwargs.get('write_uid'),
            'time_sheet_id': self.time_sheet_id,
            'reference': kwargs.get('reference'),
            'credit_clock': kwargs.get('credit_clock'),
            'time_start': kwargs.get('time_start'),
            'time_stop': kwargs.get('time_stop'),
            'time_spent': kwargs.get('time_spent'),
        }

        # TODO - REMOVE
        log.info('TIME RECORD CREATION VALUES : {}'.format(values))

        return values

    def fetch_time_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found(kwargs)
        record = list(
            kwargs['active_session'].query(
                TimeSheetRecord
            ).filter_by(record_id=kwargs['record_id'])
        )
        if record:
            log.info('Successfully fetched time record by id.')
        return self.warning_could_not_fetch_time_record(kwargs) if not \
            record else record[0]

    def fetch_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_time_sheet_record_identifier_specified(kwargs)
        fetchers = {
            'id': self.fetch_time_sheet_record_by_id,
        }
        return fetchers[kwargs['identifier']](**kwargs)

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
        values = {
            'id': self.time_sheet_id,
            'clock': self.clock_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'records': {
                record.fetch_record_id(): record.fetch_record_reference()
                for record in self.records
            },
        }
        return values

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

    # SETTERS

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

    def set_write_date(self, **kwargs):
        log.debug('')
        _now = kwargs.get('write_date') or datetime.datetime.now()
        self.write_date = _now
        return True

    # UPDATES

    def update_time_sheet_records(self, record):
        log.debug('')
        self.records.append(record)
        log.info('Successfully update time sheet records.')
        return self.records

    def update_write_date(self):
        log.debug('')
        return self.set_write_date(write_date=datetime.datetime.now())

    # ACTIONS

#   @pysnooper.snoop('logs/ewallet.log')
    def action_add_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        values = self.fetch_time_record_creation_values(**kwargs)
        record = TimeSheetRecord(**values)
        updated_records = self.update_time_sheet_records(record)
        if record:
            log.info('Successfully added new time record.')
        return record or False

    def action_remove_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found()
        try:
            kwargs['active_session'].query(
                TimeSheetRecord
            ).filter_by(record_id=kwargs['record_id']).delete()
        except:
            return self.error_could_not_remove_time_sheet_record(kwargs)
        return True

    def action_interogate_all_time_sheet_records(self, **kwargs):
        log.debug('')
        return self.fetch_time_sheet_records(identifier='all')

    def action_clear_time_sheet_records(self, **kwargs):
        log.debug('')
        _clear = self.set_time_sheet_records(records={})
        log.info('Successfully cleared all time sheet records.')
        return _clear

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

    # GENERIC

    def search_time_sheet_record_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_date_found()
        return self.fetch_time_sheet_record(
                identifier='date', code=kwargs['code']
                )

    def search_time_sheet_record_by_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_time_record_time_found()
        return self.fetch_time_sheet_record(
                identifier='time', code=kwargs['code']
                )

    # TODO
    def search_time_sheet_record_before_date(self, **kwargs):
        pass
    def search_time_sheet_record_after_date(self, **kwargs):
        pass
    def search_time_sheet_record_greater_time(self, **kwargs):
        pass
    def search_time_sheet_record_lesser_time(self, **kwargs):
        pass

    # CONTROLLERS

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

    # WARNINGS

    def warning_could_not_fetch_time_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch credit clock time sheet record. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS

    def error_could_not_remove_time_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not remove time sheet record. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_record_identifier_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record identifier specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No time record id found. Command chain details : {}'\
                        .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

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

    def error_no_time_record_reference_found(self):
        log.error('No time record reference found.')
        return False


###############################################################################
# CODE DUMP
###############################################################################


