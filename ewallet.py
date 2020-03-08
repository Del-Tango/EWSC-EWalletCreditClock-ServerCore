#from validate_email import validate_email
from itertools import count
from sqlalchemy import Table, Column, String, Integer, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship, backref

from ewallet_login import EWalletLogin
from ewallet_logout import EWalletLogout
from base.res_user import ResUser
from base.res_utils import ResUtils, Base
from base.credit_wallet import CreditEWallet
from base.contact_list import ContactList
from base.config import Config

import time
import datetime
import random
import hashlib
import logging
import datetime
import pysnooper
import threading

config = Config()
res_utils = ResUtils()

def log_init():
    log_config = config.log_config

    log = logging.getLogger(log_config['log_name'])
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(
        log_config['log_dir'] + '/' + log_config['log_file'], 'a'
        )
    formatter = logging.Formatter(
        log_config['log_record_format'],
        log_config['log_date_format']
        )
    logging.Formatter.converter = res_utils.fetch_now_eet
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    return log

log = log_init()

'''
    [ NOTE ]: Many2many table for user sessions.
'''
class SessionUser(Base):
    __tablename__ = 'session_user'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('ewallet.id'))
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    datetime = Column(DateTime, default=datetime.datetime.now())
    user = relationship('ResUser', backref=backref('session_user', cascade='all, delete-orphan'))
    session = relationship('EWallet', backref=backref('session_user', cascade='all, delete-orphan'))

'''
    [ NOTE ]: Ewallet session.
'''
class EWallet(Base):
    __tablename__ = 'ewallet'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String)
    create_date = Column(Date)
    session = None
    # O2O
    contact_list = relationship(
       'ContactList', back_populates='active_session',
       )
    # O2O
    credit_wallet = relationship(
       'CreditEWallet', back_populates='active_session',
       )
    # O2O
    active_user = relationship(
       'ResUser', back_populates='active_session',
       )
    # M2M
    user_account_archive = relationship('ResUser', secondary='session_user')

#   @pysnooper.snoop(
#           config.log_config['log_dir'] + '/' + config.log_config['log_file']
#           )
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.session = kwargs.get('session') or res_utils.session_factory()
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.contact_list = kwargs.get('contact_list') or []
        self.credit_wallet = kwargs.get('credit_wallet') or []
        self.active_user = kwargs.get('active_user') or []
        self.user_account_archive = kwargs.get('user_account_archive') or []

    # TODO - Apply ORM
    def fetch_user_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_user_id_found()
        log.info('Successfully fetched user by id.')
        return self.user_account_archive.get(kwargs['code'])
    # TODO - Apply ORM
    def fetch_user_by_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_user_name_found()
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_name() == kwargs['code']:
                log.info('Successfully fetched user by name.')
                return self.user_account_archive[item]
        return self.warning_no_user_account_found('name', kwargs['code'])
    # TODO - Apply ORM
    def fetch_user_by_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_user_email_found()
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_email() == kwargs['code']:
                log.info('Successfully fetched user by email.')
                return self.user_account_archive[item]
        return self.warning_no_user_account_found('email', kwargs['code'])
    # TODO - Apply ORM
    def fetch_user_by_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_user_phone_found()
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_phone() == kwargs['code']:
                log.info('Successfully fetched user by phone.')
                return self.user_account_archive[item]
        return self.warning_no_user_account_found('phone', kwargs['code'])
    # TODO - Apply ORM
    def fetch_user_by_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_user_alias_found()
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_alias() == kwargs['code']:
                log.info('Successfully fetched user by alias.')
                return self.user_account_archive[item]
        return self.warning_no_user_account_found('alias', kwargs['code'])

    def fetch_user(self, **kwargs):
        log.debug('')
        if not kwargs.get('identifier'):
            return self.error_no_user_identifier_found()
        _handlers = {
            'id': self.fetch_user_by_id,
            'name': self.fetch_user_by_name,
            'email': self.fetch_user_by_email,
            'phone': self.fetch_user_by_phone,
            'alias': self.fetch_user_by_alias,
            }
        return _handlers[kwargs['identifier']](**kwargs)

    def fetch_active_session_user(self):
        log.debug('')
        if not len(self.active_user):
            return self.error_no_session_active_user_found()
        return self.active_user[0]

    def fetch_active_session_credit_wallet(self):
        log.debug('')
        if not len(self.credit_wallet):
            return self.error_no_session_credit_wallet_found()
        return self.credit_wallet[0]

    def fetch_active_session_credit_clock(self):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet()
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        return _credit_clock or False

    def fetch_active_session_contact_list(self):
        log.debug('')
        if not len(self.contact_list):
            return self.error_no_session_contact_list_found()
        return self.contact_list[0]

    def fetch_next_active_session_user(self, **kwargs):
        log.debug('')
        if not len(self.user_account_archive):
            return self.error_empty_session_user_account_archive()
        _active_user = kwargs.get('active_user')
        _filtered = [
                item for item in self.user_account_archive
                if item is not _active_user
                ]
        return [] if not _filtered else _filtered[0]

    def set_session_active_user(self, active_user):
        log.debug('')
        self.active_user = active_user if isinstance(active_user, list) \
                else [active_user]
        return self.active_user

#   @pysnooper.snoop('logs/ewallet.log')
    def set_session_credit_wallet(self, credit_wallet):
        log.debug('')
        self.credit_wallet = credit_wallet if isinstance(credit_wallet, list) \
                else [credit_wallet]
        return self.credit_wallet

    def set_session_contact_list(self, contact_list):
        log.debug('')
        self.contact_list = contact_list if isinstance(contact_list, list) \
                else [contact_list]
        return self.contact_list

    def set_session_data(self, data_dct):
        log.debug('')
        _handlers = {
                'active_user': self.set_session_active_user,
                'credit_wallet': self.set_session_credit_wallet,
                'contact_list': self.set_session_contact_list,
                }
        for item in data_dct:
            if item in _handlers and data_dct[item]:
                _handlers[item](data_dct[item])
        return data_dct

    def clear_session_active_user(self):
        log.debug('')
        self.active_user = []
        return True

    def clear_session_credit_wallet(self):
        log.debug('')
        self.credit_wallet = []
        return True

    def clear_session_contact_list(self):
        log.debug('')
        self.contact_list = []
        return True

    def clear_session_user_account_archive(self):
        log.debug('')
        self.user_account_archive = []
        return True

    def clear_active_session_user_data(self, data_dct):
        log.debug('')
        _handlers = {
                'active_user': self.clear_session_active_user,
                'credit_wallet': self.clear_session_credit_wallet,
                'contact_list': self.clear_session_contact_list,
                'user_account_archive': self.clear_session_user_account_archive,
                }
        for item in data_dct:
            if item in _handlers and data_dct[item]:
                _handlers[item]()
        return data_dct

    def update_session_from_user(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_active_user'):
            return self.error_no_session_active_user_found()
        _user = kwargs['session_active_user']
        _session_data = {
                'active_user': _user,
                'credit_wallet': _user.fetch_user_credit_wallet(),
                'contact_list': _user.fetch_user_contact_list(),
                }
        _set_data = self.set_session_data(_session_data)
        log.info('Successfully updated ewallet session from current active user.')
        return True

#   @pysnooper.snoop()
    def update_user_account_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('user'):
            return self.error_no_user_object_found()
        self.user_account_archive.append(kwargs['user'])
        log.info(
                'Successfully updated session user account archive with user {}.' \
                .format(kwargs['user'].fetch_user_name())
                )
        return self.user_account_archive

    def action_reset_user_password(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('user_pass'):
            return self.error_no_user_password_found()
        _pass_check_func = EWalletCreateAccount().check_user_pass
        _pass_hash_func = EWalletLogin().hash_password
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_pass',
                password=kwargs['user_pass'],
                pass_check_func=_pass_check_func,
                pass_hash_func=_pass_hash_func,
                )

    def action_reset_user_email(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('user_email'):
            return self.error_no_user_email_found()
        _email_check_func = EwalletCreateAccount().check_user_email
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_email',
                email=kwargs['user_email'],
                email_check_func=_email_check_func,
                )

    def action_reset_user_alias(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('user_alias'):
            return self.error_no_user_alias_found()
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_alias',
                alias=kwargs['user_alias']
                )

    def action_reset_user_phone(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('user_phone'):
            return self.error_no_user_phone_found()
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_phone',
                phone=kwargs['user_phone']
                )

    def action_create_new_user_account(self, **kwargs):
        log.debug('')
        session_create_account = EWalletLogin().ewallet_login_controller(
                action='new_account',
                user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
                user_email=kwargs.get('user_email'),
                active_session=self.session,
                )
        if not session_create_account:
            return self.warning_could_not_create_user_account(kwargs['user_name'])
        self.session.add(session_create_account)
        log.info('Successfully created new user account.')
        self.update_user_account_archive(
                user=session_create_account,
                )
        self.update_session_from_user(
                session_active_user=session_create_account,
                )
        self.session.commit()
        return session_create_account

    def action_create_new_conversion_credits_to_clock(self, **kwargs):
        log.debug('')
        _credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not _credit_clock:
            return self.error_could_not_fetch_active_session_credit_clock()
        return _credit_clock.main_controller(**kwargs)

    def action_create_new_conversion_clock_to_credits(self, **kwargs):
        log.debug('')
        _credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not _credit_clock:
            return self.error_could_not_fetch_active_session_credit_clock()
        return _credit_clock.main_controller(**kwargs)

    def action_create_new_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_type_specified()
        _handlers = {
                'credits2clock': self.action_create_new_conversion_credits_to_clock,
                'clock2credits': self.action_create_new_conversion_clock_to_credits,
                }
        return _handlers[kwargs['conversion']](**kwargs)

    def action_create_new_credit_wallet(self, **kwargs):
        log.debug('')
        if not self.active_user:
            return self.error_no_session_active_user_found()
        _new_wallet = self.active_user.user_controller(
                ctype='action', action='create', target='credit_wallet',
                reference=kwargs.get('reference'),
                credits=kwargs.get('credits'),
                )
        if not _new_wallet:
            return self.warning_could_not_create_credit_wallet(
                self.active_user.fetch_user_name()
                )
        log.info('Successfully created new credit wallet.')
        return _new_wallet

    def action_create_new_credit_clock(self, **kwargs):
        log.debug('')
        if not self.active_user:
            return self.error_no_session_active_user_found()
        _new_clock = self.active_user.user_controller(
                ctype='action', action='create', target='credit_clock',
                reference=kwargs.get('reference'),
                credit_clock=kwargs.get('credit_clock'),
                )
        if not _new_clock:
            return self.warning_could_not_create_credit_clock(
                self.active_user.fetch_user_name()
                )
        log.info('Successfully created new credit clock.')
        return _new_clock

    def action_create_new_contact_list(self, **kwargs):
        log.debug('')
        if not self.active_user:
            return self.error_no_session_active_user_found()
        _new_list = self.active_user.user_controller(
                ctype='action', action='create', target='contact_list',
                reference=kwargs.get('reference'),
                )
        if not _new_list:
            return self.warning_could_not_create_contact_list(
                self.active_user.fetch_user_name()
                )
        log.info('Successfully created new contact list.')
        return _new_list

    def action_create_new_contact_record(self, **kwargs):
        log.debug('')
        if not self.session_contact_list:
            return self.error_no_active_session_contact_list_found(
                self.active_user.fetch_user_name()
                )
        _new_record = self.session_contact_list.contact_list_controller(
                action='create', user_name=kwargs.get('user_name'),
                user_email=kwargs.get('user_email'),
                user_phone=kwargs.get('user_phone'),
                notes=kwargs.get('notes'),
                )
        if not _new_record:
            return self.warning_could_not_create_contact_record(
                self.active_user.fetch_user_name()
                )
        log.info('Successfully created new contact record.')
        return _new_record

    def action_create_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_found()
        _handlers = {
                'list': self.action_create_new_contact_list,
                'record': self.action_create_new_contact_record,
                }
        return _handlers[kwargs['contact']](**kwargs)

    # TODO - FIX ME
    def action_create_new_transfer(self, **kwargs):
        log.debug('')
        if not self.credit_wallet or not kwargs.get('active_session') or \
                not kwargs.get('transfer_type') or \
                not kwargs.get('partner_ewallet'):
            return self.error_handler_action_create_new_transfer(
                    session_wallet=self.credit_wallet,
                    transfer_type=kwargs.get('transfer_type'),
                    partner_wallet=kwargs.get('partner_ewallet'),
                    active_session=kwargs.get('active_session'),
                    )
        _credit_wallet = self.fetch_active_session_credit_wallet()
        return False if not _credit_wallet else _credit_wallet.user_controller(
                action='transfer', transfer_type=kwargs['transfer_type'],
                partner_ewallet=kwargs['partner_ewallet'],
                credits=kwargs['credits'] or 0,
                reference=kwargs.get('reference'),
                transfer_from=kwargs.get('transfer_from'),
                transfer_to=kwargs.get('transfer_to'),
                active_session=kwargs['active_session']
                )

    def action_unlink_user_account(self, **kwargs):
        log.debug('')
        if not self.user_account_archive or not kwargs.get('user_id'):
            return self.error_handler_action_unlink_user_account(
                    archive=self.user_account_archive,
                    user_id=kwargs.get('user_id'),
                    )
        _user = self.fetch_user(identifier='id', code=kwargs['user_id'])
        if not _user:
            self.warning_could_not_fetch_user_by_id(kwargs['user_id'])
        return self.user_account_archive.pop(kwargs['user_id'])

    def action_unlink_credit_wallet(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('wallet_id'):
            return self.error_handler_action_unlink_credit_wallet(
                    session_user=self.active_user,
                    wallet_id=kwargs.get('wallet_id'),
                    )
        return self.active_user.user_controller(
                ctype='action', action='unlink', target='credit_wallet',
                wallet_id=kwargs['wallet_id'],
                )

    def action_unlink_contact_list(self, **kwargs):
        log.debug('')
        if not self.active_user or not kwargs.get('list_id'):
            return self.error_handler_action_unlink_contact_list(
                    session_user=self.active_user,
                    list_id=kwargs.get('list_id'),
                    )
        return self.active_user.user_controller(
                ctype='action', action='unlink', target='contact_list',
                list_id=kwargs['list_id']
                )

    def action_unlink_contact_record(self, **kwargs):
        log.debug('')
        if not self.session_contact_list or not kwargs.get('record_id'):
            return self.error_handler_action_unlink_contact_record(
                    contact_list=self.session_contact_list,
                    record_id=kwargs.get('record_id'),
                    )
        return self.session_contact_list.contact_list_controller(
                action='update', update_type='remove',
                record_id=kwargs['record_id'],
                )

    def action_unlink_invoice_list(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return self.error_handler_action_unlink_invoice_list(
                    credit_wallet=self.session_credit_wallet,
                    list_id=kwargs.get('list_id'),
                    )
        return self.session_credit_wallet.main_controller(
                controller='system', action='unlink_sheet', sheet='invoice',
                sheet_id=kwargs['list_id'],
                )

    def action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_unlink_invoice_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        _invoice_list = self.session_credit_wallet.fetch_invoice_sheet()
        if not _invoice_list:
            return self.warning_could_not_fetch_credit_wallet_invoice_sheet()
        return _invoice_list.credit_invoice_sheet_controller(
                action='remove', record_id=kwargs['record_id'],
                )

    def action_unlink_transfer_list(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return self.error_handler_action_unlink_transfer_list(
                    credit_wallet=self.session_credit_wallet,
                    list_id=kwargs.get('list_id'),
                    )
        return self.session_credit_wallet.main_controller(
                controller='system', action='unlink_sheet', sheet='transfer',
                sheet_id=kwargs['list_id'],
                )

    def action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_unlink_transfer_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active transfer sheet...')
        _transfer_list = self.session_credit_wallet.fetch_transfer_sheet()
        if not _transfer_list:
            return self.warning_could_not_fetch_credit_wallet_transfer_sheet()
        return _transfer_list.credit_transfer_sheet_controller(
                action='remove', record_id=kwargs['record_id'],
                )

    def action_unlink_time_list(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return self.error_handler_action_unlink_time_list(
                    credit_wallet=self.session_credit_wallet,
                    list_id=kwargs.get('list_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        return _credit_clock.main_controller(
                controller='system', action='unlink', unlink='sheet',
                sheet_type='time', sheet_id=kwargs['list_id']
                )

    def action_unlink_time_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            log.error('No active session credit wallet or time record id found.')
            return self.error_handler_action_unlink_time_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active time sheet...')
        _time_list = _credit_clock.fetch_credit_clock_time_sheet()
        if not _time_list:
            return self.warning_could_not_fetch_time_sheet()
        return _time_list.credit_clock_time_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )

    def action_unlink_conversion_list(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return self.error_handler_action_unlink_conversion_list(
                    credit_wallet=self.session_credit_wallet,
                    list_id=kwargs.get('list_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        return _credit_clock.main_controller(
                controller='system', action='unlink', unlink='sheet',
                sheet_type='conversion', sheet_id=kwargs['list_id']
                )

    def action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_unlink_conversion_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        if not _conversion_list:
            return self.warning_could_not_fetch_conversion_sheet()
        return _conversion_list.credit_clock_conversion_sheet_controller(
                action='remove', record_id=kwargs['record_id']
                )

    def action_unlink_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'list': self.action_unlink_contact_list,
                'record': self.action_unlink_contact_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'list': self.action_unlink_invoice_list,
                'record': self.action_unlink_invoice_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'list': self.action_unlink_transfer_list,
                'record': self.action_unlink_transfer_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'list': self.action_unlink_time_list,
                'record': self.action_unlink_time_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'list': self.action_unlink_conversion_list,
                'record': self.action_unlink_conversion_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_view_user_account(self, **kwargs):
        log.debug('')
        if not self.active_user:
            return self.error_no_session_active_user_found()
        res = self.active_user[0].fetch_user_values()
        log.debug(res)
        return res

    def action_view_credit_wallet(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_no_session_credit_wallet_found()
        res = _credit_wallet.fetch_credit_ewallet_values()
        log.debug(res)
        return res

    def action_view_credit_clock(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        res = _credit_clock.fetch_credit_clock_values()
        log.debug(res)
        return res

    def action_view_contact_list(self, **kwargs):
        log.debug('')
        _contact_list = self.fetch_active_session_contact_list()
        if not _contact_list:
            return self.error_no_session_contact_list_found()
        res = _contact_list.fetch_contact_list_values()
        log.debug(res)
        return res

    def action_view_contact_record(self, **kwargs):
        log.debug('')
        if not self.contact_list or not kwargs.get('record_id'):
            return self.error_handler_action_view_contact_record(
                    contact_list=self.contact_list,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch contact record by id...')
        _record = self.contact_list.fetch_contact_list_record(
                search_by='id' if not kwargs.get('search_by') else kwargs['search_by'],
                code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_contact_record()
        res = _record.fetch_record_values()
        log.debug(res)
        return res

    def action_view_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_target_specified()
        _handlers = {
                'list': self.action_view_contact_list,
                'record': self.action_view_contact_record,
                }
        return _handlers[kwargs['contact']](**kwargs)

    def action_view_invoice_list(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active invoice sheet...')
        _invoice_sheet = _credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not _invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet()
        res = _invoice_sheet.fetch_invoice_sheet_values()
        log.debug(res)
        return res

    def action_view_invoice_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_invoice_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active invoice sheet...')
        _invoice_sheet = self.session_credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not _invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet()
        log.info('Attempting to fetch invoice record by id...')
        _record = _invoice_sheet.fetch_credit_invoice_records(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_invoice_sheet_record()
        res = _record.fetch_record_values()
        log.debug(res)
        return res

    def action_view_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        _handlers = {
                'list': self.action_view_invoice_list,
                'record': self.action_view_invoice_record,
                }
        return _handlers[kwargs['invoice']](**kwargs)

    def action_view_transfer_list(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active transfer sheet...')
        _transfer_sheet = _credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not _transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet()
        res = _transfer_sheet.fetch_transfer_sheet_values()
        log.debug(res)
        return res

    def action_view_transfer_record(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_transfer_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active transfer sheet...')
        _transfer_sheet = _credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not _transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet()
        log.info('Attempting to fetch transfer record by id...')
        _record = _transfer_sheet.fetch_transfer_sheet_records(
                search_by='id', code=kwargs['record_id'], active_session=self.session
                )
        if not _record:
            return self.warning_could_not_fetch_transfer_sheet_record()
        res = _record.fetch_record_values()
        log.debug(res)
        return res

    def action_view_time_list(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active time sheet...')
        _time_sheet = _credit_clock.fetch_credit_clock_time_sheet()
        if not _time_sheet:
            return self.warning_could_not_fetch_time_sheet()
        res = _time_sheet.fetch_time_sheet_values()
        log.debug(res)
        return res

    def action_view_time_record(self, **kwargs):
        log.debug('')
        _credit_wallet = self.fetch_active_session_credit_wallet()
        if not _credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_time_record(
                    credit_wallet=_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active time sheet...')
        _time_sheet = _credit_clock.fetch_credit_clock_time_sheet()
        if not _time_sheet:
            return self.warning_could_not_fetch_time_sheet()
        log.info('Attempting to fetch time record...')
        _record = _time_sheet.fetch_time_sheet_record(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_time_sheet_record()
        res = _record.fetch_record_data()
        log.debug(res)
        return res

    def action_view_conversion_list(self, **kwargs):
        log.debug('')
        _credit_clock = self.fetch_active_session_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        if not _conversion_list:
            return self.warning_could_not_fetch_conversion_sheet()
        res = _conversion_list.fetch_conversion_sheet_values()
        log.debug(res)
        return res

    def action_view_conversion_record(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_conversion_record(
                    credit_wallet=self.session_credit_wallet,
                    record_id=kwargs.get('record_id'),
                    )
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        if not _conversion_list:
            return self.warning_could_not_fetch_conversion_sheet()
        log.info('Attempting to fetch conversion record by id...')
        _record = _conversion_list.fetch_conversion_sheet_record(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return self.warning_could_not_fetch_conversion_record()
        res = _record.fetch_record_data()
        log.debug(res)
        return res

    def action_view_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_transfer_view_target_specified()
        _handlers = {
                'list': self.action_view_transfer_list,
                'record': self.action_view_transfer_record,
                }
        return _handlers[kwargs['transfer']](**kwargs)

    def action_view_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_time_view_target_specified()
        _handlers = {
                'list': self.action_view_time_list,
                'record': self.action_view_time_record,
                }
        return _handlers[kwargs['time']](**kwargs)

    def action_view_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_view_target_specified()
        _handlers = {
                'list': self.action_view_conversion_list,
                'record': self.action_view_conversion_record,
                }
        return _handlers[kwargs['conversion']](**kwargs)

    # TODO
    def action_system_user_check(self, **kwargs):
        pass

    # TODO
    def action_system_session_check(self, **kwargs):
        pass

#   @pysnooper.snoop('logs/ewallet.log')
    def action_system_user_logout(self, **kwargs):
        log.debug('')
        _user = self.fetch_active_session_user()
        _set_user_state = _user.set_user_state(
                set_by='code', state_code=0
                )
        _search_user_for_session = self.fetch_next_active_session_user(active_user=_user)
        _clear_user_data = self.clear_active_session_user_data({
            'active_user':True if not _search_user_for_session else False,
            'credit_wallet':True, 'contact_list':True,
            })
        return True if not _search_user_for_session \
                else _search_user_for_session

    # [ NOTE ]: Allows multiple logged in users to switch.
    def action_system_user_update(self, **kwargs):
        log.debug('')
        if not kwargs.get('user'):
            return self.error_no_user_specified()
        if kwargs['user'] not in self.user_account_archive:
            return self.warning_user_not_in_session_archive()
        _set_user = self.set_session_active_user(active_user=kwargs['user'])
        self.update_session_from_user(session_active_user=kwargs['user'])
        return self.active_user

    def action_system_session_update(self, **kwargs):
        log.debug('')
        kwargs.update({'session_active_user': self.fetch_active_session_user()})
        _update = self.update_session_from_user(**kwargs)
        return _update or False

    def handle_system_action_update(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_update_target_specified()
        _handlers = {
                'user': self.action_system_user_update,
                'session': self.action_system_session_update,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_system_action_check(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_check_target_specified()
        _handlers = {
                'user': self.action_system_user_check,
                'session': self.action_system_session_check,
                }
        return _handlers[kwargs['target']](**kwargs)

    '''
        [ RETURN ]: Loged in user if login action succesful, else False.
    '''
#   @pysnooper.snoop('logs/ewallet.log')
    def handle_user_action_login(self, **kwargs):
        log.debug('')
        _login_record = EWalletLogin()
        session_login = _login_record.ewallet_login_controller(
                action='login', user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
                user_archive=self.user_account_archive,
                active_session=self.session,
                )
        if not session_login:
            return self.warning_could_not_login()
        self.session.add(_login_record)
        self.user_account_archive.append(session_login)
        self.action_system_user_update(user=session_login)
        self.session.commit()
        log.info('User successfully loged in.')
        return session_login

    '''
        [ RETURN ]: True if no other users loged in. If loged in users found in
        user account archive, returns next.
    '''
    def handle_user_action_logout(self, **kwargs):
        log.debug('')
        _user = self.fetch_active_session_user()
        _session_logout = self.action_system_user_logout()
        _logout_record = EWalletLogout(
                user_id=_user.fetch_user_id(),
                logout_status=False if not _session_logout else True,
                )
        self.session.add(_logout_record)
        if not _session_logout:
            self.session.rollback()
            return self.warning_could_not_logout()
        _update_next = False if isinstance(_session_logout, bool) \
                else self.action_system_user_update(user=_session_logout)
        self.user_account_archive.remove(_user)
        self.session.commit()
        log.info('User successfully loged out.')
        return _update_next or True

    def handle_user_action_reset(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_reset_target_specified()
        _handlers = {
                'user_alias': self.action_reset_user_alias,
                'user_pass': self.action_reset_user_password,
                'user_email': self.action_reset_user_email,
                'user_phone': self.action_reset_user_phone,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_create(self, **kwargs):
        log.debug('')
        if not kwargs.get('create'):
            return self.error_no_user_create_target_specified()
        _handlers = {
                'account': self.action_create_new_user_account,
                'credit_wallet': self.action_create_new_credit_wallet,
                'credit_clock': self.action_create_new_credit_clock,
                'transfer': self.action_create_new_transfer,
                'conversion': self.action_create_new_conversion,
                'contact': self.action_create_new_contact,
                }
        return _handlers[kwargs['create']](**kwargs)

    def action_start_credit_clock_timer(self, **kwargs):
        log.debug('')
        if not self.credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        return _credit_clock.main_controller(
                controller='user', action='start'
                )

    def action_stop_credit_clock_timer(self, **kwargs):
        log.debug('')
        if not self.session_credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        return _credit_clock.main_controller(
                controller='user', action='stop'
                )

    def handle_user_action_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('timer'):
            return self.error_no_timer_action_specified()
        _handlers = {
                'start': self.action_start_credit_clock_timer,
                'stop': self.action_stop_credit_clock_timer,
                }
        return _handlers[kwargs['timer']](**kwargs)

    def handle_user_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_view_target_specified()
        _handlers = {
                'account': self.action_view_user_account,
                'credit_wallet': self.action_view_credit_wallet,
                'credit_clock': self.action_view_credit_clock,
                'contact': self.action_view_contact,
                'invoice': self.action_view_invoice,
                'transfer': self.action_view_transfer,
                'time': self.action_view_time,
                'conversion': self.action_view_conversion,
                }
        return _handlers[kwargs['view']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        _handlers = {
                'account': self.action_unlink_user_account,
                'credit_wallet': self.action_unlink_credit_wallet,
                'credit_clock': self.action_unlink_credit_clock,
                'contact': self.action_unlink_contact,
                'invoice': self.action_unlink_invoice,
                'transfer': self.action_unlink_transfer,
                'time': self.action_unlink_time,
                'conversion': self.action_unlink_conversion,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    # TODO
    def handle_user_event_signal(self, **kwargs):
        pass

    # TODO
    def handle_user_event_notification(self, **kwargs):
        pass

    # TODO
    def handle_user_event_request(self, **kwargs):
        pass

    # TODO
    def handle_system_event_signal(self, **kwargs):
        pass

    # TODO
    def handle_system_event_notification(self, **kwargs):
        pass

    # TODO
    def handle_system_event_request(self, **kwargs):
        pass

    def ewallet_user_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_action_specified()
        _handlers = {
                'login': self.handle_user_action_login,
                'logout': self.handle_user_action_logout,
                'create': self.handle_user_action_create,
                'time': self.handle_user_action_time,
                'reset': self.handle_user_action_reset,
                'view': self.handle_user_action_view,
                'unlink': self.handle_user_action_unlink,
                }
        return _handlers[kwargs['action']](**kwargs)

    def ewallet_user_event_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_user_event_specified()
        _handlers = {
                'signal': self.handle_user_event_signal,
                'notification': self.handle_user_event_notification,
                'request': self.handle_user_event_request,
                }
        return _handlers[kwargs['event']](**kwargs)

    def ewallet_system_event_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_system_event_specified()
        _handlers = {
                'signal': self.handle_system_event_signal,
                'notification': self.handle_system_event_notification,
                'request': self.handle_system_event_request,
                }
        return _handlers[kwargs['event']](**kwargs)

    def ewallet_system_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_action_specified()
        _handlers = {
                'check': self.handle_system_action_check,
                'update': self.handle_system_action_update,
                }
        return _handlers[kwargs['action']](**kwargs)

    def ewallet_system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_controller_type_specified()
        _handlers = {
                'action': self.ewallet_system_action_controller,
                'event': self.ewallet_system_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    def ewallet_user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_user_controller_type_specified()
        _handlers = {
                'action': self.ewallet_user_action_controller,
                'event': self.ewallet_user_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    # [ NOTE ]: Main
    def ewallet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_ewallet_controller_specified()
        _controllers = {
                'system': self.ewallet_system_controller,
                'user': self.ewallet_user_controller,
                'test': self.test_ewallet,
                }
        return _controllers[kwargs['controller']](**kwargs)

    def error_handler_action_create_new_transfer(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'session_wallet': kwargs.get('session_wallet'),
                    'transfer_type': kwargs.get('transfer_type'),
                    'partner_wallet': kwargs.get('partner_wallet'),
                    },
                'handlers': {
                    'session_wallet': self.error_no_session_credit_wallet_found,
                    'transfer_type': self.error_no_transfer_type_found,
                    'partner_wallet': self.error_no_partner_credit_wallet_found,
                    }
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_user_account(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'archive': kwargs.get('archive'),
                    'user_id': kwargs.get('user_id'),
                    },
                'handlers': {
                    'archive': self.error_empty_session_user_account_archive,
                    'user_id': self.error_no_user_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]
        return False

    def error_handler_action_unlink_credit_wallet(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'session_user': kwargs.get('session_user'),
                    'wallet_id': kwargs.get('wallet_id'),
                    },
                'handlers': {
                    'session_user': self.error_no_active_session_user_found,
                    'wallet_id': self.error_no_wallet_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_contact_list(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'session_user': kwargs.get('session_user'),
                    'list_id': kwargs.get('list_id'),
                    },
                'handlers': {
                    'session_user': self.error_no_active_session_user_found,
                    'list_id': self.error_no_contact_list_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_contact_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'contact_list': kwargs.get('contact_list'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'contact_list': self.error_no_session_contact_list_found,
                    'record_id': self.error_no_contact_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_invoice_list(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'list_id': kwargs.get('list_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'list_id': self.error_no_invoice_list_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_invoice_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_invoice_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_transfer_list(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'list_id': kwargs.get('list_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'list_id': self.error_no_transfer_sheet_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_transfer_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_transfer_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_time_list(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_clock'),
                    'list_id': kwargs.get('list_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'list_id': self.error_no_time_sheet_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_time_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_time_sheet_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_conversion_list(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'list_id': kwargs.get('list_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'list_id': self.error_no_conversion_sheet_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_unlink_conversion_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_conversion_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_view_contact_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'contact_list': kwargs.get('contact_list'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'contact_list': self.error_no_session_contact_list_found,
                    'record_id': self.error_no_contact_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_view_invoice_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_invoice_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_view_transfer_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_transfer_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_view_time_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_time_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_action_view_conversion_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_conversion_record_id_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return_reasons_and_handlers['handlers'][item]()
        return False

    def error_no_transfer_view_target_specified(self):
        log.error('No transfer view target specified.')
        return False

    def error_no_time_view_target_specified(self):
        log.error('No time view target specified.')
        return False

    def error_no_conversion_view_target_specified(self):
        log.error('No conversion view target specified.')
        return False

    def error_no_user_action_specified(self):
        log.error('No user action specified.')
        return False

    def error_no_user_event_specified(self):
        log.error('No user event specified.')
        return False

    def error_no_system_event_specified(self):
        log.error('No system event specified.')
        return False

    def error_no_system_action_specified(self):
        log.error('No system action specified.')
        return False

    def error_no_system_controller_type_specified(self):
        log.error('No system controller type specified.')
        return False

    def error_no_user_controller_type_specified(self):
        log.error('No user controller type specified.')
        return False

    def error_no_ewallet_controller_specified(self):
        log.error('No ewallet controller specified.')
        return False

    def error_no_timer_action_specified(self):
        log.error('No timer action specified.')
        return False

    def error_no_user_reset_target_specified(self):
        log.error('No user reset target specified.')
        return False

    def error_no_user_create_target_specified(self):
        log.error('No user create target specified.')
        return False

    def error_no_system_update_target_specified(self):
        log.error('No system update target specified.')
        return False

    def error_no_system_check_target_specified(self):
        log.error('No system check target specified.')
        return False

    def error_no_user_specified(self):
        log.error('No user specified.')
        return False

    def error_no_view_target_specified(self):
        log.error('No view target specified.')
        return False

    def error_no_transfer_target_specified(self):
        log.error('No transfer target specified.')
        return False

    def error_no_time_target_specified(self):
        log.error('No time target specified.')
        return False

    def error_no_conversion_target_specified(self):
        log.error('No conversion target specified.')
        return False

    def error_no_conversion_record_id_found(self):
        log.error('No conversion record id found.')
        return False

    def error_no_time_record_id_found(self):
        log.error('No time sheet record id found.')
        return False

    def error_no_transfer_record_id_found(self):
        log.error('No transfer record_id_found.')
        return False

    def error_no_invoice_target_specified(self):
        log.error('No invoice target specified.')
        return False

    def error_no_contact_target_specified(self):
        log.error('No contact target specified.')
        return False

    def error_no_unlink_target_specified(self):
        log.error('No unlink target specified.')
        return False

    def error_no_conversion_sheet_id_found(self):
        log.error('No conversion sheet id found.')
        return False

    def error_no_time_sheet_record_id_found(self):
        log.error('No time sheet record id found.')
        return False

    def error_no_time_sheet_id_found(self):
        log.error('No time sheet id found.')
        return False

    def error_no_transfer_record_id_found(self):
        log.error('No transfer record id found.')
        return False

    def error_no_transfer_sheet_id_found(self):
        log.error('No transfer sheet id found.')
        return False

    def error_no_invoice_record_id_found(self):
        log.error('No invoice record id found.')
        return False

    def error_no_invoice_list_id_found(self):
        log.error('No invoice list id found.')
        return False

    def error_no_session_contact_list_found(self):
        log.error('No active session contact list found.')
        return False

    def error_no_contact_record_id_found(self):
        log.error('No contact record id found.')
        return False

    def error_no_user_id_found(self):
        log.error('No user id found.')
        return False

    def error_no_user_name_found(self):
        log.error('No user name found.')
        return False

    def error_no_user_email_found(self):
        log.error('No user email found.')
        return False

    def error_no_user_phone_found(self):
        log.error('No user phone found.')
        return False

    def error_no_user_alias_found(self):
        log.error('No user alias found.')
        return False

    def error_no_user_identifier_found(self):
        log.error('No user identifier found.')
        return False

    def error_no_session_active_user_found(self):
        log.error('No session active user found.')
        return False

    def error_no_user_object_found(self):
        log.error('No user object found.')
        return False

    def error_no_user_password_found(self):
        log.error('No user password found.')
        return False

    def error_no_contact_found(self):
        log.error('No contact found.')
        return False

    def error_no_session_credit_wallet_found(self):
        log.error('No session credit wallet found.')
        return False

    def error_no_transfer_type_found(self):
        log.error('No transfer type found.')
        return False

    def error_no_partner_credit_wallet_found(self):
        log.error('No partner credit wallet found.')
        return False

    def error_no_active_session_contact_list_found(self, user_name):
        log.error(
            'No active session contact list found for user %s', user_name
            )
        return False

    def error_empty_session_user_account_archive(self):
        log.error('Session user account archive is empty.')
        return False

    def error_no_active_session_credit_clock_found(self):
        log.error('No active session credit clock found.')
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_no_contact_list_id_found(self):
        log.error('No contact list id found.')
        return False

    def error_no_conversion_type_specified(self):
        log.error('No conversion type specified.')
        return False

    def error_could_not_fetch_active_session_credit_wallet(self):
        log.error('Could not fetch active session credit wallet.')
        return False

    def error_could_not_fetch_active_session_credit_clock(self):
        log.error('Could not fetch active session credit clock.')
        return False

    def warning_could_not_login(self):
        log.warning(
                'Something went wrong. '
                'Login subroutine failure.'
                )
        return False

    def warning_could_not_logout(self, **kwargs):
        log.warning(
                'Something went wrong. '
                'Logout subroutine failure for user {}.'.format(
                    self.active_user.fetch_user_name()
                    )
                )
        return False

    def warning_could_not_fetch_conversion_record(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch conversion sheet record.'
                )
        return False

    def warning_user_not_in_session_archive(self):
        log.error('User account not found in session user archive.')
        return False

    def warning_could_not_fetch_conversion_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock conversion sheet.'
                )
        return False

    def warning_could_not_fetch_time_sheet_record(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch time sheet record.'
                )
        return False

    def warning_could_not_fetch_time_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch time sheet.'
                )
        return False

    def warning_could_not_fetch_transfer_sheet_record(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch transfer sheet record.'
                )
        return False

    def warning_could_not_fetch_transfer_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit wallet transfer sheet.'
                )
        return False

    def warning_could_not_fetch_invoice_sheet_record(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch invoice sheet record.'
                )
        return False

    def warning_could_not_fetch_invoice_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit wallet invoice sheet.'
                )
        return False

    def warning_could_not_fetch_contact_record(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch contact record.'
                )
        return False

    def warning_could_not_fetch_conversion_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock conversion sheet.'
                )
        return False

    def warning_could_not_fetch_time_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock time sheet.'
                )
        return False

    def warning_could_not_fetch_credit_clock(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock.'
                )
        return False

    def warning_could_not_fetch_credit_wallet_transfer_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit wallet transfer sheet.'
                )
        return False

    def warning_could_not_fetch_credit_wallet_invoice_sheet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit wallet invoice sheet.'
                )
        return False

    def warning_no_user_acount_found(self, search_code, code):
        log.warning('No user account found by %s %s.', search_code, code)
        return False

    def warning_could_not_create_user_account(self, user_name):
        log.warning(
                'Something went wrong. '
                'Could not create new user account for %s.', user_name
                )
        return False

    def warning_could_not_create_credit_wallet(self, user_name):
        log.warning(
                'Something went wrong. '
                'Could not create new credit wallet for user %s.', user_name
                )
        return False

    def warning_could_not_create_credit_clock(self, user_name):
        log.warning(
                'Something went wrong. '
                'Could not create new credit clock for user %s.', user_name
                )
        return False

    def warning_could_not_create_contact_list(self, user_name):
        log.warning(
                'Something went wrong. '
                'Could not create new contact list for user %s.', user_name
                )
        return False

    def warning_could_not_create_contact_record(self, user_name):
        log.warning(
                'Something went wrong. '
                'Could not create new contact record for %s contact list.', user_name
                )
        return False

    def warning_could_not_fetch_user_by_id(self, user_id):
        log.warning(
                'Something went wrong. '
                'Could not fetch user by id %s.', user_id
                )
        return False

    def test_ewallet_user_controller(self):
        print('[ TEST ] User.')
        print('[ * ] Create account')
        _create = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='test user', user_pass='123abc@xxx', user_email='example@example.com'
                )
        print(str(_create) + '\n')
        print('[ * ] Login')
        _login = self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='test user',
                user_pass='123abc@xxx'
                )
        self.test_orm()
        print(str(_login) + '\n')
        print('[ * ] View account')
        _view_account = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='account'
                )
        print(str(_view_account) + '\n')
        print('[ * ] Create second account')
        _create_second = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='user2', user_pass='123abc@xxx', user_email='example2@example.com'
                )
        print(str(_create_second) + '\n')
        print('[ * ] Second Login')
        _second_login = self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='user2',
                user_pass='123abc@xxx'
                )
        self.test_orm()
        print(str(_second_login) + '\n')
        print('[ * ] Supply credits')
        _supply_credits = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='transfer',
                transfer_type='incomming',
                partner_ewallet=self.fetch_active_session_credit_wallet(),
                credits=10, reference='First Credit Supply',
                transfer_to=self.fetch_active_session_user().fetch_user_id(), active_session=self.session
                )
        print(str(_supply_credits) + '\n')
        print('[ * ] View Credit Wallet')
        _view_credit_wallet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='credit_wallet',
                )
        print(str(_view_credit_wallet) + '\n')
        print('[ * ] View Transfer Sheet')
        _view_transfer_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='transfer',
                transfer='list'
                )
        print(str(_view_transfer_sheet) + '\n')
        print('[ * ] View Transfer Sheet Record')
        _view_transfer_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='transfer',
                transfer='record', record_id=1
                )
        print(str(_view_transfer_sheet_record) + '\n')
        print('[ * ] View Invoice Sheet')
        _view_invoice_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='invoice',
                invoice='list'
                )
        print(str(_view_invoice_sheet) + '\n')
        print('[ * ] View Time Sheet')
        _view_time_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='time',
                time='list'
                )
        print(str(_view_time_sheet) + '\n')
        print('[ * ] View Conversion Sheet')
        _view_conversion_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='conversion',
                conversion='list'
                )
        print(str(_view_conversion_sheet) + '\n')
        print('[ * ] View Contact List')
        _view_contact_list = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='contact',
                contact='list'
                )
        print(str(_view_conversion_sheet) + '\n')
        print('[ * ] Extract credits')
        _extract_credits = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='transfer',
                transfer_type='outgoing',
                partner_ewallet=self.fetch_active_session_credit_wallet(),
                credits=10, reference='First Credit Extract',
                transfer_to=self.fetch_active_session_user().fetch_user_id(), active_session=self.session
                )
        print(str(_extract_credits) + '\n')
        print('[ * ] Second view account')
        _second_view_account = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='account'
                )
        print(str(_second_view_account) + '\n')
        print('[ TEST ] System.')
        print('[ * ] Update session')
        _update_session = self.ewallet_controller(
                controller='system', ctype='action', action='update', target='session'
                )
        print(str(_update_session) + '\n')
        print('[ * ] Logout')
        _logout = self.ewallet_controller(
                controller='user', ctype='action', action='logout',
                )
        print(str(_logout) + '\n')
        print('[ * ] Second Logout')
        _second_logout = self.ewallet_controller(
                controller='user', ctype='action', action='logout',
                )
        print(str(_second_logout) + '\n')

    def test_ewallet_system_controller(self):
        print('[ TEST ] System.')
        print('[ * ] Update session')
        _update_session = self.ewallet_controller(
                controller='system', ctype='action', action='update', target='session'
                )
        print(str(_update_session) + '\n')

    def test_orm(self):
        print('Active user : {}'.format(self.active_user))
        print('Session Contact List : {}'.format(self.contact_list))
        print('Session Credit Wallet : {}'.format(self.credit_wallet))
        print('User account archive : {}'.format(self.user_account_archive))


    def test_ewallet(self, **kwargs):
        self.test_ewallet_user_controller()
        self.test_ewallet_system_controller()
        self.test_orm()


# TODO - Manage initialisation and sqlalchemy sessions (add session manager)
Base.metadata.create_all(res_utils.engine)
_working_session = res_utils.session_factory()

ewallet = EWallet(session=_working_session)
_working_session.add(ewallet)
_working_session.commit()

ewallet.ewallet_controller(controller='test')


################################################################################
# CODE DUMP
################################################################################

#   ewallet_session_user_ref = Table(
#           'ewallet_session_user_ref', Base.metadata,
#           Column('ewallet_session_id', Integer, ForeignKey('ewallet.id')),
#           Column('res_user_id', Integer, ForeignKey('res_user.user_id'))
#           )

#   session_credit_wallet = Column(
#      Integer, ForeignKey('credit_ewallet.wallet_id')
#      )
#   session_contact_list = Column(
#      Integer, ForeignKey('contact_list.contact_list_id')
#      )
#   session_active_user = Column(Integer, ForeignKey('res_user.user_id'))

