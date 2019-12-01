import time
import datetime
import random
import logging
import pysnooper
from itertools import count

from .credit_clock import CreditClock
from .transfer_sheet import CreditTransferSheet
from .invoice_sheet import CreditInvoiceSheet
from .res_utils import ResUtils
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class CreditEWallet():

#   @pysnooper.snoop()
    def __init__(self, **kwargs):
        self.seq = count()
        self.wallet_id = kwargs.get('wallet_id') or next(self.seq)
        self.client_id = kwargs.get('client_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.credits = kwargs.get('credits') or 0
        self.credit_clock = kwargs.get('credit_clock') or CreditClock(
                wallet_id=self.wallet_id,
                reference='Default Credit Clock',
                credit_clock=0.0
                )
        self.credit_clock_archive = kwargs.get('credit_clock_archive') or {
                self.credit_clock.fetch_credit_clock_id():
                self.credit_clock
                }
        self.transfer_sheet = kwargs.get('transfer_sheet') \
                or CreditTransferSheet(
                wallet_id=self.wallet_id,
                reference='Default Credit Transfer Sheet'
                )
        self.transfer_sheet_archive = kwargs.get('transfer_sheet_archive') or {
                self.transfer_sheet.fetch_transfer_sheet_id():
                self.transfer_sheet
                }
        self.invoice_sheet = kwargs.get('invoice_sheet') or CreditInvoiceSheet(
                wallet_id=self.wallet_id,
                reference='Default Credit Invoice Sheet',
                )
        self.invoice_sheet_archive = kwargs.get('invoice_sheet_archive') or {
                self.invoice_sheet.fetch_invoice_sheet_id(): self.invoice_sheet
                }

    def fetch_credit_ewallet_id(self):
        log.debug('')
        return self.wallet_id

    def fetch_credit_ewallet_reference(self):
        log.debug('')
        return self.reference

    def fetch_credit_ewallet_client_id(self):
        log.debug('')
        return self.client_id

    def fetch_credit_ewallet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_credit_ewallet_credits(self):
        log.debug('')
        return self.credits

    def fetch_credit_ewallet_credit_clock(self):
        log.debug('')
        return self.credit_clock

    def fetch_credit_ewallet_transfer_sheet(self):
        log.debug('')
        return self.transfer_sheet

    def fetch_credit_ewallet_invoice_sheet(self):
        log.debug('')
        return self.invoice_sheet

#   @pysnooper.snoop()
    def fetch_credit_ewallet_values(self):
        log.debug('')
        _values = {
                'id': self.wallet_id,
                'client_id': self.client_id,
                'reference': self.reference,
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
        log.debug('')
        _transfer_sheet = self.transfer_sheet_archive.get(code)
        if not _transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet('id', code)
        log.info('Successfully fetched credit transfer sheet by id.')
        return _transfer_sheet

    def fetch_credit_wallet_transfer_sheet_by_ref(self, code):
        log.debug('')
        for item in self.transfer_sheet_archive:
            if self.transfer_sheet_archive[item].reference == code:
                log.info('Successfully fetched transfer sheet by reference.')
                return self.transfer_sheet_archive[item]
        return self.warning_could_not_Fetch_transfer_sheet('reference', code)

    def fetch_credit_wallet_transfer_sheets(self, **kwargs):
        log.debug('')
        return self.transfer_sheet_archive.values()

    def fetch_credit_wallet_invoice_sheet_by_id(self, code):
        log.debug('')
        _invoice_sheet = self.invoice_sheet_archive.get(code)
        if not _invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet('id', code)
        log.info('Successfully fetched invoice sheet by id.')
        return _invoice_sheet

    def fetch_credit_wallet_invoice_sheet_by_ref(self, code):
        log.debug('')
        for item in self.invoice_sheet_archive:
            if self.invoice_sheet_archive[item].reference == code:
                log.info('Successfully fetched invoice sheet by reference.')
                return self.invoice_sheet_archive[item]
        return self.warning_could_not_fetch_invoice_sheet('reference', code)

    def fetch_credit_wallet_invoice_sheets(self, **kwargs):
        log.debug('')
        return self.invoice_sheet_archive.values()

    def fetch_credit_wallet_clock_by_id(self, code):
        log.debug('')
        _clock = self.credit_clock_archive.get(code)
        if not _clock:
            return self.warning_could_not_fetch_credit_clock('id', code)
        log.info('Successfully fetched credit clock by id.')
        return _clock

    def fetch_credit_wallet_clock_by_ref(self, code):
        log.debug('')
        if not self.credit_clock_archive:
            return self.error_empty_credit_clock_archive()
        for item in self.credit_clock_archive:
            if self.credit_clock_archive[item].fetch_credit_clock_reference() == code:
                log.info('Successfully fetched credit clock by reference.')
                return self.credit_clock_archive[item]
        return self.warning_could_not_fetch_credit_clock('reference', code)

    def fetch_credit_wallet_clocks(self, **kwargs):
        log.debug('')
        return self.credit_clock_archive.values()

    def fetch_credit_wallet_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_transfer_sheet_identifier_found()
        _handlers = {
                'id': self.fetch_credit_wallet_transfer_sheet_by_id,
                'reference': self.fetch_credit_wallet_transfer_sheet_by_ref,
                'all': self.fetch_credit_wallet_transfer_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_wallet_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_invoice_sheet_identifier_found()
        _handlers = {
                'id': self.fetch_credit_wallet_invoice_sheet_by_id,
                'reference': self.fetch_credit_wallet_invoice_sheet_by_ref,
                'all': self.fetch_credit_wallet_invoice_sheets,
                }
        return _handlers[kwargs['identifier']](kwargs.get('code'))

    def fetch_credit_wallet_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_credit_clock_identifier_found()
        _handlers = {
                'id': self.fetch_credit_wallet_clock_by_id,
                'reference': self.fetch_credit_wallet_clock_by_ref,
                'all': self.fetch_credit_wallet_clocks,
                }
        return _handlers[kwargs['identifier']](code=kwargs.get(code))

    def set_wallet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        self.wallet_id = kwargs['wallet_id']
        return True

    def set_client_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found()
        self.client_id = kwargs['client_id']
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits = kwargs['credits']
        return True

    def set_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_clock'):
            return self.error_no_credit_clock_found()
        self.credit_clock = kwargs['credit_clock']
        return False

    def set_credit_clock_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_clock_archive'):
            return self.error_no_credit_clock_archive_found()
        self.credit_clock_archive = kwargs['credit_clock_archive']
        return True

    def set_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_sheet'):
            return self.error_no_transfer_sheet_found()
        self.transfer_sheet = kwargs['transfer_sheet']
        return True

    def set_transfer_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_sheet_archive'):
            return self.error_no_transfer_sheet_archive_found()
        self.transfer_sheet_archive = kwargs['transfer_sheet_archive']
        return True

    def set_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet'):
            return self.error_no_invoice_sheet_found()
        self.invoice_sheet = kwargs['invoice_sheet']
        return True

    def set_invoice_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_archive'):
            return self.error_no_invoice_sheet_archive_found()
        self.invoice_sheet_archive = kwargs['invoice_sheet_archive']
        return True

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def update_credit_clock_archive(self, credit_clock):
        log.debug('')
        self.credit_clock_archive.update({
            credit_clock.fetch_credit_clock_id():
            credit_clock,
            })
        log.info('Successfully updated credit clock archive.')
        return self.credit_clock_archive

    def update_invoice_sheet_archive(self, invoice_sheet):
        log.debug('')
        self.invoice_sheet_archive.update({
            invoice_sheet.fetch_invoice_sheet_id():
            invoice_sheet
            })
        log.info('Successfully updated invoice sheet archive.')
        return self.invoice_sheet_archive

    def update_transfer_sheet_archive(self, transfer_sheet):
        log.debug('')
        self.transfer_sheet_archive.update({
            transfer_sheet.fetch_transfer_sheet_id():
            transfer_sheet
            })
        log.info('Successfully updated transfer sheet archive.')
        return self.transfer_sheet_archive

    def handle_switch_credit_wallet_transfer_sheet_by_ref(self, code):
        log.debug('')
        _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
                identifier='reference', code=code
                )
        self.transfer_sheet = _new_transfer_sheet
        log.info('Successfully switched transfer sheet by reference.')
        return _new_transfer_sheet

    def handle_switch_credit_wallet_transfer_sheet_by_id(self, code):
        log.debug('')
        _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
                identifier='id', code=code
                )
        self.transfer_sheet = _new_transfer_sheet
        log.info('Successfully switched transfer sheet by id.')
        return _new_transfer_sheet

    def handle_switch_credit_wallet_invoice_sheet_by_ref(self, code):
        log.debug('')
        _new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet(
                identifier='ref', code=code
                )
        self.invoice_sheet = _new_invoice_sheet
        log.info('Successfully switched invoice sheet by reference.')
        return _new_invoice_sheet

    def handle_switch_credit_wallet_invoice_sheet_by_id(self, code):
        log.debug('')
        _new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet(
                identifier='id', code=code
                )
        self.invoice_sheet = _new_invoice_sheet
        log.info('Successfully switched invoice sheet by id.')
        return _new_invoice_sheet

    def handle_switch_credit_wallet_clock_by_id(self, code):
        log.debug('')
        _new_credit_clock = self.fetch_credit_wallet_clock(
                identifier='id', code=code
                )
        self.credit_clock = _new_credit_clock
        log.info('Successfully switched credit clock by id.')
        return _new_credit_clock

    def supply_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits += kwargs['credits']
        log.info('Successfully supplied wallet with credits.')
        return self.credits

    def extract_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits -= kwargs['credits']
        log.info('Successfully extracted credits from wallet.')
        return self.credits

    def convert_credits_to_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        _credit_clock = self.credit_clock
        _convert = _credit_clock.system_controller(
                action='convert', conversion='to_minutes',
                credits=kwargs['credits']
                )
        _credit_clock.update_write_date()
        self.system_controller(action='extract', credits=kwargs['credits'])
        log.info('Successfully converted credits to minutes.')
        return _convert

    def convert_minutes_to_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        _credit_clock = self.credit_clock
        _convert = _credit_clock.system_controller(
                action='convert', conversion='to_credits',
                minutes=kwargs['minutes']
                )
        self.update_write_date()
        self.system_controller(action='supply', credits=kwargs['minutes'])
        log.info('Successfully converted minutes to credits.')
        return _convert

    def convert_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_target_specified()
        _handlers = {
                'to_minutes': self.convert_credits_to_minutes,
                'to_credits': self.convert_minutes_to_credits,
                }
        return _handlers[kwargs['conversion']](**kwargs)

    def buy_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('seller_id'):
            return self.error_handler_buy_credits(
                    credits=kwargs.get('credits'),
                    seller_id=kwargs.get('seller_id')
                    )
        log.info('Attempting to supply wallet with credits...')
        _supply = self.system_controller(
                action='supply', credits=kwargs['credits']
                )
        log.info('Creating invoice record...')
        _invoice_record = self.invoice_sheet.credit_invoice_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                credits=kwargs['credits'], currency=kwargs.get('currency'),
                cost=kwargs.get('cost'), seller_id=kwargs['seller_id'],
                notes=kwargs.get('notes')
                )
        return _supply

    def use_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('used_on'):
            return self.error_handler_use_credits(
                    credits=kwargs.get('credits'),
                    used_on=kwargs.get('used_on'),
                    )
        log.info('Attempting to extract credits from wallet...')
        _extract = self.system_controller(
                action='extract', credits=kwargs['credits'],
                )
        log.info('Creating transfer record...')
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                credits=kwargs['credits'],
                transfer_type=kwargs.get('transfer_type'),
                transfer_from=kwargs.get('transfer_from'),
                transfer_to=kwargs['used_on'],
                )
        return _extract

    def share_transfer_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_record') or not kwargs.get('partner_ewallet'):
            return self.error_handler_share_transfer_record(
                    transfer_record=kwargs.get('transfer_record'),
                    partner_ewallet=kwargs.get('partner_ewallet'),
                    )
        log.info('Attempting to share transfer record...')
        _share = kwargs['partner_ewallet'].transfer_sheet.credit_transfer_sheet_controller(
                action='append', records=[kwargs['transfer_record']]
                )
        return _share

#   @pysnooper.snoop()
    def transfer_credits_incomming(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('partner_ewallet'):
            return self.error_handler_transfer_credits(
                    credits=kwargs.get('credits'),
                    partner_ewallet=kwargs.get('partner_ewallet'),
                    )
        log.info('Extracting credits from partner ewallet...')
        _source_extract = kwargs['partner_ewallet'].system_controller(
                action='extract', credits=kwargs['credits']
                )
        log.info('Supplying wallet with credits...')
        _destination_supply = self.system_controller(
                action='supply', credits=kwargs['credits']
                )
        log.info('Creating transfer record...')
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                transfer_type=kwargs.get('transfer_type'),
                transfer_from=kwargs.get('transfer_from'),
                transfer_to=self.client_id, credits=kwargs['credits']
                )
        log.info('Attempting transfer record share with partner...')
        self.share_transfer_record(
                partner_ewallet=kwargs['partner_ewallet'],
                transfer_records=[_transfer_record],
                )
        return _destination_supply

#   @pysnooper.snoop()
    def transfer_credits_outgoing(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('partner_ewallet'):
            return self.error_handler_transfer_credits(
                    credits=kwargs.get('credits'),
                    partner_ewallet=kwargs.get('partner_ewallet'),
                    )
        log.info('Extracting credits from wallet...')
        _source_extract = self.system_controller(
                action='extract', credits=kwargs['credits']
                )
        log.info('Supplying partner wallet with credits...')
        _destination_supply = kwargs['partner_ewallet'].system_controller(
                action='supply', credits=kwargs['credits']
                )
        log.info('Creating transfer record...')
        _transfer_record = self.transfer_sheet.credit_transfer_sheet_controller(
                action='add', reference=kwargs.get('reference'),
                transfer_type=kwargs.get('transfer_type'), transfer_from=self.client_id,
                transfer_to=kwargs.get('transfer_to'), credits=kwargs['credits']
                )
        log.info('Attempting transfer record share with partner...')
        self.share_transfer_record(
                partner_ewallet=kwargs['partner_ewallet'],
                transfer_record=_transfer_record,
                )
        return _source_extract

    def transfer_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_type'):
            return self.error_no_transfer_type_found()
        _handlers = {
                'incomming': self.transfer_credits_incomming,
                'outgoing': self.transfer_credits_outgoing,
                }
        _handle = _handlers[kwargs['transfer_type']](**kwargs)
        return _handle

    # TODO - Refactor
    def display_credit_wallet_credits(self, **kwargs):
        log.debug('')
        print('Credit Wallet {} Credits: {}'.format(
            self.reference, self.credits
            ))
        return self.credits

    # TODO - Refactor
#   @pysnooper.snoop()
    def display_credit_wallet_transfer_sheets(self, **kwargs):
        log.debug('')
        for k, v in self.transfer_sheet_archive.items():
            print('{}: {} - {}'.format(
               v.fetch_transfer_sheet_create_date(), k,
               v.fetch_transfer_sheet_reference()
               ))
        return self.transfer_sheet_archive

    # TODO - Refactor
    def display_credit_wallet_transfer_records(self, **kwargs):
        log.debug('')
        return self.transfer_sheet.display_transfer_sheet_records()

    # TODO - Refactor
    def display_credit_wallet_invoice_sheets(self, **kwargs):
        log.debug('')
        for k, v in self.invoice_sheet_archive.items():
            print('{}: {} - {}'.format(
                v.fetch_invoice_sheet_create_date(), k,
                v.fetch_invoice_sheet_reference(),
                ))
        return self.invoice_sheet_archive

    # TODO - Refactor
    def display_credit_wallet_invoice_records(self, **kwargs):
        log.debug('')
        return self.invoice_sheet.display_credit_invoice_sheet_records()

    def interogate_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_credit_wallet_interogation_target_not_found()
        _handlers = {
                'credits': self.display_credit_wallet_credits,
                'credit_transfer_sheets': self.display_credit_wallet_transfer_sheets,
                'credit_transfer_records': self.display_credit_wallet_transfer_records,
                'credit_invoice_sheets': self.display_credit_wallet_invoice_sheets,
                'credit_invoice_records': self.display_credit_wallet_invoice_records,
                }
        return _handlers[kwargs['target']](**kwargs)

    def interogate_credit_clock(self, **kwargs):
        log.debug('')
        return self.credit_clock.user_controller(
                action='interogate', target=kwargs.get('target'),
                )

    def interogate_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_credit_interogation_target_not_found()
        _handlers = {
                'credit_wallet': self.interogate_credit_wallet,
                'credit_clock': self.interogate_credit_clock,
                }
        return _handlers[kwargs['interogate']](**kwargs)

    def switch_credit_wallet_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return self.error_handler_switch_credit_wallet_transfer_sheet(
                    identifier=kwargs.get('identifier'),
                    code=kwargs.get('code'),
                    )
        _handlers = {
                'id': self.handle_switch_credit_wallet_transfer_sheet_by_id,
                'ref': self.handle_switch_credit_wallet_transfer_sheet_by_ref,
                }
        return _handlers[kwargs['identifier']](kwargs['code'])

    def switch_credit_wallet_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier') or not kwargs.get('code'):
            return self.error_handler_switch_credit_wallet_invoice_sheet(
                    identifier=kwargs.get('identifier'),
                    code=kwargs.get('code'),
                    )
        _handlers = {
                'id': self.handle_switch_credit_wallet_invoice_sheet_by_id,
                'ref': self.handle_switch_credit_wallet_invoice_sheet_by_ref,
                }
        return _handlers[kwargs['identifier']](kwargs['code'])

    def create_transfer_sheet(self, **kwargs):
        log.debug('')
        _transfer_sheet = CreditTransferSheet(
                wallet_id=self.wallet_id,
                reference=kwargs.get('reference'),
                )
        self.transfer_sheet_archive.update({
            _transfer_sheet.fetch_transfer_sheet_id(): _transfer_sheet
            })
        log.info('Successfully created transfer sheet.')
        return _transfer_sheet

    def create_invoice_sheet(self, **kwargs):
        log.debug('')
        _invoice_sheet = CreditInvoiceSheet(
                wallet_id=self.wallet_id,
                reference=kwargs.get('reference'),
                )
        self.invoice_sheet_archive.update({
            _invoice_sheet.fetch_invoice_sheet_id(): _invoice_sheet
            })
        log.info('Successfully created invoice sheet.')
        return _invoice_sheet

    def switch_credit_wallet_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_credit_wallet_sheet_target_specified()
        _handlers = {
                'transfer': self.switch_credit_wallet_transfer_sheet,
                'invoice': self.switch_credit_wallet_invoice_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def switch_credit_wallet_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found()
        _clock = self.handle_switch_credit_wallet_clock_by_id(kwargs['clock_id'])
        if not _clock:
            return self.warning_could_not_fetch_credit_clock()
        return _clock

    def create_sheets(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_sheet_creation_target_specified()
        _handlers = {
                'transfer': self.create_transfer_sheet,
                'invoice': self.create_invoice_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def create_clock(self, **kwargs):
        log.debug('')
        _new_credit_clock = CreditClock(
                wallet_id=self.wallet_id,
                reference=kwargs.get('reference') or str(),
                credit_clock=kwargs.get('credit_clock') or float(),
                )
        self.update_credit_clock_archive(_new_credit_clock)
        log.info('Successfully created new credit clock.')
        return _new_credit_clock

    def unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_transfer_sheet_id_not_found()
        log.info('Attempting to fetch transfer sheet...')
        _transfer_sheet = self.fetch_transfer_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        if not _transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet(
                    'id', kwargs['sheet_id']
                    )
        _unlink = self.transfer_sheet_archive.pop(kwargs['sheet_id'])
        if _unlink:
            log.info('Successfully removed transfer sheet.')
        return _unlink

    def unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_invoice_sheet_id_found()
        log.info('Attempting to fetch invoice sheet.')
        _invoice_sheet = self.fetch_invoice_sheet(
                identifier='id', code=kwargs['sheet_id']
                )
        if not _invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet(
                    'id', kwargs['sheet_id']
                    )
        _unlink = self.invoice_sheet_archive.pop(kwargs['sheet_id'])
        if _unlink:
            log.info('Successfully removed invoice sheet.')
        return _unlink

    def unlink_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_sheet_unlink_target_specified()
        _handlers = {
                'transfer': self.unlink_transfer_sheet,
                'invoice': self.unlink_invoice_sheet,
                }
        return _handlers[kwargs['sheet']](**kwargs)

    def unlink_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found()
        log.info('Attempting to fetch credit clock...')
        _clock = self.fetch_credit_wallet_clock(
                identifier='id', code=kwargs['clock_id']
                )
        if not _clock:
            return self.warning_could_not_fetch_credit_clock(
                    'id', kwargs['clock_id']
                    )
        _unlink = self.credit_clock_archive.pop(kwargs['clock_id'])
        if _unlink:
            log.info('Successfully removed credit clock.')
        return _unlink

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_controller_action_specified()
        _handlers = {
                'supply': self.supply_credits,
                'extract': self.extract_credits,
                'convert': self.convert_credits,
                'create_sheet': self.create_sheets,
                'create_clock': self.create_clock,
                'unlink_sheet': self.unlink_sheet,
                'unlink_clock': self.unlink_clock,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle:
            self.update_write_date()
        return _handle

    def user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_controller_action_specified()
        _handlers = {
                'buy': self.buy_credits,
                'use': self.use_credits,
                'transfer': self.transfer_credits,
                'interogate': self.interogate_credits,
                'switch_sheet': self.switch_credit_wallet_sheet,
                'switch_clock': self.switch_credit_wallet_clock,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return _handle

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_controller_type_specified()
        _handlers = {
                'system': self.system_controller,
                'user': self.user_controller,
                'test': self.test_controller,
                }
        return _handlers[kwargs['controller']](**kwargs)

    def error_handler_buy_credits(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credits': kwargs.get('credits'),
                    'seller_id': kwargs.get('seller_id'),
                    },
                'handlers': {
                    'credits': self.error_no_credits_found,
                    'seller_id': self.error_no_seller_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_user_credits(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credits': kwargs.get('credits'),
                    'used_on': kwargs.get('used_on'),
                    },
                'handlers': {
                    'credits': self.error_no_credits_found,
                    'used_on': self.error_no_expence_target_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_share_transfer_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'transfer_record': kwargs.get('transfer_record'),
                    'partner_ewallet': kwargs.get('partner_ewallet'),
                    },
                'handlers': {
                    'transfer_record': self.error_no_transfer_record_found,
                    'partner_ewallet': self.error_no_partner_ewallet_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_transfer_credits(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credits': kwargs.get('credits'),
                    'partner_ewallet': kwargs.get('partner_ewallet'),
                    },
                'handlers': {
                    'credits': self.error_no_credits_found,
                    'partner_ewallet': self.error_no_partner_ewallet_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_switch_credit_wallet_transfer_sheet(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'identifier': kwargs.get('identifier'),
                    'code': kwargs.get('code'),
                    },
                'handlers': {
                    'identifier': self.error_no_transfer_sheet_identifier_found,
                    'code': self.error_no_transfer_sheet_code_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_switch_credit_wallet_invoice_sheet(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'identifier': kwargs.get('identifier'),
                    'code': kwargs.get('code'),
                    },
                'handlers': {
                    'identifier': self.error_no_invoice_sheet_identifier_found,
                    'code': self.error_no_invoice_sheet_code_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_no_client_id_found(self):
        log.error('No client id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_credit_clock_found(self):
        log.error('No credit clock found.')
        return False

    def error_no_credit_clock_archive_found(self):
        log.error('No credit clock archive found.')
        return False

    def error_no_transfer_sheet_found(self):
        log.error('No transfer sheet found.')
        return False

    def error_no_transfer_sheet_archive_found(self):
        log.error('No transfer sheet archive found.')
        return False

    def error_no_invoice_sheet_found(self):
        log.error('No invoice sheet found.')
        return False

    def error_no_invoice_sheet_archive_found(self):
        log.error('No invoice sheet archive found.')
        return False

    def error_no_invoice_sheet_identifier_found(self):
        log.error('No invoice sheet identifier found.')
        return False

    def error_no_invoice_sheet_code_found(self):
        log.error('No invoice sheet code found.')
        return False

    def error_no_transfer_sheet_identifier_found(self):
        log.error('No transfer sheet identifier found.')
        return False

    def error_no_transfer_sheet_code_found(self):
        log.error('No tranfer sheet code found.')
        return False

    def error_no_transfer_record_found(self):
        log.error('No transfer record found.')
        return False

    def error_no_partner_ewallet_found(self):
        log.error('No partner ewallet found.')
        return False

    def error_no_expence_target_found(self):
        log.error('No expence target found.')
        return False

    def error_no_minutes_found(self):
        log.error('No minutes found.')
        return False

    def error_no_conversion_target_specified(self):
        log.error('No conversion target specified.')
        return False

    def error_no_seller_id_found(self):
        log.error('No seller id found.')
        return False

    def error_no_transfer_sheet_identifier_found(self):
        log.error('No transfer sheet identifier found.')
        return False

    def error_no_invoice_sheet_identifier_found(self):
        log.error('No invoice sheet identifier found.')
        return False

    def error_no_credit_clock_identifier_found(self):
        log.error('No credit clock identifier found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_empty_credit_clock_archive(self):
        log.error('Credit clock archive is empty.')
        return False

    def error_no_transfer_type_found(self):
        log.error('No transfer type found.')
        return False

    def error_credit_wallet_interogation_target_not_found(self):
        log.error('Credit wallet interogation target not found.')
        return False

    def error_credit_interogation_target_not_found(self):
        log.error('Credit interogation target not found.')
        return False

    def error_no_credit_wallet_sheet_target_specified(self):
        log.error('No credit wallet sheet target specified.')
        return False

    def error_no_credit_clock_id_found(self):
        log.error('No credit clock id found.')
        return False

    def error_no_sheet_creation_target_specified(self):
        log.error('No sheet creation target specified.')
        return False

    def error_no_invoice_sheet_id_found(self):
        log.error('No invoice sheet id found.')
        return False

    def error_transfer_sheet_id_not_found(self):
        log.error('Transfer sheet id not found.')
        return False

    def error_no_sheet_unlink_target_specified(self):
        log.error('No sheet unlink target specified.')
        return False

    def error_no_system_controller_action_specified(self):
        log.error('No system controller action specified.')
        return False

    def error_no_user_controller_action_specified(self):
        log.error('No user controller action specified.')
        return False

    def error_no_controller_type_specified(self):
        log.error('No controller type specified.')
        return False

    def warning_could_not_fetch_credit_clock(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock by %s %s.', search_code, code
                )
        return False

    def warning_could_not_fetch_transfer_sheet(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch transfer sheet by %s %s.', search_code, code
                )
        return False

    def warning_could_not_fetch_invoice_sheet(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch invoice sheet by %s %s.', search_code, code
                )
        return False

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



