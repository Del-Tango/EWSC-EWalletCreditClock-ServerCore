from base.ewallet_session_manager import EWalletSessionManager
from base.config import Config
from base.res_utils import ResUtils
import logging
import datetime
import time

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])


class EWalletServer(EWalletSessionManager):

    def test_request_session_token(self, client_id):
        log.debug('')
        print('[ * ]: User action Request Session Token')
        session_token = self.session_manager_controller(
                controller='client', ctype='action', action='request', request='session_token',
                client_id=client_id
                )
        print(str(session_token) + '\n')
        return session_token

    def test_new_session(self):
        log.debug('')
        print('[ * ]: System Action New Session')
        session = self.session_manager_controller(
                controller='system', ctype='action', action='new', new='session',
                )
        print(str(session) + '\n')
        return session

    def test_instruction_set_listener(self):
        log.debug('')
        print('[ * ]: System Action Start Instruction Set Listener')
        listen = self.session_manager_controller(
                controller='system', ctype='action', action='start',
                start='instruction_listener'
                )
        print(str(listen) + '\n')
        return listen

    def test_open_instruction_listener_port(self):
        log.debug('')
        print('[ * ]: System Action Open Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='open',
                opening='sockets', in_port=8080, out_port=8081
                )
        print(str(_in_port) + '\n')
        return _in_port

    def test_close_instruction_listener_port(self):
        log.debug('')
        print('[ * ]: System Action Close Instruction Listener Port')
        _in_port = self.session_manager_controller(
                controller='system', ctype='action', action='close',
                closing='sockets',
                )
        print(str(_in_port) + '\n')
        return _in_port


    def test_request_client_id(self):
        log.debug('')
        print('[ * ]: User Action Request Client ID')
        _client_id = self.session_manager_controller(
                controller='client', ctype='action', action='request',
                request='client_id'
                )
        print(str(_client_id) + '\n')
        return _client_id

    def test_new_worker(self):
        log.debug('')
        print('[ * ]: System Action New Worker')
        _worker = self.session_manager_controller(
                controller='system', ctype='action', action='new',
                new='worker'
                )
        print(str(_worker) + '\n')
        return _worker

    def test_user_action_create_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Create Account')
        _create_account = self.session_manager_controller(
                controller='client', ctype='action', action='new',
                new='account', client_id=kwargs.get('client_id'),
                session_token=kwargs.get('session_token'), user_name=kwargs.get('user_name'),
                user_pass=kwargs.get('user_pass'), user_email=kwargs.get('user_email')
                )
        print(str(_create_account) + '\n')
        return _create_account

    def test_user_action_session_login(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Session Login')
        _login = self.session_manager_controller(
                controller='client', ctype='action', action='login',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                user_name=kwargs['user_name'], user_pass=kwargs['user_pass'],
                )
        print(str(_login) + '\n')
        return _login

    def test_user_action_supply_credits(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Supply Credits')
        _supply = self.session_manager_controller(
                controller='client', ctype='action', action='supply', supply='credits',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                currency=kwargs['currency'], credits=kwargs['credits'], cost=kwargs['cost'],
                notes=kwargs['notes']
                )
        print(str(_supply) + '\n')
        return _supply

    def test_user_action_convert_credits_to_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Convert Credits To Clock')
        _convert = self.session_manager_controller(
                controller='client', ctype='action', action='convert', convert='credits2clock',
                client_id=kwargs['client_id'], session_token=kwargs['session_token'],
                credits=kwargs['credits'], notes=kwargs['notes']
                )
        print(str(_convert) + '\n')
        return _convert

    def test_user_action_start_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Start Clock Timer')
        _start = self.session_manager_controller(
            controller='client', ctype='action', action='start', start='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_start) + '\n')
        return _start

    def test_user_action_pause_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Pause Clock Timer')
        _pause = self.session_manager_controller(
            controller='client', ctype='action', action='pause', pause='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_pause) + '\n')
        return _pause

    def test_user_action_resume_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Resume Clock Timer')
        _resume = self.session_manager_controller(
            controller='client', ctype='action', action='resume', resume='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_resume) + '\n')
        return _resume

    def test_user_action_stop_clock_timer(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Stop Clock Timer')
        _stop = self.session_manager_controller(
            controller='client', ctype='action', action='stop', stop='clock_timer',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_stop) + '\n')
        return _stop

    def test_user_action_pay_credits_to_partner(self, **kwargs):
        '''
        [ NOTE ]: Instruction Set Details
            - pay = Target user email address
        '''
        log.debug('')
        print('[ * ]: User Action Pay Credits To Partner')
        _pay = self.session_manager_controller(
            controller='client', ctype='action', action='pay', pay=kwargs['pay'],
            credits=kwargs['credits'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_pay) + '\n')
        return _pay

    def test_user_action_add_contact_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action Add Contact List Record')
        _add_record = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact', contact='record',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            contact_list=kwargs['contact_list'],
            user_name=kwargs['user_name'], user_email=kwargs['user_email'],
            user_phone=kwargs['user_phone'], user_reference=kwargs['user_reference'],
            notes=kwargs['notes'],
        )
        print(str(_add_record) + '\n')
        return _add_record

    def test_user_action_view_contact_list(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action View Active Contact List')
        _view_list = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='contact',
            contact='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view_list) + '\n')
        return _view_list

    def test_user_action_view_contact_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User Action View Active Contact List Record')
        _view_record = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='contact',
            contact='record', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'], record=kwargs['record']
        )
        print(str(_view_record) + '\n')
        return _view_record

    def test_user_action_transfer_credits(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Transfer Credits.')
        _transfer = self.session_manager_controller(
            controller='client', ctype='action', action='transfer',
            transfer='credits', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'], transfer_to=kwargs['transfer_to'],
            credits=kwargs['credits']
        )
        print(str(_transfer) + '\n')
        return _transfer

    def test_user_action_convert_clock_to_credits(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Convert Clock To Credits')
        _convert = self.session_manager_controller(
            controller='client', ctype='action', action='convert', convert='clock2credits',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            minutes=kwargs['minutes']
        )
        print(str(_convert) + '\n')
        return _convert

    def test_user_action_view_transfer_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Transfer Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='transfer',
            transfer='list', client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_transfer_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Transfer Sheet Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='transfer',
            transfer='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_time_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Time Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='time',
            time='list', client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_time_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Time Sheet Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='time',
            time='record', record_id=kwargs['record_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_conversion_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Conversion Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='conversion',
            conversion='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_conversion_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Conversion Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='conversion',
            conversion='record', record_id=kwargs['record_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Account')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='account',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_edit_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Edit Account')
        _edit = self.session_manager_controller(
            controller='client', ctype='action', action='edit', edit='account',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            user_name=kwargs['user_name'], user_phone=kwargs['user_phone'],
#           user_email=kwargs['user_email'], user_pass=kwargs['user_pass'],
            user_alias=kwargs['user_alias']
        )
        print(str(_edit) + '\n')
        return _edit

    def test_user_action_view_credit_ewallet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Credit EWallet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='credit',
            credit='ewallet', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_credit_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Credit Clock')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='credit',
            credit='clock', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_invoice_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Invoice Sheet')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='invoice',
            invoice='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_invoice_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Invoice Record')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='invoice',
            invoice='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_create_credit_ewallet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Credit EWallet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='credit',
            credit='ewallet', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_credit_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Credit Clock')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='credit',
            credit='clock', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_transfer_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Transfer Sheet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='transfer',
            transfer='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_invoice_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Invoice Sheet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='invoice',
            invoice='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_conversion_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Conversion Sheet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='conversion',
            conversion='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_time_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Time Sheet')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='time',
            time='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_create_contact_list(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Create Contact List')
        _create = self.session_manager_controller(
            controller='client', ctype='action', action='new', new='contact',
            contact='list', client_id=kwargs['client_id'],
            session_token=kwargs['session_token'],
        )
        print(str(_create) + '\n')
        return _create

    def test_user_action_switch_credit_ewallet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Credit EWallet')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='credit',
            credit='ewallet', ewallet_id=kwargs['ewallet_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_credit_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Credit Clock')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='credit',
            credit='clock', clock_id=kwargs['clock_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_transfer_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Transfer Sheet')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='transfer_sheet',
            client_id=kwargs['client_id'], session_token=kwargs['session_token'],
            sheet_id=kwargs['sheet_id']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_invoice_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Invoice Sheet')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='invoice_sheet',
            sheet_id=kwargs['sheet_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_conversion_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Conversion Sheet')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='conversion_sheet',
            sheet_id=kwargs['sheet_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_time_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Time Sheet')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='time_sheet',
            sheet_id=kwargs['sheet_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_switch_contact_list(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Contact List')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='contact_list',
            list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_unlink_transfer_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Transfer Record')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='transfer',
            transfer='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_invoice_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Invoice Record')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='invoice',
            invoice='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_conversion_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Conversion Record')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='conversion',
            conversion='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_time_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Time Record')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='time',
            time='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_contact_record(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Contact Record')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='contact',
            contact='record', record_id=kwargs['record_id'],
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_transfer_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Transfer Sheet')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='transfer',
            transfer='list', list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_invoice_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Invoice Sheet')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='invoice',
            invoice='list', list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_conversion_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Conversion Sheet')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='conversion',
            conversion='list', list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_time_sheet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Time Sheet')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='time',
            time='list', list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_contact_list(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Contact List')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='contact',
            contact='list', list_id=kwargs['list_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_credit_ewallet(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Credit EWallet')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='credit',
            credit='ewallet', ewallet_id=kwargs['ewallet_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_credit_clock(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Credit Clock')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='credit',
            credit='clock', clock_id=kwargs['clock_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_unlink_user_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Unlink Account')
        _unlink = self.session_manager_controller(
            controller='client', ctype='action', action='unlink', unlink='account',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_unlink) + '\n')
        return _unlink

    def test_user_action_view_login_records(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Login Records')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='login',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_view_logout_records(self, **kwargs):
        log.debug('')
        print('[ * ]: User action View Logout Records')
        _view = self.session_manager_controller(
            controller='client', ctype='action', action='view', view='logout',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_view) + '\n')
        return _view

    def test_user_action_switch_active_session_user(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Switch Active Session User')
        _switch = self.session_manager_controller(
            controller='client', ctype='action', action='switch', switch='account',
            account_id=kwargs['account_id'], client_id=kwargs['client_id'],
            session_token=kwargs['session_token']
        )
        print(str(_switch) + '\n')
        return _switch

    def test_user_action_logout_account(self, **kwargs):
        log.debug('')
        print('[ * ]: User action Logout Account')
        _logout = self.session_manager_controller(
            controller='client', ctype='action', action='logout',
            client_id=kwargs['client_id'], session_token=kwargs['session_token']
        )
        print(str(_logout) + '\n')
        return _logout

    def test_system_action_interogate_ewallet_session(self, **kwargs):
        log.debug('')
        print('[ * ]: System action Interogate EWallet Session')
        _interogate = self.session_manager_controller(
            controller='system', ctype='action', action='interogate',
            interogate='session', session_id=kwargs['session_id']
        )
        print(str(_interogate) + '\n')
        return _interogate

    def test_system_action_interogate_ewallet_workers(self, **kwargs):
        log.debug('')
        print('[ * ]: System action Interogate EWallet Workers')
        _interogate = self.session_manager_controller(
            controller='system', ctype='action', action='interogate',
            interogate='workers'
        )
#       pp = pprint.PrettyPrinter(indent=4)
#       pp.pprint(str(_interogate) + '\n')
        print(str(_interogate) + '\n')
        return _interogate

    def test_system_action_cleanup_worker(self, **kwargs):
        log.debug('')
        print('[ * ]: System action Cleanup Session Workers')
        _clean = self.session_manager_controller(
            controller='system', ctype='action', action='cleanup',
            cleanup='workers'
        )
        print(str(_clean) + '\n')
        return _clean

    def test_system_action_cleanup_target_session(self, **kwargs):
        log.debug('')
        print('[ * ]: System action Cleanup Target Ewallet Session')
        _clean = self.session_manager_controller(
            controller='system', ctype='action', action='cleanup',
            cleanup='sessions', session_id=kwargs['session_id']
        )
        print(str(_clean) + '\n')
        return _clean

    def test_system_action_sweep_cleanup_ewallet_sessions(self, **kwargs):
        log.debug('')
        print('[ * ]: System action Sweep Cleanup Ewallet Sessions')
        _clean = self.session_manager_controller(
            controller='system', ctype='action', action='cleanup',
            cleanup='sessions',
        )
        print(str(_clean) + '\n')
        return _clean

    def test_session_manager_controller(self, **kwargs):
        print('[ TEST ] Session Manager')
#       open_in_port = self.test_open_instruction_listener_port()
#       listen = self.test_instruction_set_listener()
#       close_in_port = self.test_close_instruction_listener_port()
        client_id = self.test_request_client_id()
        worker = self.test_new_worker()
        session = self.test_new_session()
        session_token = self.test_request_session_token(client_id['client_id'])
        create_account = self.test_user_action_create_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user', user_pass='1234@!xxA', user_email='testuser@mail.com'
        )
        session_login = self.test_user_action_session_login(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user', user_pass='1234@!xxA'
        )
        print('[ 2 ]: Second user create.')
        create_account2 = self.test_user_action_create_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user_dinosaur', user_pass='1234@!xxA', user_email='testuserdinosaur@mail.com'
        )
        print('[ 2 ]: Second user login.')
        session_login2 = self.test_user_action_session_login(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='test_user_dinosaur', user_pass='1234@!xxA'
        )
        print('[ 2 ]: Second worker spawned')
        worker2 = self.test_new_worker()
        create_credit_ewallet = self.test_user_action_create_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_credit_clock = self.test_user_action_create_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_transfer_sheet = self.test_user_action_create_transfer_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_invoice_sheet = self.test_user_action_create_invoice_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_conversion_sheet = self.test_user_action_create_conversion_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_time_sheet = self.test_user_action_create_time_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        create_contact_list = self.test_user_action_create_contact_list(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )

        supply_credits = self.test_user_action_supply_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            currency='RON', credits=15, cost=4.74,
            notes='Test Credit Wallet Supply Notes...'
        )
        convert_credits_2_clock = self.test_user_action_convert_credits_to_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'], credits=5,
            notes='Test Credits To Clock Conversion Notes...'
        )
        start_clock_timer = self.test_user_action_start_clock_timer(
            client_id=client_id['client_id'], session_token=session_token['session_token']
        )
        time.sleep(3)
        pause_clock_timer = self.test_user_action_pause_clock_timer(
            client_id=client_id['client_id'], session_token=session_token['session_token']
        )
        time.sleep(3)
        resume_clock_timer = self.test_user_action_resume_clock_timer(
            client_id=client_id['client_id'], session_token=session_token['session_token']
        )
        time.sleep(3)
        stop_clock_timer = self.test_user_action_stop_clock_timer(
            client_id=client_id['client_id'], session_token=session_token['session_token']
        )
        pay_credits = self.test_user_action_pay_credits_to_partner(
            partner_account=1, credits=5, client_id=client_id['client_id'],
            session_token=session_token['session_token'],
            pay='system.core@alvearesolutions.com'
        )
        view_contact_list = self.test_user_action_view_contact_list(
            client_id=client_id['client_id'],
            session_token=session_token['session_token'],
        )
        add_contact_record = self.test_user_action_add_contact_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            contact_list=view_contact_list['contact_list'],
            user_name='This is bob', user_email='example@example.com', user_phone='095551234',
            user_reference='That weird guy coding wallets.', notes='WOOHO.'
        )
        view_contact_record = self.test_user_action_view_contact_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record=add_contact_record['contact_record']
        )
        transfer_credits = self.test_user_action_transfer_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            transfer_to='example@example.com', credits=50
        )
        convert_clock_2_credits = self.test_user_action_convert_clock_to_credits(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            minutes=13,
        )
        view_transfer_sheet = self.test_user_action_view_transfer_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_transfer_record = self.test_user_action_view_transfer_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
        view_time_sheet = self.test_user_action_view_time_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_time_record = self.test_user_action_view_time_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=33
        )
        view_conversion_sheet = self.test_user_action_view_conversion_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_conversion_record = self.test_user_action_view_conversion_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
        view_account = self.test_user_action_view_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        # TODO - password and email edits not supported
        edit_account = self.test_user_action_edit_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            user_name='New Name', user_phone='555555555', user_alias='New Alias',
            user_pass='1234asscdYEEBOY@!', user_email='new@user.mail'
        )
        view_credit_ewallet = self.test_user_action_view_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_credit_clock = self.test_user_action_view_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_invoice_sheet = self.test_user_action_view_invoice_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_invoice_record = self.test_user_action_view_invoice_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=1
        )
        switch_credit_ewallet = self.test_user_action_switch_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            ewallet_id=2
        )
        switch_credit_clock = self.test_user_action_switch_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            clock_id=2
        )
        switch_transfer_sheet = self.test_user_action_switch_transfer_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            sheet_id=2
        )
        switch_invoice_sheet = self.test_user_action_switch_invoice_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            sheet_id=2
        )
        switch_conversion_sheet = self.test_user_action_switch_conversion_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            sheet_id=2
        )
        switch_time_sheet = self.test_user_action_switch_time_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            sheet_id=2
        )
        switch_contact_list = self.test_user_action_switch_contact_list(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_transfer_record = self.test_user_action_unlink_transfer_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=2
        )
        unlink_invoice_record = self.test_user_action_unlink_invoice_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=2
        )
        unlink_conversion_record = self.test_user_action_unlink_conversion_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=2
        )
        unlink_time_record = self.test_user_action_unlink_time_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=2
        )
        unlink_contact_record = self.test_user_action_unlink_contact_record(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            record_id=2
        )
        unlink_transfer_sheet = self.test_user_action_unlink_transfer_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_invoice_sheet = self.test_user_action_unlink_invoice_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_conversion_sheet = self.test_user_action_unlink_conversion_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_time_sheet = self.test_user_action_unlink_time_sheet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_contact_list = self.test_user_action_unlink_contact_list(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            list_id=2
        )
        unlink_credit_ewallet = self.test_user_action_unlink_credit_ewallet(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            ewallet_id=2
        )
        unlink_credit_clock = self.test_user_action_unlink_credit_clock(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            clock_id=2
        )
        unlink_user_account = self.test_user_action_unlink_user_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_login_records = self.test_user_action_view_login_records(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        view_logout_records = self.test_user_action_view_logout_records(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        switch_active_account = self.test_user_action_switch_active_session_user(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
            account_id=2
        )
        logout_account = self.test_user_action_logout_account(
            client_id=client_id['client_id'], session_token=session_token['session_token'],
        )
        interogate_session = self.test_system_action_interogate_ewallet_session(
            session_id=1
        )
        interogate_workers = self.test_system_action_interogate_ewallet_workers()
        cleanup_workers = self.test_system_action_cleanup_worker()
        cleanup_target_session = self.test_system_action_cleanup_target_session(
            session_id=2
        )
        sweep_cleanup_sessions = self.test_system_action_sweep_cleanup_ewallet_sessions()

if __name__ == '__main__':
    ewallet_server = EWalletServer()
    run_tests = ewallet_server.test_session_manager_controller()


