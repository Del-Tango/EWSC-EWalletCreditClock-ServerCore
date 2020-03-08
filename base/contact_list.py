import random
import datetime
import pysnooper
import logging
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .config import Config
from .res_utils import ResUtils, Base

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


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
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.contact_list_id = kwargs.get('contact_list_id')
        self.user_id = kwargs.get('user_id')
        self.user_name = kwargs.get('user_name')
        self.user_email = kwargs.get('user_email')
        self.user_phone = kwargs.get('user_phone')
        self.notes = kwargs.get('notes')
        self.reference = kwargs.get('reference') or 'Contact List Record'

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
        _values = {
                'record_id': self.record_id,
                'contact_list_id': self.contact_list_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'user_name': self.user_name,
                'user_email': self.user_email,
                'user_phone': self.user_phone,
                'notes': self.notes,
                }
        return _values

    def set_record_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_record_id_found()
        self.record_id = kwargs['record_id']
        return True

    def set_contact_list_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact_list_id'):
            return self.error_no_contact_list_id_found()
        self.contact_list_id = kwargs['contact_list_id']
        return True

    def set_user_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_name'):
            return self.error_no_user_name_found()
        self.user_name = kwargs['user_name']
        return True

    def set_user_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_email'):
            return self.error_no_user_email_found()
        self.user_name = kwargs['user_email']
        return True

    def set_user_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('user_phone'):
            return self.error_no_user_phone_found()
        self.user_phone = kwargs['user_phone']
        return True

    def set_notes(self, **kwargs):
        log.debug('')
        if not kwargs.get('notes'):
            return self.error_no_notes_found()
        self.notes = kwargs['notes']
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def error_no_record_id_found(self):
        log.error('No record id found.')
        return False

    def error_no_contact_list_id_found(self):
        log.error('No contact list id found.')
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

    def error_no_notes_found(self):
        log.error('No notes found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False


class ContactList(Base):
    __tablename__ = 'contact_list'

    contact_list_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('res_user.user_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    active_session_id = Column(Integer, ForeignKey('ewallet.id'))
    active_session = relationship('EWallet', back_populates='contact_list')
    # O2O
    client = relationship(
        'ResUser', back_populates='user_contact_list'
        )
    # O2M
    records = relationship('ContactListRecord')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.client_id = kwargs.get('client_id')
        self.reference = kwargs.get('reference') or 'Contact List'
        self.active_session_id = kwargs.get('active_session_id')
        self.records = kwargs.get('records') or []

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
        _values = {
                'id': self.contact_list_id,
                'client_id': self.client_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    # TODO
    def fetch_contact_list_records_from_database():
        log.debug('')
        self.records = {}
        return self.records

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    # TODO
    def fetch_contact_list_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_id_found()
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_id() == kwargs['code']:
                _records.append(v)
        if _records:
            log.info('Successfully fetched contact record by id.')
        return _records

    def fetch_contact_list_record_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_reference_found()
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_reference() == kwargs['code']:
                _records.append(v)
        if _records:
            log.info('Successfully fetched contact records by reference.')
        return _records

    def fetch_contact_list_record_by_name(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_name_found()
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_name() == kwargs['code']:
                _records.append(v)
        if _records:
            log.info('Successfully fetched contact records by name.')
        return _records

    def fetch_contact_list_record_by_email(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_email_found()
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_email() == kwargs['code']:
                _records.append(v)
        if _records:
            log.info('Successfully fetched contact records by email.')
        return _records

    def fetch_contact_list_record_by_phone(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_contact_record_phone_found()
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_phone() == kwargs['code']:
                _records.append(v)
        if _records:
            log.info('Successfully fetched contact records by phone.')
        return _records

    def fetch_contact_list_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_contact_record_search_identifier_found()
        _handlers = {
                'id': self.fetch_contact_list_record_by_id,
                'reference': self.fetch_contact_list_record_by_ref,
                'name': self.fetch_contact_list_record_by_name,
                'email': self.fetch_contact_list_record_by_email,
                'phone': self.fetch_contact_list_record_by_phone,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def set_contact_list_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('contact_list_id'):
            return self.error_no_contact_list_id_found()
        self.contact_list_id = kwargs['contact_list_id']
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

    def set_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_records_found()
        self.records = kwargs['records']
        return True

    def handle_update_contact_list_rewrite(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_contact_records_found()
        self.records = {}
        _new_records = kwargs['records']
        for item in _new_records:
            self.records.update({item.fetch_record_id(): item})
        if self.records:
            log.info('Successfully updated contact list.')
        return self.records

    def handle_update_contact_list_append(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_contact_records_found()
        _new_records = kwargs['records']
        for item in _new_records:
            _record_id = item.fetch_record_id()
            self.records.update({_record_id: item})
        if self.records:
            log.info('Successfully updated contact list.')
        return self.records

    def handle_update_contact_list_remove(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_contact_record_id_found()
        log.info('Successfully removed contact record.')
        return self.records.pop(kwargs['record_id'])

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

    # TODO
    def handle_display_contact_list_records_to_desktop(self, **kwargs):
        log.debug('')
        print('Unimplemented functionality: - handle_display_contact_list_to_desktop')
        pass

    # TODO
    def handle_display_contact_list_records_to_web(self, **kwargs):
        log.debug('')
        print('Unimplemented functionality: - handle_display_contact_list_to_web')
        pass

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

    def create_contact_list_record(self, **kwargs):
        log.debug('')
        _record = ContactListRecord(
                contact_list_id=self.contact_list_id,
                user_name=kwargs.get('user_name'),
                user_email=kwargs.get('user_email'),
                user_phone=kwargs.get('user_phone'),
                notes=kwargs.get('notes')
                )
        self.handle_update_contact_list_append(records=[_record])
        return _record

    def display_contact_list_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('display_to'):
            return self.error_no_record_display_target_specified()
        _handlers = {
                'terminal': self.handle_display_contact_list_records_to_terminal,
                'desktop': self.handle_display_contact_list_records_to_desktop,
                'web': self.handle_display_contact_list_records_to_web,
                }
        return _handlers[kwargs['display_to']](**kwargs)

    def load_contact_list_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('source'):
            return self.error_no_contact_records_load_target_specified()
        _handlers = {
                'database': self.handle_load_contacts_from_database,
                'args': self.handle_load_contacts_from_args,
                }
        return _handlers[kwargs.get('source')](**kwargs)

    # [ INPUT ]: values = {'update_type': '', records: []}
    def update_contact_list(self, **kwargs):
        log.debug('')
        if not kwargs.get('update_type'):
            return self.error_no_contact_list_update_type_specified()
        _handlers = {
                'rewrite': self.handle_update_contact_list_rewrite,
                'append': self.handle_update_contact_list_append,
                'remove': self.handle_update_contact_list_remove,
                'clear': self.handle_update_contact_list_clear,
                }
        self.contact_list_record_buffer = _handlers[kwargs.get('update_type')](**kwargs)
        return True

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

    def contact_list_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_contact_list_controller_action_specified()
        _handlers = {
                'load': self.load_contact_list_records,
                'create': self.create_contact_list_record,
                'update': self.update_contact_list,
                'interogate': self.interogate_contact_list,
                }
        return _handlers[kwargs['action']](**kwargs)

    def error_no_contact_list_id_found(self):
        log.error('No contact list id found.')
        return False

    def error_no_client_id_found(self):
        log.error('No client id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_records_found(self):
        log.error('No records found.')
        return False

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

    def error_no_contact_record_id_found(self):
        log.error('No contact list record id found.')
        return False

    def error_no_contact_record_reference_found(self):
        log.error('No contact list record reference found.')
        return False

    def error_no_contact_record_name_found(self):
        log.error('No contact list record name found.')
        return False

    def warning_could_not_fetch_contact_records_from_database(self):
        log.warning('Could not fetch contact records from database.')
        return False

    def test_contact_list_record_generator(self, count):
        _records = []
        for item in range(1,count):
            _record = self.create_contact_list_record(
                    user_name='Test Username {}'.format(item),
                    user_email='test{}@mail.com'.format(item),
                    user_phone='555 555 555',
                    notes='Test {} notes'.format(item),
                    )
            _records.append(_record)
        return _records

    def test_contact_list_load(self):
        print('[ TEST ]: Contact list load...')
        print('[ * ]: Args')
        _records = self.test_contact_list_record_generator(5)
        return self.contact_list_controller(
                action='load', source='args', records=_records
                )
        return True

    def test_contact_list_update(self):
        print('[ TEST ]: Contact list update...')
        print('[ * ]: Append')
        _records = self.test_contact_list_record_generator(5)
        test_append = self.contact_list_controller(
                action='update', update_type='append', records=_records
                )
        print('[ * ]: Remove')
        _all_records = [item for item in self.records.values()]
        test_remove = self.contact_list_controller(
                action='update', update_type='remove', records=_all_records
                )
        print('[ * ]: Clear')
        test_clear = self.contact_list_controller(
                action='update', update_type='clear'
                )
        print('[ * ]: Rewrite')
        test_rewrite = self.contact_list_controller(
                action='update', update_type='rewrite', records=_records
                )
        return True

    def test_contact_list_interogate(self):
        print('[ TEST ]: Contact list interogate...')
        print('[ * ]: Single')
        code = [item for item in self.records.values()]
        test_single = self.contact_list_controller(
                action='interogate', search_type='single', search_by='id',
                code=code[0].fetch_record_id()
                )
        print('[ * ]: Filter')
        test_filter = self.contact_list_controller(
                action='interogate', search_type='filter', search_by='name',
                code=code[0].fetch_record_user_name(),
                )
        print('[ * ]: All')
        test_filter = self.contact_list_controller(
                action='interogate', search_type='all'
                )
        return True

    def test_contact_list_regression(self):
        self.test_contact_list_load()
        self.test_contact_list_update()
        self.test_contact_list_interogate()


#contact_list = ContactList(client_id=1234, reference='Test Contact List')
#contact_list.test_contact_list_regression()

# ==============================================================================
# CODE DUMP
# ==============================================================================

# O2O
#   active_session = relationship('EWallet', back_populates="contact_list", foreign_keys=[active_session_id])
    # M2O
#   user = relationship('ResUser')
