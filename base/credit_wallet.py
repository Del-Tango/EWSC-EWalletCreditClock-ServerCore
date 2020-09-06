# import time
import datetime
import random
import logging
import pysnooper
# from itertools import count
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime  # Table,Float,Date,
from sqlalchemy.orm import relationship

from .credit_clock import CreditClock
from .transfer_sheet import CreditTransferSheet
from .invoice_sheet import CreditInvoiceSheet
from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class CreditEWallet(Base):
    __tablename__ = 'credit_ewallet'

    wallet_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('res_user.user_id'))
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    credits = Column(Integer)
    active_session = relationship('EWallet', back_populates='credit_wallet')
    client = relationship('ResUser', back_populates='user_credit_wallet')
    credit_clock = relationship(
       'CreditClock', back_populates='wallet',
    )
    transfer_sheet = relationship(
       'CreditTransferSheet', back_populates='wallet',
    )
    invoice_sheet = relationship(
       'CreditInvoiceSheet', back_populates='wallet',
    )
    credit_clock_archive = relationship('CreditClock')
    transfer_sheet_archive = relationship('CreditTransferSheet')
    invoice_sheet_archive = relationship('CreditInvoiceSheet')

#   @pysnooper.snoop('logs/ewallet.log')
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
        self.reference = kwargs.get('reference') or \
            config.wallet_config['wallet_reference']
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

    def fetch_credit_wallet_invoice_sheet_by_id(self, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session')
        if not active_session:
            return self.error_no_active_session_found()
        if not kwargs.get('code') or not isinstance(kwargs['code'], int):
            return self.error_invalid_invoice_sheet_id(kwargs)
        invoice_sheet = list(
            active_session.query(CreditInvoiceSheet).filter_by(
                invoice_sheet_id=kwargs['code']
            )
        )
        if invoice_sheet:
            log.info('Successfully fetched credit transfer sheet by id.')
        return self.warning_no_invoice_sheet_found_by_id(kwargs) if not \
            invoice_sheet else invoice_sheet[0]

    def fetch_credit_wallet_transfer_sheet_by_id(self, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session')
        if not active_session:
            return self.error_no_active_session_found()
        if not kwargs.get('code') or not isinstance(kwargs['code'], int):
            return self.error_invalid_transfer_sheet_id(kwargs)
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
        query = list(
            active_session.query(CreditClock).filter_by(clock_id=kwargs['code'])
        )
        clock = None if not query else query[0]
        if not clock:
            return self.warning_no_credit_clock_found_by_id(
                kwargs, active_session, clock
            )
        log.info('Successfully fetched credit clock by id.')
        return clock

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
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        transfer_sheet = self.fetch_credit_ewallet_transfer_sheet()
        invoice_sheet = self.fetch_credit_ewallet_invoice_sheet()
        values = {
            'id': self.wallet_id,
            'user': self.client_id,
            'reference': self.reference or config.wallet_config['wallet_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'credits': self.credits or 0,
            'clock': None if not credit_clock else \
                credit_clock.fetch_credit_clock_id(),
            'clock_archive': {
                item.fetch_credit_clock_id(): item.fetch_credit_clock_reference() \
                for item in self.credit_clock_archive
            },
            'transfer_sheet': None if not transfer_sheet else \
                transfer_sheet.fetch_transfer_sheet_id(),
            'transfer_sheet_archive': {
                item.fetch_transfer_sheet_id(): item.fetch_transfer_sheet_reference() \
                for item in self.transfer_sheet_archive
            },
            'invoice_sheet': None if not invoice_sheet else \
                invoice_sheet.fetch_invoice_sheet_id(),
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

    def set_ewallet_id(self, ewallet_id):
        log.debug('')
        try:
            self.ewallet_id = ewallet_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_ewallet_id(
                ewallet_id, self.ewallet_id, e
            )
        log.info('Successfully set credit ewallet id.')
        return True

    def set_client_id(self, client_id):
        log.debug('')
        try:
            self.client_id = client_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_client_user_id(
                client_id, self.client_id, e
            )
        log.info('Successfully set user client id.')
        return True

    def set_active_session_id(self, ewallet_session_id):
        log.debug('')
        try:
            self.active_session_id = ewallet_session_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_active_session_id(
                ewallet_session_id, self.active_session_id, e
            )
        log.info('Successfully set credit ewallet session id.')
        return True

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_create_date(
                create_date, self.create_date, e
            )
        log.info('Successfully set credit ewallet create date.')
        return True

    def set_active_session(self, ewallet_session):
        log.debug('')
        try:
            self.active_session = ewallet_session
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_active_ewallet_session(
                ewallet_session, self.active_session, e
            )
        log.info('Successfully set active ewallet session.')
        return True

    def set_client(self, user):
        log.debug('')
        try:
            self.client = user
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_client_user(
                user, self.client, e
            )
        log.info('Successfully set credit ewallet client user.')
        return True



    def set_to_credit_clock_archive(self, credit_clock):
        log.debug('')
        try:
            self.credit_clock_archive.append(credit_clock)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_clock_to_archive(
                credit_clock, self.credit_clock_archive, e
            )
        log.info('Successfully updated credit clock archive.')
        return True

    def set_to_invoice_sheet_archive(self, invoice_sheet):
        log.debug('')
        try:
            self.invoice_sheet_archive.append(invoice_sheet)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_to_archive(
                invoice_sheet, self.invoice_sheet_archive, e
            )
        log.info('Successfully updated invoice sheet archive.')
        return True

    def set_to_transfer_sheet_archive(self, transfer_sheet):
        log.debug('')
        try:
            self.transfer_sheet_archive.append(transfer_sheet)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_transfer_sheet_to_archive(
                transfer_sheet, self.transfer_sheet_archive, e
            )
        log.info('Successfully updated transfer sheet archive.')
        return True

    def set_invoice_sheet(self, invoice_sheet):
        log.debug('')
        try:
            self.invoice_sheet = [invoice_sheet]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet(
                invoice_sheet, self.invoice_sheet, e
            )
        log.info('Successfully set invoice sheet.')
        return True

    def set_transfer_sheet(self, transfer_sheet):
        log.debug('')
        try:
            self.transfer_sheet = [transfer_sheet]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_transfer_sheet(
                transfer_sheet, self.transfer_sheet, e
            )
        log.info('Successfully set transfer sheet.')
        return True

    def set_credit_clock(self, credit_clock):
        log.debug('')
        try:
            self.credit_clock = [credit_clock]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_clock(
                credit_clock, self.credit_clock, e
            )
        log.info('Successfully set credit clock.')
        return True

    def set_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('id'):
            return self.error_no_id_found(kwargs)
        try:
            self.wallet_id = kwargs['id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_ewallet_id(
                kwargs, self.wallet_id, e
            )
        log.info('Successfully set credit ewallet id.')
        return True

    def set_client_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('client_id'):
            return self.error_no_client_id_found(kwargs)
        try:
            self.client_id = kwargs['client_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_client_id(
                kwargs, self.client_id, e
            )
        log.info('Successfully set client id.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_ewallet_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set credit ewallet reference.')
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found(kwargs)
        try:
            self.credits = kwargs['credits']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_ewallet_credits(
                kwargs, self.credits, e
            )
        log.info('Successfully set ewallet credits.')
        return True

    def set_credit_clock_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_clock_archive'):
            return self.error_no_credit_clock_archive_found(kwargs)
        try:
            self.credit_clock_archive = kwargs['credit_clock_archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_credit_clock_archive(
                kwargs, self.credit_clock_archive, e
            )
        log.info('Successfully set credit clock archive.')
        return True

    def set_transfer_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_sheet_archive'):
            return self.error_no_transfer_sheet_archive_found(kwargs)
        try:
            self.transfer_sheet_archive = kwargs['transfer_sheet_archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_transfer_sheet_archive(
                kwargs, self.transfer_sheet_archive, e
            )
        log.info('Successfully set transfer sheet archive.')
        return True

    def set_invoice_sheet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_sheet_archive'):
            return self.error_no_invoice_sheet_archive_found(kwargs)
        try:
            self.invoice_sheet_archive = kwargs['invoice_sheet_archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_invoice_sheet_archive(
                kwargs, self.invoice_sheet_archive, e
            )
        log.info('Successfully set invoice sheet archive.')
        return True

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_ewallet_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set write date.')
        return True

    # UPDATERS

    def update_credit_clock_archive(self, credit_clock):
        log.debug('')
        set_to = self.set_to_credit_clock_archive(credit_clock)
        return set_to if isinstance(set_to, dict) and \
            set_to.get('failed') else self.credit_clock_archive

    def update_invoice_sheet_archive(self, invoice_sheet):
        log.debug('')
        set_to = self.set_to_invoice_sheet_archive(invoice_sheet)
        return set_to if isinstance(set_to, dict) and \
            set_to.get('failed') else self.invoice_sheet_archive

    def update_transfer_sheet_archive(self, transfer_sheet):
        log.debug('')
        set_to = self.set_to_transfer_sheet_archive(transfer_sheet)
        return set_to if isinstance(set_to, dict) and \
            set_to.get('failed') else self.transfer_sheet_archive

    def update_write_date(self):
        log.debug('')
        return self.set_write_date(datetime.datetime.now())

    # CHECKERS

    def check_invoice_sheet_belongs_to_credit_ewallet(self, sheet):
        log.debug('')
        return False if sheet not in self.invoice_sheet_archive \
            else True

    def check_transfer_sheet_belongs_to_credit_ewallet(self, sheet):
        log.debug('')
        return False if sheet not in self.transfer_sheet_archive \
            else True

    def check_clock_belongs_to_credit_ewallet(self, credit_clock):
        log.debug('')
        return False if credit_clock not in self.credit_clock_archive \
            else True

    # HANDLERS

#   @pysnooper.snoop()
    def handle_switch_credit_wallet_clock_by_id(self, **kwargs):
        log.debug('')
        new_credit_clock = self.fetch_credit_wallet_clock(
            identifier='id', **kwargs
        )
        check = self.check_clock_belongs_to_credit_ewallet(new_credit_clock)
        if not check:
            return self.warning_clock_does_not_belong_to_current_credit_ewallet(
                kwargs, new_credit_clock, check
            )
        set_clock = self.set_credit_clock(new_credit_clock)
        if not set_clock or isinstance(set_clock, dict) and \
                set_clock.get('failed'):
            return self.error_could_not_set_active_credit_clock(
                kwargs, new_credit_clock, check, set_clock
            )
        log.info('Successfully switched credit clock.')
        return new_credit_clock

    def handle_switch_credit_wallet_invoice_sheet_by_id(self, code):
        log.debug('')
        new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet(
            identifier='id', code=code
        )
        set_sheet = self.set_invoice_sheet(new_invoice_sheet)
        if set_sheet:
            log.info('Successfully switched invoice sheet by id.')
        return new_invoice_sheet

    # GENERAL

    # TODO - Set up Access Controll List check
    def view_credits(self, **kwargs):
        log.debug('')
        return self.fetch_credit_ewallet_credits()

    def supply_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        credits = self.credits + int(kwargs['credits'])
        if self.credits is credits:
            return self.error_could_not_supply_credits_to_credit_ewallet()
        self.set_credits(credits=credits)
        log.info('Successfully supplied wallet with credits.')
        return self.credits

    def extract_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        credits = self.credits - int(kwargs['credits'])
        if self.credits is credits:
            return self.error_could_not_extract_credits()
        self.set_credits(credits=credits)
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

    # INTEROGATORS

    # TODO
    def interogate_credit_wallet_transfer_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_transfer_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_invoice_sheets(self, **kwargs):
        log.debug('UNIMPLEMENTED')
    def interogate_credit_wallet_invoice_records(self, **kwargs):
        log.debug('UNIMPLEMENTED')

    def interogate_credit_wallet_credits(self, **kwargs):
        log.debug('')
        return self.fetch_credit_ewallet_credits()

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

    # SWITCHERS

    def switch_credit_wallet_clock_time_sheet(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet'
        )
        set_sheet = credit_clock.main_controller(
            controller='user', action='switch_sheet', sheet='time',
            **sanitized_command_chain
        )
        if not set_sheet or isinstance(set_sheet, dict) and \
                set_sheet.get('failed'):
            return self.warning_could_not_switch_credit_ewallet_time_sheet(
                kwargs, credit_clock, set_sheet
            )
        log.info('Successfully switched time sheet.')
        return set_sheet

    def switch_credit_wallet_clock_conversion_sheet(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet'
        )
        switch = credit_clock.main_controller(
            controller='user', action='switch_sheet', sheet='conversion',
            **sanitized_command_chain
        )
        if not switch or isinstance(switch, dict) and switch.get('failed'):
            return self.warning_could_not_switch_credit_ewallet_conversion_sheet(
                kwargs, credit_clock, switch
            )
        log.info('Successfully switched conversion sheet.')
        return switch

    def switch_credit_wallet_invoice_sheet(self, **kwargs):
        log.debug('')
        new_invoice_sheet = self.fetch_credit_wallet_invoice_sheet_by_id(
            code=kwargs['sheet_id'], **kwargs
        )
        check = self.check_invoice_sheet_belongs_to_credit_ewallet(
            new_invoice_sheet
        )
        if not check:
            return self.warning_invoice_sheet_does_not_belong_to_credit_ewallet(
                kwargs, new_invoice_sheet, check
            )
        set_sheet = self.set_invoice_sheet(new_invoice_sheet)
        if not set_sheet or isinstance(set_sheet, dict) and \
                set_sheet.get('failed'):
            return self.warning_could_not_switch_credit_ewallet_invoice_sheet(
                kwargs, new_invoice_sheet, set_sheet
            )
        log.info('Successfully switched invoice sheet.')
        return self.warning_could_not_switch_credit_ewallet_invoice_sheet(kwargs) \
            if not set_sheet else new_invoice_sheet

    def switch_credit_wallet_transfer_sheet(self, **kwargs):
        log.debug('')
        new_transfer_sheet = self.fetch_credit_wallet_transfer_sheet_by_id(
            code=kwargs['sheet_id'], **kwargs
        )
        check = self.check_transfer_sheet_belongs_to_credit_ewallet(
            new_transfer_sheet
        )
        if not check:
            return self.warning_transfer_sheet_does_not_belong_to_credit_ewallet(
                kwargs, new_transfer_sheet, check
            )
        set_sheet = self.set_transfer_sheet(new_transfer_sheet)
        if not set_sheet or isinstance(set_sheet, dict) and \
                set_sheet.get('failed'):
            return self.warning_could_not_switch_credit_ewallet_transfer_sheet(
                kwargs, new_transfer_sheet, set_sheet
            )
        log.info('Successfully switched transfer sheet.')
        return new_transfer_sheet

    # CREATORS

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
            return self.error_no_active_session_found(kwargs)
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

    # ACTIONS

    def action_unlink_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found(kwargs)
        clock = self.fetch_credit_wallet_clock_by_id(
            code=kwargs['clock_id'],
            active_session=kwargs.get('active_session'),
        )
        check = self.check_clock_belongs_to_credit_ewallet(clock)
        if not check:
            return self.warning_clock_does_not_belong_to_current_credit_ewallet(
                kwargs, clock, check
            )
        try:
            unlink = kwargs['active_session'].query(
                CreditClock
            ).filter_by(
                clock_id=kwargs['clock_id']
            ).delete()
        except Exception as e:
            return self.error_could_not_unlink_credit_clock(kwargs, e)
        log.info('Successfully unlinked credit clock.')
        return kwargs['clock_id']

    def action_switch_credit_wallet_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found()
        clock = self.handle_switch_credit_wallet_clock_by_id(code=kwargs['clock_id'], **kwargs)
        if not clock or isinstance(clock, dict) and \
                clock.get('failed'):
            return self.warning_could_not_switch_credit_clock(
                kwargs, clock
            )
        return clock

    def action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_credit_ewallet_unlink_time_target_specified(kwargs)
        handlers = {
            'list': self.unlink_time_list,
            'record': self.unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_credit_ewallet_unlink_conversion_target_specified(kwargs)
        handlers = {
            'list': self.unlink_conversion_list,
            'record': self.unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_credit_ewallet_unlink_invoice_target_specified(kwargs)
        handlers = {
            'list': self.unlink_invoice_list,
            'record': self.unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def action_unlink_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_credit_ewallet_unlink_transfer_target_specified(kwargs)
        handlers = {
            'list': self.unlink_transfer_list,
            'record': self.unlink_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_credit_ewallet_unlink_target_specified(kwargs)
        handlers = {
            'transfer': self.action_unlink_transfer,
            'invoice': self.action_unlink_invoice,
            'conversion': self.action_unlink_conversion,
            'time': self.action_unlink_time,
            'clock': self.action_unlink_clock,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def action_interogate_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_credit_interogation_target_not_found()
        _handlers = {
                'credit_wallet': self.interogate_credit_wallet,
                'credit_clock': self.interogate_credit_clock,
                }
        return _handlers[kwargs['interogate']](**kwargs)

    def action_switch_credit_wallet_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet'):
            return self.error_no_credit_wallet_sheet_target_specified()
        handlers = {
            'transfer': self.switch_credit_wallet_transfer_sheet,
            'invoice': self.switch_credit_wallet_invoice_sheet,
            'conversion': self.switch_credit_wallet_clock_conversion_sheet,
            'time': self.switch_credit_wallet_clock_time_sheet,
        }
        return handlers[kwargs['sheet']](**kwargs)

    def action_use_credits(self, **kwargs):
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

    # UNLINKERS

    def unlink_transfer_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_transfer_record_id_not_found(kwargs)
        log.info('Attempting to fetch transfer sheet...')
        transfer_sheet = self.fetch_credit_ewallet_transfer_sheet()
        if not transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action',
        )
        unlink = transfer_sheet.credit_transfer_sheet_controller(
            action='remove', **sanitized_command_chain
        )
        if not unlink or isinstance(unlink, dict) and unlink.get('failed'):
            return self.warning_could_not_unlink_transfer_record(kwargs)
        command_chain_response = {
            'failed': False,
            'transfer_sheet': transfer_sheet.fetch_transfer_sheet_id(),
            'transfer_record': kwargs['record_id'],
        }
        return command_chain_response

    def unlink_transfer_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_transfer_list_id_specified(kwargs)
        transfer_sheet = self.fetch_credit_wallet_transfer_sheet_by_id(
            code=kwargs['list_id'],
            active_session=kwargs['active_session'],
        )
        check = self.check_transfer_sheet_belongs_to_credit_ewallet(
            transfer_sheet
        )
        if not check:
            return self.warning_transfer_sheet_does_not_belong_to_credit_ewallet(
                kwargs, transfer_sheet, check
            )
        try:
            kwargs['active_session'].query(
                CreditTransferSheet
            ).filter_by(
                transfer_sheet_id=kwargs['list_id']
            ).delete()
        except:
            return self.error_could_not_remove_transfer_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'transfer_sheet': kwargs['list_id'],
        }
        return command_chain_response

    def unlink_time_record(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'time'
        )
        unlink = credit_clock.main_controller(
            controller='user', ctype='action', action='unlink', unlink='time',
            time='record', **sanitized_command_chain
        )
        return self.warning_could_not_unlink_time_record(kwargs) \
            if not unlink or isinstance(unlink, dict) and unlink.get('failed') \
            else unlink

#   @pysnooper.snoop()
    def unlink_conversion_list(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'conversion'
        )
        unlink = credit_clock.main_controller(
            controller='user', ctype='action', action='unlink', unlink='conversion',
            conversion='list', **sanitized_command_chain
        )
        return self.warning_could_not_unlink_conversion_sheet(
            kwargs, credit_clock, unlink
        ) if not unlink or isinstance(unlink, dict) \
            and unlink.get('failed') else unlink

    def unlink_time_list(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'time'
        )
        unlink = credit_clock.main_controller(
            controller='user', ctype='action', action='unlink', unlink='time',
            time='list', **sanitized_command_chain
        )
        return self.warning_could_not_unlink_time_sheet(
            kwargs, credit_clock, unlink
        ) if not unlink or isinstance(unlink, dict) and unlink.get('failed') \
            else unlink

    def unlink_invoice_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_invoice_list_id_specified(kwargs)
        try:
            kwargs['active_session'].query(
                CreditInvoiceSheet
            ).filter_by(
                invoice_sheet_id=kwargs['list_id']
            ).delete()
        except:
            self.error_could_not_remove_invoice_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'invoice_sheet': kwargs['list_id'],
        }
        return command_chain_response

    def unlink_conversion_record(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.error_could_not_fetch_credit_ewallet_credit_clock(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'conversion'
        )
        unlink = credit_clock.main_controller(
            controller='user', ctype='action', action='unlink', unlink='conversion',
            conversion='record', **sanitized_command_chain
        )
        return self.warning_could_not_unlink_conversion_record(kwargs) \
            if not unlink or isinstance(unlink, dict) and unlink.get('failed') \
            else unlink

    def unlink_invoice_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_invoice_record_id_not_found(kwargs)
        log.info('Attempting to fetch invoice sheet...')
        invoice_sheet = self.fetch_credit_ewallet_invoice_sheet()
        if not invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action',
        )
        unlink = invoice_sheet.credit_invoice_sheet_controller(
            action='remove', **sanitized_command_chain
        )
        if not unlink or isinstance(unlink, dict) and unlink.get('failed'):
            return self.warning_could_not_unlink_invoice_record(kwargs)
        command_chain_response = {
            'failed': False,
            'invoice_sheet': invoice_sheet.fetch_invoice_sheet_id(),
            'invoice_record': kwargs['record_id'],
        }
        return command_chain_response

    def unlink_transfer_sheet(self, **kwargs):
        log.debug('TODO - DEPRECATED')
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
            'use': self.action_use_credits,
            'interogate': self.action_interogate_credits,
            'unlink': self.action_unlink,
            'switch_sheet': self.action_switch_credit_wallet_sheet,
            'switch_clock': self.action_switch_credit_wallet_clock,
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
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def warning_could_not_unlink_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink time sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_record(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not unlink conversion record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_invoice_sheet_does_not_belong_to_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Invoice sheet does not belong to active credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_transfer_sheet_does_not_belong_to_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Transfer sheet does not belong to active credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_clock_does_not_belong_to_current_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Clock does not belong to active credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not switch credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_invoice_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch invoice sheet. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink invoice sheet record. '\
                       'Command chain details : {}'.format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_transfer_sheet(self, command_chain, *args, **kwargs):
        command_chain_response = {
            'failed': True,
            'warning': 'Could not fetch transfer sheet. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_invoice_sheet_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'No invoice sheet found by id. Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_transfer_sheet_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'No transfer sheet found by id. Command chain details : {}'.format(command_chain),
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

    # ERRORS
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_could_not_unlink_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not unlink credit clock. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_active_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set active ewallet credit clock. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_client_user(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet client user. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_active_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set active ewallet session. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_create_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet create date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_active_session_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet active session id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_client_user_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet client user id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_ewallet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_clock_to_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit clock to archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_to_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set invoice sheet to archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_transfer_sheet_to_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set transfer sheet to archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_ewallet_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set ewallet write date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set ewallet invoice sheet archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_archive_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No invoice sheet archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_transfer_sheet_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set ewallet transfer sheet archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_sheet_archive_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer sheet archive found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_clock_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set ewallet credit clock archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_clock_archive_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credit clock archive found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_ewallet_credits(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set ewallet credits. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credits_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No ewallet credits found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_ewallet_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet reference. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet reference found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_client_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet client id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client id found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_ewallet_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet id. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet id found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet credit clock. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet transfer sheet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set credit ewallet invoice sheet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_transfer_record_id_not_found(self, command_chain, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer record id found. Details: {}, {}'
                     .format(command_chain, args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No active session found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_clock_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet credit clock id found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_transfer_sheet_found(self):
        log.error('No credit ewallet transfer sheet found.')
        return False

    def error_no_credit_ewallet_invoice_sheet_found(self):
        log.error('No credit ewallet invoice sheet found.')
        return False

    def error_could_not_remove_invoice_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove invoice sheet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_list_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No transfer list id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_transfer_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove transfer sheet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_unlink_time_targe_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet unlink time target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_unlink_conversion_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet unlink conversion target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invoice_record_id_not_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Invoice record id not found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_unlink_invoice_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet unlink invoice target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_unlink_transfer_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet unlink transfer target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_unlink_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No credit ewallet unlink target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_credit_ewallet_credit_clock(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch credit ewallet credit clock. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_invoice_sheet_id(self, command_chain):
        log.error()
        command_chain_response = {
            'failed': True,
            'error': 'Invalid invoice sheet id. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_transfer_sheet_id(self, command_chain):
        log.error()
        command_chain_response = {
            'failed': True,
            'error': 'Invalid transfer sheet id. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_switch_credit_ewallet_transfer_sheet_indentifier_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No switch credit ewallet transfer sheet identifier specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_ewallet_credit_clock_found(self):
        log.error('No credit clock found.')
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

    def error_no_credit_clock_found(self):
        log.error('No credit clock found.')
        return False

    def error_no_transfer_sheet_found(self):
        log.error('No transfer sheet found.')
        return False

    def error_no_invoice_sheet_found(self):
        log.error('No invoice sheet found.')
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


