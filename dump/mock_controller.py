from ewallet import EWallet
from ewallet_session_manager import EWalletSessionManager, EWalletWorker


ewallet_session = EWallet()

def test_command_create_account():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='create',
            create='account',#
            user_name='test_user_name',
            user_email='mock@email.com',
            user_pass='Davidson13$',
            user_phone='test_user_phone',
            user_alias='test_user_alias',
            )

def test_command_login():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='login',#
            user_name='test_user_name',
            user_pass='Davidson13$',
            )

def test_command_logout():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='logout',
            )

def test_command_view_account():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='account',
            )

def test_command_view_transfer_sheet():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='transfer',
            transfer='list',
            )

def test_command_view_transfer_sheet_record():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='transfer',
            transfer='record',#
            record_id=1,
            )

def test_command_view_conversion_sheet():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='conversion',
            conversion='list',
            )

def test_command_view_conversion_sheet_record():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='conversion',
            conversion='record',#
            record_id=1,
            )

def test_command_view_credit_clock_time_sheet():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='time',
            time='list',
            )

def test_command_view_credit_clock_time_sheet_record():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='time',
            time='record',#
            record_id=1,
            )

def test_command_view_contact_list():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='contact',
            contact='list',
            )

def test_command_view_contact_list_record():
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='view',
            view='contact',
            contact='record',#
            record_id=1,
            )

def test_command_supply_credits(**kwargs):
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='create',
            create='transfer',#
            transfer_type='incomming',
            partner_ewallet=kwargs.get('partner_ewallet'),
            credits=10,
            transfer_from=kwargs.get('transfer_from'),
            transfer_to=kwargs.get('transfer_to'),
            reference='test_reference',
            )

def test_command_start_credit_clock(**kwargs):
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='time',
            timer='start',
            )

def test_command_stop_credit_clock(**kwargs):
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='time',
            timer='stop',
            )

def test_command_convert_credits_to_credit_clock(**kwargs):
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='create',
            create='conversion',
            conversion='to_minutes',#
            reference='test_reference',
            conversion_type='to_minutes',
            minutes=5,
            credits=5,
            )

def test_command_transfer_credits(**kwargs):
    return ewallet_session.ewallet_controller(
            controller='user',
            ctype='action',
            action='create',
            create='transfer',
            transfer_type='outgoing',#
            reference='test_reference',
            transfer_from=kwargs.get('transfer_from'),
            transfer_to=kwargs.get('transfer_to'),
            partner_ewallet=kwargs.get('partner_ewallet'),
            credits=3,
            )


