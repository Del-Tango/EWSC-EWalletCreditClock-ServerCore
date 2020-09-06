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

#   @pysnooper.snoop('logs/ewallet.log')
    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.create_uid = kwargs.get('create_uid')
        self.write_uid = kwargs.get('write_uid')
        self.reference = kwargs.get('reference') or \
            config.time_sheet_config['time_record_reference']
        self.time_start = kwargs.get('time_start', float())
        self.time_stop = kwargs.get('time_stop', float())
        self.time_spent = kwargs.get('time_spent', float())
        self.time_pending = kwargs.get('time_pending', float())
        self.pending_count = kwargs.get('pending_count', int())
        self.time_sheet_id = kwargs.get('time_sheet_id')
        self.credit_clock_id = kwargs.get('credit_clock_id')

    # FETCHERS (RECORD)

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

    # SETTERS (RECORD)

    def set_credit_clock_id(self, clock_id):
        log.debug('')
        try:
            self.credit_clock_id = clock_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_clock_id(
                clock_id, self.credit_clock_id, e
            )
        log.info('Successfully set record credit clock id.')
        return True

    def set_create_uid(self, **kwargs):
        log.debug('')
        if not kwargs.get('create_uid'):
            return self.error_no_create_uid_found(kwargs)
        try:
            self.create_uid = kwargs['create_uid']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_record_create_uid(
                kwargs, self.create_uid, e
            )
        log.info('Successfully set time record write date.')
        return True

    def set_write_uid(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_uid'):
            return self.error_no_write_uid_found(kwargs)
        try:
            self.write_uid = kwargs['write_uid']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_record_write_uid(
                kwargs, self.write_uid, e
            )
        log.info('Successfully set time record write UID.')
        return True

    def set_time_pending(self, **kwargs):
        log.debug('')
        if kwargs.get('time_pending') is None:
            return self.error_no_pending_time_found(kwargs)
        try:
            self.time_pending = kwargs['time_pending']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_pending(
                kwargs, self.time_pending, e
            )
        log.info('Successfully set record pending time.')
        return True

    def set_pending_count(self, **kwargs):
        log.debug('')
        if kwargs.get('pending_count') is None:
            return self.error_no_pending_count_found(kwargs)
        try:
            self.pending_count = kwargs['pending_count']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_pending_count(
                kwargs, self.pending_count, e
            )
        log.info('Successfully set record pending count.')
        return True

    def set_time_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_sheet_id'):
            return self.error_no_time_sheet_id_found(kwargs)
        try:
            self.time_sheet_id = kwargs['time_sheet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_sheet_id(
                kwargs, self.time_sheet_id, e
            )
        log.info('Succesdfully set record time sheet id.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_record_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set time record reference.')
        return True

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_write_date_found(kwargs)
        try:
            self.write_date = kwargs['write_date']
        except Exception as e:
            return self.error_could_not_set_time_record_write_date(
                kwargs, self.write_date, e
            )
        log.info('Successfully set time record write date.')
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_start(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_start'):
            return self.error_no_start_time_found(kwargs)
        try:
            self.time_start = kwargs['time_start']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_start_time(
                kwargs, self.time_start, e
            )
        log.info('Successfully set record start timestamp.')
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_stop(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_stop'):
            return self.error_no_stop_time_found(kwargs)
        try:
            self.time_stop = kwargs['time_stop']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_stop_time(
                kwargs, self.time_stop, e
            )
        log.info('Successfully set record stop timestamp.')
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_spent'):
            return self.error_no_spent_time_found(kwargs)
        try:
            self.time_spent = kwargs['time_spent']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_spent_time(
                kwargs, self.time_spent, e
            )
        log.info('Successfully set record time spent.')
        return True

    # UPDATERS (RECORD)

    def update_write_date(self, **kwargs):
        log.debug('')
        set_date = self.set_write_date(write_date=datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_write_date()

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

    # WARNINGS (RECORD)
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_could_not_fetch_time_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch credit clock time sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS (RECORD)
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_could_not_set_credit_clock_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record credit clock id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_record_create_uid(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time record create UID. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_record_write_uid(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time record write UID. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_pending(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record pending time. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_pending_count(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record pending count. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_sheet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record time sheet id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_record_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time record reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_record_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time record write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_start_time(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record start timestamp. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_stop_time(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record stop timestamp. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_spent_time(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set record time spent. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time record id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_write_uid(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet write UID. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_create_uid_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet create UID found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_write_uid_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet write UID found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_pending_time_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No pending time found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_pending_count_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No pending count found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_start_time_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No start time found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_stop_time_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No stop time found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_spent_time_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No spent time found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_write_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No write date found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_spent_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time spent found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response


class CreditClockTimeSheet(Base):
    __tablename__ = 'credit_clock_time_sheet'

    time_sheet_id = Column(Integer, primary_key=True)
    clock_id = Column(Integer, ForeignKey('credit_clock.clock_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    clock = relationship('CreditClock', back_populates='time_sheet')
    records = relationship('TimeSheetRecord')

#   @pysnooper.snoop('logs/ewallet.log')
    def __init__(self, **kwargs):
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.clock_id = kwargs.get('clock_id')
        self.reference = kwargs.get('reference') or \
            config.time_sheet_config['time_sheet_reference']
        self.clock = kwargs.get('clock')
        self.records = kwargs.get('records') or []

    # FETCHERS (LIST)

    def fetch_time_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found(kwargs)
        query = list(
            kwargs['active_session'].query(
                TimeSheetRecord
            ).filter_by(record_id=kwargs['record_id'])
        )
        record = None if not query else query[0]
        check = self.check_record_in_time_sheet(record)
        if not check:
            return self.warning_record_not_in_time_sheet(
                kwargs, record
            )
        log.info('Successfully fetched time record by id.')
        return record

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
        return values

    def fetch_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_time_record_identifier_specified(kwargs)
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

    def fetch_time_sheet_records(self, **kwargs):
        log.debug('')
        return self.records

    # SETTERS (LIST)

    def set_time_sheet_clock(self, credit_clock):
        log.debug('')
        try:
            self.clock = credit_clock
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_sheet_credit_clock(
                credit_clock, self.clock, e
            )
        log.info('Successfully set time sheet credit clock.')
        return True

    def set_time_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_time_sheet_id_found(kwargs)
        try:
            self.time_sheet_id = kwargs['sheet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_sheet_id(
                kwargs, self.time_sheet_id, e
            )
        log.info('Successfully set time sheet id.')
        return True

    def set_time_sheet_clock_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_time_sheet_clock_id_found(kwargs)
        try:
            self.clock_id = kwargs['clock_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_clock_id(
                kwargs, self.clock_id, e
            )
        log.info('Successfully set time sheet credit clock id.')
        return True

    def set_time_sheet_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_time_sheet_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_sheet_reference(
                kwargs, self.reference, e
            )
        return True

    def set_time_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_time_sheet_records_found(kwargs)
        try:
            self.records = kwargs['records']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_time_sheet_records(
                kwargs, self.records, e
            )
        log.info('Successfully set time sheet records.')
        return True

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_time_sheet_write_date_found(kwargs)
        try:
            self.write_date = kwargs['write_date']
        except Exception as e:
            return self.error_could_not_set_time_sheet_write_date(
                kwargs, self.write_date, e
            )
        log.info('Successfully set time sheet write date.')
        return True

    def set_to_time_sheet_records(self, record):
        log.debug('')
        try:
            self.records.append(record)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_update_time_sheet_records(
                record, self.records, e
            )
        log.info('Successfully updated time sheet records.')
        return True

    # UPDATES (LIST)

    def update_time_sheet_records(self, record):
        log.debug('')
        set_to = self.set_to_time_sheet_records(record)
        return set_to if isinstance(set_to, dict) and \
            set_to.get('failed') else self.fetch_time_sheet_records()

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(write_date=datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_time_sheet_write_date()

    # CHECKERS (LIST)

    def check_record_in_time_sheet(self, record):
        log.debug('')
        return False if record not in self.records else True

    # ACTIONS (LIST)

    def action_remove_time_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found()
        record = self.fetch_time_sheet_record_by_id(
            record_id=kwargs['record_id'],
            active_session=kwargs['active_session'],
        )
        check = self.check_record_in_time_sheet(record)
        if not check:
            return self.warning_record_not_in_time_sheet(kwargs, record, check)
        try:
            kwargs['active_session'].query(
                TimeSheetRecord
            ).filter_by(record_id=kwargs['record_id']).delete()
        except:
            return self.error_could_not_remove_time_sheet_record(kwargs)
        return True

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

    def action_interogate_all_time_sheet_records(self, **kwargs):
        log.debug('')
        return self.fetch_time_sheet_record(identifier='all')

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

    # GENERAL (LIST)

    # TODO
    def search_time_sheet_record_before_date(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def search_time_sheet_record_after_date(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def search_time_sheet_record_greater_time(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def search_time_sheet_record_lesser_time(self, **kwargs):
        log.debug('UNIMPLEMENTED')

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

    # CONTROLLERS (LIST)

    def action_interogate_time_sheet_records_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('date'):
            return self.error_no_time_record_date_found(kwargs)
        handlers = {
            'date': self.search_time_sheet_record_by_date,
            'before': self.search_time_sheet_record_before_date,
            'after': self.search_time_sheet_record_after_date,
        }
        return handlers[kwargs['date']](**kwargs)

    def action_interogate_time_sheet_records_by_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_time_record_time_found(kwargs)
        handlers = {
            'time': self.search_time_sheet_record_by_time,
            'more': self.search_time_sheet_record_greater_time,
            'less': self.search_time_sheet_record_lesser_time,
        }
        return handlers[kwargs['time']](**kwargs)

    def action_interogate_time_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_time_record_identifier_specified(kwargs)
        handlers = {
            'id': self.action_interogate_time_sheet_records_by_id,
            'reference': self.action_interogate_time_sheet_records_by_reference,
            'date': self.action_interogate_time_sheet_records_by_date,
            'time_spent': self.action_interogate_time_sheet_records_by_time_spent,
            'all': self.action_interogate_all_time_sheet_records,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def credit_clock_time_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_time_sheet_controller_action_specified(kwargs)
        handlers = {
            'add': self.action_add_time_sheet_record,
            'remove': self.action_remove_time_sheet_record,
            'interogate': self.action_interogate_time_sheet_records,
            'clear': self.action_clear_time_sheet_records,
        }
        return handlers[kwargs['action']](**kwargs)

    # WARNINGS (LIST)
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_record_not_in_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Record no in time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_time_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch time sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS (LIST)
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_could_not_set_time_sheet_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet credit clock. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_sheet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet id. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_clock_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet credit clock id. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_sheet_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet reference. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_sheet_records(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet records. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_time_sheet_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set time sheet write date. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_write_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet write date found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_time_sheet_records(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not update time sheet records. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_time_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove time sheet record. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_identifier_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record identifier specified. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time record id found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No active session found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_controller_action_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet controller action specified. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet id found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_clock_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet credit clock id found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet reference found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet records found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record date found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_time_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record time found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record reference found. '
                     'Details: {}'.format(args),
        }
        log.warning(command_chain_response['error'])
        return command_chain_response


###############################################################################
# CODE DUMP
###############################################################################

    # TODO
#   def fetch_time_sheet_record_by_ref(self, **kwargs):
#       log.debug('TODO - Refactor')
#       if not kwargs.get('code'):
#           return self.error_no_time_record_reference_found()
#       for item in self.records:
#           if self.records[item].fetch_record_reference() == kwargs['code']:
#               log.info('Successfully fetched time record by reference.')
#               return self.records[item]
#       return self.warning_could_not_fetch_time_record(
#               'reference', kwargs['code']
#               )

#   # TODO
#   def fetch_time_sheet_record_by_date(self, **kwargs):
#       log.debug('TODO - Refactor')
#       if not kwargs.get('code'):
#           return self.error_no_time_record_date_found()
#       for item in self.records:
#           if self.records[item].fetch_record_create_date() == kwargs['code']:
#               log.info('Successfully fetched time record by date.')
#               return self.records[item]
#       return self.warning_could_not_fetch_time_record(
#               'date', kwargs['code']
#               )

#   # TODO
#   def fetch_time_sheet_record_by_time(self, **kwargs):
#       log.debug('TODO - Refactor')
#       if not kwargs.get('code'):
#           return self.error_no_time_record_time_found()
#       for item in self.records:
#           if self.record[item].fetch_record_time_spent() == kwargs['code']:
#               log.info('Successfully fetched time record by time.')
#               return self.records[item]
#       return self.warning_could_not_fetch_time_record(
#               'time', kwargs['code']
#               )

