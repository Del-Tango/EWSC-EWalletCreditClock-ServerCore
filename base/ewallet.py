#from validate_email import validate_email
from itertools import count
from sqlalchemy import Table, Column, String, Integer, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship, backref

from base.res_user import ResUser
from base.ewallet_login import EWalletLogin, EWalletCreateUser
from base.ewallet_logout import EWalletLogout
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
log = logging.getLogger(config.log_config['log_name'])


class SessionUser(Base):
    '''
    [ NOTE ]: Many2many table for user sessions.
    '''
    __tablename__ = 'session_user'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('ewallet.id'))
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    datetime = Column(DateTime, default=datetime.datetime.now())
    user = relationship('ResUser', backref=backref('session_user', cascade='all, delete-orphan'))
    session = relationship('EWallet', backref=backref('session_user', cascade='all, delete-orphan'))


class EWallet(Base):
    '''
    [ NOTE ]: EWallet session. Managed by EWallet Workers within the Session Manager.
    '''
    __tablename__ = 'ewallet'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String)
    create_date = Column(Date)
    write_date = Column(Date)
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

    # FETCHERS

    def fetch_active_session_values(self):
        log.debug('')
        user_account_archive = self.fetch_active_session_user_account_archive()
        values = {
            'id': self.id,
            'name': self.name,
            'orm_session': self.session,
            'create_date': self.create_date,
            'write_date': self.write_date,
            'contact_list': self.fetch_active_session_contact_list(),
            'credit_ewallet': self.fetch_active_session_credit_wallet(),
            'user_account': self.fetch_active_session_user(),
            'user_account_archive': {} if not user_account_archive else {
                item.fetch_user_id(): item.fetch_user_name() for item in \
                user_account_archive
            }
        }
        return values

    def fetch_user_account_from_active_session_user_archive(self, **kwargs):
        log.debug('')
        account_archive = self.fetch_active_session_user_account_archive()
        account_ids = False if not account_archive \
            else [account.fetch_user_id() for account in account_archive]
        if not account_ids:
            return self.error_active_session_account_archive_empty(kwargs)
        user_account = self.fetch_user_by_id(**kwargs)
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return self.warning_no_user_account_found_by_id(kwargs)
        return self.error_user_account_does_not_belong_to_active_session_archive(kwargs) \
            if user_account.fetch_user_id() not in account_ids else user_account

    def fetch_user_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('account_id'):
            return self.error_no_user_account_id_found(kwargs)
        try:
            user_account = list(kwargs['active_session'].query(
                ResUser
            ).filter_by(user_id=kwargs['account_id']))
        except:
            return self.error_could_not_fetch_user_account_by_id(kwargs)
        log.info('Successfully fetched user by id.')
        return self.warning_no_user_account_found_by_id(kwargs) if not \
            user_account else user_account[0]

    def fetch_active_session_user_account_archive(self):
        log.debug('')
        return False if not self.user_account_archive \
            else self.user_account_archive

    def fetch_active_session_contact_list(self):
        log.debug('')
        return False if not self.contact_list else \
            self.contact_list[0]

    def fetch_partner_credit_wallet(self, partner_account):
        log.debug('')
        partner_wallet = False if not partner_account.user_credit_wallet else \
                partner_account.user_credit_wallet[0]
        return self.warning_no_partner_credit_wallet_found() if not partner_wallet \
                else partner_wallet

#   @pysnooper.snoop()
    def fetch_user_by_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('email'):
            return self.error_no_user_email_found()
        active_session = kwargs.get('active_session') or self.fetch_active_session()
        if not active_session:
            return self.error_no_active_session_found()
        user_account = list(
            active_session.query(ResUser).filter_by(user_email=kwargs['email'])
        )
        return self.warning_no_user_account_found(kwargs) \
                if not user_account else user_account[0]

    def fetch_system_core_user_account(self, **kwargs):
        '''
        [ NOTE   ]: Fetches S:Core user account used for administration and automation.
        [ INPUT  ]: active_session=<orm-session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_active_session()
        score_account = active_session.query(ResUser).filter_by(user_id=1)
        return False if not score_account else score_account[0]

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
        '''
        [ NOTE   ]: Fetches a ResUser object by a specified criteria.
        [ INPUT  ]: indentifier=(id | name | email | phone | alias)
        [ RETURN ]: (ResUser object | False)
        '''
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

    def fetch_active_session_id(self):
        log.debug('')
        return self.id

    def fetch_active_session(self):
        log.debug('')
        if not self.session:
            return self.error_no_active_session_found()
        return self.session

    def fetch_active_session_user(self, obj=True):
        log.debug('')
        if not len(self.active_user):
            return self.error_no_session_active_user_found()
        return self.active_user[0] if obj else self.active_user[0].fetch_user_id()

    def fetch_active_session_credit_wallet(self):
        log.debug('')
        if not len(self.credit_wallet):
            return self.error_no_session_credit_wallet_found()
        return self.credit_wallet[0]

    def fetch_active_session_credit_clock(self, **kwargs):
        log.debug('')
        _credit_wallet = kwargs.get('credit_ewallet') or \
                self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet()
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        return _credit_clock or False

    def fetch_active_session_contact_list(self):
        log.debug('')
        if not len(self.contact_list):
            return self.error_no_session_contact_list_found()
        return self.contact_list[0]

    '''
    [ NOTE   ]: Fetches either specified credit wallet or active user credit wallet credit count.
    [ INPUT  ]: credit_wallet=<wallet>
    [ RETURN ]: (Credit wallet credits | False)
    '''
    def fetch_credit_wallet_credits(self, **kwargs):
        log.debug('')
        credit_wallet = kwargs.get('credit_wallet') or \
                self.fetch_active_session_credit_wallet()
        return self.error_no_credit_wallet_found() if not credit_wallet else \
            credit_wallet.main_controller(
                controller='system', action='view'
            )

    def fetch_next_active_session_user(self, **kwargs):
        '''
        [ NOTE   ]: Fetches next user object in login stack.
        [ INPUT  ]: active_user=<user>
        [ RETURN ]: (ResUser object | [] if empty login stack | False)
        '''
        log.debug('')
        if not len(self.user_account_archive):
            return self.error_empty_session_user_account_archive()
        _active_user = kwargs.get('active_user')
        _filtered = [
                item for item in self.user_account_archive
                if item is not _active_user
                ]
        return [] if not _filtered else _filtered[0]

    # SETTERS

    def set_orm_session(self, orm_session):
        self.session = orm_session
        return self.session

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
        '''
        [ NOTE   ]: Sets user data to active EWallet session.
        [ INPUT  ]: {'active_user': <user>, 'credit_wallet': <wallet>, 'contact_list': <list>}
        [ RETURN ]: ({'active_user': <user>, 'credit_wallet': <wallet>, 'contact_list': <list>} | False)
        '''
        log.debug('')
        handlers = {
            'active_user': self.set_session_active_user,
            'credit_wallet': self.set_session_credit_wallet,
            'contact_list': self.set_session_contact_list,
        }
        for item in data_dct:
            if item in handlers and data_dct[item]:
                handlers[item](data_dct[item])
        return data_dct

    # CLEANERS

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
        '''
        [ NOTE   ]: Clears all user information from active EWallet session.
        [ RETURN ]: ({'field-name': (True | False), ...} | False)
        '''
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

    # UPDATERS

    def update_session_from_user(self, **kwargs):
        '''
        [ NOTE   ]: Update current session values from active user data.
        [ INPUT  ]: session_active_user=<active_user>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not kwargs.get('session_active_user'):
            return self.error_no_session_active_user_found()
        user = kwargs['session_active_user']
        session_data = {
            'active_user': user,
            'credit_wallet': user.fetch_user_credit_wallet(),
            'contact_list': user.fetch_user_contact_list(),
        }
        set_data = self.set_session_data(session_data)
        log.info('Successfully updated ewallet session from current active user.')
        return session_data

#   @pysnooper.snoop()
    def update_user_account_archive(self, **kwargs):
        '''
        [ NOTE   ]: Update EWallet session user login stack with new user.
        [ INPUT  ]: user=<user>
        [ RETURN ]: (User login stack | False)
        '''
        log.debug('')
        if not kwargs.get('user'):
            return self.error_no_user_object_found(kwargs)
        self.user_account_archive.append(kwargs['user'])
        log.info(
            'Successfully updated session user account archive with user {}.' \
            .format(kwargs['user'].fetch_user_name())
        )
        return self.user_account_archive

    # UNLINKERS

    def unlink_user_account(self, **kwargs):
        '''
        [ NOTE   ]: Deletes specific user or active session user.
        [ INPUT  ]: active_session=<session>, user_id=<user_id>
        [ RETURN ]:
        '''
        log.debug('')
        if not kwargs.get('user_id'):
            return self.error_no_user_account_id_found(kwargs)
        try:
            kwargs['active_session'].query(
                ResUser
            ).filter_by(
                user_id=kwargs['user_id']
            ).delete()
        except:
            return self.error_could_not_unlink_user_account(kwargs)
        return kwargs['user_id']

    # ACTIONS
    '''
    [ NOTE ]: Command chain responses are formatted here.
    '''

    def action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'ewallet_session': self.fetch_active_session_id(),
            'session_data': session_values,
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_system_user_logout(self, **kwargs):
        '''
        [ NOTE   ]: System action 'user logout', accessible from external api call.
        [ RETURN ]: (Next user in login stack | True if login stack empty | False)
        '''
        log.debug('')
        user = self.fetch_active_session_user()
        if not user:
            return self.error_no_active_session_user_found(kwargs)
        set_user_state = user.set_user_state(set_by='code', state_code=0)
        search_user_for_session = self.fetch_next_active_session_user(active_user=user)
        clear_user_data = self.clear_active_session_user_data({
            'active_user': True if not search_user_for_session else False,
            'credit_wallet': True,
            'contact_list': True,
        })
        return True if not search_user_for_session \
            else search_user_for_session

    def action_view_logout_records(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_could_not_fetch_active_session_user(kwargs)
        try:
            logout_records = list(kwargs['active_session'].query(
                EWalletLogout
            ).filter_by(user_id=active_user.fetch_user_id()))
        except:
            return self.warning_could_not_view_logout_records(
                active_user.fetch_user_name(), kwargs
            )
        command_chain_response = {
            'failed': False,
            'user_account': active_user.fetch_user_id(),
            'logout_records': {
                item.logout_id: item.logout_date.strftime("%d-%m-%Y %H:%M ") \
                for item in logout_records
            },
        }
        return command_chain_response

    def action_view_login_records(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_could_not_fetch_active_session_user(kwargs)
        try:
            login_records = list(kwargs['active_session'].query(
                EWalletLogin
            ).filter_by(user_id=active_user.fetch_user_id()))
        except:
            return self.warning_could_not_view_login_records(
                active_user.fetch_user_name(), kwargs
            )
        command_chain_response = {
            'failed': False,
            'user_account': active_user.fetch_user_id(),
            'login_records': {
                item.login_id: item.login_date.strftime("%d-%m-%Y %H:%M ") \
                for item in login_records
            },
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_unlink_user_account(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink user account', accessible from external api calls.
        [ INPUT  ]: user=<user>, active_session=<session>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        user_id = kwargs.get('user_id') or self.fetch_active_session_user(obj=False)
        if not user_id:
            return self.error_no_user_account_id_found(kwargs)
        unlink_account = self.unlink_user_account(user_id=user_id, **kwargs)
        if not unlink_account or isinstance(unlink_account, dict) and \
                unlink_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_user_account(user_id, **kwargs)
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'user_id': user_id,
        }
        return command_chain_response

    def action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_could_not_fetch_active_session_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'unlink',
        )
        unlink_clock = active_user.user_controller(
            ctype='action', action='unlink', unlink='credit_clock',
            **sanitized_command_chain
        )
        if not unlink_clock or isinstance(unlink_clock, dict) and \
                unlink_clock.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_credit_clock(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'credit_clock': kwargs['clock_id'],
        }
        return command_chain_response

    def action_unlink_credit_wallet(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink credit wallet', accessible from external api calls.
        [ INPUT  ]: wallet_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_could_not_fetch_active_session_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'unlink',
        )
        unlink_ewallet = active_user.user_controller(
            ctype='action', action='unlink', unlink='credit_wallet',
            **sanitized_command_chain
        )
        if not unlink_ewallet or isinstance(unlink_ewallet, dict) and \
                unlink_ewallet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_credit_ewallet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'credit_ewallet': kwargs['ewallet_id'],
        }
        return command_chain_response

    def action_unlink_contact_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink contact list', accessible from external api calls.
        [ INPUT  ]: list_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_could_not_fetch_active_session_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'unlink', 'contact'
        )
        unlink_list = active_user.user_controller(
            ctype='action', action='unlink', unlink='contact_list',
            **sanitized_command_chain
        )
        if not unlink_list or isinstance(unlink_list, dict) and \
                unlink_list.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_contact_list(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'contact_list': kwargs['list_id'],
        }
        return command_chain_response

    def action_unlink_time_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink time list', accessible from external api calls.
        [ INPUT  ]: list_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = self.fetch_active_session_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'time'
        )
        unlink_sheet = credit_ewallet.main_controller(
            controller='user', ctype='action', action='unlink', unlink='time',
            time='list', **sanitized_command_chain
        )
        if not unlink_sheet or isinstance(unlink_sheet, dict) and \
                unlink_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_time_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_conversion_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink conversion list', accessible from external api calls.
        [ INPUT  ]: list_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = self.fetch_active_session_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'conversion'
        )
        unlink_sheet = credit_ewallet.main_controller(
            controller='user', ctype='action', action='unlink', unlink='conversion',
            conversion='list', **sanitized_command_chain
        )
        if not unlink_sheet or isinstance(unlink_sheet, dict) and \
                unlink_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_conversion_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_invoice_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink invoice list', accessible from external api calls.
        [ INPUT  ]: list_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = self.fetch_active_session_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'invoice'
        )
        unlink_sheet = credit_ewallet.main_controller(
            controller='user', ctype='action', action='unlink', unlink='invoice',
            invoice='list', **sanitized_command_chain
        )
        if not unlink_sheet or isinstance(unlink_sheet, dict) and \
                unlink_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_invoice_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_transfer_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink transfer list', accessible from external api calls.
        [ INPUT  ]: list_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = self.fetch_active_session_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'unlink', 'transfer'
        )
        unlink_sheet = credit_ewallet.main_controller(
            controller='user', ctype='action', action='unlink', unlink='transfer',
            transfer='list', **sanitized_command_chain
        )
        if not unlink_sheet or isinstance(unlink_sheet, dict) and \
                unlink_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_transfer_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_contact_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink contact record', accessible from external api calls.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        contact_list = active_user.fetch_user_contact_list()
        if not contact_list:
            return self.error_could_not_fetch_active_session_contact_list(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink', 'contact'
        )
        unlink_record = contact_list.contact_list_controller(
            controller='user', action='update', utype='remove',
            **sanitized_command_chain
        )
        if not unlink_record or isinstance(unlink_record, dict) and \
                unlink_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_contact_list_record(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_contact(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'unlink contact', accessible from external api call.
        [ INPUT  ]: unlink=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.action_unlink_contact_list,
            'record': self.action_unlink_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def action_unlink_time_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink time record', accessible from external api calls.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = active_user.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink', 'time'
        )
        unlink_record = credit_ewallet.main_controller(
            controller='user', action='unlink', unlink='time', time='record',
            **sanitized_command_chain
        )
        if not unlink_record or isinstance(unlink_record, dict) and \
                unlink_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_time_sheet_record(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_time(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'unlink time', accessible from external api call.
        [ INPUT  ]: unlinl=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.action_unlink_time_list,
            'record': self.action_unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def action_unlink_conversion_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink conversion record', accessible from external api calls.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = active_user.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink', 'conversion'
        )
        unlink_record = credit_ewallet.main_controller(
            controller='user', action='unlink', unlink='conversion', conversion='record',
            **sanitized_command_chain
        )
        if not unlink_record or isinstance(unlink_record, dict) and \
                unlink_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_conversion_sheet_record(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_conversion(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'unlink conversion', accessible from external api call.
        [ INPUT  ]: unlink=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.action_unlink_conversion_list,
            'record': self.action_unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def action_unlink_invoice_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink invoice record', accessible from external api calls.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = active_user.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink', 'invoice'
        )
        unlink_record = credit_ewallet.main_controller(
            controller='user', action='unlink', unlink='invoice', invoice='record',
            **sanitized_command_chain
        )
        if not unlink_record or isinstance(unlink_record, dict) and \
                unlink_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_invoice_sheet_record(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_invoice(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'unlink invoice', accessible from external api call.
        [ INPUT  ]: unlink=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.action_unlink_invoice_list,
            'record': self.action_unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def action_unlink_transfer_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'unlink transfer record', accessible from external api calls.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        credit_ewallet = active_user.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_active_session_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink', 'transfer'
        )
        unlink_record = credit_ewallet.main_controller(
            controller='user', action='unlink', unlink='transfer', transfer='record',
            **sanitized_command_chain
        )
        if not unlink_record or isinstance(unlink_record, dict) and \
                unlink_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_transfer_sheet_record(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_transfer(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'unlink transfer', accessible from external api call.
        [ INPUT  ]: unlink=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_unlink_target_specified(kwargs)
        handlers = {
            'list': self.action_unlink_transfer_list,
            'record': self.action_unlink_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def action_switch_contact_list(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_contact_list = active_user.user_controller(
            ctype='action', action='switch', target='contact_list',
            **sanitized_command_chain
        )
        if not switch_contact_list or isinstance(switch_contact_list, dict) and \
                switch_contact_list.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_contact_list(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched contact list.')
        command_chain_response = {
            'failed': False,
            'contact_list': switch_contact_list.fetch_contact_list_id(),
            'list_data': switch_contact_list.fetch_contact_list_values(),
        }
        return command_chain_response

    def action_switch_time_sheet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_time_sheet = active_user.user_controller(
            ctype='action', action='switch', target='time_sheet',
            **sanitized_command_chain
        )
        if not switch_time_sheet or isinstance(switch_time_sheet, dict) and \
                switch_time_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_time_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched conversion sheet.')
        command_chain_response = {
            'failed': False,
            'time_sheet': switch_time_sheet.fetch_time_sheet_id(),
            'sheet_data': switch_time_sheet.fetch_time_sheet_values(),
        }
        return command_chain_response

    def action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_conversion_sheet = active_user.user_controller(
            ctype='action', action='switch', target='conversion_sheet',
            **sanitized_command_chain
        )
        if not switch_conversion_sheet or isinstance(switch_conversion_sheet, dict) and \
                switch_conversion_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_conversion_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched conversion sheet.')
        command_chain_response = {
            'failed': False,
            'conversion_sheet': switch_conversion_sheet.fetch_conversion_sheet_id(),
            'sheet_data': switch_conversion_sheet.fetch_conversion_sheet_values(),
        }
        return command_chain_response

    def action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_invoice_sheet = active_user.user_controller(
            ctype='action', action='switch', target='invoice_sheet',
            **sanitized_command_chain
        )
        if not switch_invoice_sheet or isinstance(switch_invoice_sheet, dict) and \
                switch_invoice_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_invoice_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched invoice sheet.')
        command_chain_response = {
            'failed': False,
            'invoice_sheet': switch_invoice_sheet.fetch_invoice_sheet_id(),
            'sheet_data': switch_invoice_sheet.fetch_invoice_sheet_values(),
        }
        return command_chain_response

    def action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_transfer_sheet = active_user.user_controller(
            ctype='action', action='switch', target='transfer_sheet',
            **sanitized_command_chain
        )
        if not switch_transfer_sheet or isinstance(switch_transfer_sheet, dict) and \
                switch_transfer_sheet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_transfer_sheet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched transfer sheet.')
        command_chain_response = {
            'failed': False,
            'transfer_sheet': switch_transfer_sheet.fetch_transfer_sheet_id(),
            'sheet_data': switch_transfer_sheet.fetch_transfer_sheet_values(),
        }
        return command_chain_response

    def action_switch_credit_clock(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_credit_clock = active_user.user_controller(
            ctype='action', action='switch', target='credit_clock',
            **sanitized_command_chain,
        )
        if not switch_credit_clock or isinstance(switch_credit_clock, dict) and \
                switch_credit_clock.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_credit_clock(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched credit clock.')
        command_chain_response = {
            'failed': False,
            'credit_clock': switch_credit_clock.fetch_credit_clock_id(),
            'clock_data': switch_credit_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        switch_credit_ewallet = active_user.user_controller(
            ctype='action', action='switch', target='credit_wallet',
            **sanitized_command_chain,
        )
        if not switch_credit_ewallet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_credit_ewallet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched credit ewallet.')
        command_chain_response = {
            'failed': False,
            'credit_ewallet': switch_credit_ewallet.fetch_credit_ewallet_id(),
            'ewallet_data': switch_credit_ewallet.fetch_credit_ewallet_values(),
        }
        return command_chain_response

    def action_create_new_contact_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new contact list', accessible from external api calls.
        [ INPUT  ]: reference=<ref>
        [ RETURN ]: (ContactList object | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_contact_list = active_user.user_controller(
            ctype='action', action='create', target='contact_list',
            **sanitized_command_chain,
        )
        if not new_contact_list:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_contact_list(
                active_user.fetch_user_name()
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new contact list.')
        command_chain_response = {
            'failed': False,
            'contact_list': new_contact_list.fetch_contact_list_id(),
            'list_data': new_contact_list.fetch_contact_list_values(),
        }
        return command_chain_response

    def action_create_new_time_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'time'
        )
        new_time_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='time',
            **sanitized_command_chain
        )
        if not new_time_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_conversion_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully created new time sheet.')
        command_chain_response = {
            'failed': False,
            'time_sheet': new_time_sheet.fetch_time_sheet_id(),
            'sheet_data': new_time_sheet.fetch_time_sheet_values(),
        }
        return command_chain_response

    def action_create_new_conversion_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'conversion'
        )
        new_conversion_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='conversion',
            **sanitized_command_chain
        )
        if not new_conversion_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_conversion_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully created new conversion sheet.')
        command_chain_response = {
            'failed': False,
            'conversion_sheet': new_conversion_sheet.fetch_conversion_sheet_id(),
            'sheet_data': new_conversion_sheet.fetch_conversion_sheet_values(),
        }
        return command_chain_response

    def action_create_new_invoice_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'transfer'
        )
        new_invoice_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='invoice',
            **sanitized_command_chain
        )
        if not new_invoice_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_invoice_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully created new invoice sheet.')
        command_chain_response = {
            'failed': False,
            'invoice_sheet': new_invoice_sheet.fetch_invoice_sheet_id(),
            'sheet_data': new_invoice_sheet.fetch_invoice_sheet_values(),
        }
        return command_chain_response

    def action_create_new_transfer_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'transfer'
        )
        new_transfer_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='transfer',
            **sanitized_command_chain
        )
        if not new_transfer_sheet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_transfer_sheet(kwargs)
        kwargs['active_session'].commit()
        log.info('Successfully created new transfer sheet.')
        command_chain_response = {
            'failed': False,
            'transfer_sheet': new_transfer_sheet.fetch_transfer_sheet_id(),
            'sheet_data': new_transfer_sheet.fetch_transfer_sheet_values(),
        }
        return command_chain_response

    def action_create_new_credit_clock(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new credit clock', accessible from external api calls.
        [ INPUT  ]: reference=<ref>, credit_clock=<clock credits>
        [ RETURN ]: (CreditClock object | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_clock = active_user.user_controller(
            ctype='action', action='create', target='credit_clock',
            **sanitized_command_chain
        )
        if not new_clock:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_credit_clock(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new credit clock.')
        command_chain_response = {
            'failed': False,
            'credit_clock': new_clock.fetch_credit_clock_id(),
            'clock_data': new_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_create_new_credit_wallet(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new credit wallet', accessible from external api calls.
        [ INPUT  ]: reference=<ref>, credits=<wallet credits>
        [ RETURN ]: (CreditWallet object | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_wallet = active_user.user_controller(
            ctype='action', action='create', target='credit_wallet',
            **sanitized_command_chain
        )
        if not new_wallet:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_credit_wallet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new credit wallet.')
        command_chain_response = {
            'failed': False,
            'credit_ewallet': new_wallet.fetch_credit_ewallet_id(),
            'ewallet_data': new_wallet.fetch_credit_ewallet_values(),
        }
        return command_chain_response

    def action_view_invoice_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view invoice record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Invoice record values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_invoice_record(
                credit_wallet=credit_wallet,
                record_id=kwargs.get('record_id'),
            )
        log.info('Attempting to fetch active invoice sheet...')
        invoice_sheet = credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet()
        log.info('Attempting to fetch invoice record by id...')
        record = invoice_sheet.fetch_credit_invoice_records(
            search_by='id', code=kwargs['record_id'],
            active_session=self.session
        )
        if not record:
            return self.warning_could_not_fetch_invoice_sheet_record()
        command_chain_response = {
            'failed': False,
            'invoice_sheet': invoice_sheet.fetch_invoice_sheet_id(),
            'invoice_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_invoice_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view invoice list', accessible from external api call.
        [ RETURN ]: (Invoice sheet values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active invoice sheet...')
        invoice_sheet = credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not invoice_sheet:
            return self.warning_could_not_fetch_invoice_sheet()
        command_chain_response = {
            'failed': False,
            'invoice_sheet': invoice_sheet.fetch_invoice_sheet_id(),
            'sheet_data': invoice_sheet.fetch_invoice_sheet_values(),
        }
        return command_chain_response

    def action_view_credit_clock(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view credit clock', accessible from external api call.
        [ RETURN ]: (Credit clock values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        command_chain_response = {
            'failed': False,
            'credit_clock': credit_clock.fetch_credit_clock_id(),
            'clock_data': credit_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_view_credit_wallet(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view credit wallet', accessible from external api call.
        [ RETURN ]: (Credit wallet values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_no_session_credit_wallet_found()
        command_chain_response = {
            'failed': False,
            'credit_ewallet': credit_wallet.fetch_credit_ewallet_id(),
            'ewallet_data': credit_wallet.fetch_credit_ewallet_values(),
        }
        return command_chain_response

    def action_edit_account_user_name(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_name = active_user.user_controller(
            ctype='action', action='edit', edit='user_name',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_name(kwargs) if \
            edit_user_name.get('failed') else edit_user_name

    def action_edit_account_user_pass(self, **kwargs):
        log.debug('TODO')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_pass = active_user.user_controller(
            ctype='action', action='edit', edit='user_pass',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_pass(kwargs) if \
            edit_user_pass.get('failed') else edit_user_pass

    def action_edit_account_user_alias(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_alias = active_user.user_controller(
            ctype='action', action='edit', edit='user_alias',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_alias(kwargs) if \
            edit_user_alias.get('failed') else edit_user_alias

    def action_edit_account_user_email(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_email = active_user.user_controller(
            ctype='action', action='edit', edit='user_email',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_email(kwargs) if \
            edit_user_email.get('failed') else edit_user_email

    def action_edit_account_user_phone(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_phone = active_user.user_controller(
            ctype='action', action='edit', edit='user_phone',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_phone(kwargs) if \
            edit_user_phone.get('failed') else edit_user_phone

    def action_view_user_account(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view user account', accessible from external api call.
        [ RETURN ]: (Active user values | False)
        '''
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.warning_could_not_fetch_ewallet_session_active_user()
        command_chain_response = {
            'failed': False,
            'account': active_user.fetch_user_name(),
            'account_data': active_user.fetch_user_values(),
        }
        return command_chain_response

    def action_view_conversion_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view conversion record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Conversion record values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_conversion_record(
                credit_wallet=credit_wallet, record_id=kwargs.get('record_id'),
            )
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        conversion_sheet = credit_clock.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet or isinstance(conversion_sheet, dict) and \
                conversion_sheet.get('failed'):
            return self.warning_could_not_fetch_conversion_sheet()
        log.info('Attempting to fetch conversion record by id...')
        record = conversion_sheet.fetch_conversion_sheet_record(
            identifier='id', code=kwargs['record_id'],
            active_session=self.session
        )
        if not record or isinstance(record, dict) and record.get('failed'):
            return self.warning_could_not_fetch_conversion_record()
        command_chain_response = {
            'failed': False,
            'conversion_sheet': conversion_sheet.fetch_conversion_sheet_id(),
            'conversion_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_conversion_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view conversion list', accessible from external api call.
        [ RETURN ]: (Conversion sheet values | False)
        '''
        log.debug('')
        credit_clock = self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        conversion_sheet = credit_clock.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet:
            return self.warning_could_not_fetch_conversion_sheet()
        command_chain_response = {
            'failed': False,
            'conversion_sheet': conversion_sheet.fetch_conversion_sheet_id(),
            'sheet_data': conversion_sheet.fetch_conversion_sheet_values(),
        }
        return command_chain_response

    def action_view_time_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view time record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Time record values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_time_record(
                credit_wallet=credit_wallet,
                record_id=kwargs.get('record_id'),
            )
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active time sheet...')
        time_sheet = credit_clock.fetch_credit_clock_time_sheet()
        if not time_sheet:
            return self.warning_could_not_fetch_time_sheet()
        log.info('Attempting to fetch time record...')
        record = time_sheet.fetch_time_sheet_record(
            search_by='id', code=kwargs['record_id'],
            active_session=self.session
        )
        if not record or isinstance(record, dict) and record.get('failed'):
            return self.warning_could_not_fetch_time_sheet_record(kwargs)
        command_chain_response = {
            'failed': False,
            'time_sheet': time_sheet.fetch_time_sheet_id(),
            'time_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_time_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view time list', accessible from external api call.
        [ RETURN ]: (Time sheet values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active time sheet...')
        time_sheet = credit_clock.fetch_credit_clock_time_sheet()
        if not time_sheet:
            return self.warning_could_not_fetch_time_sheet()
        command_chain_response = {
            'failed': False,
            'time_sheet': time_sheet.fetch_time_sheet_id(),
            'sheet_data': time_sheet.fetch_time_sheet_values(),
        }
        return command_chain_response

#   @pysnooper.snoop()
    def action_create_new_transfer_type_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_to'):
            return self.error_no_user_action_transfer_credits_target_specified(kwargs)
        active_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
            self.fetch_user(identifier='email', email=kwargs['transfer_to'])
        if not partner_account:
            return self.error_could_not_fetch_partner_account(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'ttype', 'partner_account', 'pay',
            'transfer_to'
        )
        credits_before = self.fetch_credit_wallet_credits()
        current_account = self.fetch_active_session_user()
        action_transfer = current_account.user_controller(
            ctype='action', action='transfer', ttype='transfer',
            transfer_to=partner_account, **sanitized_command_chain
        )
        credits_after = self.fetch_credit_wallet_credits()
        if str(credits_after) == str(credits_before - kwargs.get('credits')):
            active_session.commit()
            return {
                'total_credits': credits_after,
                'transfered_credits': kwargs['credits'],
            }
        active_session.rollback()
        return self.error_transfer_type_transfer_failure(kwargs)

    def action_create_new_transfer(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'create new transfer', accessible from external api call.
        [ INPUT  ]: ttype=(supply | pay | transfer)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('ttype'):
            return self.error_no_transfer_type_specified()
        _handlers = {
                'supply': self.action_create_new_transfer_type_supply,
                'pay': self.action_create_new_transfer_type_pay,
                'transfer': self.action_create_new_transfer_type_transfer,
                }
        return _handlers[kwargs['ttype']](**kwargs)

    def action_view_contact(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'view contact', accessible from external api call.
        [ INPUT  ]: contact=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_target_specified()
        handlers = {
            'list': self.action_view_contact_list,
            'record': self.action_view_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def action_view_invoice(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'view invoice', accessible from external api call.
        [ INPUT  ]: invoice=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        handlers = {
            'list': self.action_view_invoice_list,
            'record': self.action_view_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def action_view_transfer(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'view transfer', accessible from external api call.
        [ INPUT  ]: transfer=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_transfer_view_target_specified()
        _handlers = {
                'list': self.action_view_transfer_list,
                'record': self.action_view_transfer_record,
                }
        return _handlers[kwargs['transfer']](**kwargs)

    def action_view_time(self, **kwargs):
        '''
        [ NOTE   ]: Jumpt table for user action category 'view time', accessible from external api call.
        [ INPUT  ]: time=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_time_view_target_specified()
        _handlers = {
                'list': self.action_view_time_list,
                'record': self.action_view_time_record,
                }
        return _handlers[kwargs['time']](**kwargs)

    def action_view_conversion(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action category 'view conversion', accessible from external api call.
        [ INPUT  ]: conversion=(list | record)
        [ RETURN ]: Action variable correspondent.
        '''
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
    def action_system_session_check(self, **kwargs):
        pass
    def action_send_invoice_record(self, **kwargs):
        pass
    def action_send_transfer_record(self, **kwargs):
        pass
    def action_receive_invoice_record(self, **kwargs):
        pass
    def action_receive_transfer_record(self, **kwargs):
        pass

    def action_system_user_update(self, **kwargs):
        '''
        [ NOTE   ]: System action 'user update'. Allows multiple logged in users to switch.
        [ INPUT  ]: user=<user>
        [ RETURN ]: (Active user | False)
        '''
        log.debug('')
        if not kwargs.get('user'):
            return self.error_no_user_specified()
        if kwargs['user'] not in self.user_account_archive:
            return self.warning_user_not_in_session_archive()
        _set_user = self.set_session_active_user(active_user=kwargs['user'])
        self.update_session_from_user(session_active_user=kwargs['user'])
        return self.active_user[0]

    def action_system_session_update(self, **kwargs):
        '''
        [ NOTE   ]: System action 'session update', not accessible from external api call.
        [ INPUT  ]: session_active_user=<active_user>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        kwargs.update({'session_active_user': self.fetch_active_session_user()})
        update = self.update_session_from_user(**kwargs)
        return update or False

#   @pysnooper.snoop('logs/ewallet.log')
    def action_start_credit_clock_timer(self, **kwargs):
        '''
        [ NOTE   ]: User action 'start credit clock timer', accessible from external api call.
        [ INPUT  ]: credit_clock=<clock>, active_session=<session>
        [ RETURN ]: (Legacy start time | False)
        '''
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found()
        active_session.add(credit_clock)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'active_session'
        )
        active_user = self.fetch_active_session_user()
        user_id = active_user.fetch_user_id()
        start = credit_clock.main_controller(
            controller='user', action='start',
            active_session=active_session, uid=user_id, **sanitized_command_chain
        )
        if not start:
            active_session.rollback()
            return self.error_could_not_start_credit_clock_timer()
        active_session.commit()
        return start

    def action_pause_credit_clock_timer(self, **kwargs):
        '''
        [ NOTE   ]: User action 'pause credit clock timer', accessible from external api call.
        [ INPUT  ]: credit_clock=<clock>, active_session=<session>
        [ RETURN ]: (Pause count | False)
        '''
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found()
        active_session.add(credit_clock)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'active_session'
        )
        active_user = self.fetch_active_session_user()
        user_id = active_user.fetch_user_id()
        pause = credit_clock.main_controller(
            controller='user', action='pause',
            active_session=active_session, uid=user_id, **sanitized_command_chain
        )
        if not pause:
            active_session.rollback()
            return self.error_could_not_pause_credit_clock_timer()
        active_session.commit()
        return pause

#   @pysnooper.snoop()
    def action_resume_credit_clock_timer(self, **kwargs):
        '''
        [ NOTE   ]: User action 'resume credit clock timer', accessible from external api call.
        [ INPUT  ]: credit_clock=<clock>, active_session=<session>
        [ RETURN ]: (Elapsed clock time | False)
        '''
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found()
        active_session.add(credit_clock)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'active_session'
        )
        active_user = self.fetch_active_session_user()
        user_id = active_user.fetch_user_id()
        resume = credit_clock.main_controller(
            controller='user', action='resume',
            active_session=active_session, uid=user_id,
            **sanitized_command_chain
        )
        if not isinstance(resume, float):
            active_session.rollback()
            return self.error_could_not_resume_credit_clock_timer()
        active_session.commit()
        return resume

    def action_stop_credit_clock_timer(self, **kwargs):
        '''
        [ NOTE   ]: User action 'stop credit clock timer', accessible from external api call.
        [ INPUT  ]: credit_clock=<clock>, active_session=<session>
        [ RETURN ]: (Credit clock elapsed time | False)
        '''
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock()
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found()
        active_session.add(credit_clock)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'active_session'
        )
        active_user = self.fetch_active_session_user()
        user_id = active_user.fetch_user_id()
        stop = credit_clock.main_controller(
            controller='user', action='stop', active_session=active_session,
            uid=user_id, **sanitized_command_chain
        )
        if not stop:
            active_session.rollback()
            return self.error_could_not_stop_credit_clock_timer()
        active_session.commit()
        return stop

    def action_view_transfer_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view transfer list', accessible from external api call.
        [ RETURN ]: (Transfer sheet values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_no_session_credit_wallet_found()
        log.info('Attempting to fetch active transfer sheet...')
        transfer_sheet = credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet()
        command_chain_response = {
            'failed': False,
            'transfer_sheet': transfer_sheet.fetch_transfer_sheet_id(),
            'sheet_data': transfer_sheet.fetch_transfer_sheet_values(),
        }
        return command_chain_response

    def action_view_transfer_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view transfer record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Transfer record values | False)
        '''
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or not kwargs.get('record_id'):
            return self.error_handler_action_view_transfer_record(
                credit_wallet=self.session_credit_wallet,
                record_id=kwargs.get('record_id'),
            )
        log.info('Attempting to fetch active transfer sheet...')
        transfer_sheet = credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not transfer_sheet:
            return self.warning_could_not_fetch_transfer_sheet()
        log.info('Attempting to fetch transfer record by id...')
        record = transfer_sheet.fetch_transfer_sheet_records(
            search_by='id', code=kwargs['record_id'], active_session=self.session
        )
        if not record:
            return self.warning_could_not_fetch_transfer_sheet_record()
        command_chain_response = {
            'failed': False,
            'transfer_sheet': transfer_sheet.fetch_transfer_sheet_id(),
            'transfer_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_contact_list(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view contact list', accessible from external api call.
        [ RETURN ]: (Contact list values | False)
        '''
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list:
            return self.error_no_session_contact_list_found()
        return {
            'failed': False,
            'contact_list': contact_list.fetch_contact_list_id(),
            'list_data': contact_list.fetch_contact_list_values(),
        }

#   @pysnooper.snoop()
    def action_view_contact_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view contact record', accessible from external user api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Contact record values | False)
        '''
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list or not kwargs.get('record'):
            return self.error_handler_action_view_contact_record(
                contact_list=contact_list,
                record_id=kwargs.get('record'),
            )
        log.info('Attempting to fetch contact record by id...')
        record = contact_list.fetch_contact_list_record(
            search_by='id' if not kwargs.get('search_by') else kwargs['search_by'],
            code=kwargs['record'], active_session=self.fetch_active_session()
        )
        if not record:
            return self.warning_could_not_fetch_contact_record()
        contact_record_data = record.fetch_record_values()
        log.debug(contact_record_data)
        return {
            'contact_list': contact_list.fetch_contact_list_id(),
            'contact_record': kwargs['record'],
            'record_data': contact_record_data,
        }

    def action_reset_user_password(self, **kwargs):
        '''
        [ NOTE   ]: User action 'reser user account password', accessible from external user api calls.
        [ INPUT  ]: user_pass=<pass>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not self.active_user or not kwargs.get('user_pass'):
            return self.error_no_user_password_found()
        pass_check_func = EWalletCreateUser().check_user_pass
        pass_hash_func = EWalletLogin().hash_password
        return self.active_user.user_controller(
            ctype='action', action='reset', target='field', field='user_pass',
            password=kwargs['user_pass'],
            pass_check_func=pass_check_func,
            pass_hash_func=pass_hash_func,
        )

    def action_reset_user_email(self, **kwargs):
        '''
        [ NOTE   ]: User action 'reset user account email', accessible from external user api calls.
        [ INPUT  ]: user_email=<email>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not self.active_user or not kwargs.get('user_email'):
            return self.error_no_user_email_found()
        email_check_func = EWalletCreateUser().check_user_email
        return self.active_user.user_controller(
            ctype='action', action='reset', target='field', field='user_email',
            email=kwargs['user_email'],
            email_check_func=email_check_func,
        )

    def action_reset_user_alias(self, **kwargs):
        '''
        [ NOTE   ]: User action 'reset user account alias', accessible from external user api calls.
        [ INPUT  ]: user_alias=<alias>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not self.active_user or not kwargs.get('user_alias'):
            return self.error_no_user_alias_found()
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_alias',
                alias=kwargs['user_alias']
                )

    def action_reset_user_phone(self, **kwargs):
        '''
        [ NOTE   ]: User action 'reset user account phone', accessible from external user api calls.
        [ INPUT  ]: user_phone=<phone>
        [ RETURN ]: (True | False)
        '''
        log.debug('')
        if not self.active_user or not kwargs.get('user_phone'):
            return self.error_no_user_phone_found()
        return self.active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_phone',
                phone=kwargs['user_phone']
                )

    def action_create_new_user_account(self, **kwargs):
        '''
        [ NOTE   ]: User action create new account, accessible from external user api calls.
        [ INPUT  ]: user_name=<name> user_pass=<pass> user_email=<email> user_alias=<alias>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        session_create_account = EWalletLogin().ewallet_login_controller(
                action='new_account',
                user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
                user_email=kwargs.get('user_email'),
                user_alias=kwargs.get('user_alias'),
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
        '''
        [ NOTE   ]: User action 'convert credits to clock', accessible from external api calls.
        [ INPUT  ]: credit_ewallet=<wallet>, active_session=<session>,
        [ RETURN ]: Post conversion value.
        '''
        log.debug('')
        credit_wallet = kwargs.get('credit_ewallet') or \
                self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet()
        credits_before = self.fetch_credit_wallet_credits()
        active_session = kwargs.get('active_session') or self.fetch_active_session()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'conversion', 'credit_ewallet',
            'active_session'
        )
        convert = credit_wallet.main_controller(
            controller='system', action='convert', conversion='to_minutes',
            credit_ewallet=credit_wallet, active_session=active_session,
            **sanitized_command_chain
        )
        if not convert:
            active_session.rollback()
            return self.error_could_not_convert_credits_to_minutes()
        active_session.commit()
        return convert

#   @pysnooper.snoop()
    def action_create_new_conversion_clock_to_credits(self, **kwargs):
        '''
        [ NOTE   ]: User action 'convert clock to credits', accessible from external api calls.
        [ INPUT  ]: credit_ewallet=<wallet>, credit_clock=<clock>, active_session=<session>
        [ RETURN ]: Post conversion value.
        '''
        log.debug('')
        credit_wallet = kwargs.get('credit_ewallet') or \
                self.fetch_active_session_credit_wallet()
        credit_clock = kwargs.get('credit_clock') or \
            self.fetch_active_session_credit_clock(
                credit_ewallet=credit_wallet
            )
        if not credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet()
        credits_before = self.fetch_credit_wallet_credits()
        active_session = kwargs.get('active_session') or self.fetch_active_session()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'conversion', 'credit_ewallet',
            'active_session'
        )
        convert = credit_wallet.main_controller(
            controller='system', action='convert', conversion='to_credits',
            credit_ewallet=credit_wallet, credit_clock=credit_clock,
            active_session=active_session, **sanitized_command_chain
        )
        if not convert:
            active_session.rollback()
            return self.error_could_not_convert_minutes_to_credits()
        active_session.commit()
        return convert

    def action_create_new_conversion(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action 'create new conversion', accessible from external api calls.
        [ INPUT  ]: conversion=('credits2clock' | 'clock2credits')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_type_specified()
        _handlers = {
                'credits2clock': self.action_create_new_conversion_credits_to_clock,
                'clock2credits': self.action_create_new_conversion_clock_to_credits,
                }
        return _handlers[kwargs['conversion']](**kwargs)

    def action_create_new_contact_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'create new contact record', accessible from external api calls.
        [ INPUT  ]: user_name=<name>, user_email=<email>, user_phone=<phone>, notes=<notes>
        [ RETURN ]: (ContactRecord object | False)
        '''
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list:
            return self.error_no_active_session_contact_list_found(
                self.active_user.fetch_user_name()
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        new_record = contact_list.contact_list_controller(
            action='create', **sanitized_command_chain
        )
        if not new_record:
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_contact_record(
                self.active_user.fetch_user_name()
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new contact record.')
        return {
            'contact_record': new_record.fetch_record_id(),
            'contact_list': contact_list.fetch_contact_list_id()
        }

    def action_create_new_contact(self, **kwargs):
        '''
        [ NOTE   ]: Jump table for user action 'create new contact', accessible
                    from external api calls.
        [ INPUT  ]: contact=('list', 'record')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_found()
        handlers = {
            'list': self.action_create_new_contact_list,
            'record': self.action_create_new_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

#   @pysnooper.snoop()
    def action_create_new_transfer_type_supply(self, **kwargs):
        '''
        [ NOTE   ]: User action 'supply credits' for active session user becomes
                    User event 'request credits' for SystemCore account.
                    Accessible from external api calls.
        [ INPUT  ]: active_session=<orm-session>, partner_account=<partner>,
                    credits=<credits>
        [ RETURN ]: ({'total_credits': <count>, 'supplied_credits': <count>} | False)
        '''
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
                self.fetch_system_core_user_account(**kwargs)
        if not partner_account:
            return self.error_handler_create_new_transfer(
                partner_account=partner_account,
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'partner_account', 'active_session'
        )
        credits_before = self.fetch_credit_wallet_credits()
        credit_request = partner_account.user_controller(
            ctype='event', event='request', request='credits',
            partner_account=self.fetch_active_session_user(),
            active_session=active_session, **sanitized_command_chain
        )
        credits_after = self.fetch_credit_wallet_credits()
        if str(credits_after) == str(credits_before + kwargs.get('credits')):
            active_session.commit()
            return {
                'total_credits': credits_after,
                'supplied_credits': kwargs['credits'],
            }
        active_session.rollback()
        return self.error_supply_type_transfer_failure(kwargs)

#   @pysnooper.snoop()
    def action_create_new_transfer_type_pay(self, **kwargs):
        log.debug('')
        if not kwargs.get('pay'):
            return self.error_no_user_action_pay_target_specified()
        active_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
            self.fetch_user(identifier='email', email=kwargs['pay'])
        if not partner_account:
            return self.error_handler_create_new_transfer(
                partner_account=partner_account,
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'ttype', 'partner_account', 'pay'
        )
        credits_before = self.fetch_credit_wallet_credits()
        current_account = self.fetch_active_session_user()
        action_pay = current_account.user_controller(
            ctype='action', action='transfer', ttype='payment', pay=partner_account,
            **sanitized_command_chain,
        )
        credits_after = self.fetch_credit_wallet_credits()
        if str(credits_after) == str(credits_before - kwargs.get('credits')):
            active_session.commit()
            return {
                'total_credits': credits_after,
                'spent_credits': kwargs['credits'],
            }
        active_session.rollback()
        return self.error_pay_type_transfer_failure(kwargs)

    # INTEROGATORS

    def interogate_active_session_user_archive_for_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('account_id'):
            return self.error_no_user_action_switch_active_account_id_specified(kwargs)
        search_account = self.fetch_user_account_from_active_session_user_archive(**kwargs)
        if not search_account or isinstance(search_account, dict) and \
                search_account.get('failed'):
            return self.warning_could_not_fetch_user_account_from_session_archive(kwargs)
        return search_account

    # HANDLERS

    def handle_system_action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session(**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_system_action_interogate_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_interogate_ewallet_session,
        }
        return handlers[kwargs['interogate']](**kwargs)

    def handle_user_action_logout(self, **kwargs):
        '''
        [ NOTE   ]: High level manager for user action logout.
        [ INPUT  ]:
        [ RETURN ]: True if no other users loged in. If loged in users found in
                    user account archive, returns next.
        '''
        log.debug('')
        user = self.fetch_active_session_user()
        session_logout = self.action_system_user_logout()
        logout_record = EWalletLogout(
            user_id=user.fetch_user_id(),
            logout_status=False if not session_logout else True,
        )
        kwargs['active_session'].add(logout_record)
        if not session_logout:
            kwargs['active_session'].rollback()
            return self.warning_could_not_logout_user_account(kwargs)
        update_next = False if isinstance(session_logout, bool) \
                else self.action_system_user_update(user=session_logout)
        try:
            self.user_account_archive.remove(user)
        except:
            kwargs['active_session'].rollback()
            return self.error_could_not_remove_user_from_account_archive(kwargs)
        kwargs['active_session'].commit()
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'user_account': user.fetch_user_email(),
            'session_data': {
                'session_user_account': session_values['user_account'].fetch_user_id(),
                'session_credit_ewallet': session_values['credit_ewallet'].fetch_credit_ewallet_id(),
                'session_contact_list': session_values['contact_list'].fetch_contact_list_id(),
            }
        }
        return command_chain_response

    def handle_user_action_switch_active_user_account(self, **kwargs):
        log.debug('')
        new_account = self.interogate_active_session_user_archive_for_user_account(**kwargs)
        if not new_account or isinstance(new_account, dict) and \
                new_account.get('failed'):
            return self.warning_could_not_find_user_action_switch_target_account(kwargs)
        update_session = self.update_session_from_user(session_active_user=new_account)
        if not update_session or isinstance(update_session, dict) and \
                update_session.get('failed'):
            return self.error_could_not_update_ewallet_session_from_user_account(kwargs)
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'user_account': new_account.fetch_user_email(),
            'session_data': {
                'session_user_account': update_session['active_user'].fetch_user_id(),
                'session_credit_ewallet': update_session['credit_wallet'].fetch_credit_ewallet_id(),
                'session_contact_list': update_session['contact_list'].fetch_contact_list_id(),
            }
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def handle_user_action_login(self, **kwargs):
        '''
        [ NOTE   ]: High level manager for user action login.
        [ INPUT  ]: user_name=<name>, user_pass=<pass>
        [ RETURN ]: Logged in user if login action succesful, else False.
        '''
        log.debug('')
        login_record = EWalletLogin()
        kwargs['active_session'].add(login_record)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        session_login = login_record.ewallet_login_controller(
           action='login', user_archive=self.fetch_active_session_user_account_archive(),
            **sanitized_command_chain
        )
        if not session_login:
            return self.warning_could_not_login_user_account(kwargs)
        update_archive = self.update_user_account_archive(user=session_login)
        update_session = self.action_system_user_update(user=session_login)
        kwargs['active_session'].commit()
        log.info('User successfully logged in.')
        command_chain_response = {
            'failed': False,
            'user_account': session_login.fetch_user_email(),
        }
        return command_chain_response

    def handle_user_action_switch_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_user_action_switch_contact_list_id_specified(kwargs)
        switch_contact_list = self.action_switch_contact_list(**kwargs)
        return switch_contact_list

    def handle_user_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_time_sheet_id_specified(kwargs)
        switch_time_sheet = self.action_switch_time_sheet(**kwargs)
        return switch_time_sheet

    def handle_user_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_conversion_sheet_id_specified(kwargs)
        switch_conversion_sheet = self.action_switch_conversion_sheet(**kwargs)
        return switch_conversion_sheet

    def handle_user_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_invoice_sheet_id_specified(kwargs)
        switch_invoice_sheet = self.action_switch_invoice_sheet(**kwargs)
        return switch_invoice_sheet

    def handle_user_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_transfer_sheet_id_specified(kwargs)
        switch_transfer_sheet = self.action_switch_transfer_sheet(**kwargs)
        return switch_transfer_sheet

    def handle_user_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_user_action_switch_credit_clock_id_specified(kwargs)
        switch_credit_clock = self.action_switch_credit_clock(**kwargs)
        return switch_credit_clock

    def handle_user_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet_id'):
            return self.error_no_user_action_switch_credit_ewallet_id_specified(kwargs)
        switch_credit_ewallet = self.action_switch_credit_ewallet(**kwargs)
        return switch_credit_ewallet

    def handle_user_action_switch(self, **kwargs):
        log.debug('')
        if not kwargs.get('switch'):
            return self.error_no_user_action_switch_target_specified(kwargs)
        handlers = {
            'credit_ewallet': self.handle_user_action_switch_credit_ewallet,
            'credit_clock': self.handle_user_action_switch_credit_clock,
            'transfer_sheet': self.handle_user_action_switch_transfer_sheet,
            'invoice_sheet': self.handle_user_action_switch_invoice_sheet,
            'conversion_sheet': self.handle_user_action_switch_conversion_sheet,
            'time_sheet': self.handle_user_action_switch_time_sheet,
            'contact_list': self.handle_user_action_switch_contact_list,
            'account': self.handle_user_action_switch_active_user_account,
        }
        return handlers[kwargs['switch']](**kwargs)

    def handle_user_action_edit_account_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name'):
            return False
        edit_user_name = self.action_edit_account_user_name(**kwargs)
        return False if edit_user_name.get('failed') else True

    def handle_user_action_edit_account_user_pass(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_pass'):
            return False
        edit_user_pass = self.action_edit_account_user_pass(**kwargs)
        return False if edit_user_pass.get('failed') else True

    def handle_user_action_edit_account_user_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_alias'):
            return False
        edit_user_alias = self.action_edit_account_user_alias(**kwargs)
        return False if edit_user_alias.get('failed') else True

    def handle_user_action_edit_account_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email'):
            return False
        edit_user_email = self.action_edit_account_user_email(**kwargs)
        return False if edit_user_email.get('failed') else True

    def handle_user_action_edit_account_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_phone'):
            return False
        edit_user_phone = self.action_edit_account_user_phone(**kwargs)
        return False if edit_user_phone.get('failed') else True

    def handle_user_action_edit_account(self, **kwargs):
        log.debug('')
        user = self.fetch_active_session_user()
        edit_value_set = {
            'user_name': self.handle_user_action_edit_account_user_name(**kwargs),
            'user_pass': self.handle_user_action_edit_account_user_pass(**kwargs),
            'user_alias': self.handle_user_action_edit_account_user_alias(**kwargs),
            'user_email': self.handle_user_action_edit_account_user_email(**kwargs),
            'user_phone': self.handle_user_action_edit_account_user_phone(**kwargs),
        }
        return self.warning_no_user_account_values_edited(kwargs) if True not in \
            edit_value_set.values() else {
                'failed': False,
                'account': user.fetch_user_name(),
                'edit': edit_value_set,
                'account_data': user.fetch_user_values(),
            }

    def handle_user_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_user_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_user_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_system_action_send_invoice(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action 'send invoice'.
        [ INPUT  ]: invoice=('record' | 'list')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        _handlers = {
            'record': self.action_send_invoice_record,
            'list': self.action_send_invoice_sheet,
        }
        return _handlers[kwargs['invoice']](**kwargs)

    def handle_system_action_send_transfer(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action 'send transfer'.
        [ INPUT  ]: transfer=('record' | 'list')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_transfer_target_specified()
        _handlers = {
            'record': self.action_send_transfer_record,
            'list': self.action_send_transfer_sheet,
        }
        return _handlers[kwargs['transfer']](**kwargs)

    def handle_system_action_receive_invoice(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action 'receive invoice'.
        [ INPUT  ]: invoice=('record' | 'list')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        _handlers = {
            'record': self.action_receive_invoice_record,
            'list': self.action_receive_invoice_sheet,
        }
        return _handlers[kwargs['invoice']](**kwargs)

    def handle_system_action_receive_transfer(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action 'receive transfer'.
        [ INPUT  ]: transfer=('record' | 'list')
        [ RETURN ]: Action variable correspondent
        '''
        if not kwargs.get('transfer'):
            return self.error_no_transfer_target_specified()
        _handlers = {
            'record': self.action_receive_transfer_record,
            'list': self.action_receive_transfer_sheet,
        }
        return _handlers[kwargs['transfer']](**kwargs)

    def handle_system_action_send(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action category type 'send'.
        [ INPUT  ]: send=('invoice' | 'transfer')
        [ RETURN ]: Action variable correspondent.
        '''
        if not kwargs.get('send'):
            return self.error_no_system_action_specified()
        _handlers = {
            'invoice': self.handle_system_action_send_invoice,
            'transfer': self.handle_system_action_send_transfer,
        }
        return _handlers[kwargs['send']](**kwargs)

    def handle_system_action_receive(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action category type 'receive'.
        [ INPUT  ]: receive=('invoice' | 'transfer')
        [ RETURN ]: Action variable correspondent.
        '''
        if not kwargs.get('receive'):
            return self.error_no_system_action_specified()
        _handlers = {
            'invoice': self.handle_system_action_receive_invoice,
            'transfer': self.handle_system_action_receive_transfer,
        }
        return _handlers[kwargs['send']](**kwargs)

    def handle_system_action_update(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action category type 'update'.
        [ INPUT  ]: target=('user' | 'session')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_update_target_specified()
        _handlers = {
            'user': self.action_system_user_update,
            'session': self.action_system_session_update,
        }
        return _handlers[kwargs['target']](**kwargs)

    def handle_system_action_check(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for system action category type 'check'.
        [ INPUT  ]: target=('user' | 'session')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_check_target_specified()
        _handlers = {
                'user': self.action_system_user_check,
                'session': self.action_system_session_check,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_reset(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for user action category type 'reset'.
        [ INPUT  ]: target=('user_alias' | 'user_pass' | 'user_email' | 'user_phone')
        [ RETURN ]: Action variable correspondent.
        '''
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
        '''
        [ NOTE   ]: Jump table handler for user action category type 'create'.
        [ INPUT  ]: create=('account' | 'credit_wallet' | 'credit_clock' | 'transfer' | 'conversion' | 'contact')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('create'):
            return self.error_no_user_create_target_specified()
        handlers = {
            'account': self.action_create_new_user_account,
            'credit_wallet': self.action_create_new_credit_wallet,
            'credit_clock': self.action_create_new_credit_clock,
            'transfer_sheet': self.action_create_new_transfer_sheet,
            'invoice_sheet': self.action_create_new_invoice_sheet,
            'conversion_sheet': self.action_create_new_conversion_sheet,
            'time_sheet': self.action_create_new_time_sheet,
            'transfer': self.action_create_new_transfer,
            'conversion': self.action_create_new_conversion,
            'contact': self.action_create_new_contact,
        }
        return handlers[kwargs['create']](**kwargs)

    def handle_user_action_time(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for user action category type 'time'.
        [ INPUT  ]: timer=('start' | 'pause' | 'resume' | 'stop')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('timer'):
            return self.error_no_timer_action_specified()
        _handlers = {
                'start': self.action_start_credit_clock_timer,
                'pause': self.action_pause_credit_clock_timer,
                'resume': self.action_resume_credit_clock_timer,
                'stop': self.action_stop_credit_clock_timer,
                }
        return _handlers[kwargs['timer']](**kwargs)

    def handle_user_action_view(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for user action category type 'view'.
        [ INPUT  ]: view=('account' | 'credit_wallet' | 'credit_clock' |
                          'contact' | 'invoice' | 'transfer' | 'time' |
                          'conversion')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_user_action_view_target_specified(kwargs)
        handlers = {
            'account': self.action_view_user_account,
            'credit_wallet': self.action_view_credit_wallet,
            'credit_clock': self.action_view_credit_clock,
            'contact': self.action_view_contact,
            'invoice': self.action_view_invoice,
            'transfer': self.action_view_transfer,
            'time': self.action_view_time,
            'conversion': self.action_view_conversion,
            'login': self.action_view_login_records,
            'logout': self.action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        '''
        [ NOTE   ]: Jump table handler for user action category type 'unlink'.
        [ INPUT  ]: unlink=('account' | 'credit_wallet' | 'credit_clock' |
                            'contact' | 'invoice' | 'transfer' | 'time' |
                            'conversion')
        [ RETURN ]: Action variable correspondent.
        '''
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
    def handle_user_event_notification(self, **kwargs):
        pass
    def handle_user_event_request(self, **kwargs):
        pass
    def handle_system_event_signal(self, **kwargs):
        pass
    def handle_system_event_notification(self, **kwargs):
        pass
    def handle_system_event_request(self, **kwargs):
        pass

    # CONTROLLERS

    def ewallet_user_action_controller(self, **kwargs):
        '''
        [ NOTE   ]: User action controller, accessible to external user api calls.
        [ INPUT  ]: action=('login' | 'logout' | 'create' | 'time' | 'reset' | 'view' | 'unlink')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_action_specified()
        handlers = {
            'login': self.handle_user_action_login,
            'logout': self.handle_user_action_logout,
            'create': self.handle_user_action_create,
            'time': self.handle_user_action_time,
            'reset': self.handle_user_action_reset,
            'view': self.handle_user_action_view,
            'unlink': self.handle_user_action_unlink,
            'edit': self.handle_user_action_edit,
            'switch': self.handle_user_action_switch,
        }
        return handlers[kwargs['action']](**kwargs)

    def ewallet_user_event_controller(self, **kwargs):
        '''
        [ NOTE   ]: User event controller, accessible to external user api calls.
        [ INPUT  ]: event=('signal' | 'notification' | 'request')
        [ RETURN ]: Event variable correspondent.
        '''
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
        '''
        [ NOTE   ]: System event controller, not accessible to external user api calls.
        [ INPUT  ]: event=('signal' | 'notification' | 'request')
        [ RETURN ]: Event variable correspondent.
        '''
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
        '''
        [ NOTE   ]: System action controller, not accessible to user api calls.
        [ INPUT  ]: action=('check' | 'update' | 'send' | 'receive')
        [ RETURN ]: Action variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_action_specified()
        handlers = {
            'check': self.handle_system_action_check,
            'update': self.handle_system_action_update,
            'send': self.handle_system_action_send,
            'receive': self.handle_system_action_receive,
            'interogate': self.handle_system_action_interogate,
        }
        return handlers[kwargs['action']](**kwargs)

    def ewallet_system_controller(self, **kwargs):
        '''
        [ NOTE   ]: Low level command interface for system actions and events.
        [ INPUT  ]: ctype=('action' | 'event')
        [ RETURN ]: Action/Event variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_controller_type_specified()
        _handlers = {
            'action': self.ewallet_system_action_controller,
            'event': self.ewallet_system_event_controller,
        }
        return _handlers[kwargs['ctype']](**kwargs)

    def ewallet_user_controller(self, **kwargs):
        '''
        [ NOTE   ]: High level command interface for user actions and events.
        [ INPUT  ]: ctype=('action' | 'event')
        [ RETURN ]: Action/Event variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_user_controller_type_specified()
        _handlers = {
            'action': self.ewallet_user_action_controller,
            'event': self.ewallet_user_event_controller,
        }
        return _handlers[kwargs['ctype']](**kwargs)

    def ewallet_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main command interface for EWallet session.
        [ INPUT  ]: controller=('system' | 'user' | 'test')
        [ RETURN ]: Action/Event variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_ewallet_controller_specified()
        _controllers = {
            'system': self.ewallet_system_controller,
            'user': self.ewallet_user_controller,
            'test': self.test_ewallet,
        }
        return _controllers[kwargs['controller']](**kwargs)

    # WARNINGS

    def warning_could_not_create_user_account(self, user_name):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create user account '\
                       'for {}.'.format(user_name),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'No user account found by id. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_logout_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not logout user account from ewallet session. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_find_user_action_switch_target_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not find account for user '\
                       'action switch active session user account. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_user_account_from_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch user account from active session user archive. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_user_account_from_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch user account from ewallet session archive. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_login_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not login user account. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_logout_records(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view account logout records for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_login_records(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not view login records for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_user_account(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink user account {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_clock(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit clock for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_ewallet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink credit ewallet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_transfer_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch transfer sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_list(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink contact list for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink time sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink conversion sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink invoice sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_list_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink contact list record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_time_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch time sheet record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink time sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink conversion sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink invoice sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not unlink transfer sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_contact_list(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch contact list for ewallet user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_time_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch time sheet for ewallet user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_conversion_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch conversion sheet for ewallet session user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_invoice_sheet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch invoice sheet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit clock for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not switch credit ewallet for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new conversion sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_invoice_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new invoice sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_credit_clock(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new credit clock for user {}. '\
                       'Command set details : {}'.format(user_name, command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_credit_wallet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not create new credit wallet for user {}. '\
                     'Command chain details : {}'.format(user_name, command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_name(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit account user name. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_pass(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit account user pass. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_alias(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit account user alias. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_email(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit account user email. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_phone(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not edit account user phone. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_values_edited(self, command_chain):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. No user account values edited. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_ewallet_session_active_user(self):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. Could not fetch ewallet session active user.'
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_found(self, command_chain):
        log.warning(
            'No user account found. Details : {}'.format(command_chain)
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

    # ERROR HANDLERS

    def error_handler_action_create_new_transfer(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'partner_account': kwargs.get('partner_account'),
#                   'session_wallet': kwargs.get('session_wallet'),
#                   'transfer_type': kwargs.get('transfer_type'),
#                   'partner_wallet': kwargs.get('partner_wallet'),
                    },
                'handlers': {
                    'partner_account': self.error_no_partner_account_found,
#                   'session_wallet': self.error_no_session_credit_wallet_found,
#                   'transfer_type': self.error_no_transfer_type_found,
#                   'partner_wallet': self.error_no_partner_credit_wallet_found,
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
        reasons_and_handlers = {
                'reasons': {
                    'credit_wallet': kwargs.get('credit_wallet'),
                    'record_id': kwargs.get('record_id'),
                    },
                'handlers': {
                    'credit_wallet': self.error_no_session_credit_wallet_found,
                    'record_id': self.error_no_conversion_record_id_found,
                    },
                }
        for item in reasons_and_handlers['reasons']:
            if not reasons_and_handlers['reasons'][item]:
                return reasons_and_handlers['handlers'][item]()
        return False

    # ERRORS

    def error_no_system_action_interogate_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No system action interogate target specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_user_from_account_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not remove user account from active session account archive. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_user_account_does_not_belong_to_active_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'User account does not belong to active session {} user account archive. '\
                     'Command chain details : {}'.format(self, command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_ewallet_session_from_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not update ewallet session from user account. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_active_session_account_archive_empty(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Active session user account archive is empty. '\
                     'Command chain response : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_account_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch user account by id, no database records found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user account id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_active_account_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch active account id specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_object_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user object found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_view_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action view target specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_user(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch active session user. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not unlink user account. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user account id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch active session credit ewallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_contact_list(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch active session contact list. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_unlink_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No unlink target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch active session credit wallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_contact_list_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch contact list id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_time_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch time sheet id specified. Command chain details :"{}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_conversion_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch conversion sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_invoice_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch invoice sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_transfer_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch transfer sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_credit_clock_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch credit clock id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_credit_ewallet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action switch credit ewallet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_wallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not fetch active session credit ewallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_edit_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No user action edit target specified. Command chain details : {}'\
                     .foramt(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response


    def error_could_not_fetch_partner_account(self, command_chain):
        log.error('Could not fetch partner account. Details : {}'.format(command_chain))
        return False

    def error_no_user_action_transfer_credits_target_specified(self, command_chain):
        log.error(
            'No user action transfer credits target specified. Details : {}'\
            .format(command_chain)
        )
        return False

    def error_transfer_type_transfer_failure(self, command_chain):
        log.error(
            'Transfer type transaction failure. Details : {}'\
            .format(command_chain)
        )
        return False

    def error_pay_type_transfer_failure(self, command_chain):
        log.error(
            'Credit payment failure. Details : {}'.format(command_chain)
        )
        return False

    def error_no_user_action_pay_target_specified(self):
        log.error('No user action pay target specified.')
        return False

    def error_supply_type_transfer_failure(self, command_chain):
        log.error('Supply type transfer failure. Details : {}'.format(command_chain))
        return False

    def error_could_not_pause_credit_clock_timer(self):
        log.error('Could not pause credit clock timer.')
        return False

    def error_could_not_resume_credit_clock_timer(self):
        log.error('Could not resume credit clock timer.')
        return False

    def error_no_partner_account_found(self):
        log.error('No partner account found.')
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

    def error_no_transfer_type_specified(self):
        log.error('No transfer type specified.')
        return False

    def error_could_not_convert_credits_to_minutes(self):
        log.error('Could not convert credits to minutes.')
        return False

    def error_could_not_convert_minutes_to_credits(self):
        log.error('Could not convert minutes to credits.')
        return False

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

    def error_could_not_start_credit_clock_timer(self):
        log.error('Could not start credit clock timer.')
        return False

    def error_could_not_stop_credit_clock_timer(self):
        log.error('Could not stop credit clock timer.')
        return False

    # TESTS

    def test_create_account(self):
        print('[ * ] Create account')
        _create = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='test user', user_pass='123abc@xxx', user_email='example@example.com'
                )
        print(str(_create) + '\n')
        return _create

    def test_login_account(self):
        print('[ * ] Login')
        _login = self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='test user',
                user_pass='123abc@xxx'
                )
        print(str(_login) + '\n')
        return _login

    def test_view_account(self):
        print('[ * ] View account')
        _view_account = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='account'
                )
        print(str(_view_account) + '\n')
        return _view_account

    def test_create_second_account(self):
        print('[ * ] Create second account')
        _create_second = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='user2', user_pass='123abc@xxx', user_email='example2@example.com'
                )
        print(str(_create_second) + '\n')
        return _create_second

    def test_second_login(self):
        print('[ * ] Second Login')
        _second_login = self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='user2',
                user_pass='123abc@xxx'
                )
        print(str(_second_login) + '\n')
        return _second_login

    def test_supply_credits(self):
        print('[ * ] Supply credits')
        _supply_credits = self.ewallet_controller(
                controller='user', ctype='action', action='create', create='transfer',
                ttype='supply', partner_account=self.fetch_system_core_user_account(),
                active_session=self.session, credits=10, currency='RON', cost=4.36,
                notes='Test Notes - Action Supply'
                )
        print(str(_supply_credits) + '\n')
        return _supply_credits

    def test_view_credit_wallet(self):
        print('[ * ] View Credit Wallet')
        _view_credit_wallet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='credit_wallet',
                )
        print(str(_view_credit_wallet) + '\n')
        return _view_credit_wallet

    def test_view_transfer_sheet(self):
        print('[ * ] View Transfer Sheet')
        _view_transfer_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='transfer',
                transfer='list'
                )
        print(str(_view_transfer_sheet) + '\n')
        return _view_transfer_sheet

    def test_view_transfer_sheet_record(self):
        print('[ * ] View Transfer Sheet Record')
        _view_transfer_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='transfer',
                transfer='record', record_id=1
                )
        print(str(_view_transfer_sheet_record) + '\n')
        return _view_transfer_sheet_record

    def test_view_invoice_sheet(self):
        print('[ * ] View Invoice Sheet')
        _view_invoice_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='invoice',
                invoice='list'
                )
        print(str(_view_invoice_sheet) + '\n')
        return _view_invoice_sheet

    def test_view_invoice_sheet_record(self):
        print('[ * ] View Invoice Sheet Record')
        _view_invoice_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='invoice',
                invoice='record', record_id=1
                )
        print(str(_view_invoice_sheet_record) + '\n')
        return _view_invoice_sheet_record

    def test_view_time_sheet(self):
        print('[ * ] View Time Sheet')
        _view_time_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='time',
                time='list'
                )
        print(str(_view_time_sheet) + '\n')
        return _view_time_sheet

    def test_view_time_sheet_record(self):
        print('[ * ] View Time Sheet Record')
        _view_time_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='time',
                time='record', record_id=1
                )
        print(str(_view_time_sheet_record) + '\n')

    def test_view_conversion_sheet(self):
        print('[ * ] View Conversion Sheet')
        _view_conversion_sheet = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='conversion',
                conversion='list'
                )
        print(str(_view_conversion_sheet) + '\n')
        return _view_conversion_sheet

    def test_view_conversion_sheet_record(self):
        print('[ * ] View Conversion Sheet Record')
        _view_conversion_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='conversion',
                conversion='record', record_id=1
                )
        print(str(_view_conversion_sheet_record) + '\n')
        return _view_conversion_sheet_record

    def test_view_contact_list(self):
        print('[ * ] View Contact List')
        _view_contact_list = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='contact',
                contact='list'
                )
        print(str(_view_contact_list) + '\n')
        return _view_contact_list

    def test_view_contact_list_record(self):
        print('[ * ] View Contact List Record')
        _view_contact_sheet_record = self.ewallet_controller(
                controller='user', ctype='action', action='view', view='contact',
                contact='record', record_id=1
                )
        print(str(_view_contact_sheet_record) + '\n')
        return _view_contact_sheet_record

    def test_extract_credits(self):
        print('[ * ] Extract credits')
        _extract_credits = self.ewallet_controller(
                controller='user', ctype='action', action='create',
                create='transfer', transfer_type='outgoing',
                partner_ewallet=self.fetch_active_session_credit_wallet(),
                credits=10, reference='First Credit Extract',
                transfer_to=self.fetch_active_session_user().fetch_user_id(),
                active_session=self.session
                )
        print(str(_extract_credits) + '\n')
        return _extract_credits

    def test_logout(self):
        print('[ * ] Logout')
        _logout = self.ewallet_controller(
                controller='user', ctype='action', action='logout',
                )
        print(str(_logout) + '\n')
        return _logout

    def test_convert_credits_to_clock(self):
        print('[ * ] Convert Credits To Clock')
        _convert = self.ewallet_controller(
                controller='user', ctype='action', action='create',
                create='conversion', conversion='credits2clock', credits=3,
                )
        print(str(_convert) + '\n')
        return _convert


    def test_convert_clock_to_credits(self):
        print('[ * ]: Convert Clock To Credits')
        _convert = self.ewallet_controller(
                controller='user', ctype='action', action='create',
                create='conversion', conversion='clock2credits', minutes=1,
                )
        print(str(_convert) + '\n')
        return _convert

    def test_start_credit_clock(self):
        print('[ * ]: Start Credit Clock')
        _start = self.ewallet_controller(
                controller='user', ctype='action', action='time', timer='start'
                )
        print(str(_start) + '\n')
        return _start

    def test_pause_credit_clock(self):
        print('[ * ]: Pause Credit Clock')
        _pause = self.ewallet_controller(
                controller='user', ctype='action', action='time', timer='pause'
                )
        print(str(_pause) + '\n')
        return _pause

    def test_resume_credit_clock(self):
        print('[ * ]: Resume Credit Clock')
        _resume = self.ewallet_controller(
                controller='user', ctype='action', action='time', timer='resume'
                )
        print(str(_resume) + '\n')
        return _resume

    def test_stop_credit_clock(self):
        print('[ * ]: Stop Credit Clock')
        _stop = self.ewallet_controller(
                controller='user', ctype='action', action='time', timer='stop'
                )
        print(str(_stop) + '\n')
        return _stop

    def test_unlink_user_account(self):
        print('[ * ]: Unlink User Account')
        _unlink = self.ewallet_controller(
                controller='user', ctype='action', action='unlink',
                unlink='account',
                )
        print(str(_unlink) + '\n')
        return _unlink

    def test_ewallet_user_controller(self):
        print('[ TEST ] User.')
        _create = self.test_create_account()
        _login = self.test_login_account()
        self.test_orm()
        _view_account = self.test_view_account()
        _create_second = self.test_create_second_account()
        _second_login = self.test_second_login()
        self.test_orm()
        _supply_credits = self.test_supply_credits()
        _view_credit_wallet = self.test_view_credit_wallet()
        _view_transfer_sheet = self.test_view_transfer_sheet()
        _view_transfer_sheet_record = self.test_view_transfer_sheet_record()
        _view_invoice_sheet = self.test_view_invoice_sheet()
        _view_invoice_sheet_record = self.test_view_invoice_sheet_record()
        _view_time_sheet = self.test_view_time_sheet()
        _view_time_sheet_record = self.test_view_time_sheet_record()
        _convert_credits = self.test_convert_credits_to_clock()
        _start_clock = self.test_start_credit_clock()
        self.sleep_printer()
        _pause_clock = self.test_pause_credit_clock()
        self.sleep_printer()
        _resume_clock = self.test_resume_credit_clock()
        self.sleep_printer()
        _pause_clock = self.test_pause_credit_clock()
        self.sleep_printer()
        _resume_clock = self.test_resume_credit_clock()
        _stop_clock = self.test_stop_credit_clock()
        _convert_clock = self.test_convert_clock_to_credits()
        _view_conversion_sheet = self.test_view_conversion_sheet()
        _view_conversion_sheet_record = self.test_view_conversion_sheet_record()
        _view_contact_list = self.test_view_contact_list()
        _view_contact_list_record = self.test_view_contact_list_record()
        _extract_credits = self.test_extract_credits()
        _second_view_account = self.test_view_account()
        print('[ TEST ] System.')
        _update_session = self.test_update_session()
        _logout = self.test_logout()
#       _unlink_account = self.test_unlink_user_account()
        _second_logout = self.test_logout()

    def sleep_printer(self):
        for item in range(3):
            print('Sleeping ...')
            time.sleep(1)
        print('\n')

    def test_update_session(self):
        print('[ * ] Update session')
        _update_session = self.ewallet_controller(
                controller='system', ctype='action', action='update', target='session'
                )
        print(str(_update_session) + '\n')
        return _update_session

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
        print('\n')

    def test_ewallet(self, **kwargs):
        self.test_ewallet_user_controller()
        self.test_ewallet_system_controller()
        self.test_orm()

Base.metadata.create_all(res_utils.engine)

_working_session = res_utils.session_factory()
ewallet = EWallet(session=_working_session)
_working_session.add(ewallet)
_working_session.commit()
system_user = res_utils.create_system_user(ewallet)

if __name__ == '__main__':
    ewallet.ewallet_controller(controller='test')

################################################################################
# CODE DUMP
################################################################################
#       sanitized_command_chain = res_utils.remove_tags_from_command_chain(
#           kwargs, 'ctype', 'action', 'view',
#       )
#       view_login_records = active_user.user_controller(
#           ctype='action', action='view', view='login',
#           **sanitized_command_chain
#       )
#       if not view_login_records or isinstance(view_login_records, dict) and \
#               view_login_records.get('failed'):
#           kwargs['active_session'].rollback()
#           return self.warning_could_not_view_login_records(
#               active_user.fetch_user_name(), kwargs
#           )
#       kwargs['active_session'].commit()

#       if not self.session_credit_wallet or not kwargs.get('record_id'):
#           return self.error_handler_action_unlink_conversion_record(
#                   credit_wallet=self.session_credit_wallet,
#                   record_id=kwargs.get('record_id'),
#                   )
#       log.info('Attempting to fetch active credit clock...')
#       _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
#       if not _credit_clock:
#           return self.warning_could_not_fetch_credit_clock()
#       log.info('Attempting to fetch active conversion sheet...')
#       _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
#       if not _conversion_list:
#           return self.warning_could_not_fetch_conversion_sheet()
#       return _conversion_list.credit_clock_conversion_sheet_controller(
#               action='remove', record_id=kwargs['record_id']
#               )

