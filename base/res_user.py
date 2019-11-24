import datetime
import random

from . import res_util
from . import credit_wallet
from . import contact_list

class ResUser():

    # TODO - Has dummy data
    def __init__(self, **kwargs):
        if not kwargs.get('user_name') or not kwargs.get('user_pass_hash'):
            return
        self.user_id = random.randint(10, 20)
        self.user_name = kwargs.get('user_name')
        self.user_create_date = kwargs.get('user_create_date') \
                or datetime.datetime.now()
        self.user_write_date = kwargs.get('user_write_date') \
                or datetime.datetime.now()
        self.user_credit_wallet = kwargs.get('user_credit_wallet') \
                or credit_wallet.CreditEWallet(
                        client_id=self.user_id,
                        reference='First Credit Wallet',
                        credits=0
                    )
        self.user_contact_list = kwargs.get('user_contact_list_id') \
                or contact_list.ContactList(
                        client_id=self.user_id,
                        reference='First Contact List',
                        )
        self.user_pass_hash = kwargs.get('user_pass_hash')
        self.user_email = kwargs.get('user_email')
        self.user_phone = kwargs.get('user_phone') or None
        self.user_alias = kwargs.get('user_alias') or None
        self.user_pass_hash_archive = kwargs.get('user_pass_hash_archive') \
                or {self.user_pass_hash: self.write_date}
        self.user_credit_wallet_archive = kwargs.get('user_credit_wallet_archive') \
                or {self.user_credit_wallet.fetch_credit_wallet_id(),
                        self.user_credit_wallet}
        self.user_contact_list_archive = kwargs.get('user_contact_list_archive') \
                or {self.user_contact_list.fetch_contact_list_id(),
                        self.user_contact_list}

    def fetch_user_id(self):
        return self.user_id

    def fetch_user_name(self):
        return self.user_name

    def fetch_user_create_date(self):
        return self.user_create_date

    def fetch_user_write_date(self):
        return self.user_write_date

    def fetch_user_credit_wallet(self):
        return self.user_credit_wallet

    def fetch_user_contact_list(self):
        return self.user_contact_list

    def fetch_user_pass_hash(self):
        return self.user_pass_hash

    def fetch_user_email(self):
        return self.user_email

    def fetch_user_phone(self):
        return self.user_phone

    def fetch_user_alias(self):
        return self.user_alias

    def fetch_user_pass_archive(self):
        return self.user_pass_archive

    def fetch_user_credit_wallet_archive(self):
        return self.user_credit_wallet_archive

    def fetch_user_contact_list_archive(self):
        return self.user_contact_list_archive

    def fetch_user_values(self):
        _values = {
                'user_id': self.user_id,
                'user_name': self.user_name,
                'user_create_date': self.user_create_date,
                'user_write_date': self.user_write_date,
                'user_credit_wallet': self.user_credit_wallet,
                'user_contact_list': self.user_contact_list,
                'user_pass_hash': self.user_pass_hash,
                'user_email': self.user_email,
                'user_phone': self.user_phone,
                'user_alias': self.user_alias,
                'user_pass_archive': self.user_pass_archive,
                'user_credit_wallet_archive': self.user_credit_wallet_archive,
                'user_contact_list_archive': self.user_contact_list_archive,
                }
        return _values

    def fetch_credit_wallet_by_id(self, credit_wallet_id):
        return self.user_credit_wallet_archive.get(credit_wallet_id)

    def fetch_contact_list_by_id(self, contact_list_id):
        return self.user_contact_list_archive.get(contact_list_id)

    def set_user_pass(self, **kwargs):
        global user_pass
        if not kwargs.get('password') or not kwargs.get('pass_check_func') \
                or not kwargs.get('pass_hash_func'):
            return False
        _check = kwargs['pass_check_func'](kwargs['password'])
        if not _check:
            return _create_user.error_invalid_user_pass()
        _pass_hash = kwargs['pass_hash_func'](kwargs['password'])
        self.user_pass = _pass_hash
        return True

    def set_user_alias(self, **kwargs):
        global user_alias
        if not kwargs.get('alias'):
            return False
        self.user_alias = kwargs['alias']
        return True

    def set_user_phone(self, **kwargs):
        global user_phone
        if not kwargs.get('phone'):
            return False
        self.user_phone = kwargs['phone']
        return True

    def set_user_email(self, **kwargs):
        global user_email
        if not kwargs.get('email') or not kwargs.get('email_check_func'):
            return False
        _check = kwargs['email_check_func'](kwargs['email'], severity=1)
        if not _check:
            return _create_user.error_invalid_user_email(user_email=kwargs['email'])
        self.user_email = kwargs['email']
        return True

    def set_user_credit_wallet(self, **kwargs):
        global user_credit_wallet
        if not kwargs.get('credit_wallet'):
            return False
        self.user_credit_wallet = kwargs['credit_wallet']
        return True

    def set_user_contact_list(self, **kwargs):
        global user_contact_list
        if not kwargs.get('contact_list'):
            return False
        self.user_contact_list = kwargs['contact_list']
        return True

    def set_user_name(self, **kwargs):
        global user_name
        if not kwargs.get('name'):
            return False
        self.user_name = kwargs['name']
        return True

    def set_user_credit_wallet(self, **kwargs):
        global user_credit_wallet
        if not kwargs.get('wallet'):
            return False
        self.user_credit_wallet = kwargs['wallet']
        return True

    def set_user_contact_list(self, **kwargs):
        global user_contact_list
        if not kwargs.get('contact_list'):
            return False
        self.user_contact_list = kwargs['contact_list']
        return True

    def set_user_pass_hash_archive(self, **kwargs):
        global user_pass_hash_archive
        if not kwargs.get('archive'):
            return False
        self.user_pass_hash_archive = kwargs['archive'] or {}
        return True

    def set_user_credit_wallet_archive(self, **kwargs):
        global user_credit_wallet_archive
        if not kwargs.get('archive'):
            return False
        self.user_credit_wallet_archive = kwargs['archive'] or {}
        return True

    def set_user_contact_list_archive(self, **kwargs):
        global user_contact_list_archive
        if not kwargs.get('archive'):
            return False
        self.user_contact_list_archive = kwargs['archive'] or {}
        return True

    def update_user_credit_wallet_archive(self, credit_wallet):
        global user_credit_wallet_archive
        self.user_credit_wallet_archive.update({
            credit_wallet.fetch_credit_wallet_id():
            credit_wallet
            })
        return self.user_credit_wallet_archive

    def update_user_contact_list_archive(self, contact_list):
        global user_contact_list_archive
        self.user_contact_list_archive.update({
            contact_list.fetch_contact_list_id():
            contact_list
            })
        return self.update_user_contact_list_archive

    def action_create_credit_wallet(self, **kwargs):
        _new_credit_wallet = credit_wallet.CreditEWallet(
                client_id=self.user_id,
                reference=kwargs.get('reference') or str(),
                credits=kwargs.get('credits') or int(),
                )
        self.update_user_credit_wallet_archive(_new_credit_wallet)
        return _new_credit_wallet

    def action_create_credit_clock(self, **kwargs):
        _new_credit_clock = self.user_credit_wallet.main_controller(
                controller='system', action='create_clock',
                reference=kwargs.get('reference'),
                credit_clock=kwargs.get('credit_clock'),
                )
        return _new_credit_clock

    def action_create_contact_list(self, **kwargs):
        _new_contact_list = contact_list.ContactList(
                client_id=self.user_id,
                reference=kwargs.get('reference') or str(),
                )
        self.update_user_contact_list_archive(_new_contact_list)
        return _new_contact_list

    def action_switch_credit_wallet(self, **kwargs):
        if not kwargs.get('wallet_id'):
            return False
        _wallet = self.fetch_user_credit_wallet_by_id(kwargs['wallet_id'])
        return False if not _wallet else self.set_user_credit_wallet(_wallet)

    def action_switch_credit_clock(self, **kwargs):
        if not kwargs.get('clock_id'):
            return False
        _clock = self.user_credit_wallet.main_controller(
                controller='user', action='switch_clock',
                clock_id=kwargs['clock_id']
                )
        return False if not _clock else _clock

    def action_switch_contact_list(self, **kwargs):
        if not kwargs.get('list_id'):
            return False
        _list = self.fetch_user_contact_list_by_id(kwargs['list_id'])
        return False if not _list else self.set_user_contact_list(_list)

    def action_unlink_credit_wallet(self, **kwargs):
        global user_credit_wallet_archive
        if not kwargs.get('wallet_id'):
            return False
        _wallet = self.fetch_credit_wallet_by_id(kwargs['wallet_id'])
        return False if not _wallet \
                else self.user_credit_wallet_archive.pop(kwargs['wallet_id'])

    def action_unlink_credit_clock(self, **kwargs):
        if not kwargs.get('clock_id'):
            return False
        return self.credit_wallet.main_controller(
                controller='system', action='unlink_clock',
                clock_id=kwargs['clock_id']
                )

    def action_unlink_contact_list(self, **kwargs):
        global user_contact_list_archive
        if not kwargs.get('list_id'):
            return False
        _contact_list = self.fetch_contact_list_by_id(kwargs['list_id'])
        return False if not _contact_list \
                else self.user_contact_list_archive.pop(kwargs['list_id'])

    def handle_user_action_create(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'credit_wallet': self.action_create_credit_wallet,
                'credit_clock': self.action_create_credit_clock,
                'contact_list': self.action_create_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_action_reset_field(self, **kwargs):
        if not kwargs.get('field'):
            return False
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
        if not kwargs.get('archive'):
            return False
        _handlers = {
                'password': self.set_user_pass_hash_archive,
                'credit_wallet': self.set_user_credit_wallet_archive,
                'contact_list': self.set_user_contact_list_archive,
                }
        return _handlers[kwargs['archive']](kwargs.get('value'))

    def handle_user_action_reset(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'field': self.handle_action_reset_field,
                'archive': self.handle_action_reset_archive,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_switch(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'credit_wallet': self.action_switch_credit_wallet,
                'credit_clock': self.action_switch_credit_clock,
                'contact_list': self.action_switch_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        if not kwargs.get('target'):
            return False
        _handlers = {
                'credit_wallet': self.action_unlink_credit_wallet,
                'credit_clock': self.action_unlink_credit_clock,
                'contact_list': self.action_unlink_contact_list,
                }
        return _handlers[kwargs['target']](**kwargs)

    # TODO
    def handle_user_event_request(self, **kwargs):
        pass

    # TODO
    def handle_user_event_notification(self, **kwargs):
        pass

    # TODO
    def handle_user_event_signal(self, **kwargs):
        pass

    def user_action_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'create': self.handle_user_action_create,
                'reset': self.handle_user_action_reset,
                'switch': self.handle_user_action_switch,
                'unlink': self.handle_user_action_unlink,
                }
        return _handlers[kwargs['action']](**kwargs)

    def user_event_controller(self, **kwargs):
        if not kwargs.get('event'):
            return False
        _handlers = {
                'request': self.handle_user_event_request,
                'notification': self.handle_user_event_notification,
                'signal': self.handle_user_event_signal,
                }
        return _handlers[kwargs['event']](**kwargs)

    def user_controller(self, **kwargs):
        if not kwargs.get('ctype'):
            return False
        _controllers = {
                'action': self.user_action_controller,
                'event': self.user_event_controller,
                }
        return _controllers[kwargs['ctype']](**kwargs)


