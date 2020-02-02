import time
import datetime
import random
import logging
import pysnooper
from itertools import count
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

log_config = Config().log_config
log = logging.getLogger(log_config['log_name'])


class CreditTransferSheetRecord(Base):
    __tablename__ = 'transfer_sheet_record'

    record_id = Column(Integer, primary_key=True)
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    transfer_type = Column(String)
    transfer_from = Column(Integer, ForeignKey('res_user.user_id'))
    transfer_to = Column(Integer, ForeignKey('res_user.user_id'))
    credits = Column(Integer)
    transfer_sheet_id = Column(
        Integer, ForeignKey('credit_transfer_sheet.transfer_sheet_id')
        )

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_record_id(self):
        log.debug('')
        return self.record_id

    def fetch_record_reference(self):
        log.debug('')
        return self.reference

    def fetch_record_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_record_transfer_from(self):
        log.debug('')
        return self.transfer_from

    def fetch_record_transfer_to(self):
        log.debug('')
        return self.transfer_to

    def fetch_record_values(self):
        log.debug('')
        _values = {
                'id': self.record_id,
                'transfer_sheet_id': self.transfer_sheet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'transfer_type': self.transfer_type,
                'transfer_from': self.transfer_from,
                'transfer_to': self.transfer_to,
                'credits': self.credits,
                }
        return _values

    def set_record_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_record_id_found()
        self.record_id = kwargs['record_id']
        return True

    def set_transfer_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_sheet_id'):
            return self.error_no_transfer_sheet_id_found()
        self.transfer_sheet_id = kwargs['transfer_sheet_id']
        return True

    def set_reference(self, **kwargs):
        log.debug('')
        if not kwargs.get('reference'):
            return self.error_no_reference_found()
        self.reference = kwargs['reference']
        return True

    def set_transfer_type(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_type'):
            return self.error_no_transfer_type_found()
        self.transfer_type = kwargs['transfer_type']
        return True

    def set_transfer_from(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_from'):
            return self.error_no_transfer_from_found()
        self.transfer_from = kwargs['transfer_from']
        return True

    def set_transfer_to(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_to'):
            return self.error_no_transfer_to_found()
        self.transfer_to = kwargs['transfer_to']
        return True

    def set_credits(self, **kwargs):
        log.debug('')
        if not kwargs.get('credits'):
            return self.error_no_credits_found()
        self.credits = kwargs['credits']
        return True

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def error_no_record_id_found(self):
        log.error('No record id found.')
        return False

    def error_no_transfer_sheet_id_found(self):
        log.error('No transfer sheet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_transfer_type_found(self):
        log.error('No transfer type found.')
        return False

    def error_no_transfer_from_found(self):
        log.error('No transfer source found.')
        return False

    def error_no_transfer_to_found(self):
        log.error('No transfer destination found.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False


class CreditTransferSheet(Base):
    __tablename__ = 'credit_transfer_sheet'

    transfer_sheet_id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('credit_ewallet.wallet_id'))
    reference = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    # O2O
    wallet = relationship('CreditEWallet', back_populates='transfer_sheet')
    # O2M
    records = relationship('CreditTransferSheetRecord')

    def __init__(self, **kwargs):
        self.create_date = datetime.datetime.now()
        self.write_date = datetime.datetime.now()

    def fetch_transfer_sheet_id(self):
        log.debug('')
        return self.transfer_sheet_id

    def fetch_transfer_sheet_reference(self):
        log.debug('')
        return self.reference

    def fetch_transfer_sheet_create_date(self):
        log.debug('')
        return self.create_date

    def fetch_transfer_sheet_records(self):
        log.debug('')
        return self.records

    def fetch_transfer_sheet_values(self):
        log.debug('')
        _values = {
                'id': self.transfer_sheet_id,
                'wallet_id': self.wallet_id,
                'reference': self.reference,
                'create_date': self.create_date,
                'write_date': self.write_date,
                'records': self.records,
                }
        return _values

    # [ NOTE ]: Transfer Type : (incomming | outgoing | expence)
    def fetch_transfer_record_creation_values(self, **kwargs):
        log.debug('')
        _values = {
                'reference': kwargs.get('reference'),
                'transfer_sheet_id': self.transfer_sheet_id,
                'transfer_type': kwargs.get('transfer_type'),
                'transfer_from': kwargs.get('transfer_from'),
                'transfer_to': kwargs('transfer_to'),
                'credits': kwargs('credits'),
                }
        return _values

    def fetch_transfer_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_id_found()
        _record = self.records.get(kwargs['code'])
        if not _record:
            return self.warning_could_not_fetch_transfer_record(
                    'id', kwargs['code']
                    )
        log.info('Successfully fetched transfer record by id.')
        return _record

    def fetch_transfer_sheet_record_by_ref(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_reference_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_reference() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_transfer_record(
                    'reference', kwargs['code']
                    )
        log.info('Successfully fetched transfer records by reference.')
        return _records

    def fetch_transfer_sheet_record_by_date(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_date_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_create_date() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_transfer_record(
                    'date', kwargs['code']
                    )
        log.info('Successfully fetched transfer records by date.')
        return _records

    def fetch_transfer_sheet_record_by_src(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_src_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_transfer_from() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_transfer_record(
                    'src', kwargs['code']
                    )
        log.info('Successfully fetched transfer records by transfer source.')
        return _records

    def fetch_transfer_sheet_record_by_dst(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_dst_found()
        _records = [
                self.records[item] for item in self.records
                if self.records[item].fetch_record_transfer_to() == kwargs['code']
                ]
        if not _records:
            return self.warning_could_not_fetch_transfer_record(
                    'dst', kwargs['code']
                    )
        log.info('Successfully fethced transfer records by transfer destination.')
        return _records

    # TODO - Refactor
    def fetch_all_transfer_sheet_records(self, **kwargs):
        log.debug('')
        _records = [item for item in self.records.values()]
        return _records

    def fetch_transfer_sheet_records(self, **kwargs):
        log.debug('')
        if not kwargs.get('search_by'):
            return self.error_no_transfer_sheet_record_identifier_specified()
        _handlers = {
                'id': self.fetch_transfer_sheet_record_by_id,
                'reference': self.fetch_transfer_sheet_record_by_ref,
                'date': self.fetch_transfer_sheet_record_by_date,
                'transfer_from': self.fetch_transfer_sheet_record_by_src,
                'transfer_to': self.fetch_transfer_sheet_record_by_dst,
                'all': self.fetch_all_transfer_sheet_records,
                }
        return _handlers[kwargs['search_by']](**kwargs)

    def set_transfer_sheet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_sheet_id'):
            return self.error_no_transfer_sheet_id_found()
        self.transfer_sheet_id = kwargs['transfer_sheet_id']
        return True

    def set_wallet_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('wallet_id'):
            return self.error_no_wallet_id_found()
        self.wallet_id = kwargs['wallet_id']
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

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    def update_records(self, record):
        log.debug('')
        self.records.update({
            record.fetch_record_id(): record
            })
        log.info('Successfully updated transfer sheet records.')
        return self.records

    def create_transfer_sheet_record(self, values={}):
        log.debug('')
        _record = CreditTransferSheetRecord(**values)
        return _record

    def add_transfer_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_type') or not kwargs.get('credits'):
            return self.error_handler_add_transfer_sheet_record(
                    transfer_type=kwargs.get('transfer_type'),
                    credits=kwargs.get('credits'),
                    )
        _values = self.fetch_transfer_record_creation_values(**kwargs)
        _record = self.create_transfer_sheet_record(values=_values)
        _update = self.update_records(_record)
        log.info('Successfully added new transfer record.')
        return _record

    def remove_transfer_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_transfer_record_id_found()
        _unlink = self.records.pop(kwargs['record_id'])
        if _unlink:
            log.info('Successfully removed transfer sheet record.')
        return _unlink

    def update_records(self, record):
        log.debug('')
        self.records.update({record.fetch_record_id(): record})
        return self.records

    def append_transfer_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('records'):
            return self.error_no_transfer_records_found()
        for item in kwargs['records']:
            self.update_records(item)
        log.info('Successfully appended transfer records.')
        return self.records

    def interogate_transfer_sheet_records(self, **kwargs):
        log.debug('')
        _records = self.fetch_transfer_sheet_records(**kwargs)
        _display = self.display_transfer_sheet_records(records=_records)
        return _records if _display else False

    def clear_transfer_sheet_records(self, **kwargs):
        log.debug('')
        self.records = {}
        log.info('Successfully cleared transfer sheet records.')
        return self.records

    def credit_transfer_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_transfer_sheet_controller_action_specified()
        _handlers = {
                'add': self.add_transfer_sheet_record,
                'remove': self.remove_transfer_sheet_record,
                'append': self.append_transfer_sheet_record,
                'interogate': self.interogate_transfer_sheet_records,
                'clear': self.clear_transfer_sheet_records,
                }
        _handle = _handlers[kwargs['action']](**kwargs)
        if _handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return _handle

    # TODO - Refactor
    def display_transfer_sheet_records(self, records=[]):
        log.debug('')
        if not records:
            records = [item for item in self.records.values()]
        print('Transfer Sheet {} Records:'.format(self.reference))
        for item in records:
            print('{}: {} - {}'.format(
                item.fetch_record_create_date(), item.fetch_record_id(),
                item.fetch_record_reference()
                ))
        return records

    def error_handler_add_transfer_sheet_record(self, **kwargs):
        _reasons_and_handlers = {
                'reasons': {
                    'transfer_type': kwargs.get('transfer_type'),
                    'credits': kwargs.get('credits')
                    },
                'handlers': {
                    'transfer_type': self.error_no_transfer_type_found,
                    'credits': self.error_no_credits_found,
                    },
                }
        for item in _reasons_and_handlers['reasons']:
            if not _reasons_and_handlers['reasons'][item]:
                return _reasons_and_handlers['handlers'][item]()
        return False

    def error_no_transfer_sheet_id_found(self):
        log.error('No transfer sheet id found.')
        return False

    def error_no_wallet_id_found(self):
        log.error('No wallet id found.')
        return False

    def error_no_reference_found(self):
        log.error('No reference found.')
        return False

    def error_no_records_found(self):
        log.error('No records found.')
        return False

    def error_no_transfer_type_found(self):
        log.error('No transfer type found.')
        return False

    def error_no_transfer_records_found(self):
        log.error('No transfer records found.')
        return False

    def error_no_transfer_sheet_controller_action_specified(self):
        log.error('No transfer sheet controller action specified.')
        return False

    def error_no_credits_found(self):
        log.error('No credits found.')
        return False

    def error_no_transfer_sheet_record_identifier_specified(self):
        log.error('No transfer sheet record identifier specified.')
        return False

    def error_no_transfer_record_creation_values_found(self):
        log.error('No transfer record creation values found.')
        return False

    def error_no_transfer_record_src_found(self):
        log.error('No transfer record source party found.')
        return False

    def error_no_transfer_record_dst_found(self):
        log.error('No transfer record destination party found.')

    def error_no_transfer_record_reference_found(self):
        log.error('No transfer record reference found.')
        return False

    def error_no_transfer_record_date_found(self):
        log.error('No transfer record date found.')
        return False

    def error_no_transfer_record_id_found(self):
        log.error('No transfer record id found.')
        return False

    def warning_could_not_fetch_transfer_record(self, search_code, code):
        log.warning(
                'Something went wrong. '
                'Could not fetch transfer record by %s %s.'
                )
        return False


###############################################################################
# CODE DUMP
###############################################################################

    # M2O
#   transfer_sheet = relationship(
#       'CreditTransferSheet', foreign_keys=[transfer_sheet_id]
#       )
#   # M2O
#   user_from = relationship('ResUser', foreign_keys=[transfer_from])
#   # M2O
#   user_to = relationship('ResUser', foreign_keys=[transfer_to])


