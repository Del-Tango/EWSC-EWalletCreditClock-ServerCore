import datetime
import random
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils
from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .res_user_pass_hash_archive import ResUserPassHashArchive
from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class ResUser(Base):
    __tablename__ = 'res_user'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    user_create_date = Column(DateTime)
    user_write_date = Column(DateTime)
    user_create_uid = Column(Integer, ForeignKey('res_user.user_id'))
    user_write_uid = Column(Integer, ForeignKey('res_user.user_id'))
    user_pass_hash = Column(String)
    user_email = Column(String)
    user_phone = Column(String)
    user_alias = Column(String)
    user_state_code = Column(Integer)
    user_state_name = Column(String)
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    # O2O
    active_session = relationship(
       'EWallet', back_populates='active_user'
       )
    # O2O
    user_contact_list = relationship(
       'ContactList', back_populates='client',
       )
    # O2O
    user_credit_wallet = relationship(
       'CreditEWallet', back_populates='client',
       )
    # M2M
    user_session_archive = relationship('EWallet', secondary='session_user')
    # O2M
    user_pass_hash_archive = relationship('ResUserPassHashArchive')
    # O2M
    user_credit_wallet_archive = relationship('CreditEWallet')
    # O2M
    user_contact_list_archive = relationship('ContactList')

#   @pysnooper.snoop('logs/ewallet.log')
    def __init__(self, **kwargs):
        self.user_create_date = datetime.datetime.now()
        self.user_write_date = datetime.datetime.now()
        self.user_create_uid = kwargs.get('user_create_uid')
        self.user_write_uid = kwargs.get('user_write_uid')
        _user_credit_wallet = kwargs.get('user_credit_wallet') or \
                self.user_action_controller(
                    action='create', target='credit_wallet', **kwargs
                )
        _user_contact_list = kwargs.get('user_contact_list') or \
                self.user_action_controller(
                    action='create', target='contact_list', **kwargs
                )
        self.user_name = kwargs.get('user_name')
        self.user_credit_wallet = [_user_credit_wallet]
        self.user_contact_list = [_user_contact_list]
        self.user_pass_hash = kwargs.get('user_pass_hash')
        self.user_email = kwargs.get('user_email')
        self.user_phone = kwargs.get('user_phone')
        self.user_alias = kwargs.get('user_alias')
        self.user_state_code = kwargs.get('user_state_code') or 0
        self.user_state_name = kwargs.get('user_state_name') or 'LoggedOut'
        self.user_pass_hash_archive = kwargs.get('user_pass_hash_archive') or []
        self.user_credit_wallet_archive = kwargs.get('user_credit_wallet_archive') or \
                [_user_credit_wallet]
        self.user_contact_list_archive = kwargs.get('user_contact_list_archive') or \
                [_user_contact_list]

    def fetch_user_id(self):
        log.debug('')
        return self.user_id

    def fetch_user_name(self):
        log.debug('')
        return self.user_name

    def fetch_user_create_date(self):
        log.debug('')
        return self.user_create_date

    def fetch_user_write_date(self):
        log.debug('')
        return self.user_write_date

    def fetch_user_create_uid(self):
        log.debug('')
        return self.user_create_uid

    def fetch_user_write_uid(self):
        log.debug('')
        return self.user_write_uid

    def fetch_user_credit_wallet(self):
        log.debug('')
        if not len(self.user_credit_wallet):
            return self.error_no_user_credit_wallet_found()
        return self.user_credit_wallet[0]

    def fetch_user_contact_list(self):
        log.debug('')
        if not len(self.user_contact_list):
            return self.error_no_user_contact_list_found()
        return self.user_contact_list[0]

    def fetch_user_pass_hash(self):
        log.debug('')
        return self.user_pass_hash

    def fetch_user_email(self):
        log.debug('')
        return self.user_email

    def fetch_user_phone(self):
        log.debug('')
        return self.user_phone

    def fetch_user_alias(self):
        log.debug('')
        return self.user_alias

    def fetch_user_state(self):
        log.debug('')
        return self.user_state

    def fetch_user_pass_hash_archive(self):
        log.debug('')
        return self.user_pass_hash_archive

    def fetch_user_credit_wallet_archive(self):
        log.debug('')
        return self.user_credit_wallet_archive

    def fetch_user_contact_list_archive(self):
        log.debug('')
        return self.user_contact_list_archive

    def fetch_user_values(self):
        log.debug('')
        _values = {
                'id': self.user_id,
                'user_name': self.user_name,
                'user_create_date': self.user_create_date,
                'user_write_date': self.user_write_date,
                'user_create_uid': self.user_create_uid,
                'user_write_uid': self.user_write_uid,
                'user_credit_wallet': self.fetch_user_credit_wallet(),
                'user_contact_list': self.fetch_user_contact_list(),
                'user_pass_hash': self.user_pass_hash,
                'user_email': self.user_email,
                'user_phone': self.user_phone,
                'user_alias': self.user_alias,
                'user_state_code': self.user_state_code,
                'user_state_name': self.user_state_name,
                'user_pass_hash_archive': self.user_pass_hash_archive,
                'user_credit_wallet_archive': self.user_credit_wallet_archive,
                'user_contact_list_archive': self.user_contact_list_archive,
                }
        return _values

    def fetch_credit_wallet_by_id(self, credit_wallet_id):
        log.debug('')
        _record = self.user_credit_wallet_archive.get(credit_wallet_id)
        if _record:
            log.info('Successfully fetched credit wallet by id.')
        return _record

    def fetch_contact_list_by_id(self, contact_list_id):
        log.debug('')
        _contact_list = self.user_contact_list_archive.get(contact_list_id)
        if _contact_list:
            log.info('Successfully fetched contact list by id.')
        return _contact_list

    def fetch_user_state_code_map(self):
        log.debug('')
        _state_map = {
                'code': {
                    0: 'LoggedOut',
                    1: 'LoggedIn',
                    },
                'name': {
                    'LoggedOut': 0,
                    'LoggedIn': 1,
                    }
                }
        return _state_map

    def set_user_write_date(self):
        log.debug('')
        self.user_write_date = datetime.datetime.now()
        return True

    def set_user_pass(self, **kwargs):
        log.debug('')
        if not kwargs.get('password') or not kwargs.get('pass_check_func') \
                or not kwargs.get('pass_hash_func'):
            return self.error_handler_set_user_pass(
                    password=kwargs.get('password'),
                    pass_check_func=kwargs.get('pass_check_func'),
                    pass_hash_func=kwargs.get('pass_hash_func'),
                    )
        log.info('Performing user password checks...')
        _check = kwargs['pass_check_func'](kwargs['password'])
        if not _check:
            return _create_user.error_invalid_user_pass()
        log.info('Password coresponds with security standards. Hashing...')
        _pass_hash = kwargs['pass_hash_func'](kwargs['password'])
        _hash_record = self.create_user_pass_hash_record(
                pass_hash=_pass_hash, **kwargs
                )
        self.user_pass = _pass_hash
        kwargs['active_session'].add(_hash_record)
        kwargs['active_session'].commit()
        self.set_user_write_date()
        log.info('Successfully set user password.')
        return True

    def set_user_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('alias'):
            return self.error_no_user_alias_found()
        self.user_alias = kwargs['alias']
        log.info('Successfully set user alias.')
        self.set_user_write_date()
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def set_user_state_code(self, **kwargs):
        log.debug('')
        if kwargs.get('state_code') not in [0, 1]:
            return self.error_no_state_code_found()
        self.user_state_code = kwargs['state_code']
        self.set_user_write_date()
        return True

    def set_user_state_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('state_name'):
            return self.error_no_state_name_found()
        self.user_state_name = kwargs['state_name']
        self.set_user_write_date()
        return True

    @pysnooper.snoop('logs/ewallet.log')
    def set_user_state(self, **kwargs):
        log.debug('')
        if not kwargs.get('set_by'):
            return self.error_no_set_by_parameter_specified()
        _handlers = {
                'converters': {
                    'code': self.convert_user_state_code_to_name,
                    'name': self.convert_user_state_name_to_code,
                    },
                'setters': {
                    'code': self.set_user_state_code,
                    'name': self.set_user_state_name,
                    },
                }
        _set_command_chain = {kwargs['set_by']: kwargs.get('code') or kwargs.get('name')}
        _set_command_chain.update(kwargs)
        _value_fetch = _handlers['converters'][kwargs['set_by']](
                **_set_command_chain
                )
        _field_code = kwargs.get('state_code') if kwargs['set_by'] == 'code' \
                            else _value_fetch
        _field_name = kwargs.get('name') if kwargs['set_by'] == 'name' \
                            else _value_fetch
        _setter_values = {
                'field_names': {
                    'code': 'state_code',
                    'name': 'state_name',
                    },
                'field_values': {
                    'code': _field_code,
                    'name': _field_name,
                    }
                }
        for item in _handlers['setters']:
            _field_name = _setter_values['field_names'][item]
            _field_values = _setter_values['field_values'][item]
            _set_state = _handlers['setters'][item](
                    **{_field_name: _field_values}
                    )
        return _value_fetch

    def set_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('phone'):
            return self.no_user_phone_found()
        self.user_phone = kwargs['phone']
        self.set_user_write_date()
        log.info('Successfully set user phone.')
        return True

    def set_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('email') or not kwargs.get('email_check_func'):
            return self.error_handler_set_user_email(
                    email=kwargs.get('email'),
                    email_check_func=kwargs.get('email_check_func'),
                    )
        log.info('Performing user email validation checks...')
        _check = kwargs['email_check_func'](kwargs['email'], severity=1)
        if not _check:
            return _create_user.error_invalid_user_email(
                    user_email=kwargs['email']
                    )
        log.info('User email validated.')
        self.user_email = kwargs['email']
        self.set_user_write_date()
        log.info('Successfully set user email.')
        return True

    def set_user_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_wallet'):
            return self.error_no_credit_wallet_found()
        self.user_credit_wallet = kwargs['credit_wallet']
        self.set_user_write_date()
        log.info('Successfully set user credit wallet.')
        return True

    def set_user_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact_list'):
            return self.error_no_contact_list_found()
        self.user_contact_list = kwargs['contact_list']
        self.set_user_write_date()
        log.info('Successfully set user contact list.')
        return True

    def set_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('name'):
            return self.error_no_user_name_found()
        self.user_name = kwargs['name']
        self.set_user_write_date()
        log.info('Successfully set user name.')
        return True

    def set_user_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet'):
            return self.error_no_credit_wallet_found()
        self.user_credit_wallet = kwargs['wallet']
        self.set_user_write_date()
        log.info('Successfully set user credit wallet.')
        return True

    def set_user_pass_hash_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_pass_hash_archive_found()
        self.user_pass_hash_archive = kwargs['archive'] or {}
        self.set_user_write_date()
        log.info('Successfully set user password hash archive.')
        return True

    def set_user_credit_wallet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_credit_wallet_archive_found()
        self.user_credit_wallet_archive = kwargs['archive'] or {}
        self.set_user_write_date()
        log.info('Successfully set user credit wallet archive.')
        return True

    def set_user_contact_list_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_contact_list_archive_found()
        self.user_contact_list_archive = kwargs['archive'] or {}
        self.set_user_write_date()
        log.info('Successfully set user contact list archive.')
        return True

    def update_user_credit_wallet_archive(self, credit_wallet):
        log.debug('')
        self.user_credit_wallet_archive.append(credit_wallet)
        log.info('Successfully updated user credit wallet archive.')
        return self.user_credit_wallet_archive

    @pysnooper.snoop('logs/ewallet.log')
    def update_user_contact_list_archive(self, contact_list):
        log.debug('')
        self.user_contact_list_archive.append(contact_list)
        log.info('Successfully updated user contact list archive.')
        return self.user_contact_list_archive

#   @pysnooper.snoop('logs/ewallet.log')
    def convert_user_state_code_to_name(self, **kwargs):
        log.debug('')
        if kwargs.get('state_code') not in [0, 1]:
            return self.error_no_state_code_found()
        return self.fetch_user_state_code_map()['code'].get(
                kwargs['state_code']
                )

    def create_user_pass_hash_record(self, **kwargs):
        if not kwargs.get('pass_hash'):
            return self.error_no_user_pass_hash_found()
        _pass_hash_record = ResUserPassHashArchive(
                user_id=kwargs.get('user_id') or self.fetch_user_id(),
                user_pass_hash=kwargs['pass_hash'],
                )
        return _pass_hash_record

    def convert_user_state_name_to_code(self, **kwargs):
        log.debug('')
        if not kwargs.get('name'):
            return self.error_no_state_name_found()
        return self.fetch_user_state_code_map()['name'].get(kwargs['name'])

    # TODO - Refactor - User main system controller
    @pysnooper.snoop('logs/ewallet.log')
    def action_create_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        _new_credit_wallet = CreditEWallet(
                client_id=self.user_id,
                reference=kwargs.get('reference') or 'Credit Wallet',
                credits=kwargs.get('credits') or 0,
                active_session=kwargs['active_session'],
                )
        kwargs['active_session'].add(_new_credit_wallet)
        self.update_user_credit_wallet_archive(_new_credit_wallet)
        kwargs['active_session'].commit()
        log.info('Successfully created new user credit wallet.')
        return _new_credit_wallet

    def action_create_credit_clock(self, **kwargs):
        log.debug('')
        _new_credit_clock = self.user_credit_wallet.main_controller(
                controller='system', action='create_clock',
                reference=kwargs.get('reference'),
                credit_clock=kwargs.get('credit_clock'),
                )
        log.info('Successfully created new user credit clock.')
        return _new_credit_clock

    def action_create_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found()
        _new_contact_list = ContactList(
                client_id=self.user_id,
                reference=kwargs.get('reference') or 'Contact List',
                )
        kwargs['active_session'].add(_new_contact_list)
        self.update_user_contact_list_archive(_new_contact_list)
        kwargs['active_session'].commit()
        log.info('Successfully created new user contact list.')
        return _new_contact_list

    def action_switch_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        log.info('Attempting to fetch user credit wallet...')
        _wallet = self.fetch_user_credit_wallet_by_id(kwargs['wallet_id'])
        if not _wallet:
            return self.warning_could_not_fetch_credit_wallet()
        _switch = self.set_user_credit_wallet(_wallet)
        if _switch:
            log.info('Successfully switched credit wallet by id.')
        return _switch

    def action_switch_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_clock_id_found()
        _clock_switch = self.user_credit_wallet.main_controller(
                controller='user', action='switch_clock',
                clock_id=kwargs['clock_id']
                )
        if not _clock_switch:
            return self.warning_could_not_fetch_credit_clock()
        log.info('Successfully switched user credit clock.')
        return _clock_switch

    def action_switch_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_contact_list_id_found()
        log.info('Attempting to fetch user contact list...')
        _list = self.fetch_user_contact_list_by_id(kwargs['list_id'])
        if not _list:
            return self.warning_could_not_fetch_contact_list()
        _switch = self.set_user_contact_list(_list)
        if _switch:
            log.info('Successfully switched user contact list.')
        return _switch

    def action_unlink_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        log.info('Attempting to fetch user credit wallet...')
        _wallet = self.fetch_credit_wallet_by_id(kwargs['wallet_id'])
        if not _wallet:
            return self.warning_could_not_fetch_credit_wallet()
        _unlink = self.user_credit_wallet_archive.pop(kwargs['wallet_id'])
        if _unlink:
            log.info('Successfully removed user credit wallet by id.')
        return _unlink

    def action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found()
        return self.credit_wallet.main_controller(
                controller='system', action='unlink_clock',
                clock_id=kwargs['clock_id']
                )

    def action_unlink_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_contact_list_id_found()
        log.info('Attempting to fetch user contact list...')
        _contact_list = self.fetch_contact_list_by_id(kwargs['list_id'])
        if not _contact_list:
            return self.warning_could_not_fetch_contact_list()
        _unlink = self.user_contact_list_archive.pop(kwargs['list_id'])
        if _unlink:
            log.info('Successfully removed user contact list by id.')
        return _unlink

#   @pysnooper.snoop('logs/ewallet.log')
    def action_extract_credits_from_wallet(self, **kwargs):
        log.debug('')
        _credit_wallet = kwargs.get('credit_wallet') or \
                self.fetch_user_credit_wallet()
        if not _credit_wallet:
            return False
        _extract = _credit_wallet.main_controller(
                controller='system', action='extract',
                credits=kwargs.get('credits') or 0
                )
        return True if _extract else False

#   @pysnooper.snoop('logs/ewallet.log')
    def action_supply_credits_to_wallet(self, **kwargs):
        log.debug('')
        _credit_wallet = kwargs.get('credit_wallet') or \
                self.fetch_user_credit_wallet()
        if not _credit_wallet:
            return False
        _supply = _credit_wallet.main_controller(
                controller='system', action='supply',
                credits=kwargs.get('credits') or 0
                )
        return True if isinstance(_supply, int) else False

    def handle_user_action_create(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_create_target_specified()
        _handlers = {
                'credit_wallet': self.action_create_credit_wallet,
                'credit_clock': self.action_create_credit_clock,
                'contact_list': self.action_create_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_action_reset_field(self, **kwargs):
        log.debug('')
        if not kwargs.get('field'):
            return self.error_no_user_action_reset_field_target_specified()
        _handlers = {
                'user_name': self.set_user_name,
                'user_pass': self.set_user_pass,
                'user_credit_wallet': self.set_user_credit_wallet,
                'user_contact_list': self.set_user_contact_list,
                'user_email': self.set_user_email,
                'user_phone': self.set_user_phone,
                'user_alias': self.set_user_alias,
                }
        return _handlers[kwargs['field']](**kwargs)

    def handle_action_reset_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_action_reset_archive_target_specified()
        _handlers = {
                'password': self.set_user_pass_hash_archive,
                'credit_wallet': self.set_user_credit_wallet_archive,
                'contact_list': self.set_user_contact_list_archive,
                }
        return _handlers[kwargs['archive']](kwargs.get('value'))

    def handle_user_action_reset(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_reset_target_specified()
        _handlers = {
                'field': self.handle_action_reset_field,
                'archive': self.handle_action_reset_archive,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_switch(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_switch_target_specified()
        _handlers = {
                'credit_wallet': self.action_switch_credit_wallet,
                'credit_clock': self.action_switch_credit_clock,
                'contact_list': self.action_switch_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_unlink_target_specified()
        _handlers = {
                'credit_wallet': self.action_unlink_credit_wallet,
                'credit_clock': self.action_unlink_credit_clock,
                'contact_list': self.action_unlink_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def handle_user_event_request_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('partner_account'):
            log.error('No partner account found.')
            return False

        _local_credit_wallet = self.fetch_user_credit_wallet()
        _remote_credit_wallet = kwargs['partner_account'].fetch_user_credit_wallet()

        if not _remote_credit_wallet:
            log.warning(
                'Could not fetch credit wallet for partner {}.'\
                .format(kwargs['partner_account'].fetch_user_name())
            )
            return False

        _extract_credits_from_local = self.action_extract_credits_from_wallet(**kwargs)
        _supply_credits_to_remote = kwargs['partner_account'].action_supply_credits_to_wallet(**kwargs)

        _local_transfer_sheet = _local_credit_wallet.fetch_credit_ewallet_transfer_sheet()
        _local_invoice_sheet = _local_credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not _local_transfer_sheet or not _local_invoice_sheet:
            return False


        kwargs.pop('action')
        _create_transfer_record = _local_transfer_sheet.credit_transfer_sheet_controller(
                action='add', transfer_type='outgoing', **kwargs
                )
        _create_invoice_record = _local_invoice_sheet.credit_invoice_sheet_controller(
                action='add', seller_id=self.fetch_user_id(),
                transfer_record_id=_create_transfer_record.fetch_record_id(),
                **kwargs
                )

        kwargs['active_session'].add(_create_transfer_record)
        kwargs['active_session'].add(_create_invoice_record)
        _remote_transfer_sheet = _remote_credit_wallet.fetch_credit_ewallet_transfer_sheet()
        _remote_invoice_sheet = _remote_credit_wallet.fetch_credit_ewallet_invoice_sheet()

        if not _remote_transfer_sheet:
            log.error('Could not fetch remote transfer sheet.')
            return False

        _share_transfer_record = _remote_transfer_sheet.credit_transfer_sheet_controller(
                action='add', transfer_type='incoming', **kwargs
                )
        _share_invoice_record = _remote_invoice_sheet.credit_invoice_sheet_controller(
                action='add', seller_id=self.fetch_user_id(),
                transfer_record_id=_share_transfer_record.fetch_record_id(),
                **kwargs
                )
        kwargs['active_session'].add(_share_transfer_record)
        kwargs['active_session'].add(_share_invoice_record)
        return True

    def handle_user_event_request(self, **kwargs):
        log.debug('')
        if not kwargs.get('request'):
            return self.error_no_user_event_request_specified()
        _handlers = {
            'credits': self.handle_user_event_request_credits,
        }
        return _handlers[kwargs['request']](**kwargs)

    # TODO
    def handle_user_event_notification(self, **kwargs):
        pass

    # TODO
    def handle_user_event_signal(self, **kwargs):
        pass

    def user_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_controller_action_specified()
        _handlers = {
                'create': self.handle_user_action_create,
                'reset': self.handle_user_action_reset,
                'switch': self.handle_user_action_switch,
                'unlink': self.handle_user_action_unlink,
                }
        return _handlers[kwargs['action']](**kwargs)

    def user_event_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_user_controller_event_specified()
        _handlers = {
                'request': self.handle_user_event_request,
                'notification': self.handle_user_event_notification,
                'signal': self.handle_user_event_signal,
                }
        return _handlers[kwargs['event']](**kwargs)

    def user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_user_controller_type_specified()
        _controllers = {
                'action': self.user_action_controller,
                'event': self.user_event_controller,
                }
        return _controllers[kwargs['ctype']](**kwargs)

    def error_handler_init(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'user_name': kwargs.get('user_name'),
                    'user_pass_hash': kwargs.get('user_pass_hash'),
                    },
                'handlers': {
                    'user_name': self.error_no_user_name_found,
                    'user_pass_hash': self.error_no_user_pass_hash_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_set_user_pass(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'password': kwargs.get('password'),
                    'pass_check_func': kwargs.get('pass_check_func'),
                    'pass_hash_func': kwargs.get('pass_hash_func'),
                    },
                'handlers': {
                    'password': self.error_no_password_found,
                    'pass_check_func': self.error_no_password_check_function_found,
                    'pass_hash_func': self.error_no_password_hash_function_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_handler_set_user_email(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'email': kwargs.get('email'),
                    'email_check_func': kwargs.get('email_check_func'),
                    },
                'handlers': {
                    'email': self.error_no_user_email_found,
                    'email_check_func': self.error_no_user_email_check_function_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_no_credit_transfer_type_specified(self):
        log.error('No credit transfer type specified.')
        return False

    def error_no_user_controller_type_specified(self):
        log.error('No user controller type specified.')
        return False

    def error_no_credit_wallet_transfer_sheet_found(self, wallet=None):
        log.error(
                'No active transfer sheet found for credit wallet {}.'.format(
                    wallet.reference
                    )
                )
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_no_clock_id_found(self):
        log.error('No clock id found.')
        return False

    def error_no_user_pass_hash_archive_found(self):
        log.error('No user password hash archive found.')
        return False

    def error_no_user_credit_wallet_archive_found(self):
        log.error('No user credit wallet archive found.')
        return False

    def error_no_user_contact_list_archive_found(self):
        log.error('No user contact list archive found.')
        return False

    def error_no_user_name_found(self):
        log.error('No user name found.')
        return False

    def error_no_credit_wallet_found(self):
        log.error('No credit wallet found.')
        return False

    def error_no_contact_list_found(self):
        log.error('No contact list found.')
        return False

    def error_no_credit_wallet_found(self):
        log.error('No credit wallet found.')
        return False

    def error_no_contact_list_found(self):
        log.error('No contact list found.')
        return False

    def error_no_user_email_found(self):
        log.error('No user email found.')
        return False

    def error_no_user_email_check_function_found(self):
        log.error('No user email check function found.')
        return False

    def error_no_password_found(self):
        log.error('No password found.')
        return False

    def error_no_password_check_function_found(self):
        log.error('No password check function found.')
        return False

    def error_no_password_hash_function_found(self):
        log.error('No password hash function found.')
        return False

    def error_no_user_alias_found(self):
        log.error('No user alias found.')
        return False

    def error_no_user_phone_found(self):
        log.error('No user phone found.')
        return False

    def error_no_user_name_found(self):
        log.error('No user name found.')
        return False

    def error_no_user_pass_hash_found(self):
        log.error('No user password hash found.')
        return False

    def error_no_contact_list_id_found(self):
        log.error('No contact list id found.')
        return False

    def error_no_user_action_create_target_specified(self):
        log.error('No user action create target specified.')
        return False

    def error_no_user_action_reset_field_target_specified(self):
        log.error('No user action reset target specified.')
        return False

    def error_no_user_action_reset_archive_target_specified(self):
        log.error('No user action reset archive target specified.')
        return False

    def error_no_user_action_reset_target_specified(self):
        log.error('No user action reset target specified.')
        return False

    def error_no_user_action_switch_target_specified(self):
        log.error('No user action switch target specified.')
        return False

    def error_no_user_action_unlink_target_specified(self):
        log.error('No user action unlink target specified.')
        return False

    def error_no_user_controller_action_specified(self):
        log.error('No user controller action specified.')
        return False

    def error_no_user_controller_event_specified(self):
        log.error('No user controller event specified.')
        return False

    def error_no_state_code_found(self):
        log.error('No state code found.')
        return False

    def error_no_state_name_found(self):
        log.error('No state name found.')
        return False

    def error_no_set_by_parameter_specified(self):
        log.error('No set_by parameter specified.')
        return False

    def error_no_user_pass_hash_found(self):
        log.error('No user pass hash found.')
        return False

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

    def error_no_user_event_request_specified(self):
        log.error('No user event request specified.')
        return False

    def warning_could_not_fetch_credit_wallet(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit wallet.'
                )
        return False

    def warning_could_not_fetch_contact_list(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch contact list.'
                )
        return False

    def warning_could_not_fetch_credit_clock(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock.'
                )
        return False

###############################################################################
# CODE DUMP
###############################################################################
#   user_credit_wallet_id = Column(
#      Integer, ForeignKey('credit_ewallet.wallet_id')
#      )
#   user_contact_list_id = Column(
#      Integer, ForeignKey('contact_list.contact_list_id')
#      )
    # O2O
#   active_session = relationship(
#      'EWallet', back_populates='active_user',
#      foreign_keys=[active_session_id]
#      )
#   user = relationship(
#      'ResUser', back_populates='user_pass_hash_archive',
#      foreign_keys=user_id
#      )

#   def fetch_user_credit_wallet_transfer_sheet(self):
#       log.debug('')
#       _credit_wallet = self.fetch_user_credit_wallet()
#       return _credit_wallet.transfer_sheet

#   def action_create_incomming_credit_transfer(self, **kwargs):
#       log.debug('')
#       _transfer_sheet = self.fetch_user_credit_wallet_transfer_sheet()
#       if not _transfer_sheet:
#           return self.error_no_credit_wallet_transfer_sheet_found(
#                   wallet=self.user_credit_wallet
#                   )
#       return _transfer_sheet.credit_transfer_sheet_controller(**kwargs)

#   def action_create_outgoing_credit_transfer(self, **kwargs):
#       log.debug('')
#       _transfer_sheet = self.fetch_user_credit_wallet_transfer_sheet()
#       if not _transfer_sheet:
#           return self.error_no_credit_wallet_transfer_sheet_found(
#                   wallet=self.user_credit_wallet
#                   )
#       return _transfer_sheet.credit_transfer_sheet_controller(**kwargs)

#   def action_create_credit_transfer(self, **kwargs):
#       log.debug('')
#       if not kwargs.get('atype'):
#           return self.error_no_credit_transfer_type_specified()
#       _handlers = {
#               'incomming': self.action_create_incomming_credit_transfer,
#               'outgoing': self.action_create_outgoing_credit_transfer,
#               }
#       return _handlers[kwargs['atype']](**kwargs)


