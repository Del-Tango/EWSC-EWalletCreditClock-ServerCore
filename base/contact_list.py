import datetime
import pysnooper
import logging
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .config import Config
from .res_utils import ResUtils, Base

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


class ContactListRecord(Base):
    __tablename__ = 'contact_list_record'

    record_id = Column(Integer, primary_key=True)
    contact_list_id = Column(
        Integer, ForeignKey('contact_list.contact_list_id')
    )
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    user_id = Column(Integer, ForeignKey('res_user.user_id'))
    user_name = Column(String)
    user_email = Column(String)
    user_phone = Column(String)
    notes = Column(String)
    reference = Column(String)

    def __init__(self, **kwargs):
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.contact_list_id = kwargs.get('contact_list_id', int())
        self.user_id = kwargs.get('user_id', int())
        self.user_name = kwargs.get('user_name', str())
        self.user_email = kwargs.get('user_email', str())
        self.user_phone = kwargs.get('user_phone', str())
        self.notes = kwargs.get('notes', str())
        self.reference = kwargs.get(
            'reference',
            config.contact_list_config['contact_record_reference']
        )

    # FETCHERS (RECORD)

    def fetch_record_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_record_reference(self):
        log.debug('')
        return self.reference

    def fetch_record_user_name(self):
        log.debug('')
        return self.user_name

    def fetch_record_user_email(self):
        log.debug('')
        return self.user_email

    def fetch_record_user_phone(self):
        log.debug('')
        return self.user_phone

    def fetch_record_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_record_values(self):
        log.debug('')
        values = {
            'id': self.record_id,
            'contact_list': self.contact_list_id,
            'reference': self.reference or \
                config.contact_list_config['contact_record_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'name': self.user_name,
            'email': self.user_email,
            'phone': self.user_phone,
            'notes': self.notes,
        }
        return values

    # SETTERS (RECORD)

    def set_record_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_record_id_found(kwargs)
        try:
            self.record_id = kwargs['record_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_record_id(
                kwargs, self.record_id, e
            )
        log.info('Successfully set contact record id.')
        return True

    def set_contact_list_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact_list_id'):
            return self.error_no_contact_list_id_found(kwargs)
        try:
            self.contact_list_id = kwargs['contact_list_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_id(
                kwargs, self.contact_list_id, e
            )
        log.info('Successfully set record contact list id.')
        return True

    def set_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name'):
            return self.error_no_user_name_found(kwargs)
        try:
            self.user_name = kwargs['user_name']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_name(
                kwargs, self.user_name, e
            )
        log.info('Successfully set user name.')
        return True

    def set_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email'):
            return self.error_no_user_email_found(kwargs)
        try:
            self.user_email = kwargs['user_email']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_email(
                kwargs, self.user_email, e
            )
        log.info('Successfully set user email.')
        return True

    def set_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_phone'):
            return self.error_no_user_phone_found(kwargs)
        try:
            self.user_phone = kwargs['user_phone']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_phone(
                kwargs, self.user_phone, e
            )
        log.info('Successfully set user phone.')
        return True

    def set_notes(self, **kwargs):
        log.debug('')
        if not kwargs.get('notes'):
            return self.error_no_notes_found(kwargs)
        try:
            self.notes = kwargs['notes']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_user_notes(
                kwargs, self.notes, e
            )
        log.info('Successfully set contact record notes.')
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found(kwargs)
        try:
            self.reference = kwargs['reference']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set contact record reference.')
        return True

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set contact record write date.')
        return True

    # UPDATERS (RECORD)

    def update_write_date(self):
        log.debug('')
        self.set_write_date(datetime.datetime.now())
        return self.fetch_record_write_date()

    # ERRORS (RECORD)
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_could_not_set_user_name(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record user name. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_email(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record user email. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_phone(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record user phone. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_user_notes(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record user notes. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_record_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact record id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_record_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No record id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_contact_list_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact list id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_name_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No user name found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_email_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No user email found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_user_phone_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No user phone found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_notes_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact record notes found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact record reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response


class ContactList(Base):
    __tablename__ = 'contact_list'

    contact_list_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('res_user.user_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    active_session = relationship('EWallet', back_populates='contact_list')
    client = relationship(
        'ResUser', back_populates='user_contact_list'
    )
    records = relationship('ContactListRecord')

    def __init__(self, **kwargs):
        self.create_date = kwargs.get('create_date', datetime.datetime.now())
        self.write_date = kwargs.get('write_date', datetime.datetime.now())
        self.client_id = kwargs.get('client_id', int())
        self.client = kwargs.get('client')
        self.reference = kwargs.get(
            'reference',
            config.contact_list_config['contact_list_reference']
        )
        self.active_session_id = kwargs.get('active_session_id', int())
        self.active_session = kwargs.get('active_session')
        self.records = kwargs.get('records', [])

    # FETCHERS (LIST)

    def fetch_contact_list_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_id_found()
        if kwargs.get('active_session'):
            match = list(
                kwargs['active_session'].query(ContactListRecord)\
                .filter_by(record_id=kwargs['code'])
            )
        else:
            match = [
                item for item in self.records
                if item.fetch_record_id() is kwargs['code']
            ]
        record = False if not match else match[0]
        check = self.check_record_in_contact_list(record)
        if not check:
            return self.warning_record_not_in_contact_list(
                kwargs, record, check
            )
        log.info('Successfully fetched contact record by id.')
        return record

    # TODO
    def fetch_contact_list_record(self, **kwargs):
        log.debug('TODO - Refactor')
        if not kwargs.get('search_by'):
            return self.error_no_contact_record_search_identifier_found()
        handlers = {
            'id': self.fetch_contact_list_record_by_id,
        }
        return handlers[kwargs['search_by']](**kwargs)

    def fetch_contact_list_write_date(self):
        log.debug('')
        return self.write_date

    def fetch_contact_list_id(self):
        log.debug('')
        return self.contact_list_id

    def fetch_contact_list_client_id(self):
        log.debug('')
        return self.contact_list_client_id

    def fetch_contact_list_reference(self):
        log.debug('')
        return self.reference

    def fetch_contact_list_records(self):
        log.debug('')
        return self.records

    def fetch_contact_list_values(self):
        log.debug('')
        values = {
            'id': self.contact_list_id,
            'user': self.client_id,
            'reference': self.reference or \
                config.contact_list_config['contact_list_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'records': {
                item.fetch_record_id(): item.fetch_record_reference() \
                for item in self.records
            }
        }
        return values

    def fetch_contact_list_records_from_database(self, **kwargs):
        log.debug('')
        if not kwargs.get('active_session'):
            return self.error_no_active_session_found(kwargs)
        try:
            records = list(
                kwargs['active_session'].query(
                    ContactListRecord
                ).filter_by(
                    contact_list_id=self.fetch_contact_list_id()
                )
            )
        except:
            return self.error_could_not_fetch_contact_list_records_from_database(
                kwargs
            )
        return records

    # SETTERS (LIST)

    def set_create_date(self, create_date):
        log.debug('')
        try:
            self.create_date = create_date
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_create_date(
                create_date, self.create_date, e
            )
        log.info('Successfully set contact list create date.')
        return True

    def set_active_session_id(self, ewallet_session_id):
        log.debug('')
        try:
            self.active_session_id = ewallet_session_id
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_active_session_id(
                ewallet_session_id, self.active_session_id, e
            )
        log.info('Successfully set active ewallet session id.')
        return True

    def set_active_session(self, ewallet_session):
        log.debug('')
        try:
            self.active_session = ewallet_session
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_active_session(
                ewallet_session, self.active_session, e
            )
        log.info('Successfully set contact list active ewallet session.')
        return True

    def set_client(self, user):
        log.debug('')
        try:
            self.client = user
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_client(
                user, self.client, e
            )
        log.info('Successfully set contact list client.')
        return True

    def set_to_contact_list_records(self, record):
        log.debug('')
        try:
            self.records.append(record)
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_update_contact_list_records(
                record, self.records, e
            )
        log.info('Successfully updated contact list records.')
        return True

    def set_contact_list_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact_list_id'):
            return self.error_no_contact_list_id_found(kwargs)
        try:
            self.contact_list_id = kwargs['contact_list_id']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_id(
                kwargs, self.contact_list_id, e
            )
        log.info('Successfully set contact list id.')
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
            return self.error_could_not_set_contact_list_reference(
                kwargs, self.reference, e
            )
        log.info('Successfully set contact list reference.')
        return True

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found(kwargs)
        try:
            self.records = kwargs['records']
            self.update_write_date()
        except Exception as e:
            return self.error_could_not_set_contact_list_records(
                kwargs, self.records, e
            )
        log.info('Successfully set contact list records.')
        return True

    def set_write_date(self, write_date):
        log.debug('')
        try:
            self.write_date = write_date
        except Exception as e:
            return self.error_could_not_set_contact_list_write_date(
                write_date, self.write_date, e
            )
        log.info('Successfully set contact list write date.')
        return True

    # UPDATERS (LIST)

    def update_write_date(self):
        log.debug('')
        self.set_write_date(datetime.datetime.now())
        return self.fetch_contact_list_write_date()

    def update_contact_list(self, **kwargs):
        '''
        [ INPUT ]: values = {'update_type': '', records: []}
        '''
        log.debug('')
        if not kwargs.get('utype'):
            return self.error_no_contact_list_update_type_specified()
        handlers = {
            'rewrite': self.handle_update_contact_list_rewrite,
            'append': self.handle_update_contact_list_append,
            'remove': self.handle_update_contact_list_remove,
            'clear': self.handle_update_contact_list_clear,
        }
        return handlers[kwargs.get('utype')](**kwargs)

    def update_contact_list_records(self, record):
        log.debug('')
        set_to = self.set_to_contact_list_records(record)
        return set_to if isinstance(set_to, dict) and \
            set_to.get('failed') else self.fetch_contact_list_records()

    # CHECKERS (LIST)

    def check_record_in_contact_list(self, record):
        log.debug('')
        return False if record not in self.records else True

    # HANDLERS (LIST)

    def handle_update_contact_list_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_contact_record_id_found(kwargs)
        try:
            kwargs['active_session'].query(
                ContactListRecord
            ).filter_by(record_id=kwargs['record_id']).delete()
        except:
            return self.error_could_not_remove_contact_list_record(kwargs)
        log.info('Successfully removed contact record.')
        command_chain_response = {
            'failed': False,
            'contact_list': self.contact_list_id,
            'contact_record': kwargs['record_id'],
        }
        return command_chain_response

    def handle_update_contact_list_rewrite(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_contact_records_found()
        self.records = {}
        new_records = kwargs['records']
        for item in new_records:
            self.records.update({item.fetch_record_id(): item})
        if self.records:
            log.info('Successfully updated contact list.')
        return self.records

    def handle_update_contact_list_append(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_contact_records_found()
        for item in kwargs['records']:
            update = self.update_contact_list_records(item)
        if self.records:
            log.info('Successfully updated contact list.')
        return kwargs['records']

    def handle_update_contact_list_clear(self, **kwargs):
        log.debug('')
        self.records = {}
        log.info('Successfully cleared all contact list records.')
        return self.records

    def handle_load_contacts_from_database(self, **kwargs):
        log.debug('')
        _records = self.fetch_contact_list_records_from_database()
        if not _records:
            return self.warning_could_not_fetch_contact_records_from_database()
        _update = self.update_contact_list(
            update_type='rewrite', records=_records
        )
        if _update:
            log.info('Successfully loaded contacts from database.')
        return _records

    def handle_load_contacts_from_args(self, **kwargs):
        log.debug('')
        _update = self.update_contact_list(
            update_type='rewrite', records=kwargs.get('records')
        )
        if _update:
            log.info('Successfully loaded contacts from args.')
        return kwargs.get('records')

    def handle_display_contact_list_records_to_terminal(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_contact_records_found()
        for item in kwargs['records']:
            print('{} - {}\n{}\n'.format(
                item.fetch_record_id(), item.fetch_record_reference(),
                item.fetch_record_values()
                ))
        return kwargs['records']

    # INTEROGATORS (LIST)

    def interogate_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_type'):
            return self.error_no_contact_list_interogation_type_specified()
        _handlers = {
                'single': self.interogate_contact_list_for_single_record,
                'filter': self.interogate_contact_list_for_filtered_records,
                'all': self.interogate_contact_list_for_all_records,
                }
        return _handlers[kwargs['search_type']](**kwargs)

    def interogate_contact_list_for_single_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_contact_record_search_identifier_found()
        _record = self.fetch_contact_list_records(**kwargs)
        return False if not _record else self.display_contact_list_records(
                display_to='terminal', records=_record
                )[0]

    def interogate_contact_list_for_filtered_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_contact_record_search_identifier_found()
        _records = self.fetch_contact_list_records(**kwargs)
        return False if not _records else self.display_contact_list_records(
                display_to='terminal', records=_records
                )

    def interogate_contact_list_for_all_records(self, **kwargs):
        log.debug('')
        return self.display_contact_list_records(
                display_to='terminal', records=[item for item in self.records.values()]
                )

    # CREATORS (LIST)

    def create_contact_list_record(self, **kwargs):
        log.debug('')
        record = ContactListRecord(
            contact_list_id=self.contact_list_id,
            user_name=kwargs.get('user_name'),
            user_email=kwargs.get('user_email'),
            user_phone=kwargs.get('user_phone'),
            notes=kwargs.get('notes')
        )
        self.handle_update_contact_list_append(records=[record])
        kwargs['active_session'].add(record)
        return record

    # DISPLAYS (LIST)

    def display_contact_list_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('display_to'):
            return self.error_no_record_display_target_specified()
        handlers = {
            'terminal': self.handle_display_contact_list_records_to_terminal,
        }
        return handlers[kwargs['terminal']](**kwargs)

    # GENERAL (LIST)

    def load_contact_list_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('source'):
            return self.error_no_contact_records_load_target_specified()
        _handlers = {
                'database': self.handle_load_contacts_from_database,
                'args': self.handle_load_contacts_from_args,
                }
        return _handlers[kwargs.get('source')](**kwargs)

    # CONTROLLERS (LIST)

    def contact_list_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_contact_list_controller_action_specified()
        handlers = {
            'load': self.load_contact_list_records,
            'create': self.create_contact_list_record,
            'update': self.update_contact_list,
            'interogate': self.interogate_contact_list,
        }
        return handlers[kwargs['action']](**kwargs)

    # WARNINGS (LIST)
    '''
    [ TODO ]: Fetch warning messages from message file by key codes.
    '''

    def warning_record_not_in_contact_list(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Record not found in contact list. '
                       'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def warning_could_not_fetch_contact_records_from_database(self, *args):
        command_chain_response = {
            'failed': True,
            'warning': 'Something went wrong. '
                       'Could not fetch contact records from database. '
                       'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    # ERRORS (LIST)
    '''
    [ TODO ]: Fetch error messages from message file by key codes.
    '''

    def error_no_contact_list_record_removal_target_specified(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact list record removal target specified. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_invalid_contact_record_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Invalid contact record id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_client(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list client user. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_active_session(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list active ewallet session. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_active_session_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list active ewallet session id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_create_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list create date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_records(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list records. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_records_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact records found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_reference(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list reference. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_reference_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No reference found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_write_date(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list write date. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_client_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set client id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_client_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No client id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_contact_list_id_found(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'No contact list id found. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_set_contact_list_id(self, *args):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. '
                     'Could not set contact list id. '
                     'Details: {}'.format(args),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_active_session_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No active SqlAlchemy orm session found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_fetch_contact_list_records_from_database(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Something went wrong. Could not fetch contact list records from database. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_contact_record_id_found(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'No contact list record id found. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_remove_contact_list_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not remove contact list record. Command chain details : {}'\
                     .format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_no_contact_list_interogation_type_specified(self):
        log.error('No contact list interogation type specified.')
        return False

    def error_no_contact_list_controller_action_specified(self):
        log.error('No contact list controller action specified.')
        return False

    def error_no_record_display_target_specified(self):
        log.error('No record display target specified.')
        return False

    def error_no_contact_records_load_target_specified(self):
        log.error('No contact records load target specified.')
        return False

    def error_no_contact_list_update_type_specified(self):
        log.error('No contact list update type specified.')
        return False

    def error_no_contact_record_email_found(self):
        log.error('No contact record email found.')
        return False

    def error_no_contact_record_phone_found(self):
        log.error('No contact record phone found.')
        return False

    def error_no_contact_record_search_identifier_found(self):
        log.error('No contact record search identifier found.')
        return False

    def error_no_contact_records_found(self):
        log.error('No contact records found.')
        return False

    def error_no_contact_record_reference_found(self):
        log.error('No contact list record reference found.')
        return False

    def error_no_contact_record_name_found(self):
        log.error('No contact list record name found.')
        return False

# ==============================================================================
# CODE DUMP
# ==============================================================================

#   # TODO
#   def fetch_contact_list_record_by_ref(self, **kwargs):
#       log.debug('TODO - Deprecated')
#       if not kwargs.get('code'):
#           return self.error_no_contact_record_reference_found()
#       _records = []
#       for k, v in self.records.items():
#           if v.fetch_record_reference() == kwargs['code']:
#               _records.append(v)
#       if _records:
#           log.info('Successfully fetched contact records by reference.')
#       return _records

#   # TODO
#   def fetch_contact_list_record_by_name(self, **kwargs):
#       log.debug('TODO - Deprecated')
#       if not kwargs.get('code'):
#           return self.error_no_contact_record_name_found()
#       _records = []
#       for k, v in self.records.items():
#           if v.fetch_record_user_name() == kwargs['code']:
#               _records.append(v)
#       if _records:
#           log.info('Successfully fetched contact records by name.')
#       return _records

#   # TODO
#   def fetch_contact_list_record_by_email(self, **kwargs):
#       log.debug('TODO - Deprecated')
#       if not kwargs.get('code'):
#           return self.error_no_contact_record_email_found()
#       _records = []
#       for k, v in self.records.items():
#           if v.fetch_record_user_email() == kwargs['code']:
#               _records.append(v)
#       if _records:
#           log.info('Successfully fetched contact records by email.')
#       return _records

#   # TODO
#   def fetch_contact_list_record_by_phone(self, **kwargs):
#       log.debug('TODO - Deprecated')
#       if not kwargs.get('code'):
#           return self.error_no_contact_record_phone_found()
#       _records = []
#       for k, v in self.records.items():
#           if v.fetch_record_user_phone() == kwargs['code']:
#               _records.append(v)
#       if _records:
#           log.info('Successfully fetched contact records by phone.')
#       return _records

