import time
import random
import datetime
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .time_sheet import CreditClockTimeSheet
from .conversion_sheet import CreditClockConversionSheet
from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class CreditClock(Base):
    __tablename__ = 'credit_clock'

    clock_id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('credit_ewallet.wallet_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    credit_clock = Column(Float)
    time_spent = Column(Float)
    start_time = Column(Float)
    end_time = Column(Float)
    # O2O
    wallet = relationship('CreditEWallet', back_populates='credit_clock')
    # O2O
    time_sheet = relationship('CreditClockTimeSheet', back_populates='clock')
    # O2O
    conversion_sheet = relationship(
       'CreditClockConversionSheet', back_populates='clock',
       )
    # O2M
    time_sheet_archive = relationship('CreditClockTimeSheet')
    # O2M
    conversion_sheet_archive = relationship('CreditClockConversionSheet')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_credit_id(self):
        log.debug('')
        return self.clock_id

    def fetch_credit_clock_reference(self):
        log.debug('')
        return self.reference

    def fetch_credit_clock_time_left(self):
        log.debug('')
        return self.credit_clock

    def fetch_credit_clock_time_sheet(self):
        log.debug('')
        return self.time_sheet

    def fetch_credit_clock_conversion_sheet(self):
        log.debug('')
        return self.conversion_sheet

    def fetch_credit_clock_values():
        log.debug('')
        _values = {
                'id': self.clock_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'credit_clock': self.credit_clock,
                'time_sheet': self.time_sheet,
                'time_sheet_archive': self.time_sheet_archive,
                }
        return _values

    def fetch_time_sheet_creation_values(self, **kwargs):
        _values = {
                'time_sheet_id': kwargs.get('time_sheet_id'),
                'clock_id': self.clock_id,
                'reference': kwargs.get('reference'),
                'records': kwargs.get('records'),
                }
        return _values

    def fetch_conversion_sheet_creation_values(self, **kwargs):
        _values = {
                'conversion_sheet_id': kwargs.get('conversion_sheet_id'),
                'clock_id': self.clock_id,
                'reference': kwargs.get('reference'),
                'records': kwargs.get('records'),
                }
        return _values

    def fetch_credit_clock_time_sheet_by_id(self, code):
        log.debug('')
        _time_sheet = self.time_sheet_archive.get(code)
        if not _time_sheet:
            return self.warning_could_not_fetch_time_sheet('id', code)
        log.info('Successfully fetched time sheet by id.')
        return _time_sheet

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

    def fetch_credit_clock_conversion_sheet_by_id(self, code):
        log.debug('')
        _conversion_sheet = self.conversion_sheet_archive.get(code)
        if not _conversion_sheet:
            return self.warning_could_not_fetch_conversion_sheet('id', code)
        log.info('Successfully fetched conversion sheet by id.')
        return _conversion_sheet

    def fetch_credit_clock_conversion_sheet_by_ref(self, code):
        log.debug('')
        for item in self.conversion_sheet_archive:
            if self.conversion_sheet_archive[item].reference == code:
                return self.conversion_sheet_archive[item]
        log.info('Successfully fethced conversion sheet by reference.')
        return self.warning_could_not_fetch_conversion_sheet('reference', code)

    def fetch_credit_clock_conversion_sheets(self, *args, **kwargs):
        log.debug('')
        return self.conversion_sheet_archive.values()

    def fetch_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_conversion_sheet_identifier_specified()
        _handlers = {
                'id': self.fetch_credit_clock_conversion_sheet_by_id,
                'reference': self.fetch_credit_clock_conversion_sheet_by_ref,
                'all': self.fetch_credit_clock_conversion_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_time_sheet_identifier_specified()
        _handlers = {
                'id': self.fetch_credit_clock_time_sheet_by_id,
                'reference': self.fetch_credit_clock_time_sheet_by_ref,
                'all': self.fetch_credit_clock_time_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

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

    def set_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_sheet'):
            return self.error_no_time_sheet_found()
        self.time_sheet = kwargs['time_sheet']
        return True

    def set_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_sheet'):
            return self.error_no_conversion_sheet_found()
        self.conversion_sheet = kwargs['conversion_sheet']
        return True

    def set_time_spent(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_spent'):
            return self.error_no_time_spent_found()
        self.time_spent = kwargs['time_spent']
        return True

    def set_start_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('start_time'):
            return self.error_no_start_time_found()
        self.start_time = kwargs['start_time']
        log.info('Credit Clock timer started.')
        return True

    def set_stop_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('stop_time'):
            return self.error_no_stop_time_found()
        self.stop_time = kwargs['stop_time']
        log.info('Credit Clock timer stoped.')
        return True

    def update_write_date(self):
        log.debug('')
        return self.set_credit_clock_write_date(
                write_date=datetime.datetime.now()
                )

    def update_time_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('time_sheet'):
            return self.error_no_time_sheet_found()
        self.time_sheet_archive.update({
            kwargs['time_sheet'].fetch_time_sheet_id(), kwargs['time_sheet']
            })
        log.info('Successfully updated credit clock time sheet archive.')
        return self.time_sheet_archive

    def update_conversion_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion_sheet'):
            return self.error_no_conversion_sheet_found()
        self.conversion_sheet_archive.update({
            kwargs['conversion_sheet'].fetch_conversion_sheet_id(),
            kwargs['conversion_sheet'],
            })
        log.info('Successfully updated credit clock conversion sheet archive.')
        return self.conversion_sheet_archive

    def handle_switch_credit_clock_time_sheet_by_id(self, code):
        log.debug('')
        _new_time_sheet = self.fetch_credit_clock_time_sheet(
                identifier='id', code=code
                )
        if not _new_time_sheet:
            return self.warning_could_not_fetch_time_sheet('id', code)
        self.set_time_sheet(time_sheet=_new_time_sheet)
        log.info('Successfully switched credit clock time sheet by id.')
        return _new_time_sheet

    def handle_switch_credit_clock_time_sheet_by_ref(self, code):
        log.debug('')
        _new_time_sheet = self.fetch_credit_clock_time_sheet(
                identifier='reference', code=code
                )
        if not _new_time_sheet:
            return self.warning_could_not_fetch_time_sheet('reference', code)
        self.set_time_sheet(time_sheet=_new_time_sheet)
        log.info('Successfully switched credit clock time sheet by reference.')
        return _new_time_sheet

    def handle_switch_credit_clock_conversion_sheet_by_id(self, code):
        log.debug('')
        _new_conversion_sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='id', code=code
                )
        if not _new_conversion_sheet:
            return self.warning_could_not_fetch_conversion_sheet('id', code)
        self.set_conversion_sheet(conversion_sheet=_new_conversion_sheet)
        log.info('Successfully switch credit clock conversion sheet by id.')
        return _new_conversion_sheet

    def handle_switch_credit_clock_conversion_sheet_by_ref(self, code):
        log.debug('')
        _new_conversion_sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='reference', code=code
                )
        if not _new_conversion_sheet:
            return self.warning_could_not_fetch_conversion_sheet('reference', code)
        self.set_conversion_sheet(conversion_sheet=_new_conversion_sheet)
        log.info('Successfully switched credit clock conversion sheet by reference.')
        return _new_conversion_sheet

    def switch_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return self.error_handler_switch_credit_clock_conversion_sheet(
                    identifier=kwargs.get('identifier'),
                    code=kwargs.get('code'),
                    )
        _handlers = {
                'id': self.handle_switch_credit_clock_conversion_sheet_by_id,
                'reference': self.handle_switch_credit_clock_conversion_sheet_by_ref,
                }
        _handle = _handlers[kwargs['identifier']](kwargs.get('code'))
        return _handle

    def switch_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return self.error_handler_switch_credit_clock_time_sheet(
                    identifier=kwargs.get('identifier'),
                    code=kwargs.get('code'),
                    )
        _handlers = {
                'id': self.handle_switch_credit_clock_time_sheet_by_id,
                'reference': self.handle_switch_credit_clock_time_sheet_by_ref,
                }
        _handle = _handlers[kwargs.get('identifier')](kwargs.get('code'))
        return _handle

    def switch_credit_clock_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_credit_clock_sheet_target_specified()
        _handlers = {
                    'time': self.switch_credit_clock_time_sheet,
                    'conversion': self.switch_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def create_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
        _values = self.fetch_time_sheet_creation_values(**kwargs)
        _time_sheet = CreditClockTimeSheet(**_values)
        self.update_time_sheet_archive(
                time_sheet=_time_sheet
                )
        log.info('Successfully created new credit clock time sheet.')
        return _time_sheet

    def create_credit_clock_time_record(self, **kwargs):
        log.debug('')
        if not self.time_sheet:
            return self.error_no_credit_clock_time_sheet_found()
        _record = self.time_sheet.credit_clock_time_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                time_spent=kwargs.get('time_spent'),
                credit_clock=self.credit_clock
                )
        if _record:
            log.info('Successfully created new credit clock time record.')
        return _record or False

    def create_credit_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        _values = self.fetch_conversion_sheet_creation_values(**kwargs)
        _conversion_sheet = CreditClockConversionSheet(**_values)
        self.update_conversion_sheet_archive(
                conversion_sheet=_conversion_sheet
                )
        log.info('Successfully created new credit clock conversion sheet.')
        return _conversion_sheet

    def create_credit_clock_conversion_record(self, **kwargs):
        log.debug('')
        if not self.conversion_sheet:
            return self.error_no_credit_clock_conversion_sheet_found()
        _record = self.conversion_sheet.credit_clock_conversion_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                conversion_type=kwargs.get('conversion_type'),
                minutes=kwargs.get('minutes'), credits=kwargs.get('credits')
                )
        if _records:
            log.info('Successfully created new credit clock conversion record.')
        return _record or False

    def reset_timer(self):
        log.debug('')
        self.start_time = False
        self.end_time = False
        log.info('Credit Clock timer reset.')
        return True

    def convert_time_to_minutes(self, start_time, end_time):
        log.debug('')
        _seconds_spent = round((end_time - start_time), 2)
        _minutes_spent = round((_seconds_spent / 60), 2)
        return _minutes_spent

    def compute_time(self, **kwargs):
        log.debug('')
        self.time_spent = self.convert_time_to_minutes(self.start_time, self.end_time)
        self.system_controller(action='extract', clock_credits=self.time_spent)
        self.reset_timer()
        return self.credit_clock

    # TODO - Refactor
    def display_credit_clock(self, **kwargs):
        log.debug('')
        print('Credit Clock: {} min'.format(self.credit_clock))
        return self.credit_clock

    # TODO - Refactor
    def display_time_sheets(self, **kwargs):
        log.debug('')
        print('Credit Clock {} Time Sheets:'.format(self.reference))
        for k, v in self.time_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_time_sheet_create_date(), k, v.fetch_time_sheet_reference())
                )
        return self.time_sheet_archive

    # TODO - Refactor
    def display_time_sheet_records(self, **kwargs):
        log.debug('')
        _time_sheet_records = self.time_sheet.display_time_sheet_records()
        return _time_sheet_records

    # TODO - Refactor
    def display_conversion_sheets(self, **kwargs):
        log.debug('')
        print('Credit CLock {} Conversion Sheets:'.format(self.reference))
        for k, v in self.conversion_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_conversion_sheet_create_date(), k, v.fetch_conversion_sheet_reference())
                )
        return self.conversion_sheet_archive

    # TODO - Refactor
    def display_conversion_sheet_records(self, **kwargs):
        log.debug('')
        _conversion_sheet_records = self.conversion_sheet.display_conversion_sheet_records()
        return _conversion_sheet_records

    def start_timer(self, **kwargs):
        log.debug('')
        self.start_time = time.time()
        log.info('Credit Clock timer started.')
        return self.start_time

    def stop_timer(self, **kwargs):
        log.debug('')
        self.end_time = time.time()
        self.compute_time()
        self.create_credit_clock_time_record(self.time_sheet)
        self.time_sheet.update_write_date()
        log.info('Credit Clock timer stoped.')
        return self.end_time

    def extract_credit_clock_minutes(self, **kwargs):
        log.debug('')
        self.credit_clock = round((self.credit_clock - kwargs.get('clock_credits')), 2)
        log.info('Successfully extracted credit clock minutes.')
        return self.credit_clock

    def supply_credit_clock_minutes(self, **kwargs):
        log.debug('')
        self.credit_clock = round((self.credit_clock + kwargs.get('clock_credits')), 2)
        log.info('Successfully supplied credit clock minutes.')
        return self.credit_clock

    # TODO - Refactor
    def convert_minutes_to_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        if (self.credit_clock - kwargs['minutes']) < 0:
            _remainder = abs(self.credit_clock - kwargs['minutes'])
            self.extract_credit_clock_minutes(
                    clock_credits=(self.credit_clock - kwargs['minutes'] + _remainder)
                    )
            log.info('Not enough minutes to convert to credits. Converted remainder.')
            return _remainder
        _extract = self.extract_credit_clock_minutes(
                clock_credits=kwargs['minutes']
                )
        _supply = self.supply_ewallet_credits(
                ewallet=kwargs['ewallet'],
                credits=kwargs['minutes'],
                )
        log.info('Successfully converted minutes to credits.')
        return _extract






    def error_no_ewallet_found(self):
        log.error('No ewallet found.')
        return False

    def error_no_credits_specified(self):
        log.error('No credits specified.')
        return False

    def supply_ewallet_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet'):
            return self.error_no_ewallet_found()
        if not kwargs.get('credits'):
            return self.error_no_credits_specified()
        return kwargs['ewallet'].supply_credits(credits=kwargs['credits'])

    def extract_ewallet_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet'):
            return self.error_no_ewallet_found()
        if not kwargs.get('credits'):
            return self.error_no_credits_specified()
        return kwargs['ewallet'].extract_credits(credits=kwargs['credits'])

    def convert_credits_to_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('wallet'):
            return self.error_no_credits_found()
        _supply = self.supply_credit_clock_minutes(
                clock_credits=kwargs['credits']
                )
        _extract = self.extract_ewallet_credits(
                credits=kwargs['credits'],
                ewallet=kwargs['ewallet'],
                )
        log.info('Successfully converted credits to minutes.')
        return _supply

    def credit_converter(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_credit_conversion_type_specified()
        _handlers = {
                'to_minutes': self.convert_credits_to_minutes,
                'to_credits': self.convert_minutes_to_credits,
                }
        self.create_credit_clock_conversion_record(self.conversion_sheet)
        return _handlers[kwargs['conversion']](**kwargs)

    def interogate_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_credit_clock_interogation_target_specified()
        _handlers = {
                'credit_clock': self.display_credit_clock,
                'time_sheets': self.display_time_sheets,
                'time_records': self.display_time_sheet_records,
                'conversion_sheets': self.display_conversion_sheets,
                'conversion_records': self.display_conversion_sheet_records,
                }
        return _handlers[kwargs.get('target')](**kwargs)

    def create_credit_clock_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_type'):
            return self.error_no_credit_clock_sheet_target_specified()
        _handlers = {
                'time': self.create_credit_clock_time_sheet,
                'conversion': self.create_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet_type']](**kwargs)

    def create_credit_clock_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_type'):
            return self.error_no_credit_clock_record_creation_target_specified()
        _handlers = {
                'time': self.create_credit_clock_time_record,
                'conversion': self.create_credit_clock_conversion_record,
                }
        return _handlers[kwargs['record_type']](**kwargs)

    def unlink_credit_clock_time_sheet(self, **kwargs):
        log.debug('')
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
        log.debug('')
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
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_sheet_record_id_found()
        _unlink = self.time_sheet.credit_clock_time_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )
        if _unlink:
            log.info('Successfully removed credit clock time record.')
        return _unlink

    def unlink_credit_clock_conversion_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_sheet_record_id_found()
        _unlink = self.conversion_sheet.credit_clock_conversion_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )
        if _unlink:
            log.info('Successfully removed credit clock conversion record.')
        return False

    def unlink_credit_clock_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_type'):
            return self.error_no_credit_clock_sheet_unlink_target_specified()
        _handlers = {
                'time': self.unlink_credit_clock_time_sheet,
                'conversion': self.unlink_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet_type']](**kwargs)

    def unlink_credit_clock_record(self, **kwargs):
        log.debug('')
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

    def unlink_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_credit_clock_unlink_target_specified()
        _handlers = {
                'sheet': self.unlink_credit_clock_sheet,
                'record': self.unlink_credit_clock_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

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
        _handlers = {
                'start': self.start_timer,
                'stop': self.stop_timer,
                'interogate': self.interogate_credit_clock,
                'switch_sheet': self.switch_credit_clock_sheet,
                }
        _handle = _handlers[kwargs.get('action')](**kwargs)
        if _handle and kwargs.get('action') != 'interogate':
            self.update_write_date()
        return _handle

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

    def error_no_conversion_sheet_record_id_found(self):
        log.error('No conversion sheet record id found.')
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

    def error_no_credit_conversion_type_specified(self):
        log.error('No credit conversion type specified.')
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

#   time_sheet_id = Column(
#      Integer, ForeignKey('credit_clock_time_sheet.time_sheet_id')
#      )
#   conversion_sheet_id = Column(
#      Integer, ForeignKey('credit_clock_conversion_sheet.conversion_sheet_id')
#      )

