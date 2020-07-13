import datetime
import logging
import pysnooper

from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from .res_utils import ResUtils, Base
from .config import Config

res_utils, config = ResUtils(), Config()
log = logging.getLogger(config.log_config['log_name'])


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
        self.reference = kwargs.get('reference') or \
            config.transfer_sheet_config['transfer_record_reference']
        self.transfer_type = kwargs.get('transfer_type')
        self.transfer_from = kwargs.get('transfer_from')
        self.transfer_to = kwargs.get('transfer_to')
        self.credits = kwargs.get('credits') or 0

    # FETCHERS

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
        values = {
            'id': self.record_id,
            'transfer_sheet': self.transfer_sheet_id,
            'reference': self.reference,
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'transfer_type': self.transfer_type,
            'transfer_from': self.transfer_from,
            'transfer_to': self.transfer_to,
            'credits': self.credits,
        }
        return values

    # SETTERS

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

    # UPDATERS

    def update_write_date(self):
        log.debug('')
        self.write_date = datetime.datetime.now()
        return self.write_date

    # ERRORS

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
        self.wallet_id = kwargs.get('wallet_id')
        self.reference = kwargs.get('reference') or \
            config.transfer_sheet_config['transfer_sheet_reference']
        self.records = kwargs.get('records') or []

    # FETCHERS

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
        values = {
            'id': self.transfer_sheet_id,
            'ewallet': self.wallet_id,
            'reference': self.reference or
                config.transfer_sheet_config['transfer_sheet_reference'],
            'create_date': res_utils.format_datetime(self.create_date),
            'write_date': res_utils.format_datetime(self.write_date),
            'records': {
                record.fetch_record_id(): record.fetch_record_reference()
                for record in self.records
            },
        }
        return values

    def fetch_transfer_record_creation_values(self, **kwargs):
        '''
        [ NOTE ]: Transfer Type : (incomming | outgoing | expence)
        '''
        log.debug('')
        values = {
            'reference': kwargs.get('reference') or
                config.transfer_sheet_config['transfer_record_reference'],
            'transfer_sheet': self,
            'transfer_type': kwargs.get('transfer_type'),
            'transfer_from': kwargs.get('transfer_from'),
            'transfer_to': kwargs.get('transfer_to'),
            'credits': kwargs.get('credits'),
        }
        return values

    def fetch_transfer_sheet_record_by_id(self, **kwargs):
        log.debug('')
        if not kwargs.get('code'):
            return self.error_no_transfer_record_id_found()
        if kwargs.get('active_session'):
            _match = list(
                kwargs['active_session'].query(CreditTransferSheetRecord)\
                .filter_by(record_id=kwargs['code'])
            )
        else:
            _match = [
                item for item in self.records
                if item.fetch_record_id() is kwargs['code']
            ]
        _record = False if not _match else _match[0]
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
        handlers = {
            'id': self.fetch_transfer_sheet_record_by_id,
            'reference': self.fetch_transfer_sheet_record_by_ref,
            'date': self.fetch_transfer_sheet_record_by_date,
            'transfer_from': self.fetch_transfer_sheet_record_by_src,
            'transfer_to': self.fetch_transfer_sheet_record_by_dst,
            'all': self.fetch_all_transfer_sheet_records,
        }
        return handlers[kwargs['search_by']](**kwargs)

    # SETTERS

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

    # UPDATERS

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

    # ACTIONS

    def create_transfer_sheet_record(self, values=None):
        log.debug('')
        if not values:
            log.error('No transfer sheet record creation values found.')
            return False
        _record = CreditTransferSheetRecord(**values)
        return _record

    def add_transfer_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('transfer_type') or not kwargs.get('credits'):
            return self.error_handler_add_transfer_sheet_record(
                transfer_type=kwargs.get('transfer_type'),
                credits=kwargs.get('credits'),
            )
        values = self.fetch_transfer_record_creation_values(**kwargs)
        record = self.create_transfer_sheet_record(values=values)
        update = self.update_records(record)
        log.info('Successfully added new transfer record.')
        return record

    def remove_transfer_sheet_record(self, **kwargs):
        log.debug('')
        if not kwargs.get('record_id'):
            return self.error_no_transfer_record_id_found()
        try:
            kwargs['active_session'].query(
                CreditTransferSheetRecord
            ).filter_by(
                record_id=kwargs['record_id']
            ).delete()
        except:
            return self.error_could_not_remove_transfer_sheet_record(kwargs)
        return True

    def update_records(self, record):
        log.debug('')
        try:
            self.records.append(record)
        except:
            return self.error_could_not_update_transfer_sheet_records(record)
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

    # CONTROLLERS

    def credit_transfer_sheet_controller(self, **kwargs):
        log.debug('')
        if not kwargs.get('action'):
            return self.error_no_transfer_sheet_controller_action_specified()
        handlers = {
            'add': self.add_transfer_sheet_record,
            'remove': self.remove_transfer_sheet_record,
            'append': self.append_transfer_sheet_record,
            'interogate': self.interogate_transfer_sheet_records,
            'clear': self.clear_transfer_sheet_records,
        }
        handle = handlers[kwargs['action']](**kwargs)
        if handle and kwargs['action'] != 'interogate':
            self.update_write_date()
        return handle

    # ERRORS

    def error_could_not_remove_transfer_sheet_record(self, command_chain):
        command_chain_response = {
            'failed': True,
            'error': 'Could not remove transfer sheet record. '\
                     'Command chain details : {}'.format(command_chain),
        }
        log.error(command_chain_response['error'])
        return command_chain_response

    def error_could_not_update_transfer_sheet_records(self, record):
        log.error(
            'Could not update transfer sheet records with {}.'.format(record)
        )
        return False

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

