import time
import datetime
import random
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .credit_clock import CreditClock
from .transfer_sheet import CreditTransferSheet
from .invoice_sheet import CreditInvoiceSheet
from .res_utils import ResUtils, Base
from .config import Config

res_utils, log_config = ResUtils(), Config().log_config
log = logging.getLogger(log_config['log_name'])


class CreditEWallet(Base):
    __tablename__ = 'credit_ewallet'

    wallet_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('res_user.user_id'))
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    credits = Column(Integer)
    # O2O
    active_session = relationship('EWallet', back_populates='credit_wallet')
    # O2O
    client = relationship('ResUser', back_populates='user_credit_wallet')
    # O2O
    credit_clock = relationship(
       'CreditClock', back_populates='wallet',
       )
    # O2O
    transfer_sheet = relationship(
       'CreditTransferSheet', back_populates='wallet',
       )
    # O2O
    invoice_sheet = relationship(
       'CreditInvoiceSheet', back_populates='wallet',
       )
    # O2M
    credit_clock_archive = relationship('CreditClock')
    # O2M
    transfer_sheet_archive = relationship('CreditTransferSheet')
    # O2M
    invoice_sheet_archive = relationship('CreditInvoiceSheet')

#   @pysnooper.snoop()
    def __init__(self, **kwargs):
        if not kwargs.get('active_session'):
            self.error_no_active_session_found()
            return
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        credit_clock = kwargs.get('credit_clock') or \
            self.system_controller(
                action='create_clock', reference='Credit Clock',
                credit_clock=0.0, active_session=kwargs['active_session']
            )
        transfer_sheet = kwargs.get('transfer_sheet') or \
            self.system_controller(
                action='create_sheet', sheet='transfer',
                reference='Transfer Sheet',
                active_session=kwargs['active_session']
            )
        invoice_sheet = kwargs.get('invoice_sheet') or \
            self.system_controller(
                action='create_sheet', sheet='invoice',
                reference='Invoice Sheet',
                active_session=kwargs['active_session']
            )
        self.active_session_id = kwargs.get('active_session_id')
        self.reference = kwargs.get('reference')
        self.credits = kwargs.get('credits')
        self.credit_clock = [credit_clock]
        self.transfer_sheet = [transfer_sheet]
        self.invoice_sheet = [invoice_sheet]
        self.credit_clock_archive = kwargs.get('credit_clock_archive') or \
                [credit_clock]
        self.transfer_sheet_archive = kwargs.get('transfer_sheet_archive') or \
                [transfer_sheet]
        self.invoice_sheet_archive = kwargs.get('invoice_sheet_archive') or \
                [invoice_sheet]

    # FETCHERS

    def fetch_credit_wallet_transfer_sheet_by_id(self, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session')
        if not active_session:
            return self.error_no_active_session_found()
        if not kwargs.get('code') or not isinstance(kwargs['code'], int):
            return self.error_invalid_credit_clock_id(kwargs)
        transfer_sheet = list(
            active_session.query(CreditTransferSheet).filter_by(
                transfer_sheet_id=kwargs['code']
            )
        )
        if transfer_sheet:
            log.info('Successfully fetched credit transfer sheet by id.')
        return self.warning_no_transfer_sheet_found_by_id(kwargs) if not \
            transfer_sheet else transfer_sheet[0]

    def fetch_credit_wallet_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_credit_clock_identifier_found()
        handlers = {
            'id': self.fetch_credit_wallet_clock_by_id,
            'reference': self.fetch_credit_wallet_clock_by_ref,
            'all': self.fetch_credit_wallet_clocks,
        }
        return handlers[kwargs['identifier']](**kwargs)

    def fetch_credit_wallet_clock_by_id(self, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session')
        if not active_session:
            return self.error_no_active_session_found()
        if not kwargs.get('code') or not isinstance(kwargs['code'], int):
            return self.error_invalid_credit_clock_id(kwargs)
        clock = list(
            active_session.query(CreditClock).filter_by(clock_id=kwargs['code'])
        )
        if clock:
            log.info('Successfully fetched credit clock by id.')
        return self.warning_no_credit_clock_found_by_id(kwargs) if not \
            clock else clock[0]

    def fetch_credit_ewallet_credit_clock(self):
        log.debug('')
        if not len(self.credit_clock):
            return self.error_no_credit_ewallet_credit_clock_found()
        return self.credit_clock[0]

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

    def fetch_credit_ewallet_transfer_sheet(self):
        log.debug('')
        if not len(self.transfer_sheet):
            return self.error_no_credit_ewallet_transfer_sheet_found()
        return self.transfer_sheet[0]

    def fetch_credit_ewallet_invoice_sheet(self):
        log.debug('')
        if not len(self.invoice_sheet):
            return self.error_no_credit_ewallet_invoice_sheet_found()
        return self.invoice_sheet[0]

#   @pysnooper.snoop()
    def fetch_credit_ewallet_values(self):
        log.debug('')
        values = {
            'id': self.wallet_id,
            'client_id': self.client_id,
            'reference': self.reference,
            'create_date': self.create_date,
            'write_date': self.write_date,
            'credits': self.credits,
            'credit_clock': self.fetch_credit_ewallet_credit_clock().fetch_credit_clock_id(),
            'credit_clock_archive': {
                item.fetch_credit_clock_id(): item.fetch_credit_clock_reference() \
                for item in self.credit_clock_archive
            },
            'transfer_sheet': self.fetch_credit_ewallet_transfer_sheet().fetch_transfer_sheet_id(),
            'transfer_sheet_archive': {
                item.fetch_transfer_sheet_id(): item.fetch_transfer_sheet_reference() \
                for item in self.transfer_sheet_archive
            },
            'invoice_sheet': self.fetch_credit_ewallet_invoice_sheet().fetch_invoice_sheet_id(),
            'invoice_sheet_archive': {
                item.fetch_invoice_sheet_id(): item.fetch_invoice_sheet_reference() \
                for item in self.invoice_sheet_archive
            },
        }
        return values

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
        _credit_clocks = self.credit_clock_archive
        if not _credit_clocks:
            self.error_could_not_fetch_credit_ewallet_credit_clock_archive()
        return _credit_clocks

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

    # SETTERS

    def set_transfer_sheet(self, transfer_sheet):
        log.debug('')
        try:
            self.transfer_sheet = [transfer_sheet]
        except:
            return self.error_could_not_set_transfer_sheet(transfer_sheet)
        return True

    def set_credit_clock(self, credit_clock):
        log.debug('')
        try:
            self.credit_clock = [credit_clock]
        except:
            return self.error_could_not_set_credit_clock(credit_clock)
        return True

    def set_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('id'):
            return self.error_no_id_found()
        self.wallet_id = kwargs['id']
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

    def set_credit_clock_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_clock_archive'):
            return self.error_no_credit_clock_archive_found()
        self.credit_clock_archive = kwargs['credit_clock_archive']
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

    def set_write_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('write_date'):
            return self.error_no_write_date_found()
        self.write_date = kwargs['write_date']
        return self.write_date

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        return self.set_write_date(write_date=datetime.datetime.now())

    def update_credit_clock_archive(self, credit_clock):
        log.debug('')
        self.credit_clock_archive.append(credit_clock)
        log.info('Successfully updated credit clock archive.')
        return self.credit_clock_archive

    def update_invoice_sheet_archive(self, invoice_sheet):
        log.debug('')
        self.invoice_sheet_archive.append(invoice_sheet)
        log.info('Successfully updated invoice sheet archive.')
        return self.invoice_sheet_archive

    def update_transfer_sheet_archive(self, transfer_sheet):
        log.debug('')
        self.transfer_sheet_archive.append(transfer_sheet)
        log.info('Successfully updated transfer sheet archive.')
        return self.transfer_sheet_archive

    # HANDLERS

#   @pysnooper.snoop()
    def handle_switch_credit_wallet_clock_by_id(self, **kwargs):
        log.debug('')
        new_credit_clock = self.fetch_credit_wallet_clock(
            identifier='id', **kwargs
        )
        set_clock = self.set_credit_clock(new_credit_clock)
        if set_clock:
            log.info('Successfully switched credit clock by id.')
        return new_credit_clock

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

    # GENERAL

    # TODO - Set up Access Controll List check
    def view_credits(self, **kwargs):
        log.debug('')
        return self.fetch_credit_ewallet_credits()

    def supply_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        _credits = self.credits + kwargs['credits']
        if _credits is self.credits:
            return self.error_could_not_supply_credits_to_credit_ewallet()
        self.credits = _credits
        log.info('Successfully supplied wallet with credits.')
        return self.credits

    def extract_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        _credits = self.credits - kwargs['credits']
        if self.credits is _credits:
            return self.error_could_not_extract_credits()
        self.credits = _credits
        log.info('Successfully extracted credits from wallet.')
        return self.credits

#   @pysnooper.snoop()
    def convert_credits_to_minutes(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return False
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'conversion'
        )
        convert = credit_clock.main_controller(
            controller='system', action='convert', conversion='to_minutes',
            **sanitized_command_chain
        )
        if not convert:
            kwargs['active_session'].rollback()
            return self.error_credits_to_minutes_conversion_failure(kwargs)
        kwargs['active_session'].commit()
        return convert

#   @pysnooper.snoop()
    def convert_minutes_to_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('minutes'):
            return self.error_no_minutes_found()
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_credit_ewallet_credit_clock()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'conversion'
        )
        convert = credit_clock.main_controller(
            controller='system', action='convert', conversion='to_credits',
            **sanitized_command_chain
        )
        self.update_write_date()
        log.info('Successfully converted minutes to credits.')
        return convert

    def convert_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_target_specified()
        handlers = {
            'to_minutes': self.convert_credits_to_minutes,
            'to_credits': self.convert_minutes_to_credits,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def use_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits') or not kwargs.get('used_on'):
            return self.error_handler_use_credits(
                credits=kwargs.get('credits'),
                used_on=kwargs.get('used_on'),
            )
        log.info('Attempting to extract credits from wallet...')
        return self.system_controller(
            action='extract', credits=kwargs['credits'],
        )

    # INTEROGATORS

    def interogate_credit_wallet_credits(self, **kwargs):
        log.debug('')
        return self.fetch_credit_ewallet_credits()

    # TODO
    def interogate_credit_wallet_transfer_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_transfer_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_invoice_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_invoice_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')

    def interogate_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_credit_wallet_interogation_target_not_found()
        _handlers = {
                'credits': self.interogate_credit_wallet_credits,
                'credit_transfer_sheets': self.interogate_credit_wallet_transfer_sheets,
                'credit_transfer_records': self.interogate_credit_wallet_transfer_records,
                'credit_invoice_sheets': self.interogate_credit_wallet_invoice_sheets,
                'credit_invoice_records': self.interogate_credit_wallet_invoice_records,
                }
        return _handlers[kwargs['target']](**kwargs)

    def interogate_credit_clock(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        return False if not credit_clock else credit_clock.user_controller(
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

    # SWITCHES

    def switch_credit_wallet_transfer_sheet(self, **kwargs):
        log.debug('')
        new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet_by_id(
            code=kwargs['sheet_id'], **kwargs
        )
        set_sheet = self.set_transfer_sheet(new_transfer_sheet)
        log.info('Successfully switched transfer sheet by id.')
        return self.warning_could_not_switch_credit_ewallet_transfer_sheet(kwargs) \
            if not set_sheet else new_transfer_sheet

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

    def switch_credit_wallet_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_credit_wallet_sheet_target_specified()
        handlers = {
            'transfer': self.switch_credit_wallet_transfer_sheet,
            'invoice': self.switch_credit_wallet_invoice_sheet,
        }
        return handlers[kwargs['sheet']](**kwargs)

    def switch_credit_wallet_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found()
        clock = self.handle_switch_credit_wallet_clock_by_id(code=kwargs['clock_id'], **kwargs)
        if not clock:
            return self.warning_could_not_switch_credit_clock(kwargs)
        return clock

    # CREATORS

    def create_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'create',
        )
        conversion_sheet = credit_clock.main_controller(
            controller='system', action='create', create='sheet',
            sheet_type='time', **sanitized_command_chain
        )
        if not conversion_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_new_time_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully create conversion sheet.')
        return conversion_sheet

#   @pysnooper.snoop()
    def create_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'create',
        )
        conversion_sheet = credit_clock.main_controller(
            controller='system', action='create', create='sheet',
            sheet_type='conversion', **sanitized_command_chain
        )
        if not conversion_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_new_conversion_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully create conversion sheet.')
        return conversion_sheet

    def create_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        transfer_sheet = CreditTransferSheet(
            id=self.wallet_id,
            reference=kwargs.get('reference'),
            active_session=kwargs['active_session'],
        )
        kwargs['active_session'].add(transfer_sheet)
        self.update_transfer_sheet_archive(transfer_sheet)
        kwargs['active_session'].commit()
        log.info('Successfully created transfer sheet.')
        return transfer_sheet

    def create_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        new_credit_clock = CreditClock(
            wallet_id=self.wallet_id,
            reference=kwargs.get('reference') or 'Credit Clock',
            credit_clock=kwargs.get('credit_clock') or 0.0,
            active_session=kwargs['active_session']
        )
        kwargs['active_session'].add(new_credit_clock)
        self.update_credit_clock_archive(new_credit_clock)
        kwargs['active_session'].commit()
        log.info('Successfully created new credit clock.')
        return new_credit_clock

    def create_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        invoice_sheet = CreditInvoiceSheet(
            id=self.wallet_id,
            reference=kwargs.get('reference'),
            active_session=kwargs['active_session'],
        )
        kwargs['active_session'].add(invoice_sheet)
        self.update_invoice_sheet_archive(invoice_sheet)
        kwargs['active_session'].commit()
        log.info('Successfully created invoice sheet.')
        return invoice_sheet

    def create_sheets(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_sheet_creation_target_specified()
        handlers = {
            'transfer': self.create_transfer_sheet,
            'invoice': self.create_invoice_sheet,
            'conversion': self.create_conversion_sheet,
            'time': self.create_time_sheet,
        }
        return handlers[kwargs['sheet']](**kwargs)

    # UNLINKERS

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

    # CONTROLLERS

    def system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_controller_action_specified()
        handlers = {
            'view': self.view_credits,
            'supply': self.supply_credits,
            'extract': self.extract_credits,
            'convert': self.convert_credits,
            'create_sheet': self.create_sheets,
            'create_clock': self.create_clock,
            'unlink_sheet': self.unlink_sheet,
            'unlink_clock': self.unlink_clock,
        }
        handle = handlers[kwargs['action']](**kwargs)
        if handle:
            self.update_write_date()
        return handle

    def user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_controller_action_specified()
        handlers = {
            'use': self.use_credits,
            'interogate': self.interogate_credits,
            'switch_sheet': self.switch_credit_wallet_sheet,
            'switch_clock': self.switch_credit_wallet_clock,
        }
        handle = handlers[kwargs['action']](**kwargs)
        if handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return handle

    def main_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_controller_type_specified()
        handlers = {
            'system': self.system_controller,
            'user': self.user_controller,
            'test': self.test_controller,
        }
        return handlers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_no_transfer_sheet_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'No transfer sheet found by id. Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet_transfer_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit ewallet transfer sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_credit_clock_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'No credit clock found by id. Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit clock. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_time_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new time sheet. '\
                       'Command chain detils : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_new_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new conversion sheet. '\
                       'Command chain detils : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

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

    # ERRORS

    def error_no_switch_credit_ewallet_transfer_sheet_indentifier_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No switch credit ewallet transfer sheet identifier specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_transfer_sheet(self, transfer_sheet):
        log.error('Could not set transfer sheet {}.'.format(transfer_sheet))
        return False

    def error_no_credit_ewallet_credit_clock_found(self):
        log.error('No credit clock found.')
        return False

    def error_could_not_set_credit_clock(self, credit_clock):
        log.error('Could not set credit clock {}.'.format(credit_clock))
        return False

    def error_invalid_credit_clock_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid credit clock id. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_credit_clock(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch credit clock. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_credits_to_minutes_conversion_failure(self, **kwargs):
        log.error('Credits to minutes conversion failure. Details : {}'.format(kwargs))
        return False

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

    def error_no_id_found(self):
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

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

    def error_could_not_fetch_credit_ewallet_credit_clock_archive(self):
        log.error('Could not fetch credit ewallet credit clock archive.')
        return False

    def error_could_not_extract_credits(self):
        log.error('Could not extract credits from credit wallet.')
        return False

    def error_no_write_date_found(self):
        log.error('No write date found.')
        return False

    def error_could_not_supply_credits_to_credit_ewallet():
        log.error('Could not supply credits to credit ewallet.')
        return False

    # TESTS

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

###############################################################################
# CODE DUMP
###############################################################################

#   def handle_switch_credit_wallet_transfer_sheet_by_ref(self, code):
#       log.debug('')
#       _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
#               identifier='reference', code=code
#               )
#       self.transfer_sheet = _new_transfer_sheet
#       log.info('Successfully switched transfer sheet by reference.')
#       return _new_transfer_sheet

#   def handle_switch_credit_wallet_transfer_sheet_by_id(self, code):
#       log.debug('')
#       _new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet(
#               identifier='id', code=code
#               )
#       self.transfer_sheet = _new_transfer_sheet
#       log.info('Successfully switched transfer sheet by id.')
#       return _new_transfer_sheet

#   def share_transfer_record(self, **kwargs):
#       log.debug('DEPRECATED')
#       if not kwargs.get('transfer_record') or not kwargs.get('partner_ewallet'):
#           return self.error_handler_share_transfer_record(
#               transfer_record=kwargs.get('transfer_record'),
#               partner_ewallet=kwargs.get('partner_ewallet'),
#           )
#       log.info('Attempting to share transfer record...')
#       partner_transfer_sheet = kwargs['partner_ewallet'].fetch_credit_ewallet_transfer_sheet()
#       share = partner_transfer_sheet.credit_transfer_sheet_controller(
#           action='append', records=[kwargs['transfer_record']]
#       )
#       return share

#   # TODO - Remove, replaced by transaction handler at ResUser level
#   @pysnooper.snoop()
#   def transfer_credits_incomming(self, **kwargs):
#       log.debug('DEPRECATED')
#       if not kwargs.get('credits') or not kwargs.get('partner_ewallet'):
#           return self.error_handler_transfer_credits(
#               credits=kwargs.get('credits'),
#               partner_ewallet=kwargs.get('partner_ewallet'),
#           )
#       log.info('Extracting credits from partner ewallet...')
#       source_extract = kwargs['partner_ewallet'].system_controller(
#           action='extract', credits=kwargs['credits']
#       )
#       log.info('Supplying wallet with credits...')
#       destination_supply = self.system_controller(
#           action='supply', credits=kwargs['credits']
#       )
#       log.info('Creating transfer record...')
#       transfer_sheet = self.fetch_credit_ewallet_transfer_sheet()
#       transfer_record = transfer_sheet.credit_transfer_sheet_controller(
#           action='add', reference=kwargs.get('reference'),
#           transfer_type=kwargs.get('transfer_type'),
#           transfer_from=kwargs.get('transfer_from'),
#           transfer_to=self.client_id, credits=kwargs['credits']
#       )
#       kwargs['active_session'].add(transfer_record)
#       log.info('Attempting transfer record share with partner...')
#       self.share_transfer_record(
#           partner_ewallet=kwargs['partner_ewallet'],
#           transfer_records=[transfer_record],
#       )
#       kwargs['active_session'].commit()
#       return destination_supply

#   # TODO - Remove, replaced by transaction handler at ResUser level
#   @pysnooper.snoop()
#   def transfer_credits_outgoing(self, **kwargs):
#       log.debug('DEPRECATED')
#       if not kwargs.get('active_session') or not kwargs.get('credits') or \
#               not kwargs.get('partner_ewallet'):
#           return self.error_handler_transfer_credits(
#               credits=kwargs.get('credits'),
#               partner_ewallet=kwargs.get('partner_ewallet'),
#               active_session=kwargs.get('active_session'),
#           )
#       log.info('Extracting credits from wallet...')
#       source_extract = self.system_controller(
#           action='extract', credits=kwargs['credits']
#       )
#       log.info('Supplying partner wallet with credits...')
#       destination_supply = kwargs['partner_ewallet'].system_controller(
#           action='supply', credits=kwargs['credits']
#       )
#       log.info('Creating transfer record...')
#       transfer_sheet = self.fetch_credit_ewallet_transfer_sheet()
#       transfer_record = transfer_sheet.credit_transfer_sheet_controller(
#           action='add', reference=kwargs.get('reference'),
#           transfer_type=kwargs.get('transfer_type'), transfer_from=self.client_id,
#           transfer_to=kwargs.get('transfer_to'), credits=kwargs['credits']
#       )
#       kwargs['active_session'].add(transfer_record)
#       log.info('Attempting transfer record share with partner...')
#       self.share_transfer_record(
#           partner_ewallet=kwargs['partner_ewallet'],
#           transfer_record=transfer_record,
#       )
#       kwargs['active_session'].commit()
#       return source_extract

#   def transfer_credits(self, **kwargs):
#       log.debug('DEPRECATED')
#       if not kwargs.get('transfer_type'):
#           return self.error_no_transfer_type_found()
#       handlers = {
#           'incomming': self.transfer_credits_incomming,
#           'outgoing': self.transfer_credits_outgoing,
#       }
#       return handlers[kwargs['transfer_type']](**kwargs)


#   def buy_credits(self, **kwargs):
#       log.debug('DEPRECATED')
#       if not kwargs.get('credits') or not kwargs.get('seller_id'):
#           return self.error_handler_buy_credits(
#               credits=kwargs.get('credits'),
#               seller_id=kwargs.get('seller_id')
#           )
#       log.info('Attempting to supply wallet with credits...')
#       supply = self.system_controller(
#           action='supply', credits=kwargs['credits']
#       )
#       log.info('Creating invoice record...')
#       invoice_record = self.invoice_sheet.credit_invoice_sheet_controller(
#           action='add', reference=kwargs.get('reference'),
#           credits=kwargs['credits'], currency=kwargs.get('currency'),
#           cost=kwargs.get('cost'), seller_id=kwargs['seller_id'],
#           notes=kwargs.get('notes')
#       )
#       return supply


