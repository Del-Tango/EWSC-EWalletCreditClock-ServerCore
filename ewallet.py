import time
import datetime
import random
import hashlib
from validate_email import validate_email
import pysnooper

from . import EWalletLogin
from base.res_user import ResUser
from base.credit_wallet import CreditEWallet
from base.contact_list import ContactList
from base.system.config import Config


# [ NOTE ]: Ewallet session manager.
class EWallet():

    def __init__(self, **kwargs):
        self.session_credit_wallet = kwargs.get('session_credit_wallet')
        self.session_contact_list = kwargs.get('session_contact_list')
        self.session_active_user = kwargs.get('session_active_user')
        self.user_account_archive = {}

    def fetch_user_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        return self.user_account_archive.get(kwargs['code'])

    def fetch_user_by_name(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_name() == kwargs['code']:
                return self.user_account_archive[item]
        return False

    def fetch_user_by_email(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_email() == kwargs['code']:
                return self.user_account_archive[item]
        return False

    def fetch_user_by_phone(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_phone() == kwargs['code']:
                return self.user_account_archive[item]
        return False

    def fetch_user_by_alias(self, **kwargs):
        if not kwargs.get('code'):
            return False
        for item in self.user_account_archive:
            if self.user_account_archive[item].fetch_user_alias() == kwargs['code']:
                return self.user_account_archive[item]
        return False

    def fetch_user(self, **kwargs):
        if not kwargs.get('identifier'):
            return False
        _handlers = {
                'id': self.fetch_user_by_id,
                'name': self.fetch_user_by_name,
                'email': self.fetch_user_by_email,
                'phone': self.fetch_user_by_phone,
                'alias': self.fetch_user_by_alias,
                }
        return _handlers[kwargs['identifier']](**kwargs)

    def update_session_from_user(self, **kwargs):
        global session_active_user
        global session_credit_wallet
        global session_contact_list
        if not kwargs.get('session_active_user'):
            return False
        self.active_user = kwargs['session_active_user']
        self.credit_wallet = self.active_user.fetch_user_credit_wallet()
        self.contact_list = self.active_user.fetch_user_contact_list()
        return True

#   @pysnooper.snoop()
    def update_user_account_archive(self, **kwargs):
        global user_account_archive
        if not kwargs.get('user'):
            return False
        try:
            self.user_account_archive.update({
                kwargs['user'].fetch_user_id(), kwargs['user']
                })
        except TypeError:
            self.user_account_archive[
                    kwargs['user'].fetch_user_id()] = kwargs['user']
        return self.user_account_archive

    def action_reset_user_password(self, **kwargs):
        if not self.session_active_user or not kwargs.get('user_pass'):
            return False
        _pass_check_func = EWalletCreateAccount().check_user_pass
        _pass_hash_func = EWalletLogin().hash_password
        return self.session_active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_pass',
                password=kwargs['user_pass'],
                pass_check_func=_pass_check_func,
                pass_hash_func=_pass_hash_func,
                )

    def action_reset_user_email(self, **kwargs):
        if not self.session_active_user or not kwargs.get('user_email'):
            return False
        _email_check_func = EwalletCreateAccount().check_user_email
        return self.session_active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_email',
                email=kwargs['user_email']
                email_check_func=_email_check_func
                )

    def action_reset_user_alias(self, **kwargs):
        if not self.session_active_user or not kwargs.get('user_alias'):
            return False
        return self.session_active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_alias',
                alias=kwargs['user_alias']
                )

    def action_reset_user_phone(self, **kwargs):
        if not self.session_active_user or not kwargs.get('user_phone'):
            return False
        return self.session_active_user.user_controller(
                ctype='action', action='reset', target='field', field='user_phone',
                phone=kwargs['user_phone')
                )

    def action_create_new_user_account(self, **kwargs):
        session_create_account = EWalletLogin().ewallet_login_controller(
                action='new_account',
                user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
                user_email=kwargs.get('user_email'),
                user_archive=self.user_account_archive
                )
        if not session_create_account:
            return False
        self.update_session_from_user(
                active_user=session_create_account
                )
        self.update_user_account_archive(
                user=session_create_account
                )
        return session_create_account

    def action_create_new_credit_wallet(self, **kwargs):
        if not self.session_active_user:
            return False
        _new_wallet = self.session_active_user.user_controller(
                ctype='action', action='create', target='credit_wallet',
                reference=kwargs.get('reference'),
                credits=kwargs.get('credits'),
                )
        return _new_wallet or False

    def action_create_new_credit_clock(self, **kwargs):
        if not self.session_active_user:
            return False
        _new_clock = self.session_active_user.user_controller(
                ctype='action', action='create', target='credit_clock',
                reference=kwargs.get('reference'),
                credit_clock=kwargs.get('credit_clock'),
                )
        return _new_clock or False

    def action_create_new_contact_list(self, **kwargs):
        if not self.session_active_user:
            return False
        _new_list = self.session_active_user.user_controller(
                ctype='action', action='create', target='contact_list',
                reference=kwargs.get('reference'),
                )
        return _new_list or False

    def action_create_new_contact_record(self, **kwargs):
        if not self.session_contact_list:
            return False
        _new_record = self.session_contact_list.contact_list_controller(
                action='create', user_name=kwargs.get('user_name'),
                user_email=kwargs.get('user_email'),
                user_phone=kwargs.get('user_phone'),
                notes=kwargs.get('notes'),
                )
        return _new_record or False

    def action_create_new_contact(self, **kwargs):
        if not kwargs.get('contact'):
            return False
        _handlers = {
                'list': self.action_create_new_contact_list,
                'record': self.action_create_new_contact_record,
                }
        return _handlers[kwargs['contact']](**kwargs)

    def action_create_new_transfer(self, **kwargs):
        if not session_credit_wallet or not kwargs.get('transfer_type') \
                or not kwargs.get('partner_ewallet'):
            return False
        return self.session_credit_wallet.user_controller(
                action='transfer', transfer_type=kwargs['transfer_type'],
                partner_ewallet=kwargs['partner_ewallet'],
                credits=kwargs['credits'] or 0,
                reference=kwargs.get('reference'),
                transfer_from=kwargs.get('transfer_from'),
                transfer_to=kwargs.get('transfer_to'),
                )

    def action_unlink_user_account(self, **kwargs):
        global user_account_archive
        if not self.user_account_archive or not kwargs.get('user_id'):
            return False
        _user = self.fetch_user(identifier='id', code=kwargs['user_id'])
        return False if not _user \
                else self.user_account_archive.pop(kwargs['user_id'])

    def action_unlink_credit_wallet(self, **kwargs):
        if not self.session_active_user or not kwargs.get('wallet_id'):
            return False
        return self.session_active_user.user_controller(
                ctype='action', action='unlink', target='credit_wallet',
                wallet_id=kwargs['wallet_id'],
                )

    def action_unlink_contact_list(self, **kwargs):
        if not self.session_active_user or not kwargs.get('list_id'):
            return False
        return self.session_active_user.user_controller(
                ctype='action', action='unlink', target='contact_list',
                list_id=kwargs['list_id']
                )

    def action_unlink_contact_record(self, **kwargs):
        if not self.session_contact_list or not kwargs.get('record_id'):
            return False
        return self.session_contact_list.contact_list_controller(
                action='update', update_type='remove',
                record_id=kwargs['record_id'],
                )

    def action_unlink_invoice_list(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return False
        return self.session_credit_wallet.main_controller(
                controller='system', action='unlink_sheet', sheet='invoice',
                sheet_id=kwargs['list_id'],
                )

    def action_unlink_invoice_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _invoice_list = self.session_credit_wallet.fetch_invoice_sheet()
        return False if not _invoice_list \
                else _invoice_list.credit_invoice_sheet_controller(
                        action='remove', record_id=kwargs['record_id'],
                        )

    def action_unlink_transfer_list(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return False
        return self.session_credit_wallet.main_controller(
                controller='system', action='unlink_sheet', sheet='transfer',
                sheet_id=kwargs['list_id'],
                )

    def action_unlink_transfer_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return False
        _transfer_list = self.session_credit_wallet.fetch_transfer_sheet()
        return False if not _transfer_list \
                else _transfer_list.credit_transfer_sheet_controller(
                        action='remove', record_id=kwargs['record_id'],
                        )

    def action_unlink_time_list(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        return _credit_clock.main_controller(
                controller='system', action='unlink', unlink='sheet',
                sheet_type='time', sheet_id=kwargs['list_id']
                )

    def action_unlink_time_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _time_list = _credit_clock.fetch_credit_clock_time_sheet()
        return False if not _time_list \
                else _time_list.credit_clock_time_sheet_controller(
                        action='remove', record_id=kwargs['record_id']
                        )

    def action_unlink_conversion_list(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('list_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        return _credit_clock.main_controller(
                controller='system', action='unlink', unlink='sheet',
                sheet_type='conversion', sheet_id=kwargs['list_id']
                )

    def action_unlink_conversion_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        return False if not _conversion_list \
                else _conversion_list.credit_clock_conversion_sheet_controller(
                        action='remove', record_id=kwargs['record_id']
                        )

    def action_unlink_contact(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'list': self.action_unlink_contact_list,
                'record': self.action_unlink_contact_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_invoice(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'list': self.action_unlink_invoice_list,
                'record': self.action_unlink_invoice_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_transfer(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'list': self.action_unlink_transfer_list,
                'record': self.action_unlink_transfer_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_time(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'list': self.action_unlink_time_list,
                'record': self.action_unlink_time_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_unlink_conversion(self, **kwargs):
        if not kwargs.get('unlink'):
            return False
        _handlers = {
                'list': self.action_unlink_conversion_list,
                'record': self.action_unlink_conversion_record,
                }
        return _handlers[kwargs['unlink']](**kwargs)

    def action_view_user_account(self, **kwargs):
        if not self.session_active_user:
            return False
        res = self.session_active_user.fetch_user_values()
        print(res)
        return res

    def action_view_credit_wallet(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        res = self.session_credit_wallet.fetch_credit_ewallet_values()
        print(res)
        return res

    def action_view_credit_clock(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        res = _credit_clock.fetch_credit_clock_values()
        print(res)
        return res

    def action_view_contact_list(self, **kwargs):
        if not self.session_contact_list:
            return False
        res = self.session_contact_list.fetch_contact_list_values()
        print(res)
        return res

    def action_view_contact_record(self, **kwargs):
        if not self.session_contact_list or not kwargs.get('record_id'):
            return False
        _record = self.session_contact_list.fetch_contact_list_record_by_id(
                code=kwargs['record_id']
                )
        if not _record:
            return False
        res = _record.fetch_record_values()
        print(res)
        return res

    def action_view_contact(self, **kwargs):
        if not kwargs.get('contact'):
            return False
        _handlers = {
                'list': self.action_view_contact_list,
                'record': self.action_view_contact_record,
                }
        return _handlers[kwargs['contact']](**kwargs)

    def action_view_invoice_list(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _invoice_sheet = self.session_credit_wallet.fetch_credit_ewallet_invoice_sheet()
        res = _invoice_sheet.fetch_invoice_sheet_values()
        print(res)
        return res

    def action_view_invoice_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _invoice_sheet = self.session_credit_wallet.fetch_credit_ewallet_invoice_sheet()
        _record = _invoice_sheet.fetch_credit_invoice_records(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return False
        res = _record.fetch_record_values()
        print(res)
        return res

    def action_view_invoice(self, **kwargs):
        if not kwargs.get('invoice'):
            return False
        _handlers = {
                'list': self.action_view_invoice_list,
                'record': self.action_view_invoice_record,
                }
        return _handlers[kwargs['invoice']](**kwargs)

    def action_view_transfer_list(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _transfer_sheet = self.session_credit_wallet.fetch_credit_ewallet_transfer_sheet()
        res = _transfer_sheet.fetch_transfer_sheet_values()
        print(res)
        return res

    def action_view_transfer_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _transfer_sheet = self.session_credit_wallet.fetch_credit_ewallet_transfer_sheet()
        _record = _transfer_sheet.fetch_transfer_sheet_records(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return False
        res = _record.fetch_record_values()
        print(res)
        return res

    def action_view_time_list(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _time_sheet = _credit_clock.fetch_credit_clock_time_sheet()
        if not _time_sheet:
            return False
        res = _time_sheet.fetch_credit_clock_time_sheet_values()
        print(res)
        return res

    def action_view_time_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _time_sheet = _credit_clock.fetch_credit_clock_time_sheet()
        if not _time_sheet:
            return False
        _record = _time_sheet.fetch_time_sheet_records(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return False
        res = _record.fetch_record_values()
        print(res)
        return res

    def action_view_conversion_list(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _credit_clock = self.session_credit_wallet.fetch_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        if not _conversion_list:
            return False
        res = _conversion_list.fetch_credit_clock_conversion_sheet_values()
        print(res)
        return res

    def action_view_conversion_record(self, **kwargs):
        if not self.session_credit_wallet or not kwargs.get('record_id'):
            return False
        _credit_clock = self.session_credit_wallet.fetch_ewallet_credit_clock()
        if not _credit_clock:
            return False
        _conversion_list = _credit_clock.fetch_credit_clock_conversion_sheet()
        if not _conversion_list:
            return False
        _record = _conversion_list.fetch_conversion_sheet_records(
                search_by='id', code=kwargs['record_id']
                )
        if not _record:
            return False
        res = _record.fetch_record_values()
        print(res)
        return res

    def action_view_transfer(self, **kwargs):
        if not kwargs.get('transfer'):
            return False
        _handlers = {
                'list': self.action_view_transfer_list,
                'record': self.action_view_transfer_record,
                }
        return _handlers[kwargs['transfer']](**kwargs)

    def action_view_time(self, **kwargs):
        if not kwargs.get('time'):
            return False
        _handlers = {
                'list': self.action_view_time_list,
                'record': self.action_view_time_record,
                }
        return _handlers[kwargs['time']](**kwargs)

    def action_view_conversion(self, **kwars):
        if not kwargs.get('conversion'):
            return False
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

    # [ NOTE ]: Allows multiple logged in users to switch.
    def action_system_user_update(self, **kwargs):
        global session_active_user
        if not kwargs.get('user'):
            return False
        user_id = kwargs['user'].fetch_user_id()
        if user_id not in self.user_account_archive.keys():
            return False
        self.session_active_user = kwargs['user']
        self.update_session_from_user(session_active_user=kwargs['user'])
        return self.session_active_user

    def action_system_session_update(self, **kwargs):
        _update = self.update_session_from_user(**kwargs)
        return _update or False

    def handle_system_action_update(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'user': self.action_system_user_update,
                'session': self.action_system_session_update,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_system_action_check(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'user': self.action_system_user_check,
                'session': self.action_system_session_check,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_login(self, **kwargs):
        session_login = EWalletLogin().ewallet_login_controller(
                action='login', user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'),
                user_archive=self.user_account_archive
                )
        if not session_login:
            return False
        self.update_session_from_user(active_user=session_login)
        return session_login

    def handle_user_action_reset(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'user_alias': self.action_reset_user_alias,
                'user_pass': self.action_reset_user_password,
                'user_email': self.action_reset_user_email,
                'user_phone': self.action_reset_user_phone,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_create(self, **kwargs):
        if not kwargs.get('create'):
            return False
        _handlers = {
                'account': self.action_create_new_user_account,
                'credit_wallet': self.action_create_new_credit_wallet,
                'credit_clock': self.action_create_new_credit_clock,
                'transfer': self.action_create_new_transfer,
                'contact': self.action_create_new_contact,
                }
        return _handlers[kwargs['create']](**kwargs)

    def action_start_credit_clock_timer(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        return _credit_clock.main_controller(
                controller='user', action='start'
                )

    def action_stop_credit_clock_timer(self, **kwargs):
        if not self.session_credit_wallet:
            return False
        _credit_clock = self.session_credit_wallet.fetch_credit_ewallet_credit_clock()
        if not _credit_clock:
            return False
        return _credit_clock.main_controller(
                controller='user', action='stop'
                )

    def handle_user_action_time(self, **kwargs):
        if not kwargs.get('timer'):
            return False
        _handlers = {
                'start': self.action_start_credit_clock_timer,
                'stop': self.action_stop_credit_clock_timer,
                }
        return _handlers[kwargs['timer']](**kwargs)

    def handle_user_action_view(self, **kwargs):
        if not kwargs.get('view'):
            return False
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
        if not kwargs.get('unlink'):
            return False
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
        if not kwargs.get('action'):
            return False
        _handlers = {
                'login': self.handle_user_action_login,
                'create': self.handle_user_action_create,
                'time': self.handle_user_action_time,
                'reset': self.handle_user_action_reset,
                'view': self.handle_user_action_view,
                'unlink': self.handle_user_action_unlink,
                }
        return _handlers[kwargs['action']](**kwargs)

    def ewallet_user_event_controller(self, **kwargs):
        if not kwargs.get('event'):
            return False
        _handlers = {
                'signal': self.handle_user_event_signal,
                'notification': self.handle_user_event_notification,
                'request': self.handle_user_event_request,
                }
        return _handlers[kwargs['event']](**kwargs)

    def ewallet_system_event_controller(self, **kwargs):
        if not kwargs.get('event'):
            return False
        _handlers = {
                'signal': self.handle_system_event_signal,
                'notification': self.handle_system_event_notification,
                'request': self.handle_system_event_request,
                }
        return _handlers[kwargs['event']](**kwargs)

    def ewallet_system_action_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'check': self.handle_system_action_check,
                'update': self.handle_system_action_update,
                }
        return _handlers[kwargs['action']](**kwargs)

    def ewallet_system_controller(self, **kwargs):
        if not kwargs.get('ctype'):
            return False
        _handlers = {
                'action': self.ewallet_system_action_controller,
                'event': self.ewallet_system_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    def ewallet_user_controller(self, **kwargs):
        if not kwargs.get('ctype'):
            return False
        _handlers = {
                'action': self.ewallet_user_action_controller,
                'event': self.ewallet_user_event_controller,
                }
        return _handlers[kwargs['ctype']](**kwargs)

    # [ NOTE ]: Main
    def ewallet_controller(self, **kwargs):
        if not kwargs.get('controller'):
            return False
        _controllers = {
                'system': self.ewallet_system_controller,
                'user': self.ewallet_user_controller,
                'test': self.test_ewallet,
                }
        return _controllers[kwargs['controller']](**kwargs)

    def test_ewallet_user_controller(self):
        print('[ TEST ] User.')
        print('[ * ] Create account')
        self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='test user', user_pass='123abc@xxx', user_email='example@example.com'
                )
        print('[ * ] Login')
        self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='test user',
                user_pass='123abc@xxx'
                )
        print('[ * ] View account')
        self.ewallet_controller(
                controller='user', ctype='action', action='view', target='account'
                )
        print('[ * ] Create second account')
        self.ewallet_controller(
                controller='user', ctype='action', action='create', create='account',
                user_name='user2', user_pass='123abc@xxx', user_email='example2@example.com'
                )
        print('[ * ] Second Login')
        self.ewallet_controller(
                controller='user', ctype='action', action='login', user_name='user2',
                user_pass='123abc@xxx'
                )
        print('[ * ] View account')
        self.ewallet_controller(
                controller='user', ctype='action', action='view', target='account'
                )

    def test_ewallet_system_controller(self):
        print('[ TEST ] System.')
        print('[ * ] Update session')
        self.ewallet_controller(
                controller='system', ctype='action', action='update', target='session'
                )

    def test_ewallet(self, **kwargs):
        self.test_ewallet_user_controller()
        self.test_ewallet_system_controller()


ewallet = EWallet()
ewallet.ewallet_controller(controller='test')


################################################################################
# CODE DUMP
################################################################################

