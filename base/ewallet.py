import time
import datetime
import logging
import pysnooper

# from validate_email import validate_email
from sqlalchemy import Table, Column, String, Integer, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship, backref

from .res_user import ResUser
from .res_master import ResMaster
from .ewallet_login import EWalletLogin, EWalletCreateUser
from .ewallet_logout import EWalletLogout
from .res_utils import ResUtils, Base
from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .config import Config
from .res_user_pass_hash_archive import ResUserPassHashArchive

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletSessionUser(Base):
    '''
    [ NOTE ]: Many2many table for user sessions.
    '''
    __tablename__ = 'ewallet_session_user'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('ewallet.id'))
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    datetime = Column(DateTime, default=datetime.datetime.now())
    user = relationship('ResUser', backref=backref('ewallet_session_user'))
    session = relationship('EWallet', backref=backref('ewallet_session_user'))


class EWallet(Base):
    '''
    [ NOTE ]: EWallet session. Managed by EWallet Workers within the Session Manager.
    '''
    __tablename__ = 'ewallet'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    expiration_date = Column(DateTime)
    session = None
    contact_list = relationship(
        'ContactList', back_populates='active_session',
    )
    credit_wallet = relationship(
        'CreditEWallet', back_populates='active_session',
    )
    active_user = relationship(
        'ResUser', back_populates='active_session',
    )
    active_master = relationship(
        'ResMaster', back_populates='active_session',
    )
    user_account_archive = relationship(
        'ResUser', secondary='ewallet_session_user',
    )

#   @pysnooper.snoop()
    def __init__(self, **kwargs):
        now = datetime.datetime.now()
        self.name = kwargs.get('reference')
        self.session = kwargs.get('session') or res_utils.session_factory()
        self.create_date = kwargs.get('create_date') or now
        self.write_date = kwargs.get('write_date') or now
        self.expiration_date = kwargs.get('expiration_date') or \
            now + datetime.timedelta(
                hours=self.fetch_default_ewallet_session_validity_interval_in_hours()
            )
        self.contact_list = kwargs.get('contact_list') or []
        self.credit_wallet = kwargs.get('credit_wallet') or []
        self.active_user = kwargs.get('active_user') or []
        self.user_account_archive = kwargs.get('user_account_archive') or []

    # FETCHERS

    def fetch_active_session_values(self):
        log.debug('')
        user_account_archive = self.fetch_active_session_user_account_archive()
        user_account = self.fetch_active_session_user()
        master_account = self.fetch_active_session_master()
        values = {
            'id': self.id,
            'name': self.name,
            'orm_session': self.session,
            'create_date': self.create_date,
            'write_date': self.write_date,
            'expiration_date': self.expiration_date,
            'contact_list': self.fetch_active_session_contact_list(),
            'credit_ewallet': self.fetch_active_session_credit_wallet(),
            'user_account': [] if isinstance(user_account, dict) and
                user_account.get('failed') else user_account,
            'master_account': [] if isinstance(master_account, dict) and
                master_account.get('failed') else master_account,
            'user_account_archive': {} if not user_account_archive else {
                item.fetch_user_email(): item.fetch_user_name() for item in
                user_account_archive
            }
        }
        return values

    def fetch_active_session_master(self, obj=True):
        log.debug('')
        try:
            if not self.active_master:
                return self.error_no_session_active_master_found(
                    self.active_master
                )
            return self.active_master[0] if obj else \
                self.active_master[0].fetch_user_id()
        except Exception as e:
            return self.error_could_not_fetch_active_session_master({
                'account': self.active_user
            }, e)

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_master_account_by_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_master_account_email_specified(kwargs)
        try:
            user_account = list(kwargs['active_session'].query(
                ResMaster
            ).filter_by(user_email=kwargs['master']))
        except Exception as e:
            return self.error_could_not_fetch_master_account_by_email(kwargs, e)
        if user_account:
            log.info('Successfully fetched master user account by email.')
        return self.warning_no_master_account_found_by_email(kwargs) if not \
            user_account else user_account[0]

    def fetch_master_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_master_account_search_by_specified(kwargs)
        handlers = {
            'id': self.fetch_master_account_by_id,
            'email': self.fetch_master_account_by_email,
        }
        if kwargs['search_by'] not in handlers.keys():
            return self.warning_invalid_search_by_parameter_for_master_account(
                kwargs, set(handlers.keys())
            )
        return handlers[kwargs['search_by']](**kwargs)

    def fetch_master_account_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        try:
            user_account = list(kwargs['active_session'].query(
                ResMaster
            ).filter_by(user_id=kwargs['master_id']))
        except Exception as e:
            return self.error_could_not_fetch_master_account_by_id(kwargs)
        if user_account:
            log.info('Successfully fetched master user account by id.')
        return self.warning_no_master_account_found_by_id(kwargs) if not \
            user_account else user_account[0]

#   @pysnooper.snoop('logs/ewallet.log')
    def fetch_active_session_user(self, obj=True):
        log.debug('')
        try:
            if not self.active_user:
                return self.error_no_session_active_user_found(
                    self.active_user
                )
            return self.active_user[0] if obj else \
                self.active_user[0].fetch_user_id()
        except Exception as e:
            return self.error_could_not_fetch_active_session_user({
                'account': self.active_user,
                'exception': e,
            })

    def fetch_active_session_credit_wallet(self, obj=True):
        log.debug('')
        return self.error_no_session_credit_wallet_found(
            {'credit_wallet': self.credit_wallet}
        ) if not self.credit_wallet else (
            self.credit_wallet[0] if obj else
            self.credit_wallet[0].fetch_credit_ewallet_id()
        )

    def fetch_active_session_user_account_archive(self):
        log.debug('')
        return False if not self.user_account_archive \
            else self.user_account_archive

    def fetch_active_session_contact_list(self, obj=True):
        log.debug('')
        return self.error_no_session_contact_list_found(
            {'contact_list': self.contact_list}
        ) if not self.contact_list else (
            self.contact_list[0] if obj else
            self.contact_list[0].fetch_contact_list_id()
        )

    def fetch_default_ewallet_session_validity_interval_in_hours(self):
        log.debug('')
        minutes = int(config.session_config['ewallet_session_validity'])
        minutes_in_hour = 60
        return minutes / minutes_in_hour

    def fetch_default_ewallet_session_validity_interval_in_minutes(self):
        log.debug('')
        return int(config.session_config['ewallet_session_validity'])

#   @pysnooper.snoop()
    def fetch_user_by_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('email'):
            return self.error_no_user_email_found(kwargs)
        active_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        if not active_session or isinstance('active_session', dict) and \
                active_session.get('failed'):
            return self.error_no_active_session_found(kwargs, active_session)
        try:
            user_account = list(
                active_session.query(
                    ResUser
                ).filter_by(
                    user_email=kwargs['email']
                )
            )
            return self.warning_no_user_account_found(kwargs, active_session) \
                    if not user_account else user_account[0]
        except Exception as e:
            return self.error_could_not_fetch_user_by_email(
                kwargs, active_session, e
            )

    def fetch_email_check_func(self):
        log.debug('')
        return EWalletCreateUser().check_user_email

    def fetch_user_password_check_function(self):
        log.debug('')
        return EWalletCreateUser().check_user_pass

    def fetch_user_password_hash_function(self):
        log.debug('')
        return res_utils.hash_password

    def fetch_active_session_reference(self):
        log.debug('')
        return self.name

    def fetch_active_session_expiration_date(self):
        log.debug('')
        return self.expiration_date

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

#   @pysnooper.snoop('logs/ewallet.log')
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

    def fetch_partner_credit_wallet(self, partner_account):
        log.debug('')
        partner_wallet = False if not partner_account.user_credit_wallet else \
                partner_account.user_credit_wallet[0]
        return self.warning_no_partner_credit_wallet_found() if not partner_wallet \
                else partner_wallet

    def fetch_system_core_user_account(self, **kwargs):
        '''
        [ NOTE   ]: Fetches S:Core user account used for administration and automation.
        [ INPUT  ]: active_session=<orm-session>
        [ RETURN ]: (ResUser object | False)
        '''
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_active_session()
        score_account = list(active_session.query(ResUser).filter_by(user_id=1))
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
        handlers = {
            'id': self.fetch_user_by_id,
            'name': self.fetch_user_by_name,
            'email': self.fetch_user_by_email,
            'phone': self.fetch_user_by_phone,
            'alias': self.fetch_user_by_alias,
        }
        return handlers[kwargs['identifier']](**kwargs)

    def fetch_active_session_id(self):
        log.debug('')
        return self.id

    def fetch_active_session(self):
        log.debug('')
        if not self.session:
            return self.error_no_active_session_found()
        return self.session

    def fetch_active_session_credit_clock(self, **kwargs):
        log.debug('')
        _credit_wallet = kwargs.get('credit_ewallet') or \
                self.fetch_active_session_credit_wallet()
        if not _credit_wallet:
            return self.error_could_not_fetch_active_session_credit_wallet()
        _credit_clock = _credit_wallet.fetch_credit_ewallet_credit_clock()
        return _credit_clock or False

    '''
    [ NOTE   ]: Fetches either specified credit wallet or active user credit wallet credit count.
    [ INPUT  ]: credit_wallet=<wallet>
    [ RETURN ]: (Credit wallet credits | False)
    '''
    def fetch_credit_wallet_credits(self, **kwargs):
        log.debug('')
        credit_wallet = kwargs.get('credit_wallet') or \
                self.fetch_active_session_credit_wallet()
        return self.error_no_credit_wallet_found(kwargs) if not credit_wallet else \
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
        active_user = kwargs.get('active_user')
        filtered = [
            item for item in self.user_account_archive
            if item is not active_user
        ]
        return [] if not filtered else filtered[0]

    # SETTERS

#   def set_to_master_account_archive(self, account):
#       log.debug('')
#       try:
#           self.master_account_archive.append(account)
#           self.update_write_date()
#       except Exception as e:
#           return self.error_could_not_set_master_account_to_archive(
#               account, self.master_account_archive, e
#           )
#       log.info('Successfully updated ewallet session master account archive.')
#       return self.master_account_archive

    def set_session_active_master(self, active_master):
        log.debug('')
        try:
            self.active_master = active_master if \
                isinstance(active_master, list) else [active_master]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_active_session_master(
                active_master, self.active_master, e
            )
        log.info('Successfully set ewallet session active master.')
        return self.active_master

    def set_session_name(self, name):
        log.debug('')
        try:
            self.name = name
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_session_name(
                name, self.name, e
            )
        log.info('Successfully set ewallet session reference.')
        return self.name

    def set_session_expiration_date(self, expiration_date):
        log.debug('')
        try:
            self.expiration_date = expiration_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_session_expiration_date(
                expiration_date, self.expiration_date, e
            )
        log.info('Successfully set ewallet session expiration date.')
        return self.expiration_date

    def set_to_user_account_archive(self, account):
        log.debug('')
        try:
            self.user_account_archive.append(account)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_account_to_archive(
                account, self.user_account_archive, e
            )
        log.info('Successfully updated ewallet session user account archive.')
        return self.user_account_archive

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set ewallet session write date.')
        return self.write_date

    def set_orm_session(self, orm_session):
        log.debug('')
        try:
            self.session = orm_session
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_orm_session(
                orm_session, self.session, e
            )
        log.info('Successfully set ewallet session ORM session.')
        return self.session

    def set_session_active_user(self, active_user):
        log.debug('')
        try:
            self.active_user = active_user if isinstance(active_user, list) \
                    else [active_user]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_active_session_user(
                active_user, self.active_user, e
            )
        log.info('Successfully set ewallet session active user.')
        return self.active_user

#   @pysnooper.snoop('logs/ewallet.log')
    def set_session_credit_wallet(self, credit_wallet):
        log.debug('')
        if not credit_wallet or isinstance(credit_wallet, dict):
            return self.error_invalid_credit_ewallet(credit_wallet)
        try:
            self.credit_wallet = credit_wallet if \
                isinstance(credit_wallet, list) else [credit_wallet]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_session_credit_ewallet(
                credit_wallet, self.credit_wallet, e
            )
        log.info('Successfully set ewallet session credit ewallet.')
        return self.credit_wallet

    def set_session_contact_list(self, contact_list):
        log.debug('')
        try:
            self.contact_list = contact_list if \
                isinstance(contact_list, list) else [contact_list]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_session_contact_list(
                contact_list, self.contact_list, e
            )
        log.info('Successfully set ewallet session contact list.')
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
            'active_master': self.set_session_active_master,
            'credit_wallet': self.set_session_credit_wallet,
            'contact_list': self.set_session_contact_list,
        }
        for item in data_dct:
            if item in handlers and data_dct[item]:
                handlers[item](data_dct[item])
        return data_dct

    def set_session_user_account_archive(self, archive):
        log.debug('')
        try:
            self.user_account_archive = archive
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_account_archive(
                archive, self.user_account_archive, e
            )
        log.info('Successfully set ewallet session user account archive.')
        return archive

    # CHECKERS

    def check_master_user_account_frozen(self, **kwargs):
        log.debug('')
        master_account = self.fetch_master_account_by_id(
            master_id=kwargs['master_id'],
            active_session=kwargs['active_session']
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_could_not_fetch_master_account_by_identifier(
                kwargs, master_account
            )
        check = master_account.check_master_account_frozen()
        if isinstance(check, dict) and check.get('failed'):
            return self.warning_could_not_check_master_account_frozen(
                kwargs, master_account, check
            )
        return False if not check else True

    def check_master_account_belongs_to_ewallet_session(self, account):
        log.debug('')
        try:
            return False if account.fetch_user_id() \
                != self.fetch_active_session_master(obj=False) else True
        except Exception as e:
            self.error_could_not_check_if_master_account_belongs_to_ewallet_session(
                account, self.active_master, e
            )

    def check_master_logged_in(self):
        log.debug('')
        master_account = self.fetch_active_session_master(obj=True)
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return False
        return master_account.check_user_logged_in()

    def check_master_account_flag_for_unlink(self):
        log.debug('')
        master_account = self.fetch_active_session_master(obj=True)
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return False
        flagged_for_unlink = master_account.fetch_user_to_unlink()
        if flagged_for_unlink:
            log.debug(
                'Master account {} was flagged for unlink on {}.'.format(
                    master_account.fetch_user_name(),
                    res_utils.format_datetime(
                        master_account.fetch_user_to_unlink_timestamp()
                    )
                )
            )
        return flagged_for_unlink

    def check_master_account_frozen(self):
        log.debug('')
        master_account = self.fetch_active_session_master(obj=True)
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return False
        frozen = master_account.check_master_account_frozen()
        if frozen:
            log.debug(
                'Master account {} currently frozen.'.format(
                    master_account.fetch_user_name()
                )
            )
        return frozen

#   @pysnooper.snoop('logs/ewallet.log')
    def check_user_in_master_account_pool(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id') or not kwargs.get('user_email'):
            return self.error_invalid_data_set_for_master_account_user_pool_check(
                kwargs
            )
        master_account = self.fetch_master_account_by_id(
            master_id=kwargs['master_id'],
            active_session=kwargs['active_session']
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_could_not_fetch_master_account_by_identifier(
                kwargs, master_account
            )
        check = master_account.check_user_in_subpool_by_email(
            kwargs['user_email']
        )
        if isinstance(check, dict) and check.get('failed'):
            return self.warning_could_not_check_user_belongs_to_master_account_subpool(
                kwargs, master_account, check
            )
        return False if not check else True

    def check_master_user_account_key_code(self, **kwargs):
        log.debug('')
        if not kwargs.get('key') or not kwargs.get('master_account'):
            return self.error_invalid_data_set_for_master_key_code_check(kwargs)
        return kwargs['master_account'].validate_key_code(kwargs['key'])

    def check_session_master_account_is_set(self):
        log.debug('')
        account = self.fetch_active_session_master()
        return False if not account or (
            isinstance(account, dict) and account.get('failed')
        ) else True

    def check_session_user_account_is_set(self):
        log.debug('')
        account = self.fetch_active_session_user()
        return False if not account or (
            isinstance(account, dict) and account.get('failed')
        ) else True

    def check_session_contact_list_is_set(self):
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        return False if not contact_list or (
            isinstance(contact_list, dict) and contact_list.get('failed')
        ) else True

    def check_session_credit_ewallet_is_set(self):
        log.debug('')
        ewallet = self.fetch_active_session_credit_wallet()
        return False if not ewallet or (
            isinstance(ewallet, dict) and ewallet.get('failed')
        ) else True

    def check_session_user_archive_is_set(self):
        log.debug('')
        account_archive = self.fetch_active_session_user_account_archive()
        return False if not account_archive or (
            isinstance(account_archive, dict) and account_archive.get('failed')
        ) else True

    def check_if_active_ewallet_session_empty(self):
        log.debug('')
        checks = {
            'active_user': self.check_session_user_account_is_set(),
            'active_master': self.check_session_master_account_is_set(),
            'contact_list': self.check_session_contact_list_is_set(),
            'credit_ewallet': self.check_session_credit_ewallet_is_set(),
            'user_archive': self.check_session_user_archive_is_set(),
        }
        return True if True not in checks.values() else False

    def check_user_account_flag_for_unlink(self):
        log.debug('')
        user_account = self.fetch_active_session_user(obj=True)
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return False
        flagged_for_unlink = user_account.fetch_user_to_unlink()
        if flagged_for_unlink:
            log.debug(
                'User account {} was flagged for unlink on {}.'.format(
                    user_account.fetch_user_name(),
                    res_utils.format_datetime(
                        user_account.fetch_user_to_unlink_timestamp()
                    )
                )
            )
        return flagged_for_unlink

    def check_user_account_belongs_to_ewallet_session(self, account):
        log.debug('')
        return False if account not in self.user_account_archive \
            else True

    def check_user_logged_in(self):
        log.debug('')
        user_account = self.fetch_active_session_user(obj=True)
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return False
        return user_account.check_user_logged_in()

#   @pysnooper.snoop('logs/ewallet.log')
    def check_if_active_ewallet_session_expired(self):
        log.debug('')
        expiration_date = self.fetch_active_session_expiration_date()
        now = datetime.datetime.now()
        return True if now > expiration_date else False

    # CLEANERS

#   @pysnooper.snoop('logs/ewallet.log')
    def cleanup_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_account'):
            return self.error_no_user_account_specified(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'cleanup'
        )
        cleanup_account = kwargs['user_account'].user_controller(
            ctype='action', action='cleanup', cleanup='account',
            **sanitized_command_chain
        )
        return self.warning_could_not_cleanup_user_account(
            kwargs, cleanup_account
        ) if not cleanup_account or isinstance(cleanup_account, dict) and \
            cleanup_account.get('failed') else cleanup_account

    def clear_session_active_user(self):
        log.debug('')
        self.set_session_active_user([])
        return True

    def clear_session_credit_wallet(self):
        log.debug('')
        self.set_session_credit_wallet([])
        return True

    def clear_session_contact_list(self):
        log.debug('')
        self.set_session_contact_list([])
        return True

    def clear_session_user_account_archive(self):
        log.debug('')
        self.set_session_user_account_archive([])
        return True

    def clear_session_active_master(self):
        log.debug('')
        self.set_session_active_master([])
        return True

    def clear_active_session_user_data(self, data_dct):
        '''
        [ NOTE   ]: Clears all user information from active EWallet session.
        [ RETURN ]: ({'field-name': (True | False), ...} | False)
        '''
        log.debug('')
        handlers = {
            'active_user': self.clear_session_active_user,
            'credit_wallet': self.clear_session_credit_wallet,
            'contact_list': self.clear_session_contact_list,
            'user_account_archive': self.clear_session_user_account_archive,
            'active_master': self.clear_session_active_master,
        }
        for item in data_dct:
            if item in handlers and data_dct[item]:
                handlers[item]()
        return data_dct

    # UPDATERS

#   def update_master_account_archive(self, **kwargs):
#       log.debug('')
#       if not kwargs.get('master') or isinstance(kwargs['master'], dict) and \
#               kwargs['master'].get('failed'):
#           return self.error_no_master_object_found(kwargs)
#       set_to_archive = self.set_to_master_account_archive(kwargs['master'])
#       log.info(
#           'Successfully updated session master account archive '
#           'with account {}.'.format(kwargs['user'].fetch_user_name())
#       )
#       return set_to_archive

    def update_session_from_master(self, **kwargs):
        log.debug('')
        if not kwargs.get('session_active_master'):
            return self.error_no_session_active_master_found()
        user = kwargs['session_active_master']
        orm_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        session_data = {
            'active_master': user,
        }
        set_data = self.set_session_data(session_data)
        orm_session.commit()
        log.info(
            'Successfully updated ewallet session from current active master.'
        )
        return session_data

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
        orm_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        session_data = {
            'active_user': user,
            'credit_wallet': user.fetch_user_credit_wallet(),
            'contact_list': user.fetch_user_contact_list(),
        }
        set_data = self.set_session_data(session_data)
        orm_session.commit()
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
        if not kwargs.get('user') or isinstance(kwargs['user'], dict) and \
                kwargs['user'].get('failed'):
            return self.error_no_user_object_found(kwargs)
        set_to_archive = self.set_to_user_account_archive(kwargs['user'])
        log.info(
            'Successfully updated session user account archive with user {}.'
            .format(kwargs['user'].fetch_user_name())
        )
        return set_to_archive

    def update_write_date(self):
        log.debug('')
        self.set_write_date(datetime.datetime.now())
        return True

    # GENERAL

#   @pysnooper.snoop('logs/ewallet.log')
    def assure_all_user_accounts_logged_out(self, **kwargs):
        log.debug('')
        failures = 0
        while self.active_user:
            logout = self.action_logout_user_account(**kwargs)
            if not logout or isinstance(logout, dict) and logout.get('failed'):
                self.warning_could_not_logout_user_account(
                    kwargs, logout, failures
                )
                failures += 1
            if failures > 3:
                return self.error_logout_failure_limit_exceeded(kwargs)
        return True

    def keep_alive(self, **kwargs):
        log.debug('')
        session_validity_interval = self.fetch_default_ewallet_session_validity_interval_in_minutes()
        future_date = res_utils.fetch_future_expiration_date(
            unit='minutes', minutes=session_validity_interval
        )
        set_date = self.set_session_expiration_date(future_date)
        if not set_date or isinstance(set_date, dict) and \
                set_date.get('failed'):
            return set_date
        return True

    def inspect_master_subordonate(self, **kwargs):
        log.debug('')
        if not kwargs.get('subordonate'):
            return self.error_no_subordonate_account_id_specified(kwargs)
        master_account = kwargs.get('master') or \
            self.fetch_active_session_master()
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_account_found(kwargs, master_account)
        try:
            subordonate = master_account.inspect_subordonate(
                kwargs['subordonate'], **kwargs
            )
        except Exception as e:
            return self.error_could_not_inspect_master_account_subordonate(
                kwargs, master_account, e
            )
        if not subordonate or isinstance(subordonate, dict) and \
                subordonate.get('failed'):
            return self.warning_could_not_inspect_master_subordonate_account(
                kwargs, master_account, subordonate
            )
        command_chain_response = {
            'failed': False,
            'subordonate': subordonate['subordonate'],
        }
        return command_chain_response

    def inspect_master_subpool(self, **kwargs):
        log.debug('')
        master_account = kwargs.get('master') or \
            self.fetch_active_session_master()
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_account_found(kwargs, master_account)
        try:
            subpool = master_account.inspect_subpool()
        except Exception as e:
            return self.error_could_not_inspect_master_account_subpool(
                kwargs, master_account, e
            )
        if not subpool or isinstance(subpool, dict) and \
                subpool.get('failed'):
            return self.warning_could_not_inspect_master_account_subpool(
                kwargs, master_account
            )
        command_chain_response = {
            'failed': False,
            'subpool': subpool['subpool'],
        }
        return command_chain_response

    def recover_master_account(self, **kwargs):
        log.debug('')
        master_account = kwargs.get('master') or \
            self.fetch_active_session_master()
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.error_no_master_account_found(kwargs, master_account)
        try:
            master_account.set_to_unlink(False)
            master_account.set_to_unlink_timestamp(None)
        except Exception as e:
            return self.error_could_not_recover_master_account(
                kwargs, master_account, e
            )
        if master_account.to_unlink:
            kwargs['active_session'].rollback()
            return self.warning_could_not_recover_master_account(
                kwargs, master_account
            )
        kwargs['active_session'].commit()
        master_email = master_account.fetch_user_email()
        command_chain_response = {
            'failed': False,
            'account': master_email,
        }
        return command_chain_response

#   @pysnooper.snoop()
    def recover_user_account(self, **kwargs):
        log.debug('')
        user_account = kwargs.get('user') or \
            self.fetch_active_session_user()
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return self.error_no_user_account_found(kwargs)
        try:
            user_account.set_to_unlink(False)
            user_account.set_to_unlink_timestamp(None)
        except Exception as e:
            return self.error_could_not_recover_user_account(kwargs, e)
        if user_account.to_unlink:
            kwargs['active_session'].rollback()
            return self.warning_could_not_recover_user_account(user_account, kwargs)
        kwargs['active_session'].commit()
        user_email = user_account.fetch_user_email()
        command_chain_response = {
            'failed': False,
            'account': user_email,
        }
        return command_chain_response

    # UNLINKERS
    '''
    [ WATCHOUT ]: Primordial Dragons be here from before the times of v.DeltaT.
    '''

    def unlink_user_account_credit_ewallet(self, user_id, **kwargs):
        log.debug('')
        try:
            ewallets = kwargs['active_session'].query(
                CreditEWallet
            ).filter_by(
                client_id=user_id
            )
            if len(list(ewallets)) >= 1:
                ewallets.delete()
                kwargs['active_session'].commit()
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account_login_records(
                user_id, kwargs, e
            )
        return user_id

    def unlink_user_account_contact_list(self, user_id, **kwargs):
        log.debug('')
        try:
            contact_lists = kwargs['active_session'].query(
                ContactList
            ).filter_by(
                client_id=user_id
            )
            if len(list(contact_lists)) >= 1:
                contact_lists.delete()
                kwargs['active_session'].commit()
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account_login_records(
                user_id, kwargs, e
            )
        return user_id

    def unlink_user_account_pass_hash_archive(self, user_id, **kwargs):
        log.debug('')
        try:
            pass_archives = kwargs['active_session'].query(
                ResUserPassHashArchive
            ).filter_by(
                user_id=user_id
            )
            if len(list(pass_archives)) >= 1:
                pass_archives.delete()
                kwargs['active_session'].commit()
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account_login_records(
                user_id, kwargs, e
            )
        return user_id

    def unlink_master_account_login_records(self, master_id, **kwargs):
        log.debug('')
        try:
            login_records = kwargs['active_session'].query(
                EWalletLogin
            ).filter_by(
                master_id=master_id
            )
            if len(list(login_records)) >= 1:
                login_records.delete()
                kwargs['active_session'].commit()
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_master_account_login_records(
                master_id, kwargs, e
            )
        return master_id

    def unlink_master_account_logout_records(self, master_id, **kwargs):
        log.debug('')
        try:
            logout_records = kwargs['active_session'].query(
                EWalletLogout
            ).filter_by(
                master_id=master_id
            )
            if len(list(logout_records)) >= 1:
                logout_records.delete()
                kwargs['active_session'].commit()

        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_master_account_logout_records(
                master_id, kwargs, e
            )
        return master_id

    def unlink_user_account_login_records(self, user_id, **kwargs):
        log.debug('')
        try:
            login_records = kwargs['active_session'].query(
                EWalletLogin
            ).filter_by(
                user_id=user_id
            )
            if len(list(login_records)) >= 1:
                login_records.delete()
                kwargs['active_session'].commit()
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account_login_records(
                user_id, kwargs, e
            )
        return user_id

    def unlink_user_account_logout_records(self, user_id, **kwargs):
        log.debug('')
        try:
            logout_records = kwargs['active_session'].query(
                EWalletLogout
            ).filter_by(
                user_id=user_id
            )
            if len(list(logout_records)) >= 1:
                logout_records.delete()
                kwargs['active_session'].commit()

        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account_logout_records(
                user_id, kwargs, e
            )
        return user_id

    def unlink_master_account_records(self, master_id, **kwargs):
        log.debug('')
        return {
            'login': self.unlink_master_account_login_records(master_id, **kwargs),
            'logout': self.unlink_master_account_logout_records(master_id, **kwargs),
        }

    def unlink_user_account_records(self, user_id, **kwargs):
        log.debug('')
        return {
            'login': self.unlink_user_account_login_records(user_id, **kwargs),
            'logout': self.unlink_user_account_logout_records(user_id, **kwargs),
            'password': self.unlink_user_account_pass_hash_archive(user_id, **kwargs),
        }

    # TODO
    def unlink_master_account(self, **kwargs):
        log.debug('TODO - Refactor')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_found(kwargs)
        try:
            master_account = kwargs['active_session'].query(
                ResMaster
            ).filter_by(
                user_id=kwargs['master_id']
            )
            master = list(master_account)
            # Forced user account removal easter egg
            if kwargs.get('forced_removal'):
                master_account.delete()
                self.unlink_master_account_records(
                    kwargs['master_id'], active_session=kwargs['active_session']
                )
                kwargs['active_session'].commit()
                return kwargs['master_id']
            # If account not marked for removal, mark now
            if not master[0].to_unlink:
                master[0].set_to_unlink(True)
                master[0].set_to_unlink_timestamp(datetime.datetime.now())
                kwargs['active_session'].commit()
                return kwargs['master_id']
            check = res_utils.check_days_since_timestamp(
                master[0].to_unlink_timestamp, 30
            )
            # If 30 days since account marked for removal, remove from db
            if check:
                master_account.delete()
                self.unlink_user_account_records(
                    kwargs['master_id'], active_session=kwargs['active_session']
                )
                kwargs['active_session'].commit()
                return kwargs['master_id']
            return self.warning_master_account_pending_deletion(kwargs)
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_master_account(kwargs, e)

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def unlink_user_account(self, **kwargs):
        log.debug('TODO - Refactor')
        if not kwargs.get('user_id'):
            return self.error_no_user_account_id_found(kwargs)
        try:
            user_account = kwargs['active_session'].query(
                ResUser
            ).filter_by(
                user_id=kwargs['user_id']
            )
            user = list(user_account)[0]
            # Forced user account removal easter egg
            if kwargs.get('forced_removal'):
                self.cleanup_user_account(
                    user_account=user, **kwargs
                )
                user_account.delete()
                self.unlink_user_account_records(
                    kwargs['user_id'], active_session=kwargs['active_session']
                )
                kwargs['active_session'].commit()
                return kwargs['user_id']
            # If account not marked for removal, mark now
            if not user[0].to_unlink:
                user[0].set_to_unlink(True)
                user[0].set_to_unlink_timestamp(datetime.datetime.now())
                kwargs['active_session'].commit()
                return kwargs['user_id']
            check = res_utils.check_days_since_timestamp(
                user[0].to_unlink_timestamp, 30
            )
            # If 30 days since account marked for removal, remove from db
            if check:
                self.cleanup_user_account(
                    user_account=user_account, **kwargs
                )
                user_account.delete()
                self.unlink_user_account_records(
                    kwargs['user_id'], active_session=kwargs['active_session']
                )
                kwargs['active_session'].commit()
                return kwargs['user_id']
            return self.warning_user_account_pending_deletion(kwargs)
        except Exception as e:
            kwargs['active_session'].rollback()
            return self.error_could_not_unlink_user_account(kwargs, e)

    # ACTIONS
    '''
    [ NOTE ]: Command chain responses are formatted here.
    '''

    # TODO
    def action_system_user_check(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_system_session_check(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_send_invoice_record(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_send_transfer_record(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_receive_invoice_record(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')
    def action_receive_transfer_record(self, **kwargs):
        log.debug('TODO - UNIMPLEMENTED')

#   @pysnooper.snoop('logs/ewallet.log')
    def action_unlink_user_account(self, **kwargs):
        log.debug('')
        user_id = kwargs.get('user_id') or \
            self.fetch_active_session_user(obj=False)
        if not user_id or isinstance(user_id, dict) and \
                user_id.get('failed'):
            return self.error_no_user_account_id_found(kwargs)
        user_account = self.fetch_user_by_id(account_id=user_id, **kwargs)
        if not user_account or isinstance(user_account, dict) and \
                user_account.get('failed'):
            return self.warning_could_not_fetch_user_account_by_id(kwargs)
        check = self.check_user_account_belongs_to_ewallet_session(user_account)
        if not check:
            return self.warning_account_does_not_belong_to_ewallet_session(
                kwargs, user_id, user_account, check
            )
        user_email = user_account.fetch_user_email()
        unlink_account = self.unlink_user_account(user_id=user_id, **kwargs)
        if not unlink_account or isinstance(unlink_account, dict) and \
                unlink_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_user_account(user_id, kwargs)
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'account': user_email,
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_create_new_transfer_type_supply(self, **kwargs):
        '''
        [ NOTE   ]: User action 'supply credits' for active session user becomes
                    User event 'request credits' for SystemCore account.
                    Accessible from external api calls.
        [ INPUT  ]: active_session=<orm-session>, partner_account=<partner>,
                    credits=<credits>
        [ RETURN ]: ({'ewallet_credits': <count>, 'supplied_credits': <count>} | False)
        '''
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
                self.fetch_system_core_user_account(**kwargs)
        if not partner_account or isinstance(partner_account, dict) and \
                partner_account.get('failed'):
            return self.error_could_not_fetch_partner_account_for_transfer_type_supply(
                kwargs
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
        if not credit_request or isinstance(credit_request, dict) and \
                credit_request.get('failed'):
            return self.warning_could_not_honour_credit_request(
                kwargs, active_session, partner_account, credits_before,
                credit_request
            )
        credits_after = self.fetch_credit_wallet_credits()
        if not credits_after or isinstance(credits_after, dict) and \
                credits_after.get('failed'):
            return credits_after
        if str(credits_after) != str(credits_before + kwargs.get('credits')):
            active_session.rollback()
            return self.error_supply_type_transfer_failure(
                kwargs, active_session, partner_account, credits_before,
                credit_request, credits_after
            )
        active_session.add(credit_request['invoice_record'])
        active_session.add(credit_request['transfer_record'])
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'ewallet_credits': credits_after,
            'supplied_credits': kwargs['credits'],
            'transfer_record': None if not credit_request.get('transfer_record') else \
                credit_request['transfer_record'].fetch_record_id(),
            'invoice_record': None if not credit_request.get('invoice_record') else \
                credit_request['invoice_record'].fetch_record_id(),
        }
        return command_chain_response

    def action_unlink_master_account(self, **kwargs):
        log.debug('')
        master_id = kwargs.get('master_id') or \
            self.fetch_active_session_master(obj=False)
        if not master_id or isinstance(master_id, dict) and \
                master_id.get('failed'):
            return self.error_no_master_account_id_found(kwargs)
        master_account = self.fetch_master_account(
            search_by='id', master_id=master_id, **kwargs
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_could_not_fetch_master_account_by_id(kwargs)
        check = self.check_master_account_belongs_to_ewallet_session(
            master_account
        )
        if not check:
            return self.warning_account_does_not_belong_to_ewallet_session(
                kwargs, master_id, master_account, check
            )
        user_email = master_account.fetch_user_email()
        unlink_account = self.unlink_master_account(
            master_id=master_id, **kwargs
        )
        if not unlink_account or isinstance(unlink_account, dict) and \
                unlink_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_unlink_master_account(
                master_id, kwargs
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'account': user_email,
        }
        return command_chain_response

    def action_edit_master_key_code(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_key_code = active_master.set_account_key_code(kwargs['key'])
        command_chain_response = self.warning_could_not_edit_master_key_code(
            kwargs, active_master, edit_key_code
        ) if not edit_key_code else {
            'failed': False,
            'master': active_master,
        }
        return command_chain_response

    def action_edit_master_address(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_address = active_master.set_account_address(kwargs['address'])
        command_chain_response =  self.warning_could_not_edit_master_address(
            kwargs, active_master, edit_address
        ) if not edit_address else {
            'failed': False,
            'master': active_master,
        }
        return command_chain_response

    def action_edit_master_company(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_company = active_master.set_account_company(kwargs['company'])
        command_chain_response = self.warning_could_not_edit_master_company(
            kwargs, active_master, edit_company
        ) if not edit_company else {
            'failed': False,
            'master': active_master,
        }
        return command_chain_response

    # TODO
    def action_edit_master_account(self, **kwargs):
        log.debug('TODO - Refactor')
        active_master = self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        edit_value_set = {
            'name': self.handle_master_action_edit_account_user_name(
                master_account=active_master, **kwargs
            ),
            'pass': self.handle_master_action_edit_account_user_pass(
                master_account=active_master, **kwargs
            ),
            'alias': self.handle_master_action_edit_account_user_alias(
                master_account=active_master, **kwargs
            ),
            'email': self.handle_master_action_edit_account_user_email(
                master_account=active_master, **kwargs
            ),
            'phone': self.handle_master_action_edit_account_user_phone(
                master_account=active_master, **kwargs
            ),
            'company': self.handle_master_action_edit_account_company(
                master_account=active_master, **kwargs
            ),
            'address': self.handle_master_action_edit_account_address(
                master_account=active_master, **kwargs
            ),
            'key': self.handle_master_action_edit_account_key_code(
                master_account=active_master, **kwargs
            ),
        }
        return self.warning_no_master_account_values_edited(kwargs) \
            if True not in edit_value_set.values() else {
                'failed': False,
                'account': active_master.fetch_user_email(),
                'edit': edit_value_set,
                'account_data': active_master.fetch_user_values(),
            }

#   @pysnooper.snoop('logs/ewallet.log')
    def action_create_new_user_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_id_specified(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        if kwargs['master_id'] != 'system':
            master_account = self.fetch_master_account_by_id(
                **sanitized_command_chain
            )
            if not master_account or isinstance(master_account, dict) and \
                    master_account.get('failed'):
                return self.warning_no_master_account_found_by_id(
                    kwargs, master_account
                )
            if kwargs['master_id'] != 'system':
                master_subpool_limit_reached = master_account\
                    .check_subordonate_account_pool_size_limit_reached()
                if master_subpool_limit_reached:
                    return self.warning_subordonate_account_pool_size_limit_reached(
                        kwargs, master_account, master_subpool_limit_reached
                    )
            kwargs['active_session'].add(master_account)
        session_create_account = EWalletCreateUser().action_create_new_user(
            **sanitized_command_chain
        )
        if not session_create_account or \
                isinstance(session_create_account, dict) and \
                session_create_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_user_account(
                kwargs, session_create_account
            )
        kwargs['active_session'].add(session_create_account)
        log.info('Successfully created new user account.')
        if kwargs['master_id'] != 'system':
            link_master = master_account.add_subordonate_to_pool(
                session_create_account, **kwargs
            )
            if isinstance(link_master, dict) and link_master.get('failed'):
                kwargs['active_session'].rollback()
                return self.warning_could_not_link_new_user_account_to_master(
                    kwargs, master_account, session_create_account, link_master
                )
            session_create_account.set_master_account_id(kwargs['master_id'])
        self.update_user_account_archive(
            user=session_create_account,
        )
        self.update_session_from_user(
            session_active_user=session_create_account,
        )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'account': kwargs['user_email'],
            'account_data': session_create_account.fetch_user_values(),
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_create_new_transfer_type_pay(self, **kwargs):
        log.debug('')
        if not kwargs.get('pay'):
            return self.error_no_user_action_pay_target_specified(kwargs)
        active_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
            self.fetch_user(identifier='email', email=kwargs['pay'])
        if not partner_account:
            return self.error_could_not_fetch_partner_account(
                kwargs, active_session, partner_account
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'ttype', 'partner_account', 'pay'
        )
        credits_before = self.fetch_credit_wallet_credits()
        current_account = self.fetch_active_session_user()
        action_pay = current_account.user_controller(
            ctype='action', action='transfer', ttype='payment',
            pay=partner_account, **sanitized_command_chain
        )
        credits_after = self.fetch_credit_wallet_credits()
        if str(credits_after) != str(credits_before - int(kwargs.get('credits'))) or \
                not action_pay or isinstance(action_pay, dict) and \
                action_pay.get('failed'):
            active_session.rollback()
            return self.error_pay_type_transfer_failure(
                kwargs, active_session, partner_account, credits_before,
                current_account, action_pay, credits_after
            )
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'paid': kwargs['pay'],
            'ewallet_credits': action_pay['ewallet_credits'],
            'spent_credits': int(kwargs['credits']),
            'invoice_record': action_pay['invoice_record'].fetch_record_id(),
            'transfer_record': action_pay['transfer_record'].fetch_record_id(),
        }
        return command_chain_response

    def action_edit_account_user_email(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_email = active_user.user_controller(
            ctype='action', action='edit', edit='user_email',
            email_check_func=self.fetch_email_check_func(),
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_email(kwargs) if \
            edit_user_email.get('failed') else edit_user_email

    def action_edit_master_user_email(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_email = active_master.user_controller(
            ctype='action', action='edit', edit='user_email',
            email_check_func=self.fetch_email_check_func(),
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_master_user_email(kwargs) if \
            edit_user_email.get('failed') else edit_user_email

    def action_cleanup_ewallet_session(self, **kwargs):
        log.debug('')
        logout_accounts = self.assure_all_user_accounts_logged_out(**kwargs)
        cleanup = self.clear_active_session_user_data({
            'active_user': True,
            'credit_wallet': True,
            'contact_list': True,
            'user_account_archive': True,
        })
        orm_session = self.fetch_active_session()
        try:
            orm_session.commit()
        except Exception as e:
            orm_session.rollback()
            return self.error_could_not_cleanup_ewallet_session(
                kwargs, cleanup, orm_session, e
            )
        instruction_set_response = {
            'failed': False,
            'ewallet_session': self.fetch_active_session_id(),
            'cleanup': cleanup,
        }
        return instruction_set_response

    def action_remove_master_acquired_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_identifier_specified(kwargs)
        if not kwargs.get('key'):
            return self.warning_no_master_key_code_specified(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        master_account = self.fetch_master_account(
            search_by='id', **sanitized_command_chain
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_no_master_account_found_by_id(
                kwargs, master_account
            )
        check_master_key_code = self.check_master_user_account_key_code(
            key=kwargs['key'], master_account=master_account
        )
        if not check_master_key_code:
            return self.warning_invalid_master_account_key_code(
                kwargs, master_account, check_master_key_code
            )
        remove_ctoken = master_account.remove_ctoken_from_acquired(kwargs['client_id'])
        if not remove_ctoken or isinstance(remove_ctoken, dict) and \
                remove_ctoken.get('failed'):
            return self.error_could_not_remove_master_acquired_ctoken(
                kwargs, master_account, check_master_key_code, remove_ctoken
            )
        command_chain_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'master': master_account.fetch_user_email(),
            'master_id': kwargs['master_id'],
        }
        return command_chain_response

    def action_view_master_logout_records(self, **kwargs):
        log.debug('')
        active_master = self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.error_could_not_fetch_active_session_master(
                kwargs, active_master
            )
        try:
            logout_records = list(kwargs['active_session'].query(
                EWalletLogout
            ).filter_by(master_id=active_master.fetch_user_id()))
        except:
            return self.warning_could_not_view_logout_records(
                active_master.fetch_user_name(), kwargs
            )
        command_chain_response = {
            'failed': False,
            'account': active_master.fetch_user_email(),
            'logout_records': {
                item.logout_id: res_utils.format_datetime(item.logout_date) \
                for item in logout_records
            },
        }
        return command_chain_response

    def action_view_master_login_records(self, **kwargs):
        log.debug('')
        active_master = self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.error_could_not_fetch_active_session_master(
                kwargs, active_master
            )
        try:
            login_records = list(kwargs['active_session'].query(
                EWalletLogin
            ).filter_by(master_id=active_master.fetch_user_id()))
        except:
            return self.warning_could_not_view_login_records(
                active_master.fetch_user_name(), kwargs
            )
        command_chain_response = {
            'failed': False,
            'account': active_master.fetch_user_email(),
            'login_records': {
                item.login_id: res_utils.format_datetime(item.login_date) \
                for item in login_records
            },
        }
        return command_chain_response

    def action_inspect_master_subordonate(self, **kwargs):
        log.debug('')
        master = self.fetch_active_session_master()
        if not master or isinstance(master, dict) and \
                master.get('failed'):
            return self.error_could_not_fetch_active_session_master(
                kwargs, master
            )
        inspect_sub = self.inspect_master_subordonate(master=master, **kwargs)
        if not inspect_sub or isinstance(inspect_sub, dict) and \
                inspect_sub.get('failed'):
            return self.warning_could_not_inspect_master_subordonate_account(
                kwargs, master, inspect_sub
            )
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': master.fetch_user_email(),
            'subordonate': inspect_sub['subordonate'],
        }
        return command_chain_response

    def action_inspect_master_subpool(self, **kwargs):
        log.debug('')
        master = self.fetch_active_session_master()
        if not master or isinstance(master, dict) and \
                master.get('failed'):
            return self.error_could_not_fetch_active_session_master(
                kwargs, master
            )
        inspect_subpool = self.inspect_master_subpool(master=master, **kwargs)
        if not inspect_subpool or isinstance(inspect_subpool, dict) and \
                inspect_subpool.get('failed'):
            return self.warning_could_not_inspect_master_account_subpool(
                kwargs, master, inspect_subpool
            )
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': master.fetch_user_email(),
            'subpool': inspect_subpool['subpool'],
        }
        return command_chain_response

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def action_login_user_account(self, **kwargs):
        log.debug('TODO - Refactor')
        check_master = self.check_user_in_master_account_pool(**kwargs)
        if not check_master or isinstance(check_master, dict) and \
                check_master.get('failed'):
            return self.warning_user_account_not_subordonate_to_acquired_master_account(
                kwargs, check_master
            )
        check_frozen = self.check_master_user_account_frozen(**kwargs)
        if check_frozen:
            return self.warning_user_account_frozen(
                kwargs, check_master, check_frozen
            )
        login_record = EWalletLogin()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        session_login = login_record.ewallet_login_controller(
            action='login',
            user_archive=self.fetch_active_session_user_account_archive(),
            **sanitized_command_chain
        )
        if not session_login or isinstance(session_login, dict) and \
                session_login.get('failed'):
            return self.warning_could_not_login_user_account(kwargs)
        update_archive = self.update_user_account_archive(user=session_login)
        update_session = self.action_system_user_update(user=session_login)
        if not update_session or isinstance(update_session, dict) and \
                update_session.get('failed'):
            return self.warning_could_not_update_ewallet_session(
                kwargs, session_login, update_archive, update_session
            )
        kwargs['active_session'].add(login_record)
        kwargs['active_session'].commit()
        log.info('User successfully logged in.')
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': session_login.fetch_user_email(),
            'session_data': {
                'session_user_account': None
                    if not session_values['user_account']
                    or isinstance(session_values['user_account'], dict)
                    else session_values['user_account'].fetch_user_email(),
                'session_credit_ewallet': None
                    if not session_values['credit_ewallet']
                    or isinstance(session_values['credit_ewallet'], dict)
                    else session_values['credit_ewallet'].fetch_credit_ewallet_id(),
                'session_contact_list': None
                    if not session_values['contact_list']
                    or isinstance(session_values['contact_list'], dict)
                    else session_values['contact_list'].fetch_contact_list_id(),
                'session_account_archive': None
                    if not session_values['user_account_archive']
                    else session_values['user_account_archive']
            }
        }
        return command_chain_response

    def action_recover_master_account(self, **kwargs):
        log.debug('')
        master = self.fetch_active_session_master()
        if not master or isinstance(master, dict) and \
                master.get('failed'):
            return self.error_could_not_fetch_active_session_master(
                kwargs, master
            )
        recover_account = self.recover_master_account(master=master, **kwargs)
        if not recover_account or isinstance(recover_account, dict) and \
                recover_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_recover_master_account(kwargs)
        update = False if not recover_account \
                or isinstance(recover_account, bool) \
                or isinstance(recover_account, dict) \
                and recover_account.get('failed') \
                else self.action_system_master_update(master=master, **kwargs)
        if not update or isinstance(update, dict) and update.get('failed'):
            kwargs['active_session'].rollback()
            return self.error_could_not_update_ewallet_session_from_master_account(kwargs)
        kwargs['active_session'].commit()
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': master.fetch_user_email(),
            'account_data': master.fetch_user_values(),
            'session_data': {
                'id': session_values['id'],
                'master': None if not session_values.get('master_account')
                    or not isinstance(session_values['master_account'], object)
                    else session_values['master_account'].fetch_user_email(),
                'create_date': res_utils.format_datetime(
                    session_values['create_date']
                ),
                'write_date': res_utils.format_datetime(
                    session_values['write_date']
                ),
                'expiration_date': res_utils.format_datetime(
                    session_values['expiration_date']
                ),
            }
        }
        return command_chain_response

    def action_edit_master_user_pass(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_pass = active_master.user_controller(
            ctype='action', action='edit', edit='user_pass',
            pass_check_func=self.fetch_user_password_check_function(),
            pass_hash_func=self.fetch_user_password_hash_function(),
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_master_user_pass(kwargs) if \
            edit_user_pass.get('failed') else edit_user_pass

    # TODO
    def action_master_account_logout(self, **kwargs):
        log.debug('TODO - Refactor')
        master = self.fetch_active_session_master()
        session_logout = self.action_system_master_logout(master=master)
        if isinstance(session_logout, dict) and \
                session_logout.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_logout_master_account(
                kwargs, master, session_logout
            )
        logout_record = EWalletLogout(
            master_id=master.fetch_user_id(),
            logout_status=False if not session_logout else True,
        )
        kwargs['active_session'].add(logout_record)
        kwargs['active_session'].commit()
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': master.fetch_user_email(),
            'session_data': {
                'id': session_values['id'],
                'master': None if not session_values.get('master_account')
                    or not isinstance(session_values['master_account'], object)
                    else session_values['master_account'].fetch_user_email(),
                'create_date': res_utils.format_datetime(
                    session_values['create_date']
                ),
                'write_date': res_utils.format_datetime(
                    session_values['write_date']
                ),
                'expiration_date': res_utils.format_datetime(
                    session_values['expiration_date']
                ),
            }
        }
        return command_chain_response

    # TODO
#   @pysnooper.snoop('logs/ewallet.log')
    def action_master_account_login(self, **kwargs):
        log.debug('TODO - Refactor')
        check_frozen = self.check_master_user_account_frozen(**kwargs)
        if isinstance(check_frozen, dict) and check_frozen.get('failed'):
            return self.error_could_not_check_if_master_account_frozen(
                kwargs, check_frozen
            )
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_frozen
            )
        login_record = EWalletLogin()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        session_login = login_record.ewallet_login_controller(
            action='login',
            user_archive=self.fetch_active_session_user_account_archive(),
            **sanitized_command_chain
        )
        if not session_login or isinstance(session_login, dict) and \
                session_login.get('failed'):
            return self.warning_could_not_login_user_account(kwargs)
        update_session = self.action_system_master_update(master=session_login)
        if not update_session or isinstance(update_session, dict) and \
                update_session.get('failed'):
            return self.warning_could_not_update_ewallet_session(
                kwargs, session_login, update_session
            )
        kwargs['active_session'].add(login_record)
        kwargs['active_session'].commit()
        log.info('Master successfully logged in.')
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': session_login.fetch_user_email(),
            'session_data': {
                'id': session_values['id'],
                'master': None if not session_values.get('master_account')
                    or not isinstance(session_values['master_account'], object)
                    else session_values['master_account'].fetch_user_email(),
                'create_date': res_utils.format_datetime(
                    session_values['create_date']
                ),
                'write_date': res_utils.format_datetime(
                    session_values['write_date']
                ),
                'expiration_date': res_utils.format_datetime(
                    session_values['expiration_date']
                ),
            }
        }
        return command_chain_response

    def action_edit_master_user_name(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_name = active_master.user_controller(
            ctype='action', action='edit', edit='user_name',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_master_user_name(kwargs) if \
            edit_user_name.get('failed') else edit_user_name

    def action_edit_master_user_alias(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_alias = active_master.user_controller(
            ctype='action', action='edit', edit='user_alias',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_master_user_alias(kwargs) if \
            edit_user_alias.get('failed') else edit_user_alias

    def action_edit_master_user_phone(self, **kwargs):
        log.debug('')
        active_master = kwargs.get('master_account') or \
            self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_phone = active_master.user_controller(
            ctype='action', action='edit', edit='user_phone',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_master_user_phone(kwargs) if \
            edit_user_phone.get('failed') else edit_user_phone

    def action_view_master_account(self, **kwargs):
        log.debug('')
        active_master = self.fetch_active_session_master()
        if not active_master or isinstance(active_master, dict) and \
                active_master.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_master(
                kwargs, active_master
            )
        command_chain_response = {
            'failed': False,
            'account': active_master.fetch_user_email(),
            'account_data': active_master.fetch_user_values(),
        }
        return command_chain_response

    def action_system_master_logout(self, **kwargs):
        log.debug('')
        master = kwargs.get('master') or self.fetch_active_session_master()
        if not master:
            return self.error_no_active_session_master_found(kwargs)
        set_master_state = master.set_user_state(0)
        clear_master_data = self.clear_active_session_user_data({
            'active_master': True,
        })
        return True

#   @pysnooper.snoop('logs/ewallet.log')
    def action_logout_user_account(self, **kwargs):
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
            'account': user.fetch_user_email(),
            'session_data': {
                'session_user_account': None if
                    not isinstance(session_values.get('user_account'), list)
                    or len(session_values['user_account']) == 0
                    else session_values['user_account'][0].fetch_user_email(),
                'session_credit_ewallet': None if
                    not isinstance(session_values['credit_ewallet'], list)
                    or len(session_values['credit_ewallet']) == 0
                    else session_values['credit_ewallet'][0].fetch_credit_ewallet_id(),
                'session_contact_list': None if
                    not isinstance(session_values['contact_list'], list)
                    or len(session_values['contact_list']) == 0
                    else session_values['contact_list'].fetch_contact_list_id(),
                'session_account_archive': {} if
                    not session_values['user_account_archive']
                    or session_values.get('failed')
                    else session_values['user_account_archive']
            }
        }
        return command_chain_response

    def action_system_master_update(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_master_specified(kwargs)
        set_master = self.set_session_active_master(kwargs['master'])
        self.update_session_from_master(session_active_master=kwargs['master'])
        return self.active_master[0]

    def action_system_user_update(self, **kwargs):
        log.debug('')
        if not kwargs.get('user'):
            return self.error_no_user_specified()
        if kwargs['user'] not in self.user_account_archive:
            return self.warning_user_not_in_session_archive()
        _set_user = self.set_session_active_user(active_user=kwargs['user'])
        self.update_session_from_user(session_active_user=kwargs['user'])
        return self.active_user[0]

#   @pysnooper.snoop('logs/ewallet.log')
    def action_add_master_acquired_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('master_id'):
            return self.error_no_master_account_identifier_specified(kwargs)
        if not kwargs.get('key'):
            return self.warning_no_master_key_code_specified(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        master_account = self.fetch_master_account(
            search_by='id', **sanitized_command_chain
        )
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_no_master_account_found_by_id(
                kwargs, master_account
            )
        check_master_key_code = self.check_master_user_account_key_code(
            key=kwargs['key'], master_account=master_account
        )
        if not check_master_key_code:
            return self.warning_invalid_master_account_key_code(
                kwargs, master_account, check_master_key_code
            )
        add_ctoken = master_account.add_ctoken_to_acquired(kwargs['client_id'])
        if not add_ctoken or isinstance(add_ctoken, dict) and \
                add_ctoken.get('failed'):
            return self.error_could_not_add_master_acquired_ctoken(
                kwargs, master_account, check_master_key_code, add_ctoken
            )
        command_chain_response = {
            'failed': False,
            'client_id': kwargs['client_id'],
            'master': master_account.fetch_user_email(),
            'master_id': kwargs['master_id'],
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_create_new_master_account(self, **kwargs):
        log.debug('')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        session_create_account = EWalletCreateUser().action_create_new_master(
            **sanitized_command_chain
        )
        if not session_create_account or \
                isinstance(session_create_account, dict) and \
                session_create_account.get('failed'):
            return self.warning_could_not_create_user_account(
                kwargs, session_create_account
            )
        kwargs['active_session'].add(session_create_account)
        log.info('Successfully created new Master account.')
        self.update_session_from_master(
            session_active_master=session_create_account,
        )
        kwargs['active_session'].commit()
        account_data = session_create_account.fetch_user_values()
        subpool = account_data['subordonate_pool']
        command_chain_response = {
            'failed': False,
            'account': kwargs['user_email'],
            'account_data': account_data,
        }
        return command_chain_response

    def action_search_master_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_master_account_identifier_specified(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        master_account = self.fetch_master_account(**sanitized_command_chain)
        if not master_account or isinstance(master_account, dict) and \
                master_account.get('failed'):
            return self.warning_no_master_account_found_by_email(
                kwargs, master_account
            )
        command_chain_response = {
            'failed': False,
            'master': kwargs['master'],
            'master_data': master_account.fetch_user_values()
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_view_transfer_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_transfer_sheet_record_id_found(kwargs)
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_credit_ewallet(kwargs)
        log.info('Attempting to fetch active transfer sheet...')

        transfer_sheet = credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not transfer_sheet or isinstance(transfer_sheet, dict) and \
                transfer_sheet.get('failed'):
            return self.warning_could_not_fetch_transfer_sheet(kwargs)

        sheet_records = transfer_sheet.fetch_transfer_sheet_records(obj=False)
        if kwargs['record_id'] not in sheet_records:
            return self.warning_record_id_not_in_transfer_sheet(
                kwargs, credit_wallet, transfer_sheet, sheet_records
            )

        log.info('Attempting to fetch transfer record by id...')
        record = transfer_sheet.fetch_transfer_sheet_record(
            search_by='id', code=kwargs['record_id'], active_session=self.session
        )
        if not record or isinstance(record, dict) and \
                record.get('failed'):
            return self.warning_could_not_fetch_transfer_sheet_record(
                kwargs, credit_wallet, transfer_sheet, record
            )

        record_values = record.fetch_record_values()

        transfer_from_id = record.fetch_record_transfer_from()
        transfer_to_id = record.fetch_record_transfer_to()

        src_user = self.fetch_user(
            identifier='id', account_id=transfer_from_id, **kwargs
        )
        dst_user = self.fetch_user(
            identifier='id', account_id=transfer_to_id, **kwargs
        )

        record_values['transfer_from'] = None if not src_user or \
            isinstance(src_user, dict) and src_user.get('failed') \
            else src_user.fetch_user_email()
        record_values['transfer_to'] = None if not dst_user or \
            isinstance(dst_user, dict) and dst_user.get('failed') \
            else dst_user.fetch_user_email()

        command_chain_response = {
            'failed': False,
            'transfer_sheet': transfer_sheet.fetch_transfer_sheet_id(),
            'transfer_record': record.fetch_record_id(),
            'record_data': record_values,
        }
        return command_chain_response

    def action_interogate_ewallet_session_empty(self, **kwargs):
        log.debug('')
        empty = self.check_if_active_ewallet_session_empty()
        if isinstance(empty, dict) and empty.get('failed'):
            return self.error_could_not_check_if_ewallet_session_empty(
                kwargs, empty
            )
        command_chain_response = {
            'failed': False,
            'ewallet_session': self.fetch_active_session_id(),
            'empty': empty,
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_edit_account_user_pass(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_pass = active_user.user_controller(
            ctype='action', action='edit', edit='user_pass',
            pass_check_func=self.fetch_user_password_check_function(),
            pass_hash_func=self.fetch_user_password_hash_function(),
            **sanitized_command_chain
        )
        if not edit_user_pass or isinstance(edit_user_pass, dict) and \
                edit_user_pass.get('failed'):
            return self.warning_could_not_edit_account_user_pass(
                kwargs, active_user, edit_user_pass
            )
        return edit_user_pass

    def action_unlink_invoice_list(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_sheet
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_invoice_record(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_record
            )
        kwargs['active_session'].commit()
        return unlink_record

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
                kwargs, active_user, unlink_clock
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'credit_clock': kwargs['clock_id'],
        }
        return command_chain_response

    def action_unlink_credit_wallet(self, **kwargs):
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
                kwargs, active_user, unlink_ewallet
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'credit_ewallet': kwargs['ewallet_id'],
        }
        return command_chain_response

    def action_unlink_time_list(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_sheet
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_time_record(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_record
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_transfer_record(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_record
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_conversion_record(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_record
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_transfer_list(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_sheet
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_conversion_list(self, **kwargs):
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
                kwargs, active_user, credit_ewallet, unlink_sheet
            )
        kwargs['active_session'].commit()
        return unlink_sheet

    def action_unlink_contact_record(self, **kwargs):
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
                kwargs, active_user, contact_list, unlink_record
            )
        kwargs['active_session'].commit()
        return unlink_record

    def action_unlink_contact_list(self, **kwargs):
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
                kwargs, active_user, unlink_list
            )
        kwargs['active_session'].commit()
        command_chain_response = {
            'failed': False,
            'contact_list': kwargs['list_id'],
        }
        return command_chain_response

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
                kwargs, active_user, switch_contact_list
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
                kwargs, active_user, switch_time_sheet
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
                kwargs, active_user, switch_conversion_sheet
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
                kwargs, active_user, switch_invoice_sheet
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
                kwargs, active_user, switch_transfer_sheet
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched transfer sheet.')
        command_chain_response = {
            'failed': False,
            'transfer_sheet': switch_transfer_sheet.fetch_transfer_sheet_id(),
            'sheet_data': switch_transfer_sheet.fetch_transfer_sheet_values(),
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
            **sanitized_command_chain
        )
        if not switch_credit_ewallet or \
                isinstance(switch_credit_ewallet, dict) and \
                switch_credit_ewallet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_credit_ewallet(
                kwargs, active_user, switch_credit_ewallet
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched credit ewallet.')
        command_chain_response = {
            'failed': False,
            'ewallet': switch_credit_ewallet.fetch_credit_ewallet_id(),
            'ewallet_data': switch_credit_ewallet.fetch_credit_ewallet_values(),
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
            **sanitized_command_chain
        )
        if not switch_credit_clock or isinstance(switch_credit_clock, dict) and \
                switch_credit_clock.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_switch_credit_clock(
                kwargs, active_user, switch_credit_clock
            )
        kwargs['active_session'].commit()
        log.info('Successfully switched credit clock.')
        command_chain_response = {
            'failed': False,
            'clock': switch_credit_clock.fetch_credit_clock_id(),
            'clock_data': switch_credit_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_switch_active_user_account(self, **kwargs):
        log.debug('')
        account_record = self.fetch_user_by_email(email=kwargs.get('account'))
        if not account_record or isinstance(account_record, dict) and \
                account_record.get('failed'):
            return self.warning_user_account_not_found_in_database(kwargs)
        new_account = self.interogate_active_session_user_archive_for_user_account(
            account_id=account_record.fetch_user_id(), **kwargs
        )
        if not new_account or isinstance(new_account, dict) and \
                new_account.get('failed'):
            return self.warning_account_not_logged_in(
                kwargs, new_account
            )
        update_session = self.update_session_from_user(session_active_user=new_account)
        if not update_session or isinstance(update_session, dict) and \
                update_session.get('failed'):
            return self.error_could_not_update_ewallet_session_from_user_account(kwargs)
        kwargs['active_session'].commit()
        account_archive = self.fetch_active_session_user_account_archive()
        command_chain_response = {
            'failed': False,
            'account': new_account.fetch_user_email(),
            'session_data': {
                'session_user_account': None if not update_session['active_user'] \
                    else update_session['active_user'].fetch_user_email(),
                'session_credit_ewallet': None if not update_session['credit_wallet'] \
                    else update_session['credit_wallet'].fetch_credit_ewallet_id(),
                'session_contact_list': None if not update_session['contact_list'] \
                    else update_session['contact_list'].fetch_contact_list_id(),
                'session_account_archive': None if not account_archive else {
                    item.fetch_user_email(): item.fetch_user_name()
                    for item in account_archive
                }
            }
        }
        return command_chain_response

#   @pysnooper.snoop()
    def action_view_invoice_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view invoice record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Invoice record values | False)
        '''
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_invoice_record_id_specified(kwargs)
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.warning_could_not_fetch_credit_ewallet(kwargs)
        log.info('Attempting to fetch active invoice sheet...')
        invoice_sheet = credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not invoice_sheet or isinstance(invoice_sheet, dict) and \
                invoice_sheet.get('failed'):
            return self.warning_could_not_fetch_invoice_sheet(kwargs)
        log.info('Attempting to fetch invoice record by id...')
        record = invoice_sheet.fetch_credit_invoice_record(
            search_by='id', code=kwargs['record_id'], **kwargs
        )
        if not record or isinstance(record, dict) and \
                record.get('failed'):
            return self.warning_could_not_fetch_invoice_sheet_record(
                kwargs, credit_wallet, invoice_sheet, record
            )
        command_chain_response = {
            'failed': False,
            'invoice_sheet': invoice_sheet.fetch_invoice_sheet_id(),
            'invoice_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_conversion_record(self, **kwargs):
        '''
        [ NOTE   ]: User action 'view conversion record', accessible from external api call.
        [ INPUT  ]: record_id=<id>
        [ RETURN ]: (Conversion record values | False)
        '''
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_conversion_record_id_found(kwargs)
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.warning_could_not_fetch_active_session_credit_ewallet(kwargs)
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock()
        log.info('Attempting to fetch active conversion sheet...')
        conversion_sheet = credit_clock.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet or isinstance(conversion_sheet, dict) and \
                conversion_sheet.get('failed'):
            return self.warning_could_not_fetch_conversion_sheet(kwargs)
        log.info('Attempting to fetch conversion record by id...')
        record = conversion_sheet.fetch_conversion_sheet_record(
            identifier='id', **kwargs
        )
        if not record or isinstance(record, dict) and record.get('failed'):
            return self.warning_could_not_fetch_conversion_record(
                kwargs, credit_wallet, credit_clock, conversion_sheet, record
            )
        command_chain_response = {
            'failed': False,
            'conversion_sheet': conversion_sheet.fetch_conversion_sheet_id(),
            'conversion_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_view_time_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_time_record_id_found(kwargs)
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet:
            return self.error_could_not_fetch_credit_ewallet(kwargs)
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and \
                credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock(kwargs)
        log.info('Attempting to fetch active time sheet...')
        time_sheet = credit_clock.fetch_credit_clock_time_sheet()
        if not time_sheet or isinstance(time_sheet, dict) and \
                time_sheet.get('failed'):
            return self.warning_could_not_fetch_time_sheet(kwargs)
        log.info('Attempting to fetch time record...')
        record = time_sheet.fetch_time_sheet_record(
            identifier='id', **kwargs
        )
        if not record or isinstance(record, dict) and record.get('failed'):
            return self.warning_could_not_fetch_time_sheet_record(
                kwargs, credit_wallet, credit_clock, time_sheet, record
            )
        command_chain_response = {
            'failed': False,
            'time_sheet': time_sheet.fetch_time_sheet_id(),
            'time_record': record.fetch_record_id(),
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

#   @pysnooper.snoop()
    def action_view_contact_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_contact_record_id_found(kwargs)
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list or isinstance(contact_list, dict) and \
                contact_list.get('failed'):
            return self.error_could_not_fetch_contact_list(kwargs)
        log.info('Attempting to fetch contact record by id...')
        record = contact_list.fetch_contact_list_record(
            search_by='id' if not kwargs.get('search_by') else kwargs['search_by'],
            code=kwargs['record_id'], active_session=self.fetch_active_session()
        )
        if not record or isinstance(record, dict) and \
                record.get('failed'):
            return self.warning_could_not_fetch_contact_record(kwargs)
        command_chain_response = {
            'failed': False,
            'contact_list': contact_list.fetch_contact_list_id(),
            'contact_record': kwargs['record_id'],
            'record_data': record.fetch_record_values(),
        }
        return command_chain_response

    def action_edit_user_account(self, **kwargs):
        log.debug('')
        user = self.fetch_active_session_user()
        edit_value_set = {
            'name': self.handle_user_action_edit_account_user_name(**kwargs),
            'pass': self.handle_user_action_edit_account_user_pass(**kwargs),
            'alias': self.handle_user_action_edit_account_user_alias(**kwargs),
            'email': self.handle_user_action_edit_account_user_email(**kwargs),
            'phone': self.handle_user_action_edit_account_user_phone(**kwargs),
        }
        return self.warning_no_user_account_values_edited(kwargs) \
            if True not in edit_value_set.values() else {
                'failed': False,
                'account': user.fetch_user_email(),
                'edit': edit_value_set,
                'account_data': user.fetch_user_values(),
            }

    def action_recover_user_account(self, **kwargs):
        log.debug('')
        user = self.fetch_active_session_user()
        recover_account = self.recover_user_account(user=user, **kwargs)
        if not recover_account or isinstance(recover_account, dict) and \
                recover_account.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_recover_user_account(kwargs)
        update = False if not recover_account or isinstance(recover_account, bool) \
                or isinstance(recover_account, dict) and recover_account.get('failed') \
                else self.action_system_user_update(user=user, **kwargs)
        if not update or isinstance(update, dict) and update.get('failed'):
            kwargs['active_session'].rollback()
            return self.error_could_not_update_ewallet_session_from_user_account(kwargs)
        kwargs['active_session'].commit()
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'account': user.fetch_user_email(),
            'account_data': user.fetch_user_values(),
            'session_data': {
                'session_user_account': None if not session_values['user_account']
                    or isinstance(session_values['user_account'], dict)
                    else session_values['user_account'].fetch_user_email(),
                'session_credit_ewallet': None if not session_values['credit_ewallet']
                    or isinstance(session_values['credit_ewallet'], dict)
                    else session_values['credit_ewallet'].fetch_credit_ewallet_id(),
                'session_contact_list': None if not session_values['contact_list']
                    or isinstance(session_values['contact_list'], dict)
                    else session_values['contact_list'].fetch_contact_list_id(),
                'session_account_archive': None if not session_values['user_account_archive']
                    or isinstance(session_values['user_account_archive'], dict)
                    else session_values['user_account_archive']
            }
        }
        return command_chain_response

    def action_interogate_ewallet_session_expired(self, **kwargs):
        log.debug('')
        expired = self.check_if_active_ewallet_session_expired()
        if isinstance(expired, dict) and expired.get('failed'):
            return self.error_could_not_check_if_ewallet_session_expired(
                kwargs, expired
            )
        command_chain_response = {
            'failed': False,
            'ewallet_session': self.fetch_active_session_id(),
            'expired': expired,
        }
        return command_chain_response

    def action_interogate_ewallet_session_state(self, **kwargs):
        log.debug('')
        session_values = self.fetch_active_session_values()
        command_chain_response = {
            'failed': False,
            'ewallet_session': self.fetch_active_session_id(),
            'session_data': session_values,
        }
        return command_chain_response

#   @pysnooper.snoop()
    def action_create_new_transfer_type_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_to'):
            return self.error_no_user_action_transfer_credits_target_specified(
                kwargs
            )
        active_session = kwargs.get('active_session') or \
            self.fetch_active_session()
        partner_account = kwargs.get('partner_account') or \
            self.fetch_user(identifier='email', email=kwargs['transfer_to'])
        if not partner_account or isinstance(partner_account, dict) and \
                partner_account.get('failed'):
            return self.error_could_not_fetch_partner_account(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'ttype', 'partner_account', 'pay',
            'transfer_to'
        )
        credits_before = self.fetch_credit_wallet_credits()
        current_account = self.fetch_active_session_user()
        if not isinstance(credits_before, int) or isinstance(credits_before, dict) and \
                credits_before.get('failed') or not current_account or \
                isinstance(current_account, dict) and current_account.get('failed'):
            if not isinstance(credits_before, int) or isinstance(credits_before, dict) and \
                    credits_before.get('failed'):
                return credits_before
            elif not current_account or isinstance(current_account, dict) and \
                    current_account.get('failed'):
                return current_account
        action_transfer = current_account.user_controller(
            ctype='action', action='transfer', ttype='transfer',
            transfer_to=partner_account, **sanitized_command_chain
        )
        if not action_transfer or isinstance(action_transfer, dict) and \
                action_transfer.get('failed'):
            active_session.rollback()
            return self.error_transfer_type_transfer_failure(kwargs)
        active_session.commit()
        credits_after = self.fetch_credit_wallet_credits()
        if str(credits_after) != str(credits_before - int(kwargs.get('credits'))):
            active_session.rollback()
            return self.error_transfer_type_transfer_failure(kwargs)
        command_chain_response = {
            'failed': False,
            'transfered_to': kwargs['transfer_to'],
        }
        if action_transfer and isinstance(action_transfer, dict):
            command_chain_response.update(action_transfer)
        return command_chain_response

    def action_create_new_contact_record(self, **kwargs):
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list:
            return self.error_no_active_session_contact_list_found(
                self.fetch_active_session_user().fetch_user_name(), kwargs
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action'
        )
        new_record = contact_list.contact_list_controller(
            action='create', **sanitized_command_chain
        )
        if not new_record or isinstance(new_record, dict) and \
                new_record.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_contact_record(
                self.active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new contact record.')
        command_chain_response = {
            'failed': False,
            'contact_record': new_record.fetch_record_id(),
            'contact_list': contact_list.fetch_contact_list_id()
        }
        return command_chain_response

    def action_create_new_time_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'time'
        )
        new_time_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='time',
            **sanitized_command_chain
        )
        if not new_time_sheet or isinstance(new_time_sheet, dict) and \
                new_time_sheet.get('failed'):
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
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'conversion'
        )
        new_conversion_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='conversion',
            **sanitized_command_chain
        )
        if not new_conversion_sheet or isinstance(new_conversion_sheet, dict) and \
                new_conversion_sheet.get('failed'):
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

    def action_create_new_transfer_sheet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_active_session_credit_wallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'ctype', 'action', 'create', 'transfer'
        )
        new_transfer_sheet = credit_wallet.main_controller(
            controller='system', ctype='action', action='create_sheet', sheet='transfer',
            **sanitized_command_chain
        )
        if not new_transfer_sheet or isinstance(new_transfer_sheet, dict) and \
                new_transfer_sheet.get('failed'):
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
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_clock = active_user.user_controller(
            ctype='action', action='create', target='credit_clock',
            **sanitized_command_chain
        )
        if not new_clock or isinstance(new_clock, dict) and \
                new_clock.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_credit_clock(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new credit clock.')
        command_chain_response = {
            'failed': False,
            'clock': new_clock.fetch_credit_clock_id(),
            'clock_data': new_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_create_new_credit_wallet(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_wallet = active_user.user_controller(
            ctype='action', action='create', target='credit_wallet',
            **sanitized_command_chain
        )
        if not new_wallet or isinstance(new_wallet, dict) and \
                new_wallet.get('failed'):
            kwargs['active_session'].rollback()
            return self.warning_could_not_create_credit_wallet(
                active_user.fetch_user_name(), kwargs
            )
        kwargs['active_session'].commit()
        log.info('Successfully created new credit wallet.')
        command_chain_response = {
            'failed': False,
            'ewallet': new_wallet.fetch_credit_ewallet_id(),
            'ewallet_data': new_wallet.fetch_credit_ewallet_values(),
        }
        return command_chain_response

    def action_view_invoice_list(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_no_session_credit_wallet_found(kwargs)
        log.info('Attempting to fetch active invoice sheet...')
        invoice_sheet = credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not invoice_sheet or isinstance(invoice_sheet, dict) and \
                invoice_sheet.get('failed'):
            return self.warning_could_not_fetch_invoice_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'invoice_sheet': invoice_sheet.fetch_invoice_sheet_id(),
            'sheet_data': invoice_sheet.fetch_invoice_sheet_values(),
        }
        return command_chain_response

    def action_view_credit_clock(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_no_session_credit_wallet_found(kwargs)
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and \
                credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock(kwargs)
        command_chain_response = {
            'failed': False,
            'clock': credit_clock.fetch_credit_clock_id(),
            'clock_data': credit_clock.fetch_credit_clock_values(),
        }
        return command_chain_response

    def action_view_credit_wallet(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_no_session_credit_wallet_found(kwargs)
        command_chain_response = {
            'failed': False,
            'ewallet': credit_wallet.fetch_credit_ewallet_id(),
            'ewallet_data': credit_wallet.fetch_credit_ewallet_values(),
        }
        return command_chain_response

    def action_edit_account_user_name(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_name = active_user.user_controller(
            ctype='action', action='edit', edit='user_name',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_name(kwargs) if \
            edit_user_name.get('failed') else edit_user_name

    def action_edit_account_user_alias(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'edit'
        )
        edit_user_alias = active_user.user_controller(
            ctype='action', action='edit', edit='user_alias',
            **sanitized_command_chain
        )
        return self.warning_could_not_edit_account_user_alias(kwargs) if \
            edit_user_alias.get('failed') else edit_user_alias

    def action_edit_account_user_phone(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(kwargs)
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
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user or isinstance(active_user, dict) and \
                active_user.get('failed'):
            return self.warning_could_not_fetch_ewallet_session_active_user(
                kwargs
            )
        command_chain_response = {
            'failed': False,
            'account': active_user.fetch_user_email(),
            'account_data': active_user.fetch_user_values(),
        }
        return command_chain_response

    def action_create_new_conversion_credits_to_clock(self, **kwargs):
        log.debug('')
        credit_wallet = kwargs.get('credit_ewallet') or \
                self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_active_session_credit_wallet(
                kwargs
            )
        credits_before = self.fetch_credit_wallet_credits()
        active_session = kwargs.get('active_session') or self.fetch_active_session()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'conversion', 'credit_ewallet',
            'active_session'
        )
        convert = credit_wallet.main_controller(
            controller='system', action='convert', conversion='to_minutes',
            conversion_type='credits2clock', credit_ewallet=credit_wallet,
            active_session=active_session, **sanitized_command_chain
        )
        if not convert or isinstance(convert, dict) and \
                convert.get('failed'):
            active_session.rollback()
            return self.error_could_not_convert_credits_to_minutes(kwargs)
        active_session.commit()
        return convert

    def action_view_conversion_list(self, **kwargs):
        log.debug('')
        credit_clock = self.fetch_active_session_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and \
                credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock(kwargs)
        log.info('Attempting to fetch active conversion sheet...')
        conversion_sheet = credit_clock.fetch_credit_clock_conversion_sheet()
        if not conversion_sheet or isinstance(conversion_sheet, dict) and \
                conversion_sheet.get('failed'):
            return self.warning_could_not_fetch_conversion_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'conversion_sheet': conversion_sheet.fetch_conversion_sheet_id(),
            'sheet_data': conversion_sheet.fetch_conversion_sheet_values(),
        }
        return command_chain_response

    def action_view_time_list(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_no_session_credit_wallet_found(kwargs)
        log.info('Attempting to fetch active credit clock...')
        credit_clock = credit_wallet.fetch_credit_ewallet_credit_clock()
        if not credit_clock or isinstance(credit_clock, dict) and \
                credit_clock.get('failed'):
            return self.warning_could_not_fetch_credit_clock(kwargs)
        log.info('Attempting to fetch active time sheet...')
        time_sheet = credit_clock.fetch_credit_clock_time_sheet()
        if not time_sheet or isinstance(time_sheet, dict) and \
                time_sheet.get('failed'):
            return self.warning_could_not_fetch_time_sheet(
                kwargs, credit_wallet, credit_clock, time_sheet
            )
        command_chain_response = {
            'failed': False,
            'time_sheet': time_sheet.fetch_time_sheet_id(),
            'sheet_data': time_sheet.fetch_time_sheet_values(),
        }
        return command_chain_response

    def action_view_transfer_list(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_active_session_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('false'):
            return self.error_no_session_credit_wallet_found(kwargs)
        log.info('Attempting to fetch active transfer sheet...')
        transfer_sheet = credit_wallet.fetch_credit_ewallet_transfer_sheet()
        if not transfer_sheet or isinstance(transfer_sheet, dict) and \
                transfer_sheet.get('failed'):
            return self.warning_could_not_fetch_transfer_sheet(kwargs)
        command_chain_response = {
            'failed': False,
            'transfer_sheet': transfer_sheet.fetch_transfer_sheet_id(),
            'sheet_data': transfer_sheet.fetch_transfer_sheet_values(),
        }
        return command_chain_response

    def action_view_contact_list(self, **kwargs):
        log.debug('')
        contact_list = self.fetch_active_session_contact_list()
        if not contact_list:
            return self.error_no_session_contact_list_found(kwargs)
        command_chain_response = {
            'failed': False,
            'contact_list': contact_list.fetch_contact_list_id(),
            'list_data': contact_list.fetch_contact_list_values(),
        }
        return command_chain_response

    def action_stop_credit_clock_timer(self, **kwargs):
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock(kwargs)
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found(kwargs)
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
        if not stop or isinstance(stop, dict) and stop.get('failed'):
            active_session.rollback()
            return self.error_could_not_stop_credit_clock_timer(kwargs)
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'clock': credit_clock.fetch_credit_clock_id(),
        }
        if isinstance(stop, dict):
            command_chain_response.update(stop)
        return command_chain_response

#   @pysnooper.snoop()
    def action_resume_credit_clock_timer(self, **kwargs):
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock(kwargs)
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found(kwargs)
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
        if not resume or isinstance(resume, dict) and resume.get('failed'):
            active_session.rollback()
            return self.error_could_not_resume_credit_clock_timer(kwargs)
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'clock': credit_clock.fetch_credit_clock_id(),
        }
        if resume.get('write_uid'):
            del resume['write_uid']
        command_chain_response.update(resume)
        return command_chain_response

    def action_pause_credit_clock_timer(self, **kwargs):
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock(kwargs)
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found(kwargs)
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
        if not pause or isinstance(pause, dict) and pause.get('failed'):
            active_session.rollback()
            return self.error_could_not_pause_credit_clock_timer(kwargs)
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'clock': credit_clock.fetch_credit_clock_id(),
        }
        if pause.get('write_uid'):
            del pause['write_uid']
        command_chain_response.update(pause)
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_start_credit_clock_timer(self, **kwargs):
        log.debug('')
        credit_clock = kwargs.get('credit_clock') or \
                self.fetch_active_session_credit_clock()
        if not credit_clock:
            return self.warning_could_not_fetch_credit_clock(kwargs)
        active_session = kwargs.get('active_session') or self.session
        if not active_session:
            return self.error_no_active_session_found(kwargs)
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
        if not start or isinstance(start, dict) and start.get('failed'):
            active_session.rollback()
            return self.error_could_not_start_credit_clock_timer(kwargs)
        active_session.commit()
        command_chain_response = {
            'failed': False,
            'clock': credit_clock.fetch_credit_clock_id(),
            'start_timestamp': time.strftime(
                '%d-%m-%Y %H:%M:%S', time.localtime(start)
            )
        }
        return command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_system_user_logout(self, **kwargs):
        log.debug('')
        user = self.fetch_active_session_user()
        if not user:
            return self.error_no_active_session_user_found(kwargs)
        set_user_state = user.set_user_state(0)
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
            'account': active_user.fetch_user_email(),
            'logout_records': {
                item.logout_id: res_utils.format_datetime(item.logout_date)\
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
            'account': active_user.fetch_user_email(),
            'login_records': {
                item.login_id: res_utils.format_datetime(item.login_date) \
                for item in login_records
            },
        }
        return command_chain_response

    def action_create_new_contact_list(self, **kwargs):
        log.debug('')
        active_user = self.fetch_active_session_user()
        if not active_user:
            return self.error_no_session_active_user_found()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'ctype', 'action', 'target'
        )
        new_contact_list = active_user.user_controller(
            ctype='action', action='create', target='contact_list',
            **sanitized_command_chain
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

    def action_system_session_update(self, **kwargs):
        log.debug('')
        kwargs.update({'session_active_user': self.fetch_active_session_user()})
        update = self.update_session_from_user(**kwargs)
        return update or False

#   @pysnooper.snoop()
    def action_create_new_conversion_clock_to_credits(self, **kwargs):
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

    # ACTION HANDLERS
    '''
    [ NOTES ]: Enviroment checks for proper action execution are performed here.
    '''

    def handle_master_action_edit_account_company(self, **kwargs):
        log.debug('')
        if not kwargs.get('company'):
            return False
        edit_master_company = self.action_edit_master_company(**kwargs)
        return False if edit_master_company.get('failed') else True

    def handle_master_action_edit_account_address(self, **kwargs):
        log.debug('')
        if not kwargs.get('address'):
            return False
        edit_master_address = self.action_edit_master_address(**kwargs)
        return False if edit_master_address.get('failed') else True

    def handle_master_action_edit_account_key_code(self, **kwargs):
        log.debug('')
        if not kwargs.get('key'):
            return False
        edit_master_key = self.action_edit_master_key_code(**kwargs)
        return False if edit_master_key.get('failed') else True

    def handle_master_action_remove_acquired_ctoken(self, **kwargs):
        log.debug('')
        return self.action_remove_master_acquired_ctoken(**kwargs)

    def handle_master_action_view_logout_records(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_view_master_logout_records(**kwargs)

    def handle_master_action_view_login_records(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_view_master_login_records(**kwargs)

    def handle_master_action_inspect_subordonate(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_inspect_master_subordonate(**kwargs)

    def handle_master_action_inspect_subpool(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_inspect_master_subpool(**kwargs)

    def handle_master_action_recover_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if not check_unlinked:
            return self.warning_master_account_not_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_recover_master_account(**kwargs)

    def handle_master_action_unlink_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_unlink_master_account(**kwargs)

    def handle_master_action_edit_account_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name'):
            return False
        edit_master_name = self.action_edit_master_user_name(**kwargs)
        return False if edit_master_name.get('failed') else True

    def handle_master_action_edit_account_user_pass(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_pass'):
            return False
        edit_master_pass = self.action_edit_master_user_pass(**kwargs)
        return False if edit_master_pass.get('failed') else True

    def handle_master_action_edit_account_user_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_alias'):
            return False
        edit_master_alias = self.action_edit_master_user_alias(**kwargs)
        return False if edit_master_alias.get('failed') else True

    def handle_master_action_edit_account_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email'):
            return False
        edit_master_email = self.action_edit_master_user_email(**kwargs)
        return False if edit_master_email.get('failed') else True

    def handle_master_action_edit_account_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_phone'):
            return False
        edit_master_phone = self.action_edit_master_user_phone(**kwargs)
        return False if edit_master_phone.get('failed') else True

    def handle_master_action_edit_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_edit_master_account(**kwargs)

    def handle_master_action_view_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_view_master_account(**kwargs)

    def handle_master_action_account_logout(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_master_logged_in()
        if not check_logged_in:
            return self.warning_master_not_logged_in(kwargs, check_logged_in)
        check_unlinked = self.check_master_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_master_account_flagged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        check_frozen = self.check_master_account_frozen()
        if check_frozen:
            return self.warning_master_account_frozen(
                kwargs, check_logged_in, check_unlinked, check_frozen
            )
        return self.action_master_account_logout(**kwargs)

    def handle_master_action_account_login(self, **kwargs):
        log.debug('')
        return self.action_master_account_login(**kwargs)

    def handle_master_action_add_acquired_ctoken(self, **kwargs):
        log.debug('')
        return self.action_add_master_acquired_ctoken(**kwargs)

    def handle_user_action_search_master_account(self, **kwargs):
        log.debug('')
        return self.action_search_master_account(**kwargs)

    def handle_user_action_create_new_master_account(self, **kwargs):
        log.debug('')
        return self.action_create_new_master_account(**kwargs)

    def handle_system_action_interogate_session_empty(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_empty(**kwargs)

    def handle_user_action_recover_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        return self.warning_user_not_logged_in(check_logged_in, kwargs) \
            if not check_logged_in else \
            self.action_recover_user_account(**kwargs)

    def handle_user_action_unlink_invoice_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_invoice_list(**kwargs)

    def handle_user_action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_invoice_record(**kwargs)

    def handle_user_action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_credit_wallet(**kwargs)

    def handle_user_action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_credit_clock(**kwargs)

    def handle_user_action_unlink_time_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_time_list(**kwargs)

    def handle_user_action_unlink_time_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_time_record(**kwargs)

    def handle_user_action_unlink_transfer_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_transfer_list(**kwargs)

    def handle_user_action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_transfer_record(**kwargs)

    def handle_user_action_unlink_conversion_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_conversion_list(**kwargs)

    def handle_user_action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_conversion_record(**kwargs)

    def handle_user_action_unlink_contact_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_contact_list(**kwargs)

    def handle_user_action_unlink_contact_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_contact_record(**kwargs)

    def handle_user_action_unlink_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_unlink_user_account(**kwargs)

    def handle_user_action_switch_contact_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('list_id'):
            return self.error_no_user_action_switch_contact_list_id_specified(
                kwargs
            )
        switch_contact_list = self.action_switch_contact_list(**kwargs)
        return switch_contact_list

    def handle_user_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_time_sheet_id_specified(
                kwargs
            )
        switch_time_sheet = self.action_switch_time_sheet(**kwargs)
        return switch_time_sheet

    def handle_user_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_conversion_sheet_id_specified(
                kwargs
            )
        switch_conversion_sheet = self.action_switch_conversion_sheet(**kwargs)
        return switch_conversion_sheet

    def handle_user_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_invoice_sheet_id_specified(
                kwargs
            )
        switch_invoice_sheet = self.action_switch_invoice_sheet(**kwargs)
        return switch_invoice_sheet

    def handle_user_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('sheet_id'):
            return self.error_no_user_action_switch_transfer_sheet_id_specified(
                kwargs
            )
        switch_transfer_sheet = self.action_switch_transfer_sheet(**kwargs)
        return switch_transfer_sheet

    def handle_user_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('clock_id'):
            return self.error_no_user_action_switch_credit_clock_id_specified(
                kwargs
            )
        switch_credit_clock = self.action_switch_credit_clock(**kwargs)
        return switch_credit_clock

    def handle_user_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        if check_unlinked:
            return self.warning_user_account_flaged_for_removal(
                kwargs, check_logged_in, check_unlinked
            )
        if not kwargs.get('ewallet_id'):
            return self.error_no_user_action_switch_credit_ewallet_id_specified(
                kwargs
            )
        switch_credit_ewallet = self.action_switch_credit_ewallet(**kwargs)
        return switch_credit_ewallet

    def handle_user_action_switch_active_account(self, **kwargs):
        log.debug('')
        check = self.check_user_logged_in()
        return self.warning_user_not_logged_in(check, kwargs) if not check \
            else self.action_switch_active_user_account(**kwargs)

    def handle_user_action_create_new_time_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_time_sheet(**kwargs)

    def handle_user_action_create_new_conversion_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_conversion_sheet(**kwargs)

    def handle_user_action_create_new_invoice_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_invoice_sheet(**kwargs)

    def handle_user_action_create_new_transfer_sheet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_transfer_sheet(**kwargs)

    def handle_user_action_create_new_credit_clock(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_credit_clock(**kwargs)

    def handle_user_action_create_new_credit_wallet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_credit_wallet(**kwargs)

    def handle_user_action_view_login_records(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_login_records(**kwargs)

    def handle_user_action_view_logout_records(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_logout_records(**kwargs)

    def handle_user_action_view_invoice_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_invoice_list(**kwargs)

    def handle_user_action_view_invoice_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_invoice_record(**kwargs)

    def handle_user_action_view_account(self, **kwargs):
        log.debug('')
        check = self.check_user_logged_in()
        return self.warning_user_not_logged_in(check, kwargs) if not check \
            else self.action_view_user_account(**kwargs)

    def handle_user_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_credit_wallet(**kwargs)

    def handle_user_action_view_credit_clock(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_credit_clock(**kwargs)

    def handle_user_action_view_conversion_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_conversion_list(**kwargs)

    def handle_user_action_view_conversion_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_conversion_record(**kwargs)

    def handle_user_action_view_time_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_time_list(**kwargs)

    def handle_user_action_view_time_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_time_record(**kwargs)

    def handle_user_action_view_transfer_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_transfer_list(**kwargs)

    def handle_user_action_view_transfer_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_transfer_record(**kwargs)

    def handle_user_action_view_contact_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_contact_list(**kwargs)

    def handle_user_action_view_contact_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_view_contact_record(**kwargs)

    def handle_user_action_start_credit_clock_timer(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_start_credit_clock_timer(**kwargs)

    def handle_user_action_pause_credit_clock_timer(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_pause_credit_clock_timer(**kwargs)

    def handle_user_action_resume_credit_clock_timer(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_resume_credit_clock_timer(**kwargs)

    def handle_user_action_stop_credit_clock_timer(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_stop_credit_clock_timer(**kwargs)

    def handle_user_action_create_new_transfer_type_transfer(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_transfer_type_transfer(**kwargs)

    def handle_user_action_edit_account(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_edit_user_account(**kwargs)

    def handle_user_action_create_new_contact_list(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_contact_list(**kwargs)

    def handle_user_action_create_new_contact_record(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_contact_record(**kwargs)

    def handle_user_action_create_new_conversion_credits_to_clock(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_conversion_credits_to_clock(**kwargs)

    def handle_user_action_create_new_conversion_clock_to_credits(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_conversion_clock_to_credits(**kwargs)

    def handle_user_action_create_new_transfer_type_pay(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_transfer_type_pay(**kwargs)

    def handle_user_action_logout(self, **kwargs):
        log.debug('')
        check = self.check_user_logged_in()
        return self.warning_user_not_logged_in(check, kwargs) if not check \
            else self.action_logout_user_account(**kwargs)

    def handle_user_action_create_new_transfer_type_supply(self, **kwargs):
        log.debug('')
        check_logged_in = self.check_user_logged_in()
        if not check_logged_in:
            return self.warning_user_not_logged_in(check_logged_in, kwargs)
        check_unlinked = self.check_user_account_flag_for_unlink()
        return self.warning_user_account_flaged_for_removal(
            kwargs, check_logged_in, check_unlinked
        ) if check_unlinked else self.action_create_new_transfer_type_supply(**kwargs)

    def handle_user_action_login(self, **kwargs):
        log.debug('')
        return self.action_login_user_account(**kwargs)

    def handle_system_action_check_user(self, **kwargs):
        log.debug('')
        return self.action_system_user_check(**kwargs)

    def handle_system_action_check_session(self, **kwargs):
        log.debug('')
        return self.action_system_session_check(**kwargs)

    def handle_system_action_update_user(self, **kwargs):
        log.debug('')
        return self.action_system_user_update(**kwargs)

    def handle_system_action_update_session(self, **kwargs):
        log.debug('')
        return self.action_system_session_update(**kwargs)

    def handle_system_action_send_invoice_record(self, **kwargs):
        log.debug('')
        return self.action_send_invoice_record(**kwargs)

    def handle_system_action_send_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_send_invoice_sheet(**kwargs)

    def handle_system_action_send_transfer_record(self, **kwargs):
        log.debug('')
        return self.action_send_transfer_record(**kwargs)

    def handle_system_action_send_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_send_transfer_sheet(**kwargs)

    def handle_system_action_receive_invoice_record(self, **kwargs):
        log.debug('')
        return self.action_receive_invoice_record(**kwargs)

    def handle_system_action_receive_invoice_sheet(self, **kwargs):
        log.debug('')
        return self.action_receive_invoice_sheet(**kwargs)

    def handle_system_action_receive_transfer_record(self, **kwargs):
        log.debug('')
        return self.action_receive_transfer_record(**kwargs)

    def handle_system_action_receive_transfer_sheet(self, **kwargs):
        log.debug('')
        return self.action_receive_transfer_sheet(**kwargs)

    def handle_user_action_create_new_user_account(self, **kwargs):
        log.debug('')
        return self.action_create_new_user_account(**kwargs)

    def handle_system_action_interogate_session_state(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_state(**kwargs)

    def handle_system_action_interogate_session_expired(self, **kwargs):
        log.debug('')
        return self.action_interogate_ewallet_session_expired(**kwargs)

    def handle_system_action_cleanup_ewallet_session(self, **kwargs):
        log.debug('')
        return self.action_cleanup_ewallet_session(**kwargs)

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

    # EVENT HANDLERS

    # JUMPTABLE HANDLERS

    def handle_master_action_remove_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctoken'):
            return self.error_no_master_action_remove_ctoken_target_specified(kwargs)
        handlers = {
            'acquired': self.handle_master_action_remove_acquired_ctoken,
        }
        return handlers[kwargs['ctoken']](**kwargs)

    def handle_master_action_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('remove'):
            return self.error_no_master_action_remove_target_specified(kwargs)
        handlers = {
            'ctoken': self.handle_master_action_remove_ctoken,
        }
        return handlers[kwargs['remove']](**kwargs)

    def handle_master_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_master_action_view_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_view_account,
            'login': self.handle_master_action_view_login_records,
            'logout': self.handle_master_action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_master_action_inspect(self, **kwargs):
        log.debug('')
        if not kwargs.get('inspect'):
            return self.error_no_master_action_inspect_target_specified(kwargs)
        handlers = {
            'subpool': self.handle_master_action_inspect_subpool,
            'subordonate': self.handle_master_action_inspect_subordonate,
        }
        return handlers[kwargs['inspect']](**kwargs)

    def handle_master_action_recover(self, **kwargs):
        log.debug('')
        if not kwargs.get('recover'):
            return self.error_no_master_action_recover_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_recover_account,
        }
        return handlers[kwargs['recover']](**kwargs)

    def handle_master_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_master_action_unlink_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_unlink_account,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_master_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_master_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_master_action_logout(self, **kwargs):
        log.debug('')
        if not kwargs.get('logout'):
            return self.error_no_master_action_logout_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_account_logout,
        }
        return handlers[kwargs['logout']](**kwargs)

    def handle_master_action_login(self, **kwargs):
        log.debug('')
        if not kwargs.get('login'):
            return self.error_no_master_action_login_target_specified(kwargs)
        handlers = {
            'account': self.handle_master_action_account_login,
        }
        return handlers[kwargs['login']](**kwargs)

    def handle_master_action_add_ctoken(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctoken'):
            return self.error_no_master_action_add_ctoken_target_specified(kwargs)
        handlers = {
            'acquired': self.handle_master_action_add_acquired_ctoken,
        }
        return handlers[kwargs['ctoken']](**kwargs)

    def handle_master_action_add(self, **kwargs):
        log.debug('')
        if not kwargs.get('add'):
            return self.error_no_master_action_add_target_specified(kwargs)
        handlers = {
            'ctoken': self.handle_master_action_add_ctoken,
        }
        return handlers[kwargs['add']](**kwargs)

    def handle_user_action_search(self, **kwargs):
        log.debug('')
        if not kwargs.get('search'):
            return self.error_no_client_action_search_target_specified()
        handlers = {
            'master': self.handle_user_action_search_master_account,
        }
        return handlers[kwargs['search']](**kwargs)

    def handle_user_action_create_new_master(self, **kwargs):
        log.debug('')
        if not kwargs.get('master'):
            return self.error_no_create_new_master_target_specified()
        handlers = {
            'account': self.handle_user_action_create_new_master_account,
        }
        return handlers[kwargs['master']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'account': self.handle_user_action_unlink_account,
            'credit_wallet': self.handle_user_action_unlink_credit_ewallet,
            'credit_clock': self.handle_user_action_unlink_credit_clock,
            'contact': self.handle_user_action_unlink_contact,
            'invoice': self.handle_user_action_unlink_invoice,
            'transfer': self.handle_user_action_unlink_transfer,
            'time': self.handle_user_action_unlink_time,
            'conversion': self.handle_user_action_unlink_conversion,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_user_action_unlink_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.handle_user_action_unlink_conversion_list,
            'record': self.handle_user_action_unlink_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_user_action_unlink_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.handle_user_action_unlink_time_list,
            'record': self.handle_user_action_unlink_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_user_action_unlink_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_unlink_target_specified(kwargs)
        handlers = {
            'list': self.handle_user_action_unlink_transfer_list,
            'record': self.handle_user_action_unlink_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_user_action_unlink_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.handle_user_action_unlink_invoice_list,
            'record': self.handle_user_action_unlink_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_user_action_unlink_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_unlink_target_specified()
        handlers = {
            'list': self.handle_user_action_unlink_contact_list,
            'record': self.handle_user_action_unlink_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_user_action_view(self, **kwargs):
        log.debug('')
        if not kwargs.get('view'):
            return self.error_no_user_action_view_target_specified(kwargs)
        handlers = {
            'account': self.handle_user_action_view_account,
            'credit_wallet': self.handle_user_action_view_credit_ewallet,
            'credit_clock': self.handle_user_action_view_credit_clock,
            'contact': self.handle_user_action_view_contact,
            'invoice': self.handle_user_action_view_invoice,
            'transfer': self.handle_user_action_view_transfer,
            'time': self.handle_user_action_view_time,
            'conversion': self.handle_user_action_view_conversion,
            'login': self.handle_user_action_view_login_records,
            'logout': self.handle_user_action_view_logout_records,
        }
        return handlers[kwargs['view']](**kwargs)

    def handle_user_action_view_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_view_target_specified()
        handlers = {
            'list': self.handle_user_action_view_conversion_list,
            'record': self.handle_user_action_view_conversion_record,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_user_action_view_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('time'):
            return self.error_no_time_view_target_specified()
        handlers = {
            'list': self.handle_user_action_view_time_list,
            'record': self.handle_user_action_view_time_record,
        }
        return handlers[kwargs['time']](**kwargs)

    def handle_user_action_view_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_transfer_view_target_specified()
        handlers = {
            'list': self.handle_user_action_view_transfer_list,
            'record': self.handle_user_action_view_transfer_record,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_user_action_view_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        handlers = {
            'list': self.action_view_invoice_list,
            'record': self.action_view_invoice_record,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_user_action_view_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_target_specified()
        handlers = {
            'list': self.handle_user_action_view_contact_list,
            'record': self.handle_user_action_view_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_user_action_time(self, **kwargs):
        log.debug('')
        if not kwargs.get('timer'):
            return self.error_no_timer_action_specified()
        handlers = {
            'start': self.handle_user_action_start_credit_clock_timer,
            'pause': self.handle_user_action_pause_credit_clock_timer,
            'resume': self.handle_user_action_resume_credit_clock_timer,
            'stop': self.handle_user_action_stop_credit_clock_timer,
        }
        return handlers[kwargs['timer']](**kwargs)

    def handle_system_action_check(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_check_target_specified()
        handlers = {
            'user': self.handle_system_action_check_user,
            'session': self.handle_system_action_check_session,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_system_action_update(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_system_update_target_specified()
        handlers = {
            'user': self.handle_system_action_update_user,
            'session': self.handle_system_action_update_session,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_system_action_send_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        handlers = {
            'record': self.handle_system_action_send_invoice_record,
            'list': self.handle_system_action_send_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_system_action_send_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer'):
            return self.error_no_transfer_target_specified()
        handlers = {
            'record': self.handle_system_action_send_transfer_record,
            'list': self.handle_system_action_send_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_system_action_receive_invoice(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice'):
            return self.error_no_invoice_target_specified()
        handlers = {
            'record': self.handle_system_action_receive_invoice_record,
            'list': self.handle_system_action_receive_invoice_sheet,
        }
        return handlers[kwargs['invoice']](**kwargs)

    def handle_system_action_receive_transfer(self, **kwargs):
        if not kwargs.get('transfer'):
            return self.error_no_transfer_target_specified()
        handlers = {
            'record': self.handle_system_action_receive_transfer_record,
            'list': self.handle_system_action_receive_transfer_sheet,
        }
        return handlers[kwargs['transfer']](**kwargs)

    def handle_user_action_create_new_contact(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact'):
            return self.error_no_contact_found()
        handlers = {
            'list': self.handle_user_action_create_new_contact_list,
            'record': self.handle_user_action_create_new_contact_record,
        }
        return handlers[kwargs['contact']](**kwargs)

    def handle_user_action_create(self, **kwargs):
        log.debug('')
        if not kwargs.get('create'):
            return self.error_no_user_create_target_specified()
        handlers = {
            'master': self.handle_user_action_create_new_master,
            'account': self.handle_user_action_create_new_user_account,
            'credit_wallet': self.handle_user_action_create_new_credit_wallet,
            'credit_clock': self.handle_user_action_create_new_credit_clock,
            'transfer_sheet': self.handle_user_action_create_new_transfer_sheet,
            'invoice_sheet': self.handle_user_action_create_new_invoice_sheet,
            'conversion_sheet': self.handle_user_action_create_new_conversion_sheet,
            'time_sheet': self.handle_user_action_create_new_time_sheet,
            'transfer': self.handle_user_action_create_new_transfer,
            'conversion': self.handle_user_action_create_new_conversion,
            'contact': self.handle_user_action_create_new_contact,
        }
        return handlers[kwargs['create']](**kwargs)

    def handle_user_action_create_new_conversion(self, **kwargs):
        log.debug('')
        if not kwargs.get('conversion'):
            return self.error_no_conversion_type_specified()
        handlers = {
            'credits2clock': self.handle_user_action_create_new_conversion_credits_to_clock,
            'clock2credits': self.handle_user_action_create_new_conversion_clock_to_credits,
        }
        return handlers[kwargs['conversion']](**kwargs)

    def handle_user_action_create_new_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('ttype'):
            return self.error_no_transfer_type_specified()
        handlers = {
            'supply': self.handle_user_action_create_new_transfer_type_supply,
            'pay': self.handle_user_action_create_new_transfer_type_pay,
            'transfer': self.handle_user_action_create_new_transfer_type_transfer,
        }
        return handlers[kwargs['ttype']](**kwargs)

    def handle_system_action_cleanup(self, **kwargs):
        log.debug('')
        if not kwargs.get('cleanup'):
            return self.error_no_system_action_cleanup_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_cleanup_ewallet_session,
        }
        return handlers[kwargs['cleanup']](**kwargs)

    def handle_system_action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        if not kwargs.get('session'):
            return self.error_no_system_action_interogate_ewallet_session_target_specified(
                kwargs
            )
        handlers = {
            'expired': self.handle_system_action_interogate_session_expired,
            'empty': self.handle_system_action_interogate_session_empty,
            'state': self.handle_system_action_interogate_session_state,
        }
        return handlers[kwargs['session']](**kwargs)

    def handle_user_action_recover(self, **kwargs):
        log.debug('')
        if not kwargs.get('recover'):
            return self.error_no_user_action_recover_target_specified(kwargs)
        handlers = {
            'account': self.handle_user_action_recover_account,
        }
        return self.warning_invalid_user_action_recover_target(kwargs) if \
            kwargs['recover'] not in handlers.keys() else \
            handlers[kwargs['recover']](**kwargs)

    def handle_system_action_interogate(self, **kwargs):
        log.debug('')
        if not kwargs.get('interogate'):
            return self.error_no_system_action_interogate_target_specified(kwargs)
        handlers = {
            'session': self.handle_system_action_interogate_ewallet_session,
        }
        return handlers[kwargs['interogate']](**kwargs)

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
            'account': self.handle_user_action_switch_active_account,
        }
        return handlers[kwargs['switch']](**kwargs)

    def handle_user_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_user_action_edit_target_specified(kwargs)
        handlers = {
            'account': self.handle_user_action_edit_account,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_system_action_send(self, **kwargs):
        if not kwargs.get('send'):
            return self.error_no_system_action_specified()
        handlers = {
            'invoice': self.handle_system_action_send_invoice,
            'transfer': self.handle_system_action_send_transfer,
        }
        return handlers[kwargs['send']](**kwargs)

    def handle_system_action_receive(self, **kwargs):
        if not kwargs.get('receive'):
            return self.error_no_system_action_specified()
        handlers = {
            'invoice': self.handle_system_action_receive_invoice,
            'transfer': self.handle_system_action_receive_transfer,
        }
        return handlers[kwargs['send']](**kwargs)

    # CONTROLLERS

    def ewallet_master_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_master_controller_type_specified(kwargs)
        handlers = {
            'add': self.handle_master_action_add,
            'login': self.handle_master_action_login,
            'logout': self.handle_master_action_logout,
            'view': self.handle_master_action_view,
            'edit': self.handle_master_action_edit,
            'unlink': self.handle_master_action_unlink,
            'recover': self.handle_master_action_recover,
            'inspect': self.handle_master_action_inspect,
            'remove': self.handle_master_action_remove,
        }
        return handlers[kwargs['action']](**kwargs)

    def ewallet_master_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_master_controller_type_specified(kwargs)
        handlers = {
            'action': self.ewallet_master_action_controller,
#           'event': self.ewallet_master_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def ewallet_user_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_action_specified()
        handlers = {
            'login': self.handle_user_action_login,
            'logout': self.handle_user_action_logout,
            'create': self.handle_user_action_create,
            'time': self.handle_user_action_time,
#           'reset': self.handle_user_action_reset,
            'view': self.handle_user_action_view,
            'unlink': self.handle_user_action_unlink,
            'edit': self.handle_user_action_edit,
            'switch': self.handle_user_action_switch,
            'recover': self.handle_user_action_recover,
            'search': self.handle_user_action_search,
        }
        return handlers[kwargs['action']](**kwargs)

    def ewallet_system_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_system_action_specified()
        handlers = {
            'check': self.handle_system_action_check,
            'update': self.handle_system_action_update,
            'send': self.handle_system_action_send,
            'receive': self.handle_system_action_receive,
            'interogate': self.handle_system_action_interogate,
            'cleanup': self.handle_system_action_cleanup,
        }
        return handlers[kwargs['action']](**kwargs)

    def ewallet_system_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_system_controller_type_specified()
        handlers = {
            'action': self.ewallet_system_action_controller,
#           'event': self.ewallet_system_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def ewallet_user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_user_controller_type_specified()
        handlers = {
            'action': self.ewallet_user_action_controller,
#           'event': self.ewallet_user_event_controller,
        }
        return handlers[kwargs['ctype']](**kwargs)

    def ewallet_controller(self, **kwargs):
        '''
        [ NOTE   ]: Main command interface for EWallet session.
        [ INPUT  ]: controller=('system' | 'user')
        [ RETURN ]: Action/Event variable correspondent.
        '''
        log.debug('')
        if not kwargs.get('controller'):
            return self.error_no_ewallet_controller_specified()
        controllers = {
            'system': self.ewallet_system_controller,
            'user': self.ewallet_user_controller,
            'master': self.ewallet_master_controller,
        }
        return controllers[kwargs['controller']](**kwargs)

    # WARNINGS
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_could_not_cleanup_user_account(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not cleanup Subordonate user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_company(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account company. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_address(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account address. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_key_code(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account key code. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_time_sheet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_honour_credit_request(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not honour credit request. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_inspect_master_subordonate_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not inspect Master user account Subordonate. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_inspect_master_account_subpool(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not inspect Master user account Subordonate pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_account_not_flagged_for_removal(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Master user account is not flagged for deletion. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_recover_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not recover Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_account_pending_deletion(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Master user account pending deletion. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_master_account_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch Master user account by ID. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_master_account_values_edited(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'No Master account values edited. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_user_name(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account user name. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_user_pass(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account password. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_user_alias(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account alias. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_user_email(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account email address. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_master_user_phone(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit Master account phone number. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_not_logged_in(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Master user account is not logged in. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_account_flagged_for_removal(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Master user account is currently flagged for removal, '
                       'all account actions locked. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_ewallet_session_active_master(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch active session Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_logout_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not logout Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_login_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not login Master user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_master_account_frozen(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Master account is currently in a frozen state, '
                       'all master and subordonate user actions locked. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_check_master_account_frozen(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not check if Master account is in a frozen state.'
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_account_frozen(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'User account is currently in a frozen state, '
                       'all user actions locked. Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_check_user_belongs_to_master_account_subpool(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not check if user account belongs to acquired '
                       'Master account Subordonate pool. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_master_account_by_identifier(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch Master user account by ID.'
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_account_not_subordonate_to_acquired_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Illegal action. '
                       'User account is not a Subordonate of acquired '
                       'Master account. Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_subordonate_account_pool_size_limit_reached(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Illegal action. '
                       'Subordonate account pool size limit reached. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_master_key_code_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'No master key code specified. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_invalid_master_account_key_code(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Invalid master account key code. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_master_account_found_by_email(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'No master user account found by email address. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_invalid_search_by_parameter_for_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Invalid search by parameter for master account query. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_master_account_found_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'No master user account found by ID.'
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_link_new_user_account_to_master(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not link new user account to master account.'
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_record_id_not_in_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Transfer record ID not found in active transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_update_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Could not update ewallet session. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_account_flaged_for_removal(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'User account marked for removal. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'No user account found. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not create new user account. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_pass(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not edit account user account password. '
                       'Details: {}'.format(args)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_invoice_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink invoice sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink transfer sheet. '
                       'Details : {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_transfer_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink transfer sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink conversion sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_list_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink contact list record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_account_does_not_belong_to_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'User account does not belong to ewallet session. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not unlink contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_time_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not switch credit ewallet. '
                       'Command chain details : {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_account_not_logged_in(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Account not logged in. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_invoice_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch invoice sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_conversion_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch conversion sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_time_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch time sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_transfer_sheet_record(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. '
                       'Could not fetch transfer sheet record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_not_logged_in(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Illegal account state, user not logged in. '
                       'Details: {}'.format(args)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_invalid_user_action_recover_target(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Invalid user action recover target specified. '
                       'Details : {}'.format(args)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_recover_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not recover user account. '
                       'Details : {}'.format(args)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_account_pending_deletion(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'User account pending deletion. '
                       'Command chain details : {}'.format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_user_account_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch user account by id. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_account_not_found_in_database(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'User account not found in EWallet database. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_invoice_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch credit wallet invoice sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_ewallet_session_active_user(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch ewallet session active user. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_active_session_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch active session credit ewallet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch credit clock conversion sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_transfer_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'something went wrong. could not fetch credit wallet transfer sheet. '\
                       'command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_contact_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch contact record. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_contact_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not create new contact record '\
                       'for {}. Command chain details : {}'.format(
                            user_name, command_chain
                       ),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_credit_clock(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch credit clock. '\
                       'Command chain response : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_found_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'No user account found by id. Command chain details : {}'\
                       .format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_logout_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not logout user account from ewallet session. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_find_user_action_switch_target_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not find account for user '\
                       'action switch active session user account. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_user_account_from_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch user account from active session user archive. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_user_account_from_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not fetch user account from ewallet session archive. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_login_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not login user account. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_logout_records(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not view account logout records for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_view_login_records(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not view login records for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_user_account(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not unlink user account {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_unlink_time_sheet_record(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not unlink time sheet record for user {}. '\
                       'Command chain details : {}'.format(user_name, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_conversion_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not create new conversion sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_invoice_sheet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not create new invoice sheet. '\
                       'Command chain details : {}'.format(command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_credit_clock(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not create new credit clock for user {}. '\
                       'Command set details : {}'.format(user_name, command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_create_credit_wallet(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not create new credit wallet for user {}. '\
                     'Command chain details : {}'.format(user_name, command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_name(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not edit account user name. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_alias(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not edit account user alias. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_email(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not edit account user email. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_edit_account_user_phone(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. Could not edit account user phone. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_user_account_values_edited(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'warning': 'Something went wrong. No user account values edited. Command chain details : {}'\
                       .format(command_chain)
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_user_not_in_session_archive(self):
        log.error('User account not found in session user archive.')
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

    def warning_could_not_fetch_user_by_id(self, user_id):
        log.warning(
                'Something went wrong. '
                'Could not fetch user by id %s.', user_id
                )
        return False

    # ERRORS
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_invalid_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'Invalid credit ewallet. '
                     'Details : {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user account specified. '
                     'Details : {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_supply_type_transfer_failure(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Supply type transfer failure. '
                     'Details : {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_user_account_logout_records(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not unlink user account logout records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_user_account_login_records(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not unlink user account login records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_logout_failure_limit_exceeded(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Too many user account logout failures, '
                     'terminated by failsafe. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_master_acquired_ctoken(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'Somethign went wrong. '
                     'Could not remove Master account acquired CToken. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_remove_ctoken_target_specified(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'No Master action RemoveCToken target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_remove_target_specified(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'ewallet-session',
            'error': 'No Master action Remove target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_subordonate_account_id_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No Subordonate user account ID specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_inspect_master_account_subordonate(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not inspect Master user account Subordonate. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_inspect_master_account_subpool(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not inspect Master user account Subordonate pool. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_inspect_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Inspect target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No Master account found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_recover_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not recover Master user account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_ewallet_session_from_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not update ewallet session from '
                     'Master user account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_recover_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Recover target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_check_if_master_account_belongs_to_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not check if Master user account '
                     'belongs to ewallet session. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No Master account ID found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_master_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not unlink Master user account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_unlink_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Unlink target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_edit_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Edit target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_view_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action View target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_master_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active Master account found in ewallet session. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_logout_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Logout target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_check_if_master_account_frozen(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not check if Master user account is in a '
                     'frozen state. Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_login_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No Master action Login target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No Master user account ID found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_data_set_for_master_account_user_pool_check(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Invalid data set, could not verify if user account '
                     'belongs to acquired Master account Subordonate pool. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_add_master_acquired_ctoken(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not add master acquired CToken to pool. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_data_set_for_master_key_code_check(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Invalid data set for master account '
                     'key code verification. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_add_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action Add target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_action_add_ctoken_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master action AddCToken target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_controller_type_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master controller type specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_email_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master account email address specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_master_account_by_email(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch master user account by email address. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_search_by_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master account search by parameter specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_identifier_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master account identifier specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_action_search_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No client action search target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_master_account_by_id(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch master user account by ID. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_master_account_id_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No master account ID specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_master(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch active session master account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_active_session_master(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set active session master account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_active_master_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active session master user account found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_contact_list_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active session contact list found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_check_if_ewallet_session_empty(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not check if ewallet session is empty. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not unlink user account. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_pay_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action pay target specified. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_pay_type_transfer_failure(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Credit payment failure. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active SqlAlchemy ORM session found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_email_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user email found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_by_email(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch user account by email address. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_partner_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch partner account. '
                     'Details: {}'.format(*args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_active_user_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active session user found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_cleanup_ewallet_session(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not cleanup ewallet session. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_system_action_cleanup_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No system action cleanup target specified. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_system_action_interogate_ewallet_session_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No system action interogate ewallet session target specified. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_check_if_ewallet_session_expired(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not check if EWallet session expired. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_session_expiration_date(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set EWallet session expiration date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_session_name(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set EWallet session reference. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_account_to_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set user account to session account archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_account_archive(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set active session user account archive. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_session_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set active session credit ewallet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_session_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set active session contact list. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_active_session_user(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set active session user. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set EWallet session write date. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_orm_session(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not set ORM session. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_recover_user_account(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not recover user account. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_recover_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action recover target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_found(self, *args):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user account found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_pause_credit_clock_timer(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not pause credit clock timer. '
                     'Details: {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_stop_credit_clock_timer(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not stop credit clock timer. '
                     'Details: {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_wallet_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No credit ewallet found. '
                     'Command chain details: {}'.format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_record_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No invoice record id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_convert_credits_to_minutes(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not convert credits to minutes. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_conversion_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No conversion record id found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_time_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No time sheet record id found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not fetch credit ewallet. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_sheet_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No transfer sheet record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_session_credit_wallet_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No session credit wallet found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_transfer_type_transfer_failure(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Transfer type transaction failure. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_transfer_credits_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action transfer credits target specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_contact_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No contact record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_contact_list(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch contact list. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_contact_list_found(self, user_name, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No active session contact list found for user {}. '\
                     'Command chain details : {}'.format(user_name, command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_partner_account_for_transfer_type_supply(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not fetch partner account '\
                     'for transfer type supply. Command chain details : {}'\
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_resume_credit_clock_timer(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not resume credit clock timer. '\
                     'Command chain details : {}'.format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_start_credit_clock_timer(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not start credit clock timer. '\
                     'Command chain details : {}'.format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_system_action_interogate_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No system action interogate target specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_user_from_account_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not remove user account from active session account archive. '
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_user_account_does_not_belong_to_active_session_archive(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'User account does not belong to active session {} user account archive. '\
                     'Command chain details : {}'.format(self, command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_ewallet_session_from_user_account(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. Could not update ewallet session from user account. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_active_session_account_archive_empty(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Active session user account archive is empty. '\
                     'Command chain response : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_account_by_id(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Could not fetch user account by id, no database records found. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user account id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_active_account_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch active account id specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_object_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user object found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_view_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action view target specified. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_user(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Something went wrong. '
                     'Could not fetch active session user. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_account_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user account id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Could not fetch active session credit ewallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_contact_list(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Could not fetch active session contact list. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_unlink_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No unlink target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Could not fetch active session credit wallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_contact_list_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch contact list id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_time_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch time sheet id specified. Command chain details :"{}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_conversion_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch conversion sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_invoice_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch invoice sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_transfer_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch transfer sheet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_credit_clock_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch credit clock id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch target specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_switch_credit_ewallet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action switch credit ewallet id specified. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_session_credit_wallet(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'Could not fetch active session credit ewallet. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_edit_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True,
            'level': 'ewallet-session',
            'error': 'No user action edit target specified. Command chain details : {}'\
                     .foramt(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

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

    def error_no_user_name_found(self):
        log.error('No user name found.')
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

    def error_no_user_password_found(self):
        log.error('No user password found.')
        return False

    def error_no_contact_found(self):
        log.error('No contact found.')
        return False

    def error_no_transfer_type_found(self):
        log.error('No transfer type found.')
        return False

    def error_no_partner_credit_wallet_found(self):
        log.error('No partner credit wallet found.')
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

    def error_could_not_convert_minutes_to_credits(self):
        log.error('Could not convert minutes to credits.')
        return False


################################################################################
# CODE DUMP
################################################################################

#   def error_could_not_set_master_account_to_archive(self, *args):
#       command_chain_response = {
#           'failed': True,
#           'error': 'Something went wrong. '
#                    'Could not set Master user account to archive. '
#                    'Details: {}'.format(args),
#       }
#       log.error(command_chain_response['error'])
#       return command_chain_response

#   def error_no_master_object_found(self, *args):
#       command_chain_response = {
#           'failed': True,
#           'error': 'No Master account object found. '
#                    'Details: {}'.format(args),
#       }
#       log.error(command_chain_response['error'])
#       return command_chain_response

#   def ewallet_user_event_controller(self, **kwargs):
#       log.debug('')
#       if not kwargs.get('event'):
#           return self.error_no_user_event_specified()
#       handlers = {
#           'signal': self.handle_user_event_signal,
#           'notification': self.handle_user_event_notification,
#           'request': self.handle_user_event_request,
#       }
#       return handlers[kwargs['event']](**kwargs)

#   def ewallet_system_event_controller(self, **kwargs):
#       log.debug('')
#       if not kwargs.get('event'):
#           return self.error_no_system_event_specified()
#       handlers = {
#           'signal': self.handle_system_event_signal,
#           'notification': self.handle_system_event_notification,
#           'request': self.handle_system_event_request,
#       }
#       return handlers[kwargs['event']](**kwargs)

#   def handle_system_event_signal(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_event_notification(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_system_event_request(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_user_event_signal(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_user_event_notification(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')
#   def handle_user_event_request(self, **kwargs):
#       log.debug('TODO - UNIMPLEMENTED')

