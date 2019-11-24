import time
import random
import datetime
import pysnooper

from .time_sheet import CreditClockTimeSheet
from .conversion_sheet import CreditClockConversionSheet


# TODO - Create conversion sheet from controller
# TODO - Create time sheet from controller
class CreditClock():

    # TODO - Refactor - Has dummy data
    def __init__(self, **kwargs):
        self.clock_id = random.randint(10, 20)
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.credit_clock = kwargs.get('credit_clock')
        self.time_sheet = CreditClockTimeSheet(
                reference='First Clock Time Sheet', clock_id=self.clock_id
                )
        self.time_sheet_archive = {
                self.time_sheet.fetch_time_sheet_id(): self.time_sheet
                }
        self.conversion_sheet = CreditClockConversionSheet(
                reference='First Clock Conversion Sheet', clock_id=self.clock_id
                )
        self.conversion_sheet_archive = {
                self.conversion_sheet.fetch_conversion_sheet_id(): self.conversion_sheet
                }
        self.time_spent = False
        self.start_time = False
        self.end_time = False

    def fetch_credit_clock_id(self):
        return self.clock_id

    def fetch_credit_clock_reference(self):
        return self.reference

    def fetch_credit_clock_time_left(self):
        return self.credit_clock

    def fetch_credit_clock_time_sheet(self):
        return self.time_sheet

    def fetch_credit_clock_conversion_sheet(self):
        return self.conversion_sheet

    def fetch_credit_clock_values():
        _values = {
                'id': self.clock_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'credit_clock': self.credit_clock,
                'time_sheet': self.time_sheet,
                'time_sheet_archive': self.time_sheet_archive,
                }
        return _values

    def fetch_credit_clock_time_sheet_by_id(self, code):
        _time_sheet = self.time_sheet_archive.get(code)
        return _time_sheet or False

    def fetch_credit_clock_time_sheet_by_ref(self, code):
        for item in self.time_sheet_archive:
            if self.time_sheet_archive[item].reference == code:
                return self.time_sheet_archive[item]
        return False

    def fetch_credit_clock_time_sheets(self, *args, **kwargs):
        return self.time_sheet_archive.values()

    def fetch_credit_clock_conversion_sheet_by_id(self, code):
        _conversion_sheet = self.conversion_sheet_archive.get(code)
        return _conversion_sheet

    def fetch_credit_clock_conversion_sheet_by_ref(self, code):
        for item in self.conversion_sheet_archive:
            if self.conversion_sheet_archive[item].reference == code:
                return self.conversion_sheet_archive[item]
        return False

    def fetch_credit_clock_conversion_sheets(self, *args, **kwargs):
        return self.conversion_sheet_archive.values()

    def fetch_credit_clock_conversion_sheet(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_credit_clock_conversion_sheet_by_id,
                'reference': self.fetch_credit_clock_conversion_sheet_by_ref,
                'all': self.fetch_credit_clock_conversion_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_clock_time_sheet(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_credit_clock_time_sheet_by_id,
                'reference': self.fetch_credit_clock_time_sheet_by_ref,
                'all': self.fetch_credit_clock_time_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def set_credit_clock_wallet_id(self, **kwargs):
        global wallet_id
        if not kwargs.get('wallet_id'):
            return False
        self.wallet_id = kwargs['wallet_id']
        return True

    def set_credit_clock_reference(self, **kwargs):
        global reference
        if not kwargs.get('reference'):
            return False
        self.reference = kwargs['reference']
        return True

    def set_credit_clock_write_date(self, **kwargs):
        global write_date
        if not kwargs.get('write_date'):
            return False
        self.write_date = kwargs['write_date']
        return True

    def set_credit_clock(self, **kwargs):
        global credit_clock
        if not kwargs.get('credit_clock'):
            return False
        self.credit_clock = kwargs['credit_clock']
        return True

    def set_time_sheet(self, **kwargs):
        global time_sheet
        if not kwargs.get('time_sheet'):
            return False
        self.time_sheet = kwargs['time_sheet']
        return True

    def set_conversion_sheet(self, **kwargs):
        global conversion_sheet
        if not kwargs.get('conversion_sheet'):
            return False
        self.conversion_sheet = kwargs['conversion_sheet']
        return True

    def set_time_spent(self, **kwargs):
        global time_spent
        if not kwargs.get('time_spend'):
            return False
        self.time_spent = kwargs['time_spent']
        return True

    def set_start_time(self, **kwargs):
        global start_time
        if not kwargs.get('start_time'):
            return False
        self.start_time = kwargs['start_time']
        return True

    def set_stop_time(self, **kwargs):
        global stop_time
        if not kwargs.get('stop_time'):
            return False
        self.stop_time = kwargs['stop_time']
        return True

    def update_write_date(self):
        return self.set_credit_clock_write_date(
                write_date=datetime.datetime.now()
                )

    def update_time_sheet_archive(self, **kwargs):
        global time_sheet_archive
        if not kwargs.get('time_sheet'):
            return False
        self.time_sheet_archive.update({
            kwargs['time_sheet'].fetch_time_sheet_id(), kwargs['time_sheet']
            })
        return self.time_sheet_archive

    def update_conversion_sheet_archive(self, **kwargs):
        global conversion_sheet_archive
        if not kwargs.get('conversion_sheet'):
            return False
        self.conversion_sheet_archive.update({
            kwargs['conversion_sheet'].fetch_conversion_sheet_id(),
            kwargs['conversion_sheet'],
            })
        return self.conversion_sheet_archive

    def handle_switch_credit_clock_time_sheet_by_id(self, code):
        global time_sheet
        _new_time_sheet = self.fetch_credit_clock_time_sheet(
                identifier='id', code=code
                )
        self.set_time_sheet(time_sheet=_new_time_sheet)
        return _new_time_sheet

    def handle_switch_credit_clock_time_sheet_by_ref(self, code):
        global time_sheet
        _new_time_sheet = self.fetch_credit_clock_time_sheet(
                identifier='reference', code=code
                )
        self.set_time_sheet(time_sheet=_new_time_sheet)
        return _new_time_sheet

    def handle_switch_credit_clock_conversion_sheet_by_id(self, code):
        global conversion_sheet
        _new_conversion_sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='id', code=code
                )
        self.set_conversion_sheet(conversion_sheet=_new_conversion_sheet)
        return _new_conversion_sheet

    def handle_switch_credit_clock_conversion_sheet_by_ref(self, code):
        global conversion_sheet
        _new_conversion_sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='reference', code=code
                )
        self.set_conversion_sheet(conversion_sheet=_new_conversion_sheet)
        return _new_conversion_sheet

    def switch_credit_clock_conversion_sheet(self, **kwargs):
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return False
        _handlers = {
                'id': self.handle_switch_credit_clock_conversion_sheet_by_id,
                'reference': self.handle_switch_credit_clock_conversion_sheet_by_ref,
                }
        _handle = _handlers[kwargs['identifier']](kwargs.get('code'))
        return _handle

    def switch_credit_clock_time_sheet(self, **kwargs):
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return False
        _handlers = {
                'id': self.handle_switch_credit_clock_time_sheet_by_id,
                'reference': self.handle_switch_credit_clock_time_sheet_by_ref,
                }
        _handle = _handlers[kwargs.get('identifier')](kwargs.get('code'))
        return _handle

    def switch_credit_clock_sheet(self, **kwargs):
        if not kwargs.get('sheet'):
            return False
        _handlers = {
                    'time': self.switch_credit_clock_time_sheet,
                    'conversion': self.switch_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def create_credit_clock_time_sheet(self, **kwargs):
        _time_sheet = CreditClockTimeSheet(
                    clock_id=self.clock_id,
                    reference=kwargs.get('reference'),
                )
        self.update_time_sheet_archive(
                time_sheet=_time_sheet
                )
        return _time_sheet

    # TODO - Has dummy data
    def create_credit_clock_conversion_sheet(self, **kwargs):
        _conversion_sheet = CreditClockConversionSheet(
                clock_id=self.clock_id,
                reference=kwargs.get('reference'),
                )
        self.update_conversion_sheet_archive(
                conversion_sheet=_conversion_sheet
                )
        return _conversion_sheet

    # TODO - Has dummy data
    def fetch_credit_clock_time_record_create_values(self):
        _values = {
                'reference': 'Test Time Sheet Record Reference',
                'credit_clock': self.credit_clock,
                'time_spent': self.time_spent,
            }
        return _values

    # TODO - Has dummy data
    def fetch_credit_clock_conversion_record_create_values(self):
        _values = {
                'reference': 'Test Conversion Sheet Record Reference',
                'conversion_type': 'to_minutes',
                'minutes': 4,
                'credits': 4,
                }
        return _values

    def reset_timer(self):
#       global time_spent
        global start_time
        global end_time
#       self.time_spent = False
        self.start_time = False
        self.end_time = False

    def convert_time_to_minutes(self, start_time, end_time):
        _seconds_spent = round((end_time - start_time), 2)
        _minutes_spent = round((_seconds_spent / 60), 2)
        return _minutes_spent

    def compute_time(self, **kwargs):
        global time_spent
        global credit_clock
        self.time_spent = self.convert_time_to_minutes(self.start_time, self.end_time)
        self.system_controller(action='extract', clock_credits=self.time_spent)
        self.reset_timer()
        return self.credit_clock

    def display_credit_clock(self, **kwargs):
        print('Credit Clock: {} min'.format(self.credit_clock))
        return self.credit_clock

    def display_time_sheets(self, **kwargs):
        print('Credit Clock {} Time Sheets:'.format(self.reference))
        for k, v in self.time_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_time_sheet_create_date(), k, v.fetch_time_sheet_reference())
                )
        return self.time_sheet_archive

    def display_time_sheet_records(self, **kwargs):
        _time_sheet_records = self.time_sheet.display_time_sheet_records()
        return _time_sheet_records

    def display_conversion_sheets(self, **kwargs):
        print('Credit CLock {} Conversion Sheets:'.format(self.reference))
        for k, v in self.conversion_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_conversion_sheet_create_date(), k, v.fetch_conversion_sheet_reference())
                )
        return self.conversion_sheet_archive

    def display_conversion_sheet_records(self, **kwargs):
        _conversion_sheet_records = self.conversion_sheet.display_conversion_sheet_records()
        return _conversion_sheet_records

    def start_timer(self, **kwargs):
        global start_time
        self.start_time = time.time()
        return self.start_time

    def stop_timer(self, **kwargs):
        global end_time
        self.end_time = time.time()
        self.compute_time()
        self.add_credit_clock_time_record(self.time_sheet)
        self.time_sheet.update_write_date()
        return self.end_time

    def extract_credit_clock_minutes(self, **kwargs):
        global credit_clock
        self.credit_clock = round((self.credit_clock - kwargs.get('clock_credits')), 2)
        return self.credit_clock

    def supply_credit_clock_minutes(self, **kwargs):
        global credit_clock
        self.credit_clock = round((self.credit_clock + kwargs.get('clock_credits')), 2)
        return self.credit_clock

    # TODO - Refactor
    def convert_minutes_to_credits(self, **kwargs):
        if not kwargs.get('minutes'):
            return False
        if (self.credit_clock - kwargs['minutes']) < 0:
            _remainder = abs(self.credit_clock - kwargs['minutes'])
            self.extract_credit_clock_minutes(
                    clock_credits=(self.credit_clock - kwargs['minutes'] + _remainder)
                    )
            return _remainder
        _extract = self.extract_credit_clock_minutes(
                clock_credits=kwargs['minutes']
                )
        return _extract

    def convert_credits_to_minutes(self, **kwargs):
        if not kwargs.get('credits'):
            return False
        _supply = self.supply_credit_clock_minutes(
                clock_credits=kwargs['credits']
                )
        return _supply

    def credit_converter(self, **kwargs):
        if not kwargs.get('conversion'):
            return False
        _handlers = {
                'to_minutes': self.convert_credits_to_minutes,
                'to_credits': self.convert_minutes_to_credits,
                }
        self.add_credit_clock_conversion_record(self.conversion_sheet)
        return _handlers[kwargs['conversion']](**kwargs)

    def interogate_credit_clock(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'credit_clock': self.display_credit_clock,
                'time_sheets': self.display_time_sheets,
                'time_records': self.display_time_sheet_records,
                'conversion_sheets': self.display_conversion_sheets,
                'conversion_records': self.display_conversion_sheet_records,
                }
        return _handlers[kwargs.get('target')](**kwargs)

    def create_credit_clock_sheet(self, **kwargs):
        if not kwargs.get('sheet_type'):
            return False
        _handlers = {
                'time': self.create_credit_clock_time_sheet,
                'conversion': self.create_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet_type']](**kwargs)

    def create_credit_clock_conversion_record(self, **kwargs):
        if not self.conversion_sheet:
            return False
        _record = self.conversion_sheet.credit_clock_conversion_sheet_controller(
                action='add',
                )

    def create_credit_clock_time_record(self, **kwargs):
        if not self.time_sheet:
            return False
        _record = self.time_sheet.credit_clock_time_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                time_spent=kwargs.get('time_spent')
                )
        return _record or False

    def create_credit_clock_record(self, **kwargs):
        if not kwargs.get('record_type'):
            return False
        _handlers = {
                'time': self.create_credit_clock_time_record,
                'conversion': self.create_credit_clock_conversion_record,
                }
        return _handlers[kwargs['record_type']](**kwargs)

    def unlink_credit_clock_time_sheet(self, **kwargs):
        global time_sheet_archive
        if not kwargs.get('sheet_id'):
            return False
        _sheet = self.fetch_credit_clock_time_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        return False if not _sheet \
                else self.time_sheet_archive.pop(kwargs['sheet_id'])

    def unlink_credit_clock_conversion_sheet(self, **kwargs):
        global conversion_sheet_archive
        if not kwargs.get('sheet_id'):
            return False
        _sheet = self.fetch_credit_clock_conversion_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        return False if not _sheet \
                else self.conversion_sheet_archive.pop(kwargs['sheet_id'])

    def unlink_credit_clock_time_sheet_record(self, **kwargs):
        if not kwargs.get('record_id'):
            return False
        return self.time_sheet.credit_clock_time_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )

    def unlink_credit_clock_conversion_sheet_record(self, **kwargs):
        if not kwargs.get('record_id'):
            return False
        return self.conversion_sheet.credit_clock_conversion_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )

    def unlink_credit_clock_sheet(self, **kwargs):
        if not kwargs.get('sheet_type'):
            return False
        _handlers = {
                'time': self.unlink_credit_clock_time_sheet,
                'conversion': self.unlink_credit_clock_conversion_sheet,
                }
        return _handlers[kwargs['sheet_type']](**kwargs)

    def unlink_credit_clock_record(self, **kwargs):
        if not kwargs.get('record_type'):
            return False
        _handlers = {
                'time': self.unlink_credit_clock_time_sheet_record,
                'conversion': self.unlink_credit_clock_conversion_sheet_record,
                }
        return _handlers[kwargs['record_type']](**kwargs)


    def create_credit_clock(self, **kwargs):
        if not kwargs.get('create'):
            return False
        _handlers = {
                'sheet': self.create_credit_clock_sheet,
                'record': self.create_credit_clock_record,
                }
        return _handlers[kwargs['create']](**kwargs)

    def unlink_credit_clock(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'sheet': self.unlink_credit_clock_sheet,
                'record': self.unlink_credit_clock_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def system_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
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
        if not kwargs.get('action'):
            return False
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
        if not kwargs.get('controller'):
            return False
        _handlers = {
                'system': self.system_controller,
                'user': self.user_controller,
                'test': self.test_credit_clock_regression,
                }
        _action_status = _handlers[kwargs.get('controller')](**kwargs)
        return _action_status

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


