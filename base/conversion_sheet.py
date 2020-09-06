import datetime
import logging
import pysnooper

from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


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
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.conversion_sheet_id = kwargs.get('conversion_sheet_id', int())
        self.reference = kwargs.get(
            'reference',
            config.conversion_sheet_config['conversion_record_reference']
        )
        self.conversion_type = kwargs.get('conversion_type', str())
        self.minutes = kwargs.get('minutes', float())
        self.credits = kwargs.get('credits', int())

    # FETCHERS (RECORD)

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_conversion_sheet_id(self):
        log.debug('')
        return self.conversion_sheet_id

    def fetch_record_reference(self):
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

    def fetch_record_values(self):
        log.debug('')
        values = {
            'id': self.record_id,
            'conversion_sheet': self.conversion_sheet_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'conversion_type': self.conversion_type,
            'minutes': self.minutes,
            'credits': self.credits,
        }
        return values

    # SETTERS (RECORD)

    def set_conversion_record_id(self, record_id):
        log.debug('')
        try:
            self.record_id = record_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_record_id(
                record_id, self.record_id, e
            )
        log.info('Successfully set conversion record id.')
        return True

    def set_conversion_record_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_record_create_date(
                create_date, self.create_date, e
            )
        log.info('Successfully set conversion record create date.')
        return True

    def set_conversion_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_sheet_id'):
            return self.error_no_conversion_sheet_id_found(kwargs)
        try:
            self.conversion_sheet_id = kwargs['conversion_sheet_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_sheet_id(
                kwargs, self.conversion_sheet_id, e
            )
        log.info('Successfully set conversion sheet id.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_record_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set conversion record reference.')
        return True

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_write_date_found(kwargs)
        try:
            self.write_date = kwargs['write_date']
        except Exception as e:
            return self.error_could_not_set_conversion_record_write_date(
                kwargs, self.write_date, e
            )
        log.info('Successfully set conversion record write date.')
        return True

    def set_conversion_type(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_type'):
            return self.error_no_conversion_type_found(kwargs)
        try:
            self.conversion_type = kwargs['conversion_type']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_type(
                kwargs, self.conversion_type, e
            )
        log.info('Successfully set conversion type.')
        return True

    def set_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found(kwargs)
        try:
            self.minutes = kwargs['minutes']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_minutes(
                kwargs, self.minutes, e
            )
        log.info('Successfully set conversion record minutes.')
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found(kwargs)
        try:
            self.credits = kwargs['credits']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credits(
                kwargs, self.credits, e
            )
        log.info('Successfully set conversion record credits.')
        return True

    # UPDATERS (RECORD)

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(write_date=datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_write_date()

    # ERRORS (RECORD)

    def error_could_not_set_conversion_sheet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_record_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record reference. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_record_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record write date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_record_create_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record create date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_type(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion type. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_minutes(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record minutes. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credits(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record credits. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_create_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record create date found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_record_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion record id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record id found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credits found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_sheet_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion sheet id found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record reference found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_write_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record write date found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_type_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion type found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_minutes_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No minutes found. Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response


class CreditClockConversionSheet(Base):
    __tablename__ = 'credit_clock_conversion_sheet'

    conversion_sheet_id = Column(Integer, primary_key=True)
    clock_id = Column(Integer, ForeignKey('credit_clock.clock_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    clock = relationship('CreditClock', back_populates='conversion_sheet')
    records = relationship('CreditClockConversionSheetRecord')

#   @pysnooper.snoop('logs/ewallet.log')
    def __init__(self, **kwargs):
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.clock_id = kwargs.get('clock_id', int())
        self.reference = kwargs.get(
            'reference',
            config.conversion_sheet_config['conversion_sheet_reference']
        )
        self.clock = kwargs.get('clock')
        self.records = kwargs.get('records') or []

    # FETCHERS (LIST)

    def fetch_conversion_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_record_id_found(kwargs)
        query = list(
            kwargs['active_session'].query(
                CreditClockConversionSheetRecord
            ).filter_by(record_id=kwargs['record_id'])
        )
        record = None if not query else query[0]
        check = self.check_record_in_conversion_sheet(record)
        if not check:
            return self.warning_record_not_in_conversion_sheet(
                kwargs, record
            )
        log.info('Successfully fetched conversion record by id.')
        return record

    def fetch_conversion_sheet_record(self, **kwargs):
        log.debug('')
        if not self.records or not kwargs.get('identifier'):
            return self.error_no_conversion_sheet_record_identifier_specified()
        handlers = {
            'id': self.fetch_conversion_sheet_record_by_id,
            'all': self.fetch_conversion_sheet_records,
        }
        return handlers[kwargs['identifier']](**kwargs)

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
        values = {
            'id': self.conversion_sheet_id,
            'clock': self.clock_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'records': {
                item.fetch_record_id(): item.fetch_record_reference() \
                for item in self.records
            },
        }
        return values

    def fetch_conversion_record_creation_values(self, **kwargs):
        log.debug('')
        values = {
            'conversion_sheet_id': self.conversion_sheet_id,
            'reference': kwargs.get('reference'),
            'conversion_type': kwargs.get('conversion_type'),
            'minutes': kwargs.get('minutes'),
            'credits': kwargs.get('credits'),
        }
        return values

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

    # SETTERS (LIST)

    def set_clock(self, clock):
        log.debug('')
        try:
            self.clock = clock
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_sheet_clock(
                clock, self.clock, e
            )
        log.info('Successfully set conversion sheet credit clock.')
        return True

    def set_clock_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_clock_id_found(kwargs)
        try:
            self.clock_id = kwargs['clock_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_clock_id(
                kwargs, self.clock_id, e
            )
        log.info('Successfully set conversion sheet credit clock id.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_sheet_reference(
                kwargs, self.refrence, e
            )
        log.info('Successfully set conversion sheet reference.')
        return True

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_write_date_found(kwargs)
        try:
            self.write_date = kwargs['write_date']
        except Exception as e:
            return self.error_could_not_set_conversion_sheet_write_date(
                kwargs, self.write_date, e
            )
        log.info('Successfully set conversion sheet write date.')
        return True

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found(kwargs)
        try:
            self.records = kwargs['records']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_conversion_sheet_records(
                kwargs, self.records, e
            )
        log.info('Successfully set conversion sheet records.')
        return True

    # CHECKERS (LIST)

    def check_record_in_conversion_sheet(self, record):
        log.debug('')
        return False if record not in self.records else True

    # UPDATERS (LIST)

    def update_write_date(self):
        log.debug('')
        set_date = self.set_write_date(write_date=datetime.datetime.now())
        return set_date if isinstance(set_date, dict) and \
            set_date.get('failed') else self.fetch_conversion_sheet_write_date()

    def update_conversion_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('record'):
            return self.error_no_conversion_record_found()
        self.records.append(kwargs['record'])
        log.info('Successfully updated conversion sheet records.')
        return self.records

    # GENERAL (LIST)

    # TODO
    def search_conversion_sheet_records_before_date(self, **kwargs):
        pass
    def search_conversion_sheet_records_after_date(self, **kwargs):
        pass
    def search_conversion_sheet_records_lesser_minutes(self, **kwargs):
        pass
    def search_conversion_sheet_records_greater_minutes(self, **kwargs):
        pass
    def search_conversion_sheet_records_lesser_credits(self, **kwargs):
        pass
    def search_conversion_sheet_records_greater_credits(self, **kwargs):
        pass

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

    def add_conversion_sheet_record(self, **kwargs):
        log.debug('')
        values = self.fetch_conversion_record_creation_values(**kwargs)
        record = CreditClockConversionSheetRecord(**values)
        self.update_conversion_sheet_records(record=record)
        log.info('Successfully added conversion record to sheet.')
        return record

    # ACTIONS (LIST)

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

    def action_remove_conversion_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_record_id_found()
        try:
            kwargs['active_session'].query(
                CreditClockConversionSheetRecord
            ).filter_by(record_id=kwargs['record_id']).delete()
        except:
            return self.error_could_not_remove_conversion_sheet_record(kwargs)
        return True

    def action_add_conversion_sheet_record(self, **kwargs):
        log.debug('')
        record = CreditClockConversionSheetRecord(
            conversion_sheet_id=self.conversion_sheet_id,
            reference=kwargs.get('reference'),
            conversion_type=kwargs.get('conversion_type'),
            minutes=kwargs.get('minutes'),
            credits=kwargs.get('credits'),
        )
        self.update_conversion_sheet_records(record=record)
        return record

    # INTEROGATORS (LIST)

    def interogate_conversion_sheet_records(self, **kwargs):
        return self.fetch_conversion_sheet_record(identifier='all')

    def interogate_conversion_sheet_records_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_reference_found()
        records = self.fetch_conversion_sheet_record(
            identifier='reference', code=kwargs['code']
        )
        if not records:
            return self.warning_could_not_fetch_conversion_record(
                'reference', kwargs['code']
            )
        return records

    def interogate_conversion_sheet_records_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_conversion_record_id_found()
        record = self.fetch_conversion_sheet_record(
            identifier='id', code=kwargs['code'],
        )
        if not record:
            return self.warning_could_not_fetch_conversion_record(
                'id', kwargs['code']
            )
        return record or False

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

    # CONTROLLERS (LIST)

    def credit_clock_conversion_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_conversion_sheet_controller_action_specified()
        handlers = {
            'add': self.action_add_conversion_sheet_record,
            'remove': self.action_remove_conversion_sheet_record,
            'interogate': self.action_interogate_conversion_sheet_records,
            'clear': self.action_clear_conversion_sheet_records,
        }
        return handlers[kwargs['action']](**kwargs)

    # WARNINGS (LIST)

    def warning_record_not_in_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Record not in conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_conversion_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch conversion sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    # ERRORS (LIST)

    def error_could_not_set_conversion_sheet_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet credit clock. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_clock_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet credit clock id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_sheet_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_sheet_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_conversion_sheet_records(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set conversion sheet records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_conversion_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not remove conversion sheet record. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_conversion_sheet_record_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not fetch conversion sheet record by id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion sheet record id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_conversion_type_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion type found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_records_interogation_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record interogation target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_sheet_controller_action_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion sheet controller action specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion records found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_clock_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No clock id found. '
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

    def error_no_conversion_record_type_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record type found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_sheet_record_identifier_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion sheet record identifier specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record credits found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_minutes_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record minutes found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_date_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion record date found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

###############################################################################
# CODE DUMP
###############################################################################

