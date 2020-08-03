import time
import datetime
import logging
import pysnooper

from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .time_sheet import CreditClockTimeSheet
from .conversion_sheet import CreditClockConversionSheet
from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class CreditClock(Base):
    __tablename__ = 'credit_clock'

    clock_id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('credit_ewallet.wallet_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    credit_clock = Column(Float)
    credit_clock_state = Column(String)
    time_spent = Column(Float)
    start_time = Column(Float)
    end_time = Column(Float)
    pending_time = Column(Float)
    pending_count = Column(Integer)
    # O2O
    wallet = relationship('CreditEWallet', back_populates='credit_clock')
    # O2O
    time_sheet = relationship('CreditClockTimeSheet', back_populates='clock')
    active_time_record = relationship('TimeSheetRecord')
    # O2O
    conversion_sheet = relationship(
       'CreditClockConversionSheet', back_populates='clock',
    )
    # O2M
    time_sheet_archive = relationship('CreditClockTimeSheet')
    # O2M
    conversion_sheet_archive = relationship('CreditClockConversionSheet')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('active_session'):
            self.error_no_active_session_found()
            return
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        time_sheet = kwargs.get('time_sheet') or \
            self.system_controller(
                action='create', create='sheet', sheet_type='time',
                active_session=kwargs['active_session']
            )
        conversion_sheet = kwargs.get('conversion_sheet') or \
            self.system_controller(
                action='create', create='sheet', sheet_type='conversion',
                active_session=kwargs['active_session']
            )
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference') or \
            config.clock_config['clock_reference']
        self.credit_clock = kwargs.get('credit_clock') or 0.00
        self.credit_clock_state = kwargs.get('credit_clock_state') or 'inactive'
        self.time_spent = kwargs.get('time_spent') or 0.00
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.pending_time = kwargs.get('pending_time') or 0.00
        self.pending_count = kwargs.get('pending_count') or 0
        self.time_sheet = [time_sheet]
        self.conversion_sheet = [conversion_sheet]
        self.time_sheet_archive = kwargs.get(
            'time_sheet_archive') or [time_sheet]
        self.conversion_sheet_archive = kwargs.get(
            'conversion_sheet_archive') or [conversion_sheet]

    # FETCHERS

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_time_sheet_record_creation_values(self, **kwargs):
        log.debug('')
        values = {
            'create_date': kwargs.get('create_date') or datetime.datetime.now(),
            'write_date': kwargs.get('write_date') or datetime.datetime.now(),
            'create_uid': kwargs.get('uid') or None,
            'write_uid': kwargs.get('uid') or None,
            'reference': kwargs.get('reference') or
                config.time_sheet_config['time_record_reference'],
            'time_start': kwargs.get('time_start') or time.time(),
            'time_stop': kwargs.get('time_stop') or None,
            'time_spent': kwargs.get('time_spent') or None,
            'time_sheet_id': kwargs.get('time_sheet_id'),
            'credit_clock_id': kwargs.get('credit_clock_id'),
        }
        return values

    def fetch_credit_clock_pending_time(self, **kwargs):
        log.debug('')
        return self.pending_time

    def fetch_credit_clock_time_sheet_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        time_sheet = list(
            kwargs['active_session'].query(CreditClockTimeSheet).filter_by(
                time_sheet_id=kwargs['sheet_id']
            )
        )
        if time_sheet:
            log.info('Successfully fetched time sheet by id.')
        return self.warning_could_not_fetch_time_sheet_by_id(kwargs) \
            if not time_sheet else time_sheet[0]

    def fetch_credit_clock_conversion_sheet_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        conversion_sheet = list(
            kwargs['active_session'].query(CreditClockConversionSheet).filter_by(
                conversion_sheet_id=kwargs['sheet_id']
            )
        )
        if conversion_sheet:
            log.info('Successfully fetched conversion sheet by id.')
        return self.warning_could_not_fetch_conversion_sheet_by_id(kwargs) \
            if not conversion_sheet else conversion_sheet[0]

    def fetch_active_credit_clock_time_record(self, **kwargs):
        log.debug('')
        if not self.active_time_record:
            return self.error_no_active_time_record_found()
        return self.active_time_record[0]

    def fetch_action_stop_time_record_update_values(self, **kwargs):
        log.debug('')
        values = {
            'time_stop': kwargs.get('time_stop'),
            'time_spent': kwargs.get('time_spent'),
            'write_uid': kwargs.get('write_uid'),
        }
        return values

    def fetch_credit_clock_pending_time(self):
        log.debug('')
        return self.pending_time

    def fetch_credit_clock_pending_count(self):
        log.debug('')
        return self.pending_count

    def fetch_credit_clock_clear_value_map(self):
        _map = {
                'wallet_id': None,
                'reference': '',
                'create_date': None,
                'write_date': None,
                'credit_clock': 0.0,
                'credit_clock_state': '',
                'time_spent': 0.0,
                'time_start': None,
                'time_stop': None,
                'pending_time': 0.0,
                'pending_count': 0,
                'wallet': [],
                'time_sheet': [],
                'active_time_record': [],
                'conversion_sheet': [],
                'time_sheet_archive': [],
                'conversion_sheet_archive': [],
                }
        return _map

    def fetch_credit_clock_id(self):
        log.debug('')
        return self.clock_id or \
                self.error_no_credit_clock_id_found()

    def fetch_credit_clock_reference(self):
        log.debug('')
        return self.reference or \
                self.error_no_credit_clock_reference_found()

    def fetch_credit_clock_time_left(self):
        log.debug('')
        return self.credit_clock

    def fetch_credit_clock_time_sheet(self):
        log.debug('')
        if not len(self.time_sheet):
            return self.error_no_credit_clock_time_sheet_found()
        return self.time_sheet[0]

    def fetch_credit_clock_conversion_sheet(self):
        log.debug('')
        if not len(self.conversion_sheet):
            return self.error_no_credit_clock_conversion_sheet_found()
        return self.conversion_sheet[0]

    def fetch_credit_clock_state(self):
        log.debug('')
        return self.credit_clock_state or \
               self.error_no_state_found_for_credit_clock()

    def fetch_credit_clock_start_time(self):
        log.debug('')
        return self.error_no_start_time_found() \
            if not self.start_time or isinstance(self.start_time, float) \
            else self.start_time

    def fetch_active_time_record_start_time(self, **kwargs):
        log.debug('')
        time_record = kwargs.get('time_record') or \
                self.fetch_active_credit_clock_time_record()
        if not time_record:
            return self.error_no_active_time_record_found()
        start_time = time_record.fetch_time_start()
        return start_time or False

    def fetch_credit_clock_stop_time(self):
        log.debug('')
        return self.end_time or \
                self.error_no_end_time_found()

    def fetch_credit_clock_spent_time(self):
        log.debug('')
        return self.time_spent or \
                self.error_no_time_spent_found()

    def fetch_credit_clock_values(self):
        log.debug('')
        time_sheet = self.fetch_credit_clock_time_sheet()
        conversion_sheet = self.fetch_credit_clock_conversion_sheet()
        values = {
            'id': self.clock_id,
            'ewallet': self.wallet_id,
            'reference': self.reference or
                config.clock_config['clock_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'credit_clock': self.credit_clock or 0.00,
            'clock_state': self.fetch_credit_clock_state(),
            'time_sheet': None if not time_sheet else \
                time_sheet.fetch_time_sheet_id(),
            'time_sheet_archive': {
                item.fetch_time_sheet_id(): item.fetch_time_sheet_reference() \
                for item in self.time_sheet_archive
            },
            'conversion_sheet': None if not conversion_sheet else \
                conversion_sheet.fetch_conversion_sheet_id(),
            'conversion_sheet_archive': {
                item.fetch_conversion_sheet_id(): item.fetch_conversion_sheet_reference() \
                for item in self.conversion_sheet_archive
            },
        }
        return values

    def fetch_time_sheet_creation_values(self, **kwargs):
        values = {
            'time_sheet_id': kwargs.get('time_sheet_id'),
            'clock_id': self.clock_id,
            'reference': kwargs.get('reference') or
                config.time_sheet_config['time_sheet_reference'],
            'records': kwargs.get('records'),
        }
        return values

    def fetch_conversion_sheet_creation_values(self, **kwargs):
        values = {
            'conversion_sheet_id': kwargs.get('conversion_sheet_id'),
            'clock_id': self.clock_id,
            'reference': kwargs.get('reference') or
                config.conversion_sheet_config['conversion_sheet_reference'],
            'records': kwargs.get('records'),
        }
        return values

    def fetch_credit_clock_time_sheet_by_ref(self, code):
        log.debug('')
        for item in self.time_sheet_archive:
            if self.time_sheet_archive[item].reference == code:
                return self.time_sheet_archive[item]
        log.info('Successfullt fethced time sheet by reference.')
        return self.warning_could_not_fetch_time_sheet('reference', code)

    def fetch_credit_clock_time_sheets(self, *args, **kwargs):
        log.debug('')
        return self.time_sheet_archive.values()

    def fetch_credit_clock_conversion_sheet_by_ref(self, code):
        log.debug('')
        for item in self.conversion_sheet_archive:
            if self.conversion_sheet_archive[item].reference == code:
                return self.conversion_sheet_archive[item]
        log.info('Successfully fetched conversion sheet by reference.')
        return self.warning_could_not_fetch_conversion_sheet('reference', code)

    def fetch_credit_clock_conversion_sheets(self, *args, **kwargs):
        log.debug('')
        return self.conversion_sheet_archive.values()

    def fetch_credit_clock_conversion_sheet_by(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_conversion_sheet_identifier_specified()
        _handlers = {
                'id': self.fetch_credit_clock_conversion_sheet_by_id,
                'reference': self.fetch_credit_clock_conversion_sheet_by_ref,
                'all': self.fetch_credit_clock_conversion_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_clock_time_sheet_by(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_time_sheet_identifier_specified()
        _handlers = {
                'id': self.fetch_credit_clock_time_sheet_by_id,
                'reference': self.fetch_credit_clock_time_sheet_by_ref,
                'all': self.fetch_credit_clock_time_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_clock_states(self):
        log.debug('')
        return ('active', 'inactive', 'pending')

    def fetch_credit_clock_conversion_record_creation_values(self, **kwargs):
        log.debug('')
        values = {
            'create_date': kwargs.get('create_date') or datetime.datetime.now(),
            'write_date': kwargs.get('write_date') or datetime.datetime.now(),
            'conversion_sheet_id': kwargs.get('conversion_sheet_id'),
            'reference': kwargs.get('reference') or
                config.conversion_sheet_config['conversion_record_reference'],
            'conversion_type': kwargs.get('conversion_type'),
            'minutes': kwargs.get('minutes') or kwargs.get('credits'),
            'credits': kwargs.get('credits'),
        }
        return values

    # SETTERS

    def set_credit_clock_time_sheet(self, time_sheet):
        log.debug('')
        try:
            self.time_sheet = [time_sheet]
        except:
            return self.error_could_not_set_credit_clock_time_sheet(time_sheet)
        return True

    def set_credit_clock_conversion_sheet(self, conversion_sheet):
        log.debug('')
        try:
            self.conversion_sheet = [conversion_sheet]
        except:
            return self.error_could_not_set_credit_clock_conversion_sheet(conversion_sheet)
        return True

    def set_credit_clock_pending_time(self, **kwargs):
        log.debug('')
        if kwargs.get('pending_time') is None:
            return self.error_no_pending_time_found()
        self.pending_time = kwargs['pending_time']
        return True

    def set_credit_clock_pending_count(self, **kwargs):
        log.debug('')
        if kwargs.get('pending_count') is None:
            return self.error_no_pending_count_found()
        self.pending_count = kwargs['pending_count']
        return True

    def set_credit_clock_active_time_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_time_record'):
            return self.error_no_credit_clock_active_time_record_found()
        self.active_time_record = [kwargs['active_time_record']]
        return self.active_time_record or self.error_could_not_set_active_time_record()

#   @pysnooper.snoop()
    def set_credit_clock_state(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_state'):
            return self.error_no_credit_clock_state_specified()
        if kwargs['clock_state'] not in self.fetch_credit_clock_states():
            return self.warning_invalid_credit_clock_state()
        self.credit_clock_state = kwargs['clock_state']
        return True

    def set_credit_clock_time_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_sheet_archive'):
            return self.error_no_credit_clock_time_sheet_archive_found()
        self.time_sheet_archive = kwargs['time_sheet_archive']
        return True

    def set_credit_clock_conversion_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_sheet_archive'):
            return self.error_no_credit_clock_conversion_sheet_archive()
        self.conversion_sheet_archive = kwargs['conversion_sheet_archive']
        return True

    def set_credit_clock_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet'):
            return self.error_no_credit_clock_wallet_found()
        self.wallet = kwargs['wallet']
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_credit_clock_time_start(self, **kwargs):
        log.debug('')
        self.time_start = kwargs.get('time_start') or time.time()
        return True

    def set_credit_clock_time_stop(self, **kwargs):
        log.debug('')
        self.end_time = kwargs.get('time_stop')
        return True

    def set_credit_clock_time_spent(self, **kwargs):
        log.debug('')
        self.time_spent = kwargs.get('time_spent')
        return True

    def set_credit_clock_wallet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        self.wallet_id = kwargs['wallet_id']
        return True

    def set_credit_clock_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_credit_clock_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_credit_clock_create_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_credit_clock_create_date_found()
        self.create_date = kwargs['create_date']
        return True

    def set_credit_clock_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_credit_clock_write_date_found()
        self.write_date = kwargs['write_date']
        return True

    def set_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_clock'):
            return self.error_no_credit_clock_time_found()
        self.credit_clock = kwargs['credit_clock']
        return True

    # CHECKERS

    def check_clock_is_pending(self, **kwargs):
        log.debug('')
        state = self.fetch_credit_clock_state()
        if not state:
            return self.error_no_credit_clock_state_found()
        return True if state == 'pending' else False

    def check_clock_is_active(self, **kwargs):
        log.debug('')
        _state = self.fetch_credit_clock_state()
        if not _state:
            return self.error_no_credit_clock_state_found()
        return True if _state == 'active' else False

    def check_clock_is_inactive(self, **kwargs):
        log.debug('')
        _state = self.fetch_credit_clock_state()
        if not _state:
            return self.error_no_credit_clock_state_found()
        return True if _state == 'inactive' else False

#   @pysnooper.snoop('logs/ewallet.log')
    def check_clock_state(self, check=None, **kwargs):
        log.debug('')
        if not check:
            return self.error_no_clock_state_check_type_specified()
        _checkers = {
                'active': self.check_clock_is_active,
                'inactive': self.check_clock_is_inactive,
                'pending': self.check_clock_is_pending,
                }
        if check not in ('state_is', 'state_not', 'current'):
            return self.error_clock_state_check_type_not_supported()
        if kwargs[check] not in self.fetch_credit_clock_states():
            return self.error_invalid_clock_state()
        if check == 'current':
            return self.fetch_credit_clock_state()
        _check = _checkers[kwargs[check]](**kwargs)
        if check == 'state_is':
            return _check
        if _check and check == 'state_not':
            return False if _check else True

    # UPDATES

#   @pysnooper.snoop('logs/ewallet.log')
    def update_credit_clock_time_sheet_record(self, values, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        _time_record = kwargs.get('time_record') or \
                self.fetch_active_credit_clock_time_record()
        if not _time_record:
            return self.error_no_active_time_record_found()
        _update = _time_record.update_record_values(values, **kwargs)
        if not _update:
            self.error_could_not_update_active_time_record_values()
        kwargs['active_session'].commit()
        return _update or False

    def update_write_date(self):
        log.debug('')
        return self.set_credit_clock_write_date(
                write_date=datetime.datetime.now()
                )

    def update_time_sheet_archive(self, time_sheet):
        log.debug('')
        self.time_sheet_archive.append(time_sheet)
        log.info('Successfully updated credit clock time sheet archive.')
        return self.time_sheet_archive

    def update_conversion_sheet_archive(self, conversion_sheet):
        log.debug('')
        self.conversion_sheet_archive.append(conversion_sheet)
        log.info('Successfully updated credit clock conversion sheet archive.')
        return self.conversion_sheet_archive

    # HANDLERS

    # GENERAL

    # TODO - Fix active_session commit case. Brace for failure.
#   @pysnooper.snoop()
    def credit_converter(self, **kwargs):
        log.debug('TODO - Fix active_session commit case. Brace for failure.')
        if not kwargs.get('conversion'):
            return self.error_no_credit_conversion_type_specified(kwargs)
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        handlers = {
            'to_minutes': self.convert_credits_to_minutes,
            'to_credits': self.convert_minutes_to_credits,
        }
        conversion_sheet = self.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet or isinstance(conversion_sheet, dict) and \
                conversion_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_fetch_active_conversion_sheet(kwargs)
        kwargs['conversion_sheet'] = conversion_sheet
        creation_values = self.fetch_credit_clock_conversion_record_creation_values(
            **kwargs
        )
        conversion_record = self.create_credit_clock_conversion_record(
            creation_values, **kwargs
        )
        kwargs['active_session'].add(conversion_record)
        conversion = handlers[kwargs['conversion']](**kwargs)
        if not conversion or isinstance(conversion, dict) and \
                conversion.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_convert(kwargs)
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'conversion_record': conversion_record.fetch_record_id(),
        }
        if isinstance(conversion, dict):
            command_chain_response.update(conversion)
        else:
            command_chain_response.update({'conversion': conversion})
        return command_chain_response

    def extract_credit_clock_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        minutes = round((self.credit_clock - float(kwargs.get('minutes'))), 2)
        if minutes is self.credit_clock:
            return self.error_could_not_extract_credit_clock_minutes()
        self.credit_clock = minutes
        log.info('Successfully extracted credit clock minutes.')
        return self.credit_clock

    def supply_credit_clock_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        minutes = round((self.credit_clock + float(kwargs['credits'])), 2)
        if minutes is self.credit_clock:
            return self.error_could_not_supply_credit_clock_with_minutes()
        self.credit_clock = minutes
        log.info('Successfully supplied credit clock minutes.')
        return self.credit_clock

    def supply_ewallet_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_ewallet'):
            return self.error_no_ewallet_found()
        if not kwargs.get('credits'):
            return self.error_no_credits_specified()
        supply = kwargs['credit_ewallet'].main_controller(
            controller='system', action='supply', credits=kwargs['credits']
        )
        return supply

#   @pysnooper.snoop('logs/ewallet.log')
    def extract_ewallet_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_ewallet'):
            return self.error_no_ewallet_found()
        if not kwargs.get('credits'):
            return self.error_no_credits_specified()
        extract = kwargs['credit_ewallet'].main_controller(
            controller='system', action='extract', credits=kwargs['credits']
        )
        return extract

#   @pysnooper.snoop()
    def convert_credits_to_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('credit_ewallet'):
            return self.error_no_credits_found()
        supply_minutes = self.supply_credit_clock_minutes(**kwargs)
        extract_credits = self.extract_ewallet_credits(**kwargs)
        log.info('Successfully converted credits to minutes.')
        command_chain_response = {
            'failed': False,
            'ewallet_credits': kwargs['credit_ewallet'].fetch_credit_ewallet_credits(),
            'credit_clock': self.fetch_credit_clock_time_left(),
            'converted_credits': int(kwargs.get('credits')),
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def convert_minutes_to_credits(self, **kwargs):
        '''
        [ RETURN ]: Minutes left after subtraction or dictionary with error,
        minutes found in command chain and remainder
        (in case of insufficient time).
        '''
        log.debug('TODO - FIX ME')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        if (self.credit_clock - kwargs['minutes']) < 0:
            remainder = abs(self.credit_clock - kwargs['minutes'])
            extract = self.extract_credit_clock_minutes(
                clock_credits=(self.credit_clock - kwargs['minutes'] + remainder)
            )
            return self.warning_insufficient_time_to_convert(remainder, kwargs)
        extract = self.extract_credit_clock_minutes(**kwargs)
        supply = self.supply_ewallet_credits(
            credits=kwargs['minutes'], **kwargs
        )
        log.info('Successfully converted minutes to credits.')
        command_chain_response = {
            'failed': False,
            'ewallet_credits': kwargs['credit_ewallet'].fetch_credit_ewallet_credits(),
            'credit_clock': self.fetch_credit_clock_time_left(),
            'converted_minutes': int(kwargs['minutes']),
        }
        return command_chain_response

#   @pysnooper.snoop()
    def compute_pending_time(self, **kwargs):
        '''
        [ RETURN ]: Pending Time in minutes.
        '''
        log.debug('')
        now = kwargs.get('now') or time.time()
        end_time = kwargs.get('end_time') or self.fetch_credit_clock_stop_time()
        existing_pending_time = self.fetch_credit_clock_pending_time()
        pending_time = self.convert_time_to_minutes(
                start_time=end_time, end_time=now
        ) + existing_pending_time
        return round(pending_time, 2)

#   @pysnooper.snoop('logs/ewallet.log')
    def clear_credit_clock_values(self, *args):
        log.debug('')
        _handlers = {
                'wallet_id': self.set_credit_clock_wallet_id,
                'reference': self.set_credit_clock_reference,
                'create_date': self.set_credit_clock_create_date,
                'write_date': self.set_credit_clock_write_date,
                'credit_clock': self.set_credit_clock,
                'credit_clock_state': self.set_credit_clock_state,
                'time_spent': self.set_credit_clock_time_spent,
                'time_start': self.set_credit_clock_time_start,
                'time_stop': self.set_credit_clock_time_stop,
                'pending_time': self.set_credit_clock_pending_time,
                'pending_count': self.set_credit_clock_pending_count,
                'wallet': self.set_credit_clock_wallet,
                'time_sheet': self.set_credit_clock_time_sheet,
                'active_time_record': self.set_credit_clock_active_time_record,
                'conversion_sheet': self.set_credit_clock_conversion_sheet,
                'time_sheet_archive': self.set_credit_clock_time_sheet_archive,
                'conversion_sheet_archive': self.set_credit_clock_conversion_sheet_archive,
        }
        _clear_value_map = self.fetch_credit_clock_clear_value_map()
        for item in args:
            if item not in _handlers:
                return self.error_invalid_field_for_credit_clock()
            try:
                _handlers[item](**{item: _clear_value_map[item]})
            except KeyError:
                self.warning_could_not_clear_credit_clock_field()
        return True

    # TODO: Take pending time into account.
#   @pysnooper.snoop('logs/ewallet.log')
    def validate_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_start') or not kwargs.get('time_stop'):
            return self.error_no_start_or_stop_time_found()
        _time_spent = kwargs.get('time_spent')
        if not _time_spent:
            self.error_no_time_spent_found()
        _time_spent_check = self.convert_time_to_minutes(
                kwargs['time_start'], kwargs['time_stop']
                )
        _time_record = kwargs.get('time_record') or \
                self.fetch_active_credit_clock_time_record()
        if not _time_record:
            return False
        if _time_spent_check != _time_spent:
            self.warning_computed_time_spent_wont_match_command_chain_value()
        _recorded_start_time = _time_record.fetch_time_start()
        if not _recorded_start_time:
            return self.error_could_not_fetch_active_time_record_start_time()
        if kwargs['time_start'] != _recorded_start_time:
            return self.error_recorded_start_time_wont_match_command_chain_value()
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def compute_time_spent(self, **kwargs):
        log.debug('')
        _start_time = kwargs.get('time_start') or \
                self.fetch_credit_clock_start_time() or \
                self.fetch_active_time_record_start_time()
        _stop_time = kwargs.get('time_stop') or self.fetch_credit_clock_stop_time()
        if not _start_time or not _stop_time:
            return self.error_could_not_compute_time_spent()
        _used_time = self.convert_time_to_minutes( _start_time, _stop_time)
        _set_time_spent = self.set_credit_clock_time_spent(time_spent=_used_time)
        _reset_timer = self.clear_credit_clock_values('time_start', 'time_stop')
        return _used_time or self.error_identical_start_and_stop_time()

#   @pysnooper.snoop()
    def convert_time_to_minutes(self, start_time=None, end_time=None, ctime=None):
        log.debug('')
        minutes_spent = round(
            round(ctime or (end_time - start_time), 2) / 60, 2
        )
        return minutes_spent

    # SWITCHERS

    def switch_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
        new_time_sheet = self.fetch_credit_clock_time_sheet_by_id(**kwargs)
        if not new_time_sheet:
            return self.warning_could_not_fetch_time_sheet_by_id(kwargs)
        set_sheet = self.set_credit_clock_time_sheet(new_time_sheet)
        if set_sheet:
            log.info('Successfully switched credit clock time sheet by id.')
        return new_time_sheet

    def switch_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        new_conversion_sheet = self.fetch_credit_clock_conversion_sheet_by_id(**kwargs)
        if not new_conversion_sheet:
            return self.warning_could_not_fetch_conversion_sheet_by_id(kwargs)
        set_sheet = self.set_credit_clock_conversion_sheet(new_conversion_sheet)
        if set_sheet:
            log.info('Successfully switch credit clock conversion sheet by id.')
        return new_conversion_sheet

    # CREATORS

    def create_credit_clock_time_record(self, creation_values, **kwargs):
        log.debug('')
        time_sheet = kwargs.get('time_sheet') or \
                self.fetch_credit_clock_time_sheet()
        if not time_sheet:
            return self.error_no_credit_clock_time_sheet_found()
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        record = time_sheet.credit_clock_time_sheet_controller(
            action='add', active_session=kwargs['active_session'],
            **creation_values
        )
        if not record:
            kwargs['active_session'].rollback()
            return self.error_could_not_create_time_sheet_record()
        kwargs['active_session'].add(record)
        log.info('Successfully created new credit clock time record.')
        kwargs['active_session'].commit()
        return record or False

    def create_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        values = self.fetch_time_sheet_creation_values(**kwargs)
        time_sheet = CreditClockTimeSheet(**values)
        kwargs['active_session'].add(time_sheet)
        update_archive = self.update_time_sheet_archive(time_sheet)
        kwargs['active_session'].commit()
        log.info('Successfully created new credit clock time sheet.')
        return time_sheet

#   @pysnooper.snoop()
    def create_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        values = self.fetch_conversion_sheet_creation_values(**kwargs)
        conversion_sheet = CreditClockConversionSheet(**values)
        kwargs['active_session'].add(conversion_sheet)
        self.update_conversion_sheet_archive(conversion_sheet)
        kwargs['active_session'].commit()
        log.info('Successfully created new credit clock conversion sheet.')
        return conversion_sheet

#   @pysnooper.snoop('logs/ewallet.log')
    def create_credit_clock_conversion_record(self, creation_values, **kwargs):
        log.debug('')
        conversion_sheet = kwargs.get('conversion_sheet') or \
                self.fetch_credit_clock_conversion_sheet()
        if not self.conversion_sheet:
            return self.error_no_credit_clock_conversion_sheet_found()
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        record = conversion_sheet.credit_clock_conversion_sheet_controller(
            action='add', **creation_values
        )
        if record:
            kwargs['active_session'].add(record)
            log.info('Successfully created new credit clock conversion record.')
        return record or False

    # ACTIONS

#   @pysnooper.snoop()
    def action_stop_timer(self, **kwargs):
        '''
        [ RETURN ]: Stop time or False.
        '''
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        check_clock_state = self.check_clock_state(
            check='state_is', state_is='active'
        )
        if not check_clock_state:
            return self.error_illegal_credit_clock_state(kwargs)
        start_time = self.fetch_active_time_record_start_time()
        stop_time = time.time()
        set_stop_time = self.set_credit_clock_time_stop(time_stop=stop_time)
        compute_used_time = self.compute_time_spent(
            time_start=start_time, time_stop=stop_time
        )
        time_record = self.fetch_active_credit_clock_time_record(**kwargs)
        if not time_record or isinstance(time_record, dict) and \
                time_record.get('failed'):
            return self.error_could_not_fetch_active_time_record(kwargs)
        check_used_time = self.validate_time_spent(
            time_start=start_time,
            time_stop=stop_time,
            time_spent=compute_used_time,
            time_record=time_record,
        )
        record_update_values = self.fetch_action_stop_time_record_update_values(
            time_stop=stop_time, time_spent=compute_used_time, **kwargs
        )
        update_record = self.update_credit_clock_time_sheet_record(
            record_update_values, time_record=time_record, **kwargs
        )
        if not update_record:
            self.warning_unsuccessful_credit_clock_time_sheet_record_update(
                kwargs
            )
        set_inactive = self.set_credit_clock_state(clock_state='inactive')
        command_chain_response = {
            'failed': False,
            'pending_count': self.fetch_credit_clock_pending_count(),
            'pending_time': self.fetch_credit_clock_pending_time(),
            'start_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(start_time)
            ),
            'stop_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(stop_time)
            ),
            'minutes_spent': compute_used_time,
            'time_record': time_record.fetch_record_id(),
            'record_data': time_record.fetch_record_values(),
        }
        clear_values = self.clear_credit_clock_values(
            'time_start', 'time_stop', 'pending_count', 'pending_time', 'time_spent',
        )
        kwargs['active_session'].commit()
        return command_chain_response

#   @pysnooper.snoop()
    def action_resume_timer(self, **kwargs):
        '''
        [ RETURN ]: Pending Time or False.
        '''
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        check_clock_state = self.check_clock_state(
            check='state_is', state_is='pending'
        )
        if not check_clock_state:
            return self.error_illegal_credit_clock_state(kwargs)
        compute_pending_time = self.compute_pending_time(now=time.time())
        set_pending_time = self.set_credit_clock_pending_time(
            pending_time=compute_pending_time
        )
        time_record = self.fetch_active_credit_clock_time_record(
            **kwargs
        )
        if not time_record or isinstance(time_record, dict) and \
                time_record.get('failed'):
            return self.error_could_not_fetch_active_time_record(kwargs)
        record_update_values = {
            'time_pending': compute_pending_time,
            'write_uid': kwargs.get('uid'),
        }
        update_record = self.update_credit_clock_time_sheet_record(
            record_update_values, time_record=time_record, **kwargs
        )
        if not update_record:
            self.warning_unsuccessful_credit_clock_time_sheet_record_update(
                kwargs
            )
        set_active = self.set_credit_clock_state(clock_state='active')
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'pending_time': self.fetch_credit_clock_pending_time(),
            'pause_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(
                    self.fetch_credit_clock_stop_time()
                )
            ),
            'resume_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(
                    self.fetch_active_time_record_start_time()
                )
            ),
            'pending_count': self.fetch_credit_clock_pending_count(),
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_pause_timer(self, **kwargs):
        '''
        [ RETURN ]: Pending Count or False.
        '''
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        check_clock_state = self.check_clock_state(
            check='state_is', state_is='active'
        )
        if not check_clock_state:
            return self.error_illegal_credit_clock_state(kwargs)
        set_end_time = self.set_credit_clock_time_stop(time_stop=time.time())
        fetch_pending_count = self.fetch_credit_clock_pending_count()
        increase_pending_count = self.set_credit_clock_pending_count(
            pending_count=(fetch_pending_count + 1)
        )
        fetch_active_time_record = self.fetch_active_credit_clock_time_record(
            **kwargs
        )
        if not fetch_active_time_record:
            return False
        record_update_values = {
            'pending_count': (fetch_pending_count + 1),
            'write_uid': kwargs.get('uid'),
        }
        update_record = self.update_credit_clock_time_sheet_record(
            record_update_values, time_record=fetch_active_time_record,
            **kwargs
        )
        if not update_record:
            self.warning_unsuccessful_credit_clock_time_sheet_record_update(
                kwargs
            )
        kwargs['active_session'].commit()
        set_pending = self.set_credit_clock_state(clock_state='pending')
        command_chain_response = {
            'pending_time': self.fetch_credit_clock_pending_time(),
            'start_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(
                    self.fetch_active_time_record_start_time()
                )
            ),
            'pause_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(
                    self.fetch_credit_clock_stop_time()
                )
            ),
        }
        command_chain_response.update(record_update_values)
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_start_timer(self, **kwargs):
        '''
        [ RETURN ]: Start Time or False
        '''
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        check_state = self.check_clock_state(
            check='state_is', state_is='inactive'
        )
        if not check_state:
            return self.warning_illegal_credit_clock_state(kwargs)
        set_state = self.set_credit_clock_state(clock_state='active')
        start_time = time.time()
        record_creation_values = self.fetch_time_sheet_record_creation_values(
            time_start=start_time, **kwargs
        )
        time_sheet_record = self.create_credit_clock_time_record(
            record_creation_values, **kwargs
        )
        start = self.set_credit_clock_time_start(
            time_start=float(record_creation_values['time_start'])
        )
        if not set_state or not start:
            return self.error_could_not_start_credit_clock_timer(kwargs)
        set_active = self.set_credit_clock_active_time_record(
            active_time_record=time_sheet_record
        )
        kwargs['active_session'].commit()
        log.info('Credit Clock timer started.')
        return record_creation_values['time_start']

    def action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_credit_clock_action_unlink_target_specified(kwargs)
        handlers = {
            'conversion': self.unlink_conversion,
            'time': self.unlink_time,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def action_switch_credit_clock_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_credit_clock_sheet_target_specified()
        handlers = {
            'time': self.switch_credit_clock_time_sheet,
            'conversion': self.switch_credit_clock_conversion_sheet,
        }
        return handlers[kwargs['sheet']](**kwargs)

    def action_interogate_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_credit_clock_interogation_target_specified()
        _handlers = {
                'credit_clock': self.interogate_credit_clock_time_left,
                'time_sheets': self.interogate_time_sheets,
                'time_records': self.interogate_time_sheet_records,
                'conversion_sheets': self.interogate_conversion_sheets,
                'conversion_records': self.interogate_conversion_sheet_records,
                }
        return _handlers[kwargs.get('target')](**kwargs)

    # CONTROLLERS

    def interogate_credit_clock_time_left(self, **kwargs):
        log.debug('')
        return self.fetch_credit_clock_time_left()

    # TODO
    def interogate_time_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_time_sheet_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_conversion_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_conversion_sheet_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')

    # CREATORS

    def create_credit_clock_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_type'):
            return self.error_no_credit_clock_sheet_target_specified()
        handlers = {
            'time': self.create_credit_clock_time_sheet,
            'conversion': self.create_credit_clock_conversion_sheet,
        }
        return handlers[kwargs['sheet_type']](**kwargs)

    def create_credit_clock_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_type'):
            return self.error_no_credit_clock_record_creation_target_specified()
        _handlers = {
                'time': self.create_credit_clock_time_record,
                'conversion': self.create_credit_clock_conversion_record,
                }
        return _handlers[kwargs['record_type']](**kwargs)

    # UNLINKERS

    def unlink_time_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_time_list_id_specified(kwargs)
        try:
            kwargs['active_session'].query(
                CreditClockTimeSheet
            ).filter_by(
                time_sheet_id=kwargs['list_id']
            ).delete()
        except:
            self.error_could_not_remove_time_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'time_sheet': kwargs['list_id'],
        }
        return command_chain_response

    def unlink_conversion_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_conversion_list_id_specified(kwargs)
        try:
            kwargs['active_session'].query(
                CreditClockConversionSheet
            ).filter_by(
                conversion_sheet_id=kwargs['list_id']
            ).delete()
        except:
            self.error_could_not_remove_conversion_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'conversion_sheet': kwargs['list_id'],
        }
        return command_chain_response

    def unlink_time_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_sheet_record_id_found(kwargs)
        time_sheet = self.fetch_credit_clock_time_sheet()
        if not time_sheet:
            return self.error_could_not_fetch_time_sheet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        unlink = time_sheet.credit_clock_time_sheet_controller(
            action='remove', **sanitized_command_chain
        )
        if not unlink or isinstance(unlink, dict) and unlink.get('failed'):
            return self.warning_could_not_unlink_credit_clock_time_sheet_record(kwargs)
        log.info('Successfully removed credit clock time record.')
        command_chain_response = {
            'failed': False,
            'time_sheet': time_sheet.fetch_time_sheet_id(),
            'time_record': kwargs['record_id'],
        }
        return command_chain_response

    def unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_credit_clock_unlink_time_target_specified(kwargs)
        handlers = {
            'list': self.unlink_time_list,
            'record': self.unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def unlink_conversion_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_sheet_record_id_found(kwargs)
        conversion_sheet = self.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet:
            return self.error_could_not_fetch_conversion_sheet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        unlink = conversion_sheet.credit_clock_conversion_sheet_controller(
            action='remove', **sanitized_command_chain
        )
        if not unlink or isinstance(unlink, dict) and unlink.get('failed'):
            return self.warning_could_not_unlink_credit_clock_conversion_sheet_record(kwargs)
        log.info('Successfully removed credit clock conversion record.')
        command_chain_response = {
            'failed': False,
            'conversion_sheet': conversion_sheet.fetch_conversion_sheet_id(),
            'conversion_record': kwargs['record_id'],
        }
        return command_chain_response

    def unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_credit_clock_unlink_conversion_target_specified(kwargs)
        handlers = {
            'list': self.unlink_conversion_list,
            'record': self.unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def unlink_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_credit_clock_unlink_target_specified()
        handlers = {
            'sheet': self.unlink_credit_clock_sheet,
            'record': self.unlink_credit_clock_record,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def unlink_credit_clock_time_sheet(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('sheet_id'):
            return self.error_no_time_sheet_id_found()
        _sheet = self.fetch_credit_clock_time_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        if not _sheet:
            return self.warning_could_not_fetch_time_sheet(
                    'id', kwargs['sheet_id']
                    )
        log.info('Successfully removed credit clock time sheet.')
        return self.time_sheet_archive.pop(kwargs['sheet_id'])

    def unlink_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('sheet_id'):
            return self.error_no_conversion_sheet_id_found()
        _sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        if not _sheet:
            return self.warning_could_not_fetch_conversion_sheet(
                    'id', kwargs['sheet_id']
                    )
        log.info('Successfully removed credit clock conversion sheet.')
        return self.conversion_sheet_archive.pop(kwargs['sheet_id'])

    def unlink_credit_clock_time_sheet_record(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('record_id'):
            return self.error_no_time_sheet_record_id_found()
        _unlink = self.time_sheet.credit_clock_time_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )
        if _unlink:
            log.info('Successfully removed credit clock time record.')
        return _unlink

    def unlink_credit_clock_conversion_sheet_record(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_sheet_record_id_found()
        _unlink = self.conversion_sheet.credit_clock_conversion_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )
        if _unlink:
            log.info('Successfully removed credit clock conversion record.')
        return False

    def unlink_credit_clock_sheet(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('sheet_type'):
            return self.error_no_credit_clock_sheet_unlink_target_specified()
        _handlers = {
                'time': self.unlink_credit_clock_time_sheet,
                'conversion': self.unlink_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet_type']](**kwargs)

    def unlink_credit_clock_record(self, **kwargs):
        log.debug('DEPRECATED')
        if not kwargs.get('record_type'):
            return self.error_no_credit_clock_record_unlink_target_specified()
        _handlers = {
                'time': self.unlink_credit_clock_time_sheet_record,
                'conversion': self.unlink_credit_clock_conversion_sheet_record,
                }
        return _handlers[kwargs['record_type']](**kwargs)

    def create_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('create'):
            return self.error_no_credit_clock_create_target_specified()
        _handlers = {
                'sheet': self.create_credit_clock_sheet,
                'record': self.create_credit_clock_record,
                }
        return _handlers[kwargs['create']](**kwargs)

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_controller_action_specified()
        _handlers = {
                'create': self.create_credit_clock,
                'extract': self.extract_credit_clock_minutes,
                'supply': self.supply_credit_clock_minutes,
                'convert': self.credit_converter,
                'unlink': self.unlink_credit_clock,
                }
        _handle = _handlers[kwargs.get('action')](**kwargs)
        if _handle:
            self.update_write_date()
        return _handle

    def user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_controller_action_specified()
        handlers = {
            'start': self.action_start_timer,
            'pause': self.action_pause_timer,
            'resume': self.action_resume_timer,
            'stop': self.action_stop_timer,
            'interogate': self.action_interogate_credit_clock,
            'switch_sheet': self.action_switch_credit_clock_sheet,
            'unlink': self.action_unlink,
        }
        handle = handlers[kwargs.get('action')](**kwargs)
        if handle and kwargs.get('action') != 'interogate':
            self.update_write_date()
        return handle

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_credit_clock_controller_type_specified()
        _handlers = {
                'system': self.system_controller,
                'user': self.user_controller,
                'test': self.test_credit_clock_regression,
                }
        _action_status = _handlers[kwargs.get('controller')](**kwargs)
        return _action_status

    # ERROR HANDLERS

    def error_handler_switch_credit_clock_conversion_sheet(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'identifier': kwargs.get('identifier'),
                    'code': kwargs.get('code'),
                    },
                'handlers': {
                    'identifier': self.error_no_conversion_sheet_identifier_found,
                    'code': self.error_no_conversion_sheet_code_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_switch_credit_clock_time_sheet(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'identifier': kwargs.get('identifier'),
                    'code': kwargs.get('code'),
                    },
                'handlers': {
                    'identifier': self.error_no_time_sheet_identifier_found,
                    'code': self.error_no_time_sheet_code_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    # ERRORS

    def error_no_credit_conversion_type_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit conversion type specified. '\
                     'active time record. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_time_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch credit clock. '\
                     'active time record. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_illegal_credit_clock_state(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Illegal credit clock state. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No active SqlAlchemy ORM session found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_start_credit_clock_timer(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not start credit clock timer. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_list_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No time list id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_time_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove time sheet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove conversion sheet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_list_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice list id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_sheet_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No time sheet record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_time_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch time sheet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_clock_unlink_time_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit clock unlink time target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch credit clock conversion sheet. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return False

    def error_no_conversion_sheet_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No conversion sheet record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return False

    def error_no_credit_clock_unlink_conversion_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit clock action unlink conversion target specified. Command chain details : {}'\
                     .format(command_chain),
            }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_clock_action_unlink_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit clock action unlink target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_clock_time_sheet(self, time_sheet):
        log.error('Could not set credit clock time sheet {}.'.format(time_sheet))
        return False

    def error_could_not_set_credit_clock_conversion_sheet(self, conversion_sheet):
        log.error('Could not set credit clock conversion sheet {}.'.format(conversion_sheet))
        return False

    def error_no_clock_state_check_type_specified(self):
        log.error('No clock state check type specified.')
        return False

    def error_clock_state_check_type_not_supported(self):
        log.error('Credit clock state check type not supported.')
        return False

    def error_no_pending_time_found(self):
        log.error('No pending time found.')
        return False

    def error_no_pending_count_found(self):
        log.error('No pending count found.')
        return False

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

    def error_no_credit_clock_state_found(self, **kwargs):
        log.error('No credit clock state found.')
        return False

    def error_no_ewallet_found(self):
        log.error('No ewallet found.')
        return False

    def error_no_credits_specified(self):
        log.error('No credits specified.')
        return False

    def error_no_credit_clock_controller_type_specified(self):
        log.error('No credit clock controller type specified.')
        return False

    def error_no_credit_clock_sheet_unlink_target_specified(self):
        log.error('No credit clock sheet unlink target specified.')
        return False

    def error_no_system_controller_action_specified(self):
        log.error('No system controller action specified.')
        return False

    def error_no_user_controller_action_specified(self):
        log.error('No user controller action specified.')
        return False

    def error_no_credit_clock_record_unlink_target_specified(self):
        log.error('No credit clock record unlink target specified.')
        return False

    def error_no_credit_clock_create_target_specified(self):
        log.error('No credit clock create target specified.')
        return False

    def error_no_credit_clock_unlink_target_specified(self):
        log.error('No credit clock unlink target specified.')
        return False

    def error_no_time_sheet_record_id_found(self):
        log.error('No time sheet record id found.')
        return False

    def error_no_credit_clock_record_creation_target_specified(self):
        log.error('No credit clock record creation target specified.')
        return False

    def error_no_time_sheet_id_found(self):
        log.error('No time sheet id found.')
        return False

    def error_no_conversion_sheet_id_found(self):
        log.error('No conversion sheet id found.')
        return False

    def error_no_credit_clock_interogation_target_specified(self):
        log.error('No credit clock interogation target specified.')
        return False

    def error_no_credit_clock_sheet_target_specified(self):
        log.error('No credit clock sheet target specified.')
        return False

    def error_no_credit_clock_conversion_sheet_found(self):
        log.error('No credit clock conversion sheet found.')
        return False

    def error_no_credit_clock_time_sheet_found(self):
        log.error('No credit clock time sheet found.')
        return False

    def error_no_minutes_found(self):
        log.error('No minutes found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_credit_clock_sheet_target_specified(self):
        log.error('No credit clock sheet target specified.')
        return False

    def error_no_time_sheet_identifier_found(self):
        log.error('No time sheet identifier found.')
        return False

    def error_no_time_sheet_code_found(self):
        log.error('No time sheet code found.')
        return False

    def error_no_conversion_sheet_identifier_found(self):
        log.error('No conversion sheet identifiers found.')
        return False

    def error_no_conversion_sheet_code_found(self):
        log.error('No conversion sheet code found.')
        return False

    def error_no_time_sheet_found(self):
        log.error('No time sheet found.')
        return False

    def error_no_conversion_sheet_found(self):
        log.error('No conversion sheet found.')
        return False

    def error_no_time_spent_found(self):
        log.error('No time spent found.')
        return False

    def error_no_start_time_found(self):
        log.error('No start time found.')
        return False

    def error_no_stop_time_found(self):
        log.error('No stop time found.')
        return False

    def error_no_credit_clock_reference_found(self):
        log.error('No credit clock reference found.')
        return False

    def error_no_credit_clock_write_date_found(self):
        log.error('No credit clock write date found.')
        return False

    def error_no_credit_clock_time_found(self):
        log.error('No credit clock time found.')
        return False

    def error_no_conversion_sheet_identifier_specified(self):
        log.error('No conversion sheet identifier specified.')
        return False

    def error_no_time_sheet_identifier_specified(self):
        log.error('No time sheet identifier specified.')
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_could_not_supply_credit_clock_with_minutes(self):
        log.error('Could not supply credit clock with minutes.')
        return False

    def error_could_not_extract_credit_clock_minutes(self):
        log.error('Could not extract credit clock minutes.')
        return False

    def error_no_state_found_for_credit_clock(self):
        log.error('No state found for credit clock.')
        return False

    def error_could_not_create_time_sheet_record(self):
        log.error('Could not create time sheet record.')
        return False

    def error_no_credit_clock_state_specified(self):
        log.error('No credit clock state specified.')
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

    def error_no_credit_clock_start_time_found(self):
        log.error('No credit clock start time found.')
        return False

    def error_no_credit_clock_stop_time_found(self):
        log.error('No credit clock stop time found.')
        return False

    def error_no_credit_clock_time_spent_found(self):
        log.error('No credit clock time spent found.')
        return False

    def error_could_not_set_active_time_record(self):
        log.error(
                'Something went wrong. '
                'Could not set credit clock active time record.'
                )
        return False

    def error_no_start_or_stop_time_found(self):
        log.error('No start or stop time found.')
        return False

    def error_could_not_fetch_active_time_record_start_time(self):
        log.error('Could not fetch active time record start time.')
        return False

    def error_recorded_start_time_wont_match_command_chain_value(self):
        log.error('Recorded start time wont match command chain value.')
        return False

    def error_could_not_compute_time_spent(self):
        log.error('Could not compute time spent.')
        return False

    def error_identical_start_and_stop_time(self):
        log.error('Identical start and stop time values.')
        return False

    def error_no_active_time_record_found(self):
        log.error('No active time record found.')
        return False

    def error_could_not_update_active_time_record_values(self):
        log.error('Could not update active time record values.')
        return False

    def error_inactive_time_record_state(self):
        log.error('Inactive time record state.')
        return False

    def error_invalid_field_for_credit_clock(self):
        log.error('Invald field for credit clock.')
        return False

    # WARNINGS

    def warning_could_not_fetch_active_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch credit clock active conversion sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_convert(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Conversion failure. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_unsuccessful_credit_clock_time_sheet_record_update(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Unsuccessful credit clock time sheet record update. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_illegal_credit_clock_state(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Illegal credit clock state. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_insufficient_time_to_convert(self, remainder, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Not enough time to convert. Conversion remainder {}. '\
                       'Instruction set details : {}'.format(remainder, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_clock_time_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit clock time sheet record. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_clock_conversion_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit clock conversion sheet record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_time_sheet_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch time sheet by id. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_conversion_sheet_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch conversion sheet by id. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_conversion_sheet_by_id_(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch conversion sheet by id. Command chain details {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_clear_credit_clock_field(self):
        log.warning('Could not clear credit clock field.')
        return False

    def warning_computed_time_spent_wont_match_command_chain_value(self):
        log.warning('Coputed time spent wont match command chain value.')
        return False

    def warning_invalid_credit_clock_state(self):
        log.warning('Invalid credit clock state.')
        return False

    def warning_could_not_fetch_time_sheet(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch time sheet by %s %s.', search_code, code
                )
        return False

    def warning_could_not_fetch_conversion_sheet(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch conversion sheet by %s %s.', search_code, code
                )
        return False

    # TESTS

    def test_interogation(self, **kwargs):
        print('[ TEST ]: Test interogation...')
        print('[ * ]: Credit clock')
        self.main_controller(controller='user', action='interogate', target='credit_clock')
        print('[ * ]: Time sheets')
        self.main_controller(controller='user', action='interogate', target='time_sheets')
        print('[ * ]: Time sheet records')
        self.main_controller(controller='user', action='interogate', target='time_records')
        print('[ * ]: Conversion sheets')
        self.main_controller(controller='user', action='interogate', target='conversion_sheets')
        print('[ * ]: Conversion sheet records')
        self.main_controller(controller='user', action='interogate', target='conversion_records')

    def test_user_action(self, **kwargs):
        print('[ TEST ]: User action...')
        self.main_controller(controller='user', action='start')
        time.sleep(3)
        self.main_controller(controller='user', action='stop')
        self.test_interogation(**kwargs)
        self.main_controller(
                controller='user', action='switch_sheet', sheet='time',
                identifier='id', code=self.time_sheet.fetch_time_sheet_id()
                )
        self.main_controller(
                controller='user', action='switch_sheet', sheet='conversion',
                identifier='id', code=self.conversion_sheet.fetch_conversion_sheet_id()
                )

    def test_system_action(self, **kwargs):
        self.main_controller(controller='system', action='supply', clock_credits=50)
        self.test_interogation(**kwargs)
        self.main_controller(controller='system', action='extract', clock_credits=25)
        self.test_interogation(**kwargs)
        self.main_controller(controller='system', action='convert', conversion='to_minutes', credits=13)
        self.test_interogation(**kwargs)
        self.main_controller(controller='system', action='convert', conversion='to_credits', minutes=35)
        self.test_interogation(**kwargs)

    def test_credit_clock_regression(self, **kwargs):
        self.test_user_action(**kwargs)
        self.test_system_action(**kwargs)




#clock = CreditClock(reference='First Credit Clock Ever', credit_clock=100)
#clock.main_controller(controller='test')

###############################################################################
# CODE DUMP
###############################################################################


