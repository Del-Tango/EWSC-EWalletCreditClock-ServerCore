import datetime
import logging
import pysnooper

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean #Table,Float,Date,
from sqlalchemy.orm import relationship

from .credit_wallet import CreditEWallet
from .contact_list import ContactList
from .res_user_pass_hash_archive import ResUserPassHashArchive
from .res_utils import ResUtils, Base
from .config import Config
from .transaction_handler import EWalletTransactionHandler

res_utils, config = ResUtils(), Config()
log_config = config.log_config
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
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    active_session = relationship(
        'EWallet', back_populates='active_user'
    )
    user_contact_list = relationship(
        'ContactList', back_populates='client',
        cascade='delete, merge, save-update, delete-orphan'
    )
    user_credit_wallet = relationship(
        'CreditEWallet', back_populates='client',
        cascade='delete, merge, save-update'
    )
    user_session_archive = relationship(
        'EWallet', secondary='ewallet_session_user'
    )
    master_account_id = Column(Integer, ForeignKey('res_master.user_id'))
    subordonate_of = relationship(
        'ResMaster', back_populates='subordonate_pool',
        foreign_keys='ResUser.master_account_id'
    )
    user_pass_hash_archive = relationship(
        'ResUserPassHashArchive', cascade='delete, merge, save-update'
    )
    user_credit_wallet_archive = relationship(
        'CreditEWallet', cascade='delete, merge, save-update'
    )
    user_contact_list_archive = relationship(
        'ContactList', cascade='delete, merge, save-update'
    )
    to_unlink = Column(Boolean)
    to_unlink_timestamp = Column(DateTime)
    is_active = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'res_user',
        'concrete': True,
    }

#   @pysnooper.snoop('logs/ewallet.log')
    def __init__(self, **kwargs):
        self.user_create_date = datetime.datetime.now()
        self.user_write_date = datetime.datetime.now()
        self.user_create_uid = kwargs.get('user_create_uid')
        self.user_write_uid = kwargs.get('user_write_uid')
        self.user_name = kwargs.get('user_name')
        self.user_email = kwargs.get('user_email')
        self.user_phone = kwargs.get('user_phone')
        self.user_alias = kwargs.get('user_alias')
        self.user_state_code = kwargs.get('user_state_code') or 0
        self.user_state_name = kwargs.get('user_state_name') or 'LoggedOut'
        if not kwargs.get('master'):
            user_credit_wallet = kwargs.get('user_credit_wallet') or \
                self.user_action_controller(
                    action='create', target='credit_wallet', **kwargs
                )
            user_contact_list = kwargs.get('user_contact_list') or \
                self.user_action_controller(
                    action='create', target='contact_list', **kwargs
                )
            self.user_credit_wallet = [user_credit_wallet]
            self.user_contact_list = [user_contact_list]
            self.user_pass_hash = kwargs.get('user_pass_hash')
            self.user_pass_hash_archive = kwargs.get('user_pass_hash_archive') or []
            self.user_credit_wallet_archive = kwargs.get('user_credit_wallet_archive') or \
                    [user_credit_wallet]
            self.user_contact_list_archive = kwargs.get('user_contact_list_archive') or \
                    [user_contact_list]
        self.to_unlink = kwargs.get('to_unlink', False)
        self.to_unlink_timestamp = kwargs.get('to_unlink_timestamp')
        self.is_active = kwargs.get('is_active', True)
        try:
            self.master_account_id = kwargs.get('master_id')
        except Exception as e:
            log.warning(e)

    # FETCHERS

    def fetch_transaction_handler_creation_values_for_event_request_credits(self, **kwargs):
        log.debug('')
        creation_values = {
            'transaction_type': 'supply',
            'source_user_account': self,
            'target_user_account': kwargs.get('partner_account'),
            'active_session': kwargs.get('active_session'),
        }
        return creation_values

    def fetch_user_to_unlink(self):
        log.debug('')
        return self.to_unlink

    def fetch_user_to_unlink_timestamp(self):
        log.debug('')
        return self.to_unlink_timestamp

    def fetch_user_state(self):
        log.debug('')
        return self.user_state_code

    def fetch_user_contact_list_by_id(self, list_id, orm_session):
        log.debug('')
        query = list(
            orm_session.query(ContactList).filter_by(contact_list_id=list_id)
        )
        contact_list = None if not query else query[0]
        if not contact_list:
            return self.warning_no_contact_list_found_by_id(
                list_id, orm_session
            )
        log.info('Successfully fetched contact list by id.')
        return contact_list

    def fetch_user_credit_ewallet_by_id(self, ewallet_id, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_ewallet_session().fetch_active_session()
        query = list(
            active_session.query(CreditEWallet).filter_by(wallet_id=ewallet_id)
        )
        ewallet = None if not query else query[0]
        if not ewallet:
            return self.warning_no_credit_ewallet_found_by_id(ewallet_id, kwargs)
        log.info('Successfully fetched credit ewallet.')
        return ewallet

    def fetch_credit_ewallet_creation_values(self, **kwargs):
        log.debug('')
        creation_values = {
            'client_id': self.fetch_user_id(),
            'reference': kwargs.get('reference') or 'Credit EWallet',
            'credits': kwargs.get('credits') or 0,
        }
        return creation_values

    def fetch_transaction_handler_creation_values_for_action_transfer(self, **kwargs):
        log.debug('')
        creation_values = {
            'transaction_type': 'transfer',
            'source_user_account': self,
            'target_user_account': kwargs.get('transfer_to'),
            'active_session': kwargs.get('active_session'),
        }
        return creation_values

    def fetch_transaction_handler_creation_values_for_action_pay(self, **kwargs):
        log.debug('')
        creation_values = {
            'transaction_type': 'pay',
            'source_user_account': self,
            'target_user_account': kwargs.get('pay'),
            'active_session': kwargs.get('active_session'),
        }
        return creation_values

    def fetch_user_active_ewallet_session(self):
        log.debug('')
        return self.error_no_active_ewallet_user_session_found()\
                if not self.active_session else self.active_session

    def fetch_orm_session_from_ewallet_session(self, ewallet_session):
        log.debug('')
        orm_session = ewallet_session.fetch_active_session()
        return self.error_no_ewallet_orm_session_found(ewallet_session) \
                if not orm_session else orm_session

    def fetch_user_active_orm_session(self):
        log.debug('')
        ewallet_session = self.fetch_user_active_ewallet_session()
        if not ewallet_session:
            return self.error_no_ewallet_session_found()
        orm_session = self.fetch_orm_session_from_ewallet_session(ewallet_session)
        return False if not orm_session else orm_session

    def fetch_user_active_session(self, stype=None):
        log.debug('')
        if not stype:
            return self.error_no_session_type_specified(stype)
        fetchers = {
            'ewallet': self.fetch_user_active_ewallet_session,
            'orm': self.fetch_user_active_orm_session,
        }
        return fetchers[stype]()

    def fetch_credit_wallets_for_transaction(self, local_partner, remote_partner, command_chain):
        log.debug('')
        local_credit_wallet = local_partner.fetch_user_credit_wallet()
        if not local_credit_wallet:
            return self.error_no_credit_wallet_found()
        remote_credit_wallet = remote_partner.fetch_user_credit_wallet()
        if not remote_credit_wallet:
            return self.warning_could_not_fetch_partner_credit_wallet(
                remote_partner.fetch_user_name()
            )
        return {'local': local_credit_wallet, 'remote': remote_credit_wallet}

    def fetch_credit_wallet_transfer_and_invoice_sheets(self, credit_wallet):
        log.debug('')
        local_transfer_sheet = credit_wallet.fetch_credit_ewallet_transfer_sheet()
        local_invoice_sheet = credit_wallet.fetch_credit_ewallet_invoice_sheet()
        if not local_transfer_sheet or not local_invoice_sheet:
            return self.error_no_transfer_invoice_sheets_found(
                local_transfer_sheet, local_invoice_sheet, credit_wallet
            )
        return {'transfer': local_transfer_sheet, 'invoice': local_invoice_sheet}

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
            return self.error_no_credit_wallet_found()
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
        credit_ewallet = self.fetch_user_credit_wallet()
        contact_list = self.fetch_user_contact_list()
        values = {
            'id': self.user_id,
            'name': self.user_name,
            'create_date': res_utils.format_datetime(self.user_create_date),
            'write_date': res_utils.format_datetime(self.user_write_date),
            'ewallet': None if not credit_ewallet or
                isinstance(credit_ewallet, dict) and
                credit_ewallet.get('failed') else
                credit_ewallet.fetch_credit_ewallet_id(),
            'contact_list': None if not contact_list  or
                isinstance(contact_list, dict) and
                contact_list.get('failed') else
                contact_list.fetch_contact_list_id(),
            'email': self.user_email,
            'phone': self.user_phone,
            'alias': self.user_alias,
            'state': self.user_state_code,
            'ewallet_archive': {
                item.fetch_credit_ewallet_id(): item.fetch_credit_ewallet_reference()
                for item in self.user_credit_wallet_archive
            },
            'contact_list_archive': {
                item.fetch_contact_list_id(): item.fetch_contact_list_reference()
                for item in self.user_contact_list_archive
            },
            'to_unlink': self.to_unlink,
            'to_unlink_timestamp': None if not self.to_unlink_timestamp else
                res_utils.format_datetime(self.to_unlink_timestamp),
            'subordonate_of': None if not self.subordonate_of else
                self.subordonate_of.fetch_user_id(),
        }
        return values

    # SETTERS

    def set_master_account_id(self, master_id):
        log.debug('')
        try:
            self.master_account_id = master_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_master_account_id(
                master_id, self.master_asccount_id, e
            )
        log.info('Successfully set user master account ID.')
        return True

    def set_is_active(self, flag=True):
        log.debug('')
        try:
            self.is_active = flag
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_is_active_flag(
                flag, self.is_active, e
            )
        log.info('Successfully set user is active flag.')
        return True

    def set_user_email(self, email_address):
        log.debug('')
        try:
            self.user_email = email_address
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_email(
                email_address, self.user_email, e
            )
        log.info('Successfully set user email address.')
        return True

    def set_user_pass(self, password_hash):
        log.debug('')
        try:
            self.user_pass_hash = password_hash
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_pass_hash(
                password_hash, self.user_pass_hash, e
            )
        log.info('Successfully set user password.')
        return True

    def set_user_write_uid(self, uid):
        log.debug('')
        try:
            self.user_write_uid = uid
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_write_uid(
                uid, self.user_write_uid, e
            )
        log.info('Successfully set user write UID.')
        return True

    def set_user_create_uid(self, uid):
        log.debug('')
        try:
            self.user_create_uid = uid
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_create_uid(
                uid, self.user_create_uid, e
            )
        log.info('Successfully set user create UID.')
        return True

    def set_user_pass_hash(self, pass_hash):
        log.debug('')
        try:
            self.user_pass_hash = pass_hash
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_pass_hash(
                pass_hash, self.user_pass_hash, e
            )
        log.info('Successfully set user password hash.')
        return True

    def set_to_unlink(self, flag):
        log.debug('')
        try:
            self.to_unlink = flag
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_to_unlink_flag(
                flag, self.to_unlink, e
            )
        return True

    def set_to_unlink_timestamp(self, timestamp):
        log.debug('')
        try:
            self.to_unlink_timestamp = timestamp
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_to_unlink_timestamp(
                timestamp, self.to_unlink_timestamp, e
            )
        log.info('Successfully set user to unlink timestamp.')
        return True

    def set_user_contact_list(self, contact_list):
        log.debug('')
        try:
            self.user_contact_list = [contact_list]
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list(
                contact_list, self.user_contact_list, e
            )
        log.info('Successfully set user contact list.')
        return True

    def set_user_write_date(self, write_date):
        log.debug('')
        try:
            self.user_write_date = write_date
        except Exception as e:
            return self.error_could_not_set_write_date(
                write_date, self.user_write_date, e
            )
        log.info('Successfully set user write date.')
        return True

    def set_user_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('alias'):
            return self.error_no_user_alias_found(kwargs)
        try:
            self.user_alias = kwargs['alias']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_alias(
                kwargs, self.user_alias, e
            )
        log.info('Successfully set user alias.')
        return True

#   #@pysnooper.snoop('logs/ewallet.log')
    def set_user_state(self, state):
        log.debug('')
        if state not in [0, 1]:
            return self.error_invalid_user_account_state_code(state)
        try:
            self.user_state_code = state
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_state_code(
                state, self.user_state_code, e
            )
        log.info('Successfully set user state code.')
        return True

    def set_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('phone'):
            return self.no_user_phone_found(kwargs)
        try:
            self.user_phone = kwargs['phone']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_phone(
                kwargs, self.user_phone, e
            )
        log.info('Successfully set user phone.')
        return True

    def set_user_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('credit_ewallet'):
            return self.error_no_credit_wallet_found(kwargs)
        try:
            self.user_credit_wallet = kwargs['credit_ewallet']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_credit_ewallet(
                kwargs, self.user_credit_wallet, e
            )
        log.info('Successfully set user credit ewallet.')
        return True

    def set_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('name'):
            return self.error_no_user_name_found(kwargs)
        try:
            self.user_name = kwargs['name']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_name(
                kwargs, self.user_name, e
            )
        log.info('Successfully set user name.')
        return True

    def set_user_pass_hash_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_pass_hash_archive_found(kwargs)
        try:
            self.user_pass_hash_archive = kwargs['archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_pass_hash_archive(
                kwargs, self.user_pass_hash_archive, e
            )
        log.info('Successfully set user password hash archive.')
        return True

    def set_user_credit_wallet_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_credit_wallet_archive_found(kwargs)
        try:
            self.user_credit_wallet_archive = kwargs['archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_credit_ewallet_archive(
                kwargs, self.user_credit_wallet_archive, e
            )
        log.info('Successfully set user credit wallet archive.')
        return True

    def set_user_contact_list_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_contact_list_archive_found(kwargs)
        try:
            self.user_contact_list_archive = kwargs['archive']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_contact_list_archive(
                kwargs, self.user_contact_list_archive, e
            )
        log.info('Successfully set user contact list archive.')
        return True

    def set_to_credit_ewallet_archive(self, credit_ewallet):
        log.debug('')
        try:
            self.user_credit_wallet_archive.append(credit_ewallet)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_to_credit_ewallet_archive(
                credit_ewallet, self.user_credit_wallet_archive, e
            )
        log.info('Successfully updated user credit wallet archive.')
        return True

    def set_to_contact_list_archive(self, contact_list):
        log.debug('')
        try:
            self.user_contact_list_archive.append(contact_list)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_to_contact_list_archive(
                contact_list, self.user_contact_list_archive, e
            )
        log.info('Successfully updated user contact list archive.')
        return True

    # UPDATERS

    def update_user_credit_wallet_archive(self, credit_wallet):
        log.debug('')
        set_to = self.set_to_credit_ewallet_archive(credit_wallet)
        return set_to if not set_to or isinstance(set_to, dict) and \
            set_to.get('failed') else self.user_credit_wallet_archive

#   #@pysnooper.snoop('logs/ewallet.log')
    def update_user_contact_list_archive(self, contact_list):
        log.debug('')
        set_to = self.set_to_contact_list_archive(contact_list)
        return set_to if not set_to or isinstance(set_to, dict) and \
            set_to.get('failed') else self.user_contact_list_archive

    def update_write_date(self):
        log.debug('')
        self.set_user_write_date(datetime.datetime.now())
        return True

    # CHECKERS

    def check_contact_list_belongs_to_user(self, contact_list):
        log.debug('')
        return False if contact_list not in self.user_contact_list_archive \
            else True

    def check_credit_ewallet_belongs_to_user(self, ewallet):
        log.debug('')
        return False if ewallet not in self.user_credit_wallet_archive \
            else True

#   @pysnooper.snoop('logs/ewallet.log')
    def check_user_logged_in(self):
        log.debug('')
        account_state = self.fetch_user_state()
        return False if account_state == 0 else True

    def check_user_logged_out(self):
        log.debug('')
        account_state = self.fetch_user_state()
        return False if account_state == 1 else True

    # CONVERTORS

    def convert_user_state_name_to_code(self, **kwargs):
        log.debug('')
        if not kwargs.get('name'):
            return self.error_no_state_name_found()
        return self.fetch_user_state_code_map()['name'].get(kwargs['name'])

#   #@pysnooper.snoop('logs/ewallet.log')
    def convert_user_state_code_to_name(self, **kwargs):
        log.debug('')
        if kwargs.get('state_code') not in [0, 1]:
            return self.error_no_state_code_found()
        return self.fetch_user_state_code_map()['code'].get(
                kwargs['state_code']
                )

    # CREATORS

    # TODO
    def create_user_pass_hash_record(self, **kwargs):
        log.debug('TODO - Receive creation values')
        if not kwargs.get('pass_hash'):
            return self.error_no_user_pass_hash_found()
        pass_hash_record = ResUserPassHashArchive(
            user_id=kwargs.get('user_id') or self.fetch_user_id(),
            user_pass_hash=kwargs['pass_hash'],
        )
        return pass_hash_record

#   @pysnooper.snoop('logs/ewallet.log')
    def create_credit_ewallet(self, creation_values, **kwargs):
        log.debug('')
        try:
            new_credit_ewallet = CreditEWallet(
                active_session=kwargs['active_session'], **creation_values
            )
        except:
            return self.error_could_not_create_new_credit_ewallet(creation_values)
        return new_credit_ewallet

    def create_transaction_handler(self, creation_values):
        log.debug('')
        try:
            transaction_handler = EWalletTransactionHandler(**creation_values)
        except:
            return self.error_could_not_create_new_transaction_handler(creation_values)
        return transaction_handler

    # GENERAL

    def freeze_user_account(self):
        log.debug('')
        set_inactive = self.set_is_active(flag=False)
        if not set_inactive or isinstance(set_inactive, dict) and \
                set_inactive.get('failed'):
            return self.error_could_not_freeze_user_account(
                set_inactive, self.is_active
            )
        return True

    def unfreeze_user_account(self):
        log.debug('')
        set_active = self.set_is_active(flag=True)
        if not set_active or isinstance(set_active, dict) and \
                set_active.get('failed'):
            return self.error_could_not_freeze_user_account(
                set_active, self.is_active
            )
        return True

    def link_journal_records_for_transaction(self, **kwargs):
        log.debug('')
        if not kwargs.get('invoice_record') or \
                not kwargs.get('transfer_record'):
            return self.error_invalid_data_set_for_journal_record_link(kwargs)
        invoice_data = kwargs['invoice_record'].fetch_record_values()
        transfer_data = kwargs['transfer_record'].fetch_record_values()
        if invoice_data.get('transfer_record'):
            return self.warning_invoice_record_already_linked(
                kwargs, invoice_data, transfer_data
            )
        kwargs['invoice_record'].set_transfer_record_id(transfer_data['id'])
        return True

    # UNLINKERS

    def unlink_credit_ewallet(self, ewallet_id, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session') or \
            self.fetch_user_active_session(stype='orm')
        try:
            active_session.query(
                CreditEWallet
            ).filter_by(
                wallet_id=ewallet_id
            ).delete()
            kwargs['active_session'].commit()
        except:
            return self.error_could_not_unlink_credit_ewallet(
                kwargs, active_session
            )
        log.info('Successfully unlinked credit ewallet.')
        return ewallet_id

    def unlink_contact_list(self, list_id, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session') or \
            self.fetch_user_active_session(stype='orm')
        try:
            active_session.query(
                ContactList
            ).filter_by(
                contact_list_id=list_id
            ).delete()
            kwargs['active_session'].commit()
        except:
            return self.error_could_not_unlink_contact_list(
                kwargs, active_session
            )
        log.info('Successfully unlinked contact list.')
        return list_id

    # EVENTS

#   @pysnooper.snoop('logs/ewallet.log')
    def event_request_credits(self, **kwargs):
        '''
        [ NOTE   ]: User event Request Credit. Creates transaction
                    between 2 credit wallets along with transaction records
                    (transfer record & invoice record). Shares records with
                    partner.
        [ INPUT  ]: partner_account=<account>
        [ RETURN ]: ({'extract': <count>, 'supply': <count>} | False)
        '''
        log.debug('')
        if not kwargs.get('partner_account'):
            return self.error_no_partner_account_found(kwargs)
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_session(stype='orm')
        if not active_session:
            return self.error_could_not_fetch_active_orm_session()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'active_session'
        )
        creation_values = self.fetch_transaction_handler_creation_values_for_event_request_credits(
            active_session=active_session,
            **sanitized_command_chain
        )
        transaction_handler = self.create_transaction_handler(creation_values)
        transaction = transaction_handler.action_init_transaction(
            active_session=active_session, **sanitized_command_chain
        )
        link = self.link_journal_records_for_transaction(**transaction)
        if not link or isinstance(link, dict) and link.get('failed'):
            self.warning_could_not_link_journal_records_for_credit_request_event(
                kwargs, active_session, creation_values, transaction_handler,
                transaction, link
            )
        return transaction

    # ACTIONS

    def action_cleanup_credit_ewallet(self, **kwargs):
        '''
        [ NOTE ]: Cleans all user ewallets, clocks and sheets.
        '''
        log.debug('')
        ewallet_archive = self.fetch_user_credit_wallet_archive()
        command_chain_response = {
            'failed': False,
            'user_id': self.fetch_user_id(),
        }
        ewallets_cleaned, cleanup_failures = 0, 0
        if not ewallet_archive:
            command_chain_response.update({
                'ewallets_cleaned': ewallets_cleaned,
                'cleanup_failures': cleanup_failures,
            })
            return command_chain_response
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'cleanup'
        )
        for ewallet in ewallet_archive:
            cleanup_ewallet = ewallet.main_controller(
                controller='user', action='cleanup', cleanup='ewallet',
                **sanitized_command_chain,
            )
            try:
                self.unlink_credit_ewallet(
                    ewallet.fetch_credit_ewallet_id(), **kwargs
                )
            except Exception as e:
                cleanup_failures += 1
                self.warning_could_not_delete_credit_ewallet(
                    ewallet, kwargs, ewallet_archive, ewallets_cleaned,
                    cleanup_failures, e
                )
                continue
            ewallets_cleaned += 1
        command_chain_response.update({
            'ewallets_cleaned': ewallets_cleaned,
            'cleanup_failures': cleanup_failures,
        })
        return self.error_no_user_credit_ewallets_cleaned(
            kwargs, ewallet_archive, ewallets_cleaned, cleanup_failures
        ) if not ewallets_cleaned else command_chain_response

    def action_unlink_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_contact_list_id_found(kwargs)
        contact_list = self.fetch_user_contact_list_by_id(
            kwargs['list_id'], kwargs['active_session']
        )
        if isinstance(contact_list, dict) and \
                contact_list.get('failed'):
            return self.error_could_not_fetch_contact_list(
                kwargs, contact_list
            )
        check = self.check_contact_list_belongs_to_user(contact_list)
        if not check:
            return self.warning_contact_list_does_not_belong_to_user(
                kwargs, contact_list, check
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action', 'cleanup'
        )
        cleanup_list = contact_list.contact_list_controller(
            action='cleanup', cleanup='records', **sanitized_command_chain,
        )
        unlink = self.unlink_contact_list(
            kwargs['list_id'], active_session=kwargs['active_session']
        )
        if isinstance(unlink, dict) and unlink.get('failed'):
            return self.error_could_not_unlink_contact_list(
                kwargs, contact_list, check, unlink
            )
        log.info('Successfully removed user contact list.')
        return kwargs['list_id']

    def action_cleanup_contact_list(self, **kwargs):
        '''
        [ NOTE ]: Cleans all user contact lists and records.
        '''
        log.debug('')
        contact_list_archive = self.fetch_user_contact_list_archive()
        command_chain_response = {
            'failed': False,
            'user_id': self.fetch_user_id(),
        }
        lists_cleaned, cleanup_failures = 0, 0
        if not contact_list_archive:
            command_chain_response.update({
                'lists_cleaned': lists_cleaned,
                'cleanup_failures': cleanup_failures,
            })
            return command_chain_response
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'action', 'cleanup'
        )
        for contact_list in contact_list_archive:
            cleanup_list = contact_list.contact_list_controller(
                action='cleanup', cleanup='records', **sanitized_command_chain,
            )
            try:
                self.unlink_contact_list(
                    contact_list.fetch_contact_list_id(), **kwargs
                )
            except Exception as e:
                cleanup_failures += 1
                self.warning_could_not_delete_contact_list(
                    contact_list, kwargs, contact_list_archive, lists_cleaned,
                    cleanup_failures, e
                )
                continue
            lists_cleaned += 1
        command_chain_response.update({
            'lists_cleaned': lists_cleaned,
            'cleanup_failures': cleanup_failures,
        })
        return self.error_no_user_contact_lists_cleaned(
            kwargs, contact_list_archive, lists_cleaned, cleanup_failures
        ) if not lists_cleaned else command_chain_response

#   @pysnooper.snoop('logs/ewallet.log')
    def action_pay_partner_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('pay'):
            return self.error_no_user_action_pay_target_partner_account_found()
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_session(stype='orm')
        if not active_session:
            return self.error_could_not_fetch_active_orm_session(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'active_session'
        )
        creation_values = self.fetch_transaction_handler_creation_values_for_action_pay(
            active_session=active_session, **sanitized_command_chain
        )
        transaction_handler = self.create_transaction_handler(creation_values)
        transaction = transaction_handler.action_init_transaction(
            active_session=active_session, **sanitized_command_chain
        )
        return transaction

#   @pysnooper.snoop('logs/ewallet.log')
    def action_edit_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email') or not kwargs.get('email_check_func'):
            return self.error_handler_set_user_email(
                email=kwargs.get('user_email'),
                email_check_func=kwargs.get('email_check_func'),
            )
        log.info('Performing user email validation checks...')
        check = kwargs['email_check_func'](kwargs['user_email'], severity=1)
        if not check:
            return self.error_invalid_user_email(
                kwargs, check
            )
        log.info('User email validated.')
        set_email = self.set_user_email(kwargs['user_email'])
        if not set_email or isinstance(set_email, dict) and \
                set_email.get('failed'):
            return self.error_could_not_edit_user_email(
                kwargs, check, set_email
            )
        return {
            'failed': False,
            'user_email': set_email,
        }

    def action_edit_user_pass(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_pass') or not kwargs.get('pass_check_func') \
                or not kwargs.get('pass_hash_func'):
            return self.error_handler_set_user_pass(
                password=kwargs.get('user_pass'),
                pass_check_func=kwargs.get('pass_check_func'),
                pass_hash_func=kwargs.get('pass_hash_func'),
            )
        log.info('Performing user password checks...')
        check = kwargs['pass_check_func'](kwargs['user_pass'])
        if not check:
            return self.error_invalid_user_pass(kwargs, check)
        log.info('Password coresponds with security standards. Hashing...')
        pass_hash = kwargs['pass_hash_func'](kwargs['user_pass'])
        hash_record = self.create_user_pass_hash_record(
            pass_hash=pass_hash, **kwargs
        )
        set_pass = self.set_user_pass(pass_hash)
        if not set_pass or isinstance(set_pass, dict) and \
                set_pass.get('failed'):
            kwargs['active_session'].rollback()
            return self.error_could_not_edit_user_pass(
                kwargs, check, pass_hash, hash_record, set_pass
            )
        kwargs['active_session'].commit()
        return {
            'failed': False,
            'user_pass': set_pass
        }

    def action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_credit_clock_id_found(kwargs)
        log.info('Attempting to fetch user credit ewallet...')
        credit_ewallet = self.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_user_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'unlink',
        )
        unlink = credit_ewallet.main_controller(
            controller='user', action='unlink', unlink='clock',
            **sanitized_command_chain
        )
        if not unlink or isinstance(unlink, dict) and \
                unlink.get('failed'):
            return self.error_could_not_unlink_credit_clock(
                kwargs, credit_ewallet, unlink
            )
        log.info('Successfully unlinked ewallet credit clock.')
        return unlink

    def action_unlink_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet_id'):
            return self.error_no_ewallet_id_found(kwargs)
        ewallet = self.fetch_user_credit_ewallet_by_id(
            kwargs['ewallet_id'],
            active_session=kwargs['active_session'],
        )
        check = self.check_credit_ewallet_belongs_to_user(ewallet)
        if not check:
            return self.warning_credit_ewallet_does_not_belong_to_current_user(
                kwargs, ewallet, check
            )
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'cleanup',
        )
        cleanup_ewallet = ewallet.main_controller(
            controller='user', action='cleanup', cleanup='ewallet',
            **sanitized_command_chain,
        )
        try:
            kwargs['active_session'].query(
                CreditEWallet
            ).filter_by(
                wallet_id=kwargs['ewallet_id']
            ).delete()
        except Exception as e:
            return self.error_could_not_unlink_credit_ewallet(kwargs, e)
        log.info('Successfully removed user credit ewallet.')
        return kwargs['ewallet_id']

    def action_switch_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('list_id'):
            return self.error_no_contact_list_id_found()
        log.info('Attempting to fetch user contact list...')
        contact_list = self.fetch_user_contact_list_by_id(
            kwargs['list_id'], kwargs['active_session']
        )
        if not contact_list or isinstance(contact_list, dict) and \
                contact_list.get('failed'):
            return self.warning_could_not_fetch_contact_list(
                kwargs, contact_list
            )
        check = self.check_contact_list_belongs_to_user(contact_list)
        if not check:
            return self.warning_contact_list_does_not_belong_to_user(
                kwargs, contact_list, check
            )
        switch = self.set_user_contact_list(contact_list)
        if not switch or isinstance(switch, dict) and \
                switch.get('failed'):
            return self.error_could_not_switch_contact_list(
                kwargs, contact_list, check, switch
            )
        log.info('Successfully switched user contact list.')
        return contact_list

    def action_switch_time_sheet(self, **kwargs):
        log.debug('')
        log.info('Attempting to fetch user credit ewallet...')
        credit_ewallet = self.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_user_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet', 'identifier'
        )
        switch = credit_ewallet.main_controller(
            controller='user', action='switch_sheet', sheet='time',
            **sanitized_command_chain
        )
        if not switch or isinstance(switch, dict) and \
                switch.get('failed'):
            return self.warning_could_not_switch_time_sheet(
                kwargs, credit_ewallet, switch
            )
        log.info('Successfully switched credit clock time sheet.')
        return switch

    def action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        log.info('Attempting to fetch user credit ewallet...')
        credit_ewallet = self.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_user_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet', 'identifier'
        )
        switch = credit_ewallet.main_controller(
            controller='user', action='switch_sheet', sheet='conversion',
            **sanitized_command_chain
        )
        if not switch or isinstance(switch, dict) and switch.get('failed'):
            return self.warning_could_not_switch_conversion_sheet(
                kwargs, credit_ewallet, switch
            )
        log.info('Successfully switched credit clock conversion sheet.')
        return switch

    def action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_invoice_sheet_id_specified(kwargs)
        log.info('Attempting to fetch user credit ewallet...')
        credit_ewallet = self.fetch_user_credit_wallet()
        if not credit_ewallet:
            return self.error_could_not_fetch_user_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet', 'identifier'
        )
        switch = credit_ewallet.main_controller(
            controller='user', action='switch_sheet', sheet='invoice',
            **sanitized_command_chain
        )
        if not switch or isinstance(switch, dict) and \
                switch.get('failed'):
            return self.warning_could_not_switch_invoice_sheet(
                kwargs, credit_ewallet, switch
            )
        log.info('Successfully switched credit ewallet invoice sheet.')
        return switch

    def action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        if not kwargs.get('sheet_id'):
            return self.error_no_transfer_sheet_id_found(kwargs)
        log.info('Attempting to fetch user credit ewallet...')
        credit_ewallet = self.fetch_user_credit_wallet()
        if not credit_ewallet or isinstance(credit_ewallet, dict) and \
                credit_ewallet.get('failed'):
            return self.error_could_not_fetch_user_credit_ewallet(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action', 'sheet', 'identifier'
        )
        switch = credit_ewallet.main_controller(
            controller='user', action='switch_sheet', sheet='transfer',
            **sanitized_command_chain
        )
        if not switch or isinstance(switch, dict) and \
                switch.get('failed'):
            return self.warning_could_not_switch_transfer_sheet(
                kwargs, credit_ewallet, switch
            )
        log.info('Successfully switched credit ewallet transfer sheet.')
        return switch

    def action_switch_credit_clock(self, **kwargs):
        log.debug('')
        if not kwargs.get('clock_id'):
            return self.error_no_clock_id_found()
        credit_wallet = self.fetch_user_credit_wallet()
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'controller', 'action'
        )
        clock_switch = credit_wallet.main_controller(
            controller='user', action='switch_clock',
            **sanitized_command_chain
        )
        if not clock_switch or isinstance(clock_switch, dict) and \
                clock_switch.get('failed'):
            return self.warning_could_not_switch_credit_clock(
                kwargs, credit_wallet, clock_switch
            )
        log.info('Successfully switched user credit clock.')
        return clock_switch

    def action_switch_credit_wallet(self, **kwargs):
        log.debug('')
        if not kwargs.get('ewallet_id'):
            return self.error_no_wallet_id_found()
        log.info('Attempting to fetch user credit ewallet...')
        ewallet = self.fetch_user_credit_ewallet_by_id(kwargs['ewallet_id'])
        if not ewallet or isinstance(ewallet, dict) and ewallet.get('failed'):
            return self.warning_could_not_fetch_credit_wallet(
                kwargs, ewallet
            )
        check = self.check_credit_ewallet_belongs_to_user(ewallet)
        if not check:
            return self.warning_credit_ewallet_does_not_belong_to_current_user(
                kwargs, ewallet
            )
        switch = self.set_user_credit_wallet(credit_ewallet=ewallet)
        if switch:
            log.info('Successfully switched credit ewallet by id.')
        return ewallet

    def action_create_credit_clock(self, **kwargs):
        log.debug('')
        credit_wallet = self.fetch_user_credit_wallet()
        if not credit_wallet or isinstance(credit_wallet, dict) and \
                credit_wallet.get('failed'):
            return self.error_could_not_fetch_user_credit_wallet(kwargs)
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_session(stype='orm')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'active_session', 'controller', 'action'
        )
        new_credit_clock = credit_wallet.main_controller(
            controller='system', action='create_clock',
            active_session=active_session, **sanitized_command_chain
        )
        log.info('Successfully created new user credit clock.')
        return new_credit_clock

#   @pysnooper.snoop('logs/ewallet.log')
    def action_create_credit_wallet(self, **kwargs):
        log.debug('')
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_session(stype='orm')
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'active_session'
        )
        creation_values = self.fetch_credit_ewallet_creation_values(**kwargs)
        new_credit_wallet = self.create_credit_ewallet(
            creation_values, active_session=active_session,
            **sanitized_command_chain
        )
        active_session.add(new_credit_wallet)
        update_archive = self.update_user_credit_wallet_archive(
            new_credit_wallet
        )
        return new_credit_wallet

#   @pysnooper.snoop()
    def action_transfer_credits_to_partner_account(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_to'):
            return self.error_no_user_action_transfer_credits_target_partner_account_specified(
                kwargs
            )
        active_session = kwargs.get('active_session') or \
                self.fetch_user_active_session(stype='orm')
        if not active_session or isinstance(active_session, dict) and \
                active_session.get('failed'):
            return self.error_could_not_fetch_active_orm_session(kwargs)
        sanitized_command_chain = res_utils.remove_tags_from_command_chain(
            kwargs, 'active_session'
        )
        creation_values = self.fetch_transaction_handler_creation_values_for_action_transfer(
            active_session=active_session, **sanitized_command_chain
        )
        transaction_handler = self.create_transaction_handler(creation_values)
        transaction = transaction_handler.action_init_transaction(**sanitized_command_chain)
        return transaction

    def action_edit_user_name(self, **kwargs):
        log.debug('')
        set_user_name = self.set_user_name(name=kwargs['user_name'])
        return self.error_could_not_edit_user_name(kwargs) \
            if not set_user_name else {
                'failed': False,
                'user_name': set_user_name
            }

    def action_edit_user_alias(self, **kwargs):
        log.debug('')
        set_user_alias = self.set_user_alias(alias=kwargs['user_alias'])
        return self.error_could_not_edit_user_alias(kwargs) \
            if not set_user_alias else {
                'failed': False,
                'user_alias': set_user_alias,
            }

    def action_edit_user_phone(self, **kwargs):
        log.debug('')
        set_user_phone = self.set_user_phone(phone=kwargs['user_phone'])
        return self.error_could_not_edit_user_phone(kwargs) \
            if not set_user_phone else {
                'failed': False,
                'user_phone': set_user_phone,
            }

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

    # HANDLERS

    # TODO
    def handle_user_event_notification(self, **kwargs):
        pass
    def handle_user_event_signal(self, **kwargs):
        pass

    # TODO
    def handle_user_action_cleanup_account(self, **kwargs):
        log.debug('TODO - Cleanup all relationships')
        cleanup = {
            'cleanup_contact_list': self.action_cleanup_contact_list(**kwargs),
            'cleanup_ewallet': self.action_cleanup_credit_ewallet(**kwargs),
#           'cleanup_pass_hash':,
#           'cleanup_login_records':,
#           'cleanup_logout_records':,
        }
        return cleanup


    def handle_user_action_cleanup(self, **kwargs):
        log.debug('')
        if not kwargs.get('cleanup'):
            return self.error_no_user_action_cleanup_target_specified(kwargs)
        handlers = {
            'account': self.handle_user_action_cleanup_account,
        }
        return handlers[kwargs['cleanup']](**kwargs)

    def handle_user_action_edit(self, **kwargs):
        log.debug('')
        if not kwargs.get('edit'):
            return self.error_no_user_action_edit_target_specified(kwargs)
        handlers = {
            'user_name': self.handle_user_action_edit_name,
            'user_pass': self.handle_user_action_edit_pass,
            'user_alias': self.handle_user_action_edit_alias,
            'user_email': self.handle_user_action_edit_email,
            'user_phone': self.handle_user_action_edit_phone,
        }
        return handlers[kwargs['edit']](**kwargs)

    def handle_user_action_edit_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name'):
            return self.error_no_user_name_specified_for_user_action_edit(kwargs)
        edit_user_name = self.action_edit_user_name(**kwargs)
        return edit_user_name

    def handle_user_action_edit_pass(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_pass'):
            return self.error_no_user_pass_specified_for_user_action_edit(kwargs)
        edit_user_pass = self.action_edit_user_pass(**kwargs)
        return edit_user_pass

    def handle_user_action_edit_alias(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_alias'):
            return self.error_no_user_alias_specified_for_user_action_edit(kwargs)
        edit_user_alias = self.action_edit_user_alias(**kwargs)
        return edit_user_alias

    def handle_user_action_edit_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email'):
            return self.error_no_user_email_specified_for_user_action_edit(kwargs)
        edit_user_email = self.action_edit_user_email(**kwargs)
        return edit_user_email

    def handle_user_action_edit_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_phone'):
            return self.error_no_user_phone_specified_for_user_action_edit(kwargs)
        edit_user_phone = self.action_edit_user_phone(**kwargs)
        return edit_user_phone

    def handle_user_action_transfer(self, **kwargs):
        log.debug('')
        if not kwargs.get('ttype'):
            return self.error_no_user_action_transfer_type_specified(kwargs)
        handlers = {
            'payment': self.action_pay_partner_account,
            'transfer': self.action_transfer_credits_to_partner_account,
        }
        return handlers[kwargs['ttype']](**kwargs)

    def handle_user_action_create(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_create_target_specified()
        handlers = {
            'credit_wallet': self.action_create_credit_wallet,
            'credit_clock': self.action_create_credit_clock,
            'contact_list': self.action_create_contact_list,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_action_reset_field(self, **kwargs):
        log.debug('')
        if not kwargs.get('field'):
            return self.error_no_user_action_reset_field_target_specified()
        handlers = {
            'user_name': self.set_user_name,
            'user_pass': self.set_user_pass,
            'user_credit_wallet': self.set_user_credit_wallet,
            'user_contact_list': self.set_user_contact_list,
            'user_email': self.set_user_email,
            'user_phone': self.set_user_phone,
            'user_alias': self.set_user_alias,
        }
        return handlers[kwargs['field']](**kwargs)

    def handle_action_reset_archive(self, **kwargs):
        log.debug('')
        if not kwargs.get('archive'):
            return self.error_no_user_action_reset_archive_target_specified()
        handlers = {
            'password': self.set_user_pass_hash_archive,
            'credit_wallet': self.set_user_credit_wallet_archive,
            'contact_list': self.set_user_contact_list_archive,
        }
        return handlers[kwargs['archive']](kwargs.get('value'))

    def handle_user_action_reset(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_reset_target_specified()
        handlers = {
            'field': self.handle_action_reset_field,
            'archive': self.handle_action_reset_archive,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_user_action_switch(self, **kwargs):
        log.debug('')
        if not kwargs.get('target'):
            return self.error_no_user_action_switch_target_specified()
        handlers = {
            'credit_wallet': self.action_switch_credit_wallet,
            'credit_clock': self.action_switch_credit_clock,
            'contact_list': self.action_switch_contact_list,
            'transfer_sheet': self.action_switch_transfer_sheet,
            'invoice_sheet': self.action_switch_invoice_sheet,
            'conversion_sheet': self.action_switch_conversion_sheet,
            'time_sheet': self.action_switch_time_sheet,
        }
        return handlers[kwargs['target']](**kwargs)

    def handle_user_action_unlink(self, **kwargs):
        log.debug('')
        if not kwargs.get('unlink'):
            return self.error_no_user_action_unlink_target_specified()
        handlers = {
            'credit_wallet': self.action_unlink_credit_wallet,
            'credit_clock': self.action_unlink_credit_clock,
            'contact_list': self.action_unlink_contact_list,
        }
        return handlers[kwargs['unlink']](**kwargs)

    def handle_user_event_request(self, **kwargs):
        log.debug('')
        if not kwargs.get('request'):
            return self.error_no_user_event_request_specified()
        handlers = {
            'credits': self.event_request_credits,
        }
        return handlers[kwargs['request']](**kwargs)

    # CONTROLLERS

    def user_action_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_user_controller_action_specified()
        handlers = {
            'create': self.handle_user_action_create,
            'reset': self.handle_user_action_reset,
            'switch': self.handle_user_action_switch,
            'unlink': self.handle_user_action_unlink,
            'transfer': self.handle_user_action_transfer,
            'edit': self.handle_user_action_edit,
            'cleanup': self.handle_user_action_cleanup,
        }
        return handlers[kwargs['action']](**kwargs)

    def user_event_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('event'):
            return self.error_no_user_controller_event_specified()
        handlers = {
            'request': self.handle_user_event_request,
            'notification': self.handle_user_event_notification,
            'signal': self.handle_user_event_signal,
        }
        return handlers[kwargs['event']](**kwargs)

    def user_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('ctype'):
            return self.error_no_user_controller_type_specified()
        controllers = {
            'action': self.user_action_controller,
            'event': self.user_event_controller,
        }
        return controllers[kwargs['ctype']](**kwargs)

    # WARNINGS
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def warning_could_not_delete_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not delete credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_delete_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not delete contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_link_journal_records_for_credit_request_event(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not link journal records for credit request event. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_invoice_record_already_linked(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Invoice record already linked to a transfer record. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_credit_ewallet_found_by_id(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'No credit ewallet found by id. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_contact_list_does_not_belong_to_user(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Contact list does not belong to active user. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not fetch contact list. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_time_sheet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not switch time sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_conversion_sheet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not switch conversion sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_invoice_sheet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not switch invoice sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_transfer_sheet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not switch transfer sheet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_switch_credit_clock(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not switch credit clock. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_credit_ewallet_does_not_belong_to_current_user(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Credit ewallet does not belong to current user. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_could_not_fetch_credit_wallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'Something went wrong. '
                       'Could not fetch credit ewallet. '
                       'Details: {}'.format(args),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_no_contact_list_found_by_id(self, list_id, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'warning': 'No contact list found by id {}. Command chain details : {}'\
                       .format(list_id, command_chain),
        }
        log.warning(command_chain_response['warning'])
        return command_chain_response

    def warning_credit_transaction_record_share_failure(self, **kwargs):
        log.warning(
                'Something went wrong. Could not share credit wallet transaction related records. '\
                'Details : {}'.format(kwargs)
                )
        return False

    def warning_could_not_create_credit_wallet_supply_transaction_record(self, **kwargs):
        log.warning(
                'Something went wrong. Could not create credit wallet supply transaction records. '\
                'Details : {}'.format(kwargs)
                )
        return False

    def warning_credit_transaction_chain_failure(self, **kwargs):
        log.warning('Credit transaction chain failure. Details : {}'.format(kwargs))
        return False

    def warning_could_not_exract_user_account_credit_wallet_credits(self, instruction_set):
        log.warning(
                'Something went wrong. Could not extract credits from credit wallet {}. '\
                'Details : {}'.format(instruction_set['credit_wallet'], instruction_set)
                )
        return False

    def warning_could_not_supply_user_account_credit_wallet_with_credits(self, instruction_set):
        log.warning(
                'Something went wrong. Could not supply user credit wallet {} with credits. '\
                'Details : {}'.format(instruction_set['credit_wallet'], instruction_set)
                )
        return False

    def warning_could_not_fetch_partner_credit_wallet(self, partner_name):
        log.warning(
            'Something went wrong. Could not fetch credit wallet for partner {}.'\
            .format(partner_name)
        )
        return False

    def warning_could_not_fetch_credit_clock(self):
        log.warning(
                'Something went wrong. '
                'Could not fetch credit clock.'
                )
        return False

    # ERRORS
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_no_user_credit_ewallets_cleaned(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No credit ewallets cleaned. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])

    def error_could_not_unlink_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not unlink credit ewallet. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])

    def error_no_user_contact_lists_cleaned(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user contact lists cleaned. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])

    def error_no_user_action_cleanup_target_specified(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user action cleanup target specified. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])

    def error_could_not_set_user_master_account_id(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set Master account ID. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_email_check_function_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'No email address check function found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_password_check_function_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'No password check function found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_is_active_flag(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user is active flag. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_freeze_user_account(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not freeze user account. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_partner_account_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No partner account found. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_data_set_for_journal_record_link(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Invalid data set for journal record link. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_email(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user email address. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_user_email(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Invalid user email. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_pass_hash(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user password hash. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_edit_user_pass(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not edit user password. '
                     'Details: {}'.format(args)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_user_pass(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Invalid user password. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not unlink credit ewallet. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_credit_clock(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not unlink credit clock. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_unlink_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not unlink contact list. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not fetch contact list. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_switch_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not switch contact list. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_user_account_state_code(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Invalid user account state code. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_pass_hash(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user password hash. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_create_uid(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user create user id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_write_uid(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user write user id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_to_unlink_flag(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user to unlink flag. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_to_unlink_timestamp(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user to unlink timestamp. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_to_credit_ewallet_archive(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user credit ewallet to archive. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_to_contact_list_archive(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user contact list to archive. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_contact_list_archive(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user contact list archive. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_contact_list_archive_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user contact list archive found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_credit_ewallet_archive(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user credit ewallet archive. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_credit_wallet_archive_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user credit ewallet archive found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_pass_hash_archive(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user password hash archive. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_pass_hash_archive_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user password hash archive found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_name(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user name. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_name_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user name found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_credit_ewallet(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user credit ewallet. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_wallet_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No credit ewallet found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_phone(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user phone. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_phone_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user phone found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_set_by_parameter_specified(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No set by parameter specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_state_name(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user state label. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_state_name_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user state label found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_state_code_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user state code found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_user_state_code(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Invalid user state code. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_state_code(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user state code. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_alias(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set user alias. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_alias_found(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user alias found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_write_date(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list(self, *args):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. '
                     'Could not set contact list. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_active_orm_session(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not fetch active orm session. '
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_view_login_records(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not view user account login records. '
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_view_target_specified(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user action view target specified. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_credit_clock_id_found(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No ewallet credit clock id found. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_ewallet_id_found(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No ewallet id found. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_contact_list_found(self):
        log.error('No user contact list found.')
        return False

    def error_no_contact_list_id_found(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No contact list id found. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_invoice_sheet_id_specified(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No invoice sheet id specified. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_transfer_sheet_id_found(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No transfer sheet id found. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_credit_ewallet(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Could not fetch active user credit ewallet. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_user_credit_wallet(self, command_chain):
        command_chain_reply = {
            'failed': True, 'level': 'res-user',
            'error': 'Could not fetch user credit wallet. Command chain details : {}'
                     .format(command_chain),
        }
        log.error(command_chain_reply['error'])
        return command_chain_reply

    def error_could_not_create_new_transaction_handler(self, creation_values):
        command_chain_reply = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not create new transaction handler with creation values {}.'
                     .format(creation_values),
        }
        log.error(command_chain_reply['error'])
        return command_chain_reply

    def error_could_not_create_new_credit_ewallet(self, creation_values):
        command_chain_reply = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not create new credit ewallet with creation values {}.'
                     .format(creation_values),
        }
        log.error(command_chain_reply['error'])
        return command_chain_reply

    def error_could_not_edit_user_name(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not edit user name. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_edit_user_alias(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not edit user alias. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_edit_user_email(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not edit user email. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_edit_user_phone(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'Something went wrong. Could not edit user phone. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_name_specified_for_user_action_edit(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user name specified for user action edit. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_pass_specified_for_user_action_edit(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user pass specified for user action edit. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_alias_specified_for_user_action_edit(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user alias specified for user action edit. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_email_specified_for_user_action_edit(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user email specified for user action edit. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_phone_specified_for_user_action_edit(self, command_chain):
        command_chain_response = {
            'failed': True, 'level': 'res-user',
            'error': 'No user phone specified for user action edit. Command chain details : {}'
                     .format(command_chain)
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_action_transfer_credits_target_partner_account_specified(self, command_chain):
        log.error(
            'No user action transfer credits target partner account specified. Detauls : {}'
            .format(command_chain)
        )
        return False

    def error_no_credit_wallet_transaction_type_specified(self):
        log.error('No credit wallet transaction type specified.')
        return False

    def error_no_user_action_pay_target_partner_account_found(self):
        log.error('No user action pay target partner account found.')
        return False

    def error_no_active_ewallet_user_session_found(self):
        log.error('No active EWallet user session found.')
        return False

    def error_no_session_type_specified(self, session_type):
        log.error(
            'No session type specified. Got {} type {} instead.'.format(
                str(session_type), type(session_type)
            )
        )
        return False

    def error_no_ewallet_session_found(self):
        log.error('No EWallet session found for user {}.'.format(self.fetch_user_id()))
        return False

    def error_no_ewallet_orm_session_found(self, ewallet_session):
        log.error(
            'No EWallet ORM session found for EWallet session {}.'.format(
                ewallet_session.fetch_active_session_id()
            )
        )
        return False

    def error_no_user_action_transfer_type_specified(self, command_chain):
        log.error(
            'No user action transfer type specified. Details : {}'.format(command_chain)
            )
        return False

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

    def error_could_not_fetch_remote_transfer_sheet(self):
        log.error('Something went wrong. Could not fetch remote transfer sheet.')
        return False

    def error_no_transfer_invoice_sheets_found(self, transfer_sheet, invoice_sheet, credit_wallet):
        log.error(
                'No transfer sheet or invoice sheet found for credit wallet {}. '\
                'Details : {}'.format(credit_wallet, {'transfer_sheet': transfer_sheet, 'invoice_sheet': invoice_sheet})
                )
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

    def error_no_clock_id_found(self):
        log.error('No clock id found.')
        return False

    def error_no_contact_list_found(self):
        log.error('No contact list found.')
        return False

    def error_no_contact_list_found(self):
        log.error('No contact list found.')
        return False

    def error_no_user_email_found(self):
        log.error('No user email found.')
        return False

    def error_no_password_found(self):
        log.error('No password found.')
        return False

    def error_no_password_hash_function_found(self):
        log.error('No password hash function found.')
        return False

    def error_no_user_pass_hash_found(self):
        log.error('No user password hash found.')
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

    def error_no_user_pass_hash_found(self):
        log.error('No user pass hash found.')
        return False

    def error_no_active_session_found(self):
        log.error('No active session found.')
        return False

    def error_no_user_event_request_specified(self):
        log.error('No user event request specified.')
        return False



###############################################################################
# CODE DUMP
###############################################################################

