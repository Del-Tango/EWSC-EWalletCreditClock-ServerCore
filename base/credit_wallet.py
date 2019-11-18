import time
import datetime
import random
import pysnooper

from .credit_clock import CreditClock
from .record_sheets.transfer_sheet import CreditTransferSheet
from .record_sheets.invoice_sheet import CreditInvoiceSheet


class CreditEWallet():

    # TODO - Has dummy data
#   @pysnooper.snoop()
    def __init__(self, **kwargs):
        self.wallet_id = random.randint(10,20)
        self.client_id = kwargs.get('client_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.credits = kwargs.get('credits') or 0
        self.credit_clock = CreditClock(
                wallet_id=self.wallet_id,
                reference='First Credit Clock Reference',
                credit_clock=0.0
                )
        self.credit_clock_archive = {
                self.credit_clock.fetch_credit_clock_id(), self.credit_clock
                }
        self.transfer_sheet = CreditTransferSheet(
                wallet_id=self.wallet_id,
                reference='First Transfer Sheet Reference'
                )
        self.transfer_sheet_archive = {
                self.transfer_sheet.fetch_transfer_sheet_id(): self.transfer_sheet
                }
        self.invoice_sheet = CreditInvoiceSheet(
                wallet_id=self.wallet_id,
                reference='First Credit Invoice Sheet',
                )
        self.invoice_sheet_archive = {
                self.invoice_sheet.fetch_invoice_sheet_id(): self.invoice_sheet
                }
        self.session_key = random.randint(10000,999999)

    def fetch_credit_ewallet_id(self):
        return self.wallet_id

    def fetch_credit_ewallet_reference(self):
        return self.reference

    def fetch_credit_ewallet_session_key(self):
        return self.session_key

    def fetch_credit_ewallet_client_id(self):
        return self.client_id

    def fetch_credit_ewallet_create_date(self):
        return self.create_date

    def fetch_credit_ewallet_credits(self):
        return self.credits

    def fetch_credit_ewallet_credit_clock(self):
        return self.credit_clock

    def fetch_credit_ewallet_transfer_sheet(self):
        return self.transfer_sheet

#   @pysnooper.snoop()
    def fetch_credit_ewallet_values(self):
        _values = {
                'id': self.wallet_id,
                'client_id': self.client_id,
                'reference': self.reference,
                'session_key': self.session_key,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'credits': self.credits,
                'credit_clock': self.credit_clock,
                'credit_clock_archive': self.credit_clock_archive,
                'transfer_sheet': self.transfer_sheet,
                'transfer_sheet_archive': self.transfer_sheet_archive,
                }
        return _values

    def fetch_credit_wallet_transfer_sheet_by_id(self, code):
        _transfer_sheet = self.transfer_sheet_archive.get(code)
        return _transfer_sheet

    def fetch_credit_wallet_transfer_sheet_by_ref(self, code):
        for item in self.transfer_sheet_archive:
            if self.transfer_sheet_archive[item].reference == code:
                return self.transfer_sheet_archive[item]
        return False

    def fetch_credit_wallet_transfer_sheets(self, **kwargs):
        return self.transfer_sheet_archive.values()

    def fetch_credit_wallet_invoice_sheet_by_id(self, code):
        _invoice_sheet = self.invoice_sheet_archive.get(code)
        return _invoice_sheet

    def fetch_credit_wallet_invoice_sheet_by_ref(self, code):
        for item in self.invoice_sheet_archive:
            if self.invoice_sheet_archive[item].reference == code:
                return self.invoice_sheet_archive[item]
        return False

    def fetch_credit_wallet_invoice_sheets(self, **kwargs):
        return self.invoice_sheet_archive.values()

    def fetch_credit_wallet_transfer_sheet(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_credit_wallet_transfer_sheet_by_id,
                'reference': self.fetch_credit_wallet_transfer_sheet_by_ref,
                'all': self.fetch_credit_wallet_transfer_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_wallet_invoice_sheet(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_credit_wallet_invoice_sheet_by_id,
                'reference': self.fetch_credit_wallet_invoice_sheet_by_ref,
                'all': self.fetch_credit_wallet_invoice_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    # TODO - Has dummy data
    def fetch_invoice_sheet_record_values(self, **kwargs):
        _values = {
                'reference': kwargs.get('reference') or 'Test invoice sheet record reference',
                'credits': kwargs['credits'],
                'cost': kwargs.get('cost') or 1.5,
                'currency': kwargs.get('currency') or 'RON',
                'seller_id': kwargs['seller_id'],
                'notes': kwargs.get('notes') or 'Test invoice sheet record notes',
                }
        return _values

    # TODO - Has dummy data
    def fetch_transfer_sheet_record_values(self, **kwargs):
        _values = {
                'reference': kwargs.get('reference') or 'Test transfer sheet record reference',
                'transfer_type': kwargs.get('transfer_type'),
                'transfer_from': kwargs.get('transfer_from') or self.client_id,
                'transfer_to': kwargs['used_on'],
                'credits': kwargs['credits'],
                }
        return _values

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date

    def update_session_key(self):
        global session_key
        self.session_key = random.randint(10000,999999)
        return self.session_key

    def handle_switch_credit_wallet_transfer_sheet_by_ref(self, code):
        global transfer_sheet
        _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
                identifier='reference', code=code
                )
        self.transfer_sheet = _new_transfer_sheet
        return _new_transfer_sheet

    def handle_switch_credit_wallet_transfer_sheet_by_id(self, code):
        global transfer_sheet
        _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
                identifier='id', code=code
                )
        self.transfer_sheet = _new_transfer_sheet
        return _new_transfer_sheet

    def handle_switch_credit_wallet_invoice_sheet_by_ref(self, code):
        global invoice_sheet
        _new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet(
                identifier='ref', code=code
                )
        self.invoice_sheet = _new_invoice_sheet
        return _new_invoice_sheet

    def handle_switch_credit_wallet_invoice_sheet_by_id(self, code):
        global invoice_sheet
        _new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet(
                identifier='id', code=code
                )
        self.invoice_sheet = _new_invoice_sheet
        return _new_invoice_sheet

    def supply_credits(self, **kwargs):
        if not kwargs.get('credits'):
            return False
        global credits
        self.credits += kwargs['credits']
        return self.credits

    def extract_credits(self, **kwargs):
        if not kwargs.get('credits'):
            return False
        global credits
        self.credits -= kwargs['credits']
        return self.credits

    def convert_credits_to_minutes(self, **kwargs):
        if not kwargs.get('credits'):
            return False
        _credit_clock = self.credit_clock
        _convert = _credit_clock.system_controller(
                action='convert', conversion='to_minutes',
                credits=kwargs['credits']
                )
        _credit_clock.update_write_date()
        self.system_controller(action='extract', credits=kwargs['credits'])
        return _convert

    def convert_minutes_to_credits(self, **kwargs):
        if not kwargs.get('minutes'):
            return False
        _credit_clock = self.credit_clock
        _convert = _credit_clock.system_controller(
                action='convert', conversion='to_credits',
                minutes=kwargs['minutes']
                )
        self.update_write_date()
        self.system_controller(action='supply', credits=kwargs['minutes'])
        return _convert

    def convert_credits(self, **kwargs):
        if not kwargs.get('conversion'):
            return False
        _handlers = {
                'to_minutes': self.convert_credits_to_minutes,
                'to_credits': self.convert_minutes_to_credits,
                }
        return _handlers[kwargs['conversion']](**kwargs)

    def buy_credits(self, **kwargs):
        if not kwargs.get('credits') or not kwargs.get('seller_id'):
            return False
        global credits
        _supply = self.system_controller(
                action='supply', credits=kwargs['credits']
                )
        _invoice_record_values = self.fetch_invoice_sheet_record_values(**kwargs)
        _invoice_record = self.invoice_sheet.credit_invoice_sheet_controller(
                action='add', values=_invoice_record_values
                )
        return _supply

    def use_credits(self, **kwargs):
        if not kwargs.get('credits') or not kwargs.get('used_on'):
            return False
        global credits
        _extract = self.system_controller(
                action='extract', credits=kwargs['credits'],
                )
        _transfer_record_values = self.fetch_transfer_sheet_record_values(**kwargs)
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', values=_transfer_record_values
                )
        return _extract

    def share_transfer_record(self, **kwargs):
        if not kwargs.get('transfer_record') or not kwargs.get('partner_ewallet'):
            return False
        _share = kwargs['partner_ewallet'].transfer_sheet.credit_transfer_sheet_controller(
                action='append', records=[kwargs['transfer_record']]
                )
        return _share

#   @pysnooper.snoop()
    def transfer_credits_incomming(self, **kwargs):
        if not kwargs.get('credits') or not kwargs.get('partner_ewallet'):
            return False
        _source_extract = kwargs['partner_ewallet'].system_controller(
                action='extract', credits=kwargs['credits']
                )
        _destination_supply = self.system_controller(
                action='supply', credits=kwargs['credits']
                )
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                transfer_type=kwargs.get('transfer_type'),
                transfer_from=kwargs.get('transfer_from'),
                transfer_to=self.client_id, credits=kwargs['credits']
                )
        self.share_transfer_record(
                partner_ewallet=kwargs['partner_ewallet'],
                transfer_records=[_transfer_record],
                )
        return _destination_supply

#   @pysnooper.snoop()
    def transfer_credits_outgoing(self, **kwargs):
        if not kwargs.get('credits') or not kwargs.get('partner_ewallet'):
            return False
        global credits
        _source_extract = self.system_controller(
                action='extract', credits=kwargs['credits']
                )
        _destination_supply = kwargs['partner_ewallet'].system_controller(
                action='supply', credits=kwargs['credits']
                )
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                transfer_type=kwargs.get('transfer_type'), transfer_from=self.client_id,
                transfer_to=kwargs.get('transfer_to'), credits=kwargs['credits']
                )
        self.share_transfer_record(
                partner_ewallet=kwargs['partner_ewallet'],
                transfer_record=_transfer_record,
                )
        return _source_extract

    def transfer_credits(self, **kwargs):
        if not kwargs.get('transfer_type'):
            return False
        _handlers = {
                'incomming': self.transfer_credits_incomming,
                'outgoing': self.transfer_credits_outgoing,
                }
        _handle = _handlers[kwargs['transfer_type']](**kwargs)
        return _handle

    def display_credit_wallet_credits(self, **kwargs):
        print('Credit Wallet {} Credits: {}'.format(
            self.reference, self.credits
            ))
        return self.credits

#   @pysnooper.snoop()
    def display_credit_wallet_transfer_sheets(self, **kwargs):
       for k, v in self.transfer_sheet_archive.items():
           print('{}: {} - {}'.format(
               v.fetch_transfer_sheet_create_date(), k,
               v.fetch_transfer_sheet_reference()
               ))
       return self.transfer_sheet_archive

    def display_credit_wallet_transfer_records(self, **kwargs):
        return self.transfer_sheet.display_transfer_sheet_records()

    def display_credit_wallet_invoice_sheets(self, **kwargs):
        for k, v in self.invoice_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_invoice_sheet_create_date(), k,
                v.fetch_invoice_sheet_reference(),
                ))
        return self.invoice_sheet_archive

    def display_credit_wallet_invoice_records(self, **kwargs):
        return self.invoice_sheet.display_credit_invoice_sheet_records()

    def interogate_credit_wallet(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'credits': self.display_credit_wallet_credits,
                'credit_transfer_sheets': self.display_credit_wallet_transfer_sheets,
                'credit_transfer_records': self.display_credit_wallet_transfer_records,
                'credit_invoice_sheets': self.display_credit_wallet_invoice_sheets,
                'credit_invoice_records': self.display_credit_wallet_invoice_records,
                }
        return _handlers[kwargs['target']](**kwargs)

    def interogate_credit_clock(self, **kwargs):
        return self.credit_clock.user_controller(
                action='interogate', target=kwargs.get('target'),
                )

    def interogate_credits(self, **kwargs):
        if not kwargs.get('interogate'):
            return False
        _handlers = {
                'credit_wallet': self.interogate_credit_wallet,
                'credit_clock': self.interogate_credit_clock,
                }
        return _handlers[kwargs['interogate']](**kwargs)

    def switch_credit_wallet_transfer_sheet(self, **kwargs):
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return False
        _handlers = {
                'id': self.handle_switch_credit_wallet_transfer_sheet_by_id,
                'ref': self.handle_switch_credit_wallet_transfer_sheet_by_ref,
                }
        return _handlers[kwargs['identifier']](kwargs['code'])

    def switch_credit_wallet_invoice_sheet(self, **kwargs):
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return False
        _handlers = {
                'id': self.handle_switch_credit_wallet_invoice_sheet_by_id,
                'ref': self.handle_switch_credit_wallet_invoice_sheet_by_ref,
                }
        return _handlers[kwargs['identifier']](kwargs['code'])

    # TODO - Has dummy data
    def create_transfer_sheet(self, **kwargs):
        global transfer_sheet_archive
        _transfer_sheet = CreditTransferSheet(
                wallet_id=self.wallet_id,
                reference='Second Credit Transfer Sheet',
                )
        self.transfer_sheet_archive.update({
            _transfer_sheet.fetch_transfer_sheet_id(): _transfer_sheet
            })
        return _transfer_sheet

    # TODO - Has dummy data
    def create_invoice_sheet(self, **kwargs):
        global invoice_sheet_archive
        _invoice_sheet = CreditInvoiceSheet(
                wallet_id=self.wallet_id,
                reference='Second Credit Invoice Sheet',
                )
        self.invoice_sheet_archive.update({
            _invoice_sheet.fetch_invoice_sheet_id(): _invoice_sheet
            })
        return _invoice_sheet

    def switch_credit_wallet_sheet(self, **kwargs):
        if not kwargs.get('sheet'):
            return False
        _handlers = {
                'transfer': self.switch_credit_wallet_transfer_sheet,
                'invoice': self.switch_credit_wallet_invoice_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def create_sheets(self, **kwargs):
        if not kwargs.get('sheet'):
            return False
        _handlers = {
                'transfer': self.create_transfer_sheet,
                'invoice': self.create_invoice_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def system_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'supply': self.supply_credits,
                'extract': self.extract_credits,
                'convert': self.convert_credits,
                'create_sheet': self.create_sheets,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle:
            self.update_write_date()
        return _handle

    def user_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'buy': self.buy_credits,
                'use': self.use_credits,
                'transfer': self.transfer_credits,
                'interogate': self.interogate_credits,
                'switch_sheet': self.switch_credit_wallet_sheet,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return _handle

    def main_controller(self, **kwargs):
        if not kwargs.get('controller'):
            return False
        _handlers = {
                'system': self.system_controller,
                'user': self.user_controller,
                'test': self.test_controller,
                }
        return _handlers[kwargs['controller']](**kwargs)

    def test_system_controller(self):
        print('[ TEST ] System controller...')
        print('[ * ]: Supply')
        self.main_controller(controller='system', action='supply', credits=100)
        print('[ * ]: Extract')
        self.main_controller(controller='system', action='extract', credits=25)
        print('[ * ]: Convert credits to minutes')
        self.main_controller(controller='system', action='convert', conversion='to_minutes', credits=10)
        print('[ * ]: Convert minutes to credits')
        self.main_controller(controller='system', action='convert', conversion='to_credits', minutes=5)
        print('[ * ]: Create New Transfer Sheet')
        self.main_controller(controller='system', action='create_sheet', sheet='transfer')
        print('[ * ]: Create New Invoice Sheet')
        self.main_controller(controller='system', action='create_sheet', sheet='invoice')
        return True

    def test_user_controller(self):
        print('[ TEST ]: User controller...')
        print('[ * ]: Buy')
        self.main_controller(
                controller='user', action='buy', credits=15,
                reference='First Buy', cost=1.50, currency='RON',
                seller_id=random.randint(10,20), notes='Test Notes'
                )
        print('[ * ]: Use')
        self.main_controller(
                controller='user', action='use', credits=5,
                reference='First Use', used_on='Only the best'
                )
        _mock_partner_ewallet = CreditEWallet(credits=100)
        print('[ * ]: Transfer incomming')
        self.main_controller(
                controller='user', action='transfer', credits=3,
                transfer_type='incomming', partner_ewallet=_mock_partner_ewallet,
                transfer_from=random.randint(10,20), reference='Gift Transfer',
                )
        print('[ * ]: Transfer outgoing')
        self.main_controller(
                controller='user', action='transfer', credits=3,
                transfer_type='outgoing', partner_ewallet=_mock_partner_ewallet,
                transfer_to=random.randint(10,20), reference='Pay Day',
                )
        print('[ * ]: Interogate credit wallet')
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_wallet', target='credits'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_wallet', target='credit_transfer_sheets'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_wallet', target='credit_transfer_records'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_wallet', target='credit_invoice_sheets'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_wallet', target='credit_invoice_records'
                )
        print('[ * ]: Interogate credit clock')
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_clock', target='credit_clock'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_clock', target='time_sheets'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_clock', target='time_records'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_clock', target='conversion_sheets'
                )
        self.main_controller(
                controller='user', action='interogate',
                interogate='credit_clock', target='conversion_records'
                )
        print('[ * ]: Switch To New Transfer Sheet')
        self.main_controller(
                controller='user', action='switch_sheet',
                sheet='transfer', identifier='id',
                code=[item for item in self.invoice_sheet_archive.keys()][0]
                )
        print('[ * ]: Switch To New Invoice Sheet')
        self.main_controller(
                controller='user', action='switch_sheet',
                sheet='invoice', identifier='id',
                code=[item for item in self.invoice_sheet_archive.keys()][0]
                )

    def test_controller(self, **kwargs):
        self.test_system_controller()
        self.test_user_controller()
        print('[ OK ] All systems operational.')

#credit_ewallet = CreditEWallet(
#        client_id=random.randint(10,20),
#        reference='First Credit Wallet Reference',
#        credits=25
#        )
#credit_ewallet.main_controller(controller='test')



