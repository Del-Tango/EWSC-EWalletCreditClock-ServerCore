import random
import datetime
import pysnooper


class ContactListRecord():

    def __init__(self, **kwargs):
        self.record_id = random.randint(10, 20)
        self.contact_list_id = kwargs.get('contact_list_id')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.user_name = kwargs.get('user_name')
        self.user_email = kwargs.get('user_email')
        self.user_phone = kwargs.get('user_phone')
        self.notes = kwargs.get('notes')
        self.reference = self.user_name

    def fetch_record_id(self):
        return self.record_id

    def fetch_record_reference(self):
        return self.reference

    def fetch_record_user_name(self):
        return self.user_name

    def fetch_record_user_email(self):
        return self.user_email

    def fetch_record_user_phone(self):
        return self.user_phone

    def fetch_record_create_date(self):
        return self.create_date

    def fetch_record_values(self):
        _values = {
                'id': self.record_id,
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

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date


class ContactList():

    def __init__(self, **kwargs):
        self.contact_list_id = random.randint(10, 20)
        self.client_id = kwargs.get('client_id')
        self.reference = kwargs.get('reference')
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()
        self.records = {}

    def fetch_contact_list_id(self):
        return self.contact_list_id

    def fetch_contact_list_client_id(self):
        return self.contact_list_client_id

    def fetch_contact_list_reference(self):
        return self.reference

    def fetch_contact_list_records(self):
        return self.records

    def fetch_contact_list_values(self):
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
        global records
        self.records = {}
        return self.records

    def update_write_date(self):
        global write_date
        self.write_date = datetime.datetime.now()
        return self.write_date

    def fetch_contact_list_record_by_id(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_id() == kwargs['code']:
                _records.append(v)
        return _records

    def fetch_contact_list_record_by_ref(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_reference() == kwargs['code']:
                _records.append(v)
        return _records

    def fetch_contact_list_record_by_name(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_name() == kwargs['code']:
                _records.append(v)
        return _records

    def fetch_contact_list_record_by_email(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_email() == kwargs['code']:
                _records.append(v)
        return _records

    def fetch_contact_list_record_by_phone(self, **kwargs):
        if not kwargs.get('code'):
            return False
        _records = []
        for k, v in self.records.items():
            if v.fetch_record_user_phone() == kwargs['code']:
                _records.append(v)
        return _records

    def fetch_contact_list_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _handlers = {
                'id': self.fetch_contact_list_record_by_id,
                'reference': self.fetch_contact_list_record_by_ref,
                'name': self.fetch_contact_list_record_by_name,
                'email': self.fetch_contact_list_record_by_email,
                'phone': self.fetch_contact_list_record_by_phone,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def handle_update_contact_list_rewrite(self, **kwargs):
        if not kwargs.get('records'):
            return False
        global records
        self.records = {}
        _new_records = kwargs['records']
        for item in _new_records:
            _record_id = item.fetch_record_id()
            self.records.update({_record_id: item})
        return self.records

    def handle_update_contact_list_append(self, **kwargs):
        if not kwargs.get('records'):
            return False
        global records
        _new_records = kwargs['records']
        for item in _new_records:
            _record_id = item.fetch_record_id()
            self.records.update({_record_id: item})
        return self.records

    def handle_update_contact_list_remove(self, **kwargs):
        if not kwargs.get('records'):
            return False
        global records
        for item in kwargs['records']:
            _record_id = item.fetch_record_id()
            del self.records[_record_id]
        return self.records

    def handle_update_contact_list_clear(self, **kwargs):
        global records
        self.records = {}
        return self.records

    def handle_load_contacts_from_database(self, **kwargs):
        _records = self.fetch_contact_list_records_from_database()
        _update = self.update_contact_list(
            update_type='rewrite', records=_records
        )
        return _test_records

    def handle_load_contacts_from_args(self, **kwargs):
        _update = self.update_contact_list(
            update_type='rewrite', records=kwargs.get('records')
        )
        return kwargs.get('records')

    def handle_display_contact_list_records_to_terminal(self, **kwargs):
        if not kwargs.get('records'):
            return False
        for item in kwargs['records']:
            print('{} - {}\n{}\n'.format(
                item.fetch_record_id(), item.fetch_record_reference(),
                item.fetch_record_values()
                ))
        return kwargs['records']

    # TODO
    def handle_display_contact_list_records_to_desktop(self, **kwargs):
        print('Unimplemented functionality: - handle_display_contact_list_to_desktop')
        pass

    # TODO
    def handle_display_contact_list_records_to_web(self, **kwargs):
        print('Unimplemented functionality: - handle_display_contact_list_to_web')
        pass

    def interogate_contact_list_for_single_record(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _record = self.fetch_contact_list_records(**kwargs)
        return False if not _record else self.display_contact_list_records(
                display_to='terminal', records=_record
                )[0]

    def interogate_contact_list_for_filtered_records(self, **kwargs):
        if not kwargs.get('search_by'):
            return False
        _records = self.fetch_contact_list_records(**kwargs)
        return False if not _records else self.display_contact_list_records(
                display_to='terminal', records=_records
                )

    def interogate_contact_list_for_all_records(self, **kwargs):
        return self.display_contact_list_records(
                display_to='terminal', records=[item for item in self.records.values()]
                )

    def create_contact_list_record(self, **kwargs):
        _record = ContactListRecord(
                contact_list_id=self.contact_list_id,
                user_name=kwargs.get('user_name'),
                user_email=kwargs.get('user_email'),
                user_phone=kwargs.get('user_phone'),
                notes=kwargs.get('notes')
                )
        return _record

    def display_contact_list_records(self, **kwargs):
        if not kwargs.get('display_to'):
            return False
        _handlers = {
                'terminal': self.handle_display_contact_list_records_to_terminal,
                'desktop': self.handle_display_contact_list_records_to_desktop,
                'web': self.handle_display_contact_list_records_to_web,
                }
        return _handlers[kwargs['display_to']](**kwargs)

    def load_contact_list_records(self, **kwargs):
        if not kwargs.get('source'):
            return False
        _handlers = {
                'database': self.handle_load_contacts_from_database,
                'args': self.handle_load_contacts_from_args,
                }
        return _handlers[kwargs.get('source')](**kwargs)

    # [ INPUT ]: values = {'update_type': '', records: []}
    def update_contact_list(self, **kwargs):
        global contact_list_record_buffer
        if not kwargs.get('update_type'):
            return False
        _handlers = {
                'rewrite': self.handle_update_contact_list_rewrite,
                'append': self.handle_update_contact_list_append,
                'remove': self.handle_update_contact_list_remove,
                'clear': self.handle_update_contact_list_clear,
                }
        self.contact_list_record_buffer = _handlers[kwargs.get('update_type')](**kwargs)
        return True

    def interogate_contact_list(self, **kwargs):
        if not kwargs.get('search_type'):
            return False
        _handlers = {
                'single': self.interogate_contact_list_for_single_record,
                'filter': self.interogate_contact_list_for_filtered_records,
                'all': self.interogate_contact_list_for_all_records,
                }
        return _handlers[kwargs['search_type']](**kwargs)

    def contact_list_controller(self, **kwargs):
        if not kwargs.get('action'):
            return False
        _handlers = {
                'load': self.load_contact_list_records,
                'update': self.update_contact_list,
                'interogate': self.interogate_contact_list,
                }
        return _handlers[kwargs['action']](**kwargs)

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

