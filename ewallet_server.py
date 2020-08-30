import logging

from flask import Flask, request, jsonify

from base.ewallet_session_manager import EWalletSessionManager
from base.config import Config
from base.res_utils import ResUtils
from base.ewallet_dox import \
    display_ewallet_session_manager_instruction_set_option, \
    display_ewallet_session_manager_instruction_set_options

config, res_utils = Config(), ResUtils()
log = logging.getLogger(config.log_config['log_name'])
ewallet_session_manager = EWalletSessionManager(
    config=config, res_utils=res_utils,
)

app = Flask(__name__)

# HANDLERS


def handle_display_ewallet_session_manager_instruction_set_option(**kwargs):
    log.debug('')
    return display_ewallet_session_manager_instruction_set_option(**kwargs)


@app.route('/ewallet', methods=['GET'])
def handle_ewallet_session_manager_get_requests():
    log.debug('')
    return jsonify({
        'message': 'The EWallet Credit Clock Virtual Payment System\n'
                   'We make it easy for you to get paid! - Alveare Solutions -'
    })


@app.route('/ewallet/instruction-set', methods=['GET'])
def handle_ewallet_session_manager_instruction_set_get_requests():
    log.debug('')
    instruction_set = request.json or None
    if not instruction_set:
        return jsonify(
            display_ewallet_session_manager_instruction_set_options()
        )
    return jsonify(
        handle_display_ewallet_session_manager_instruction_set_option(
            **instruction_set
        )
    )


@app.route('/ewallet/instruction-set', methods=['POST'])
def handle_ewallet_session_manager_instruction_set_post_requests():
    log.debug('')
    instruction_set = request.json or None
    if not instruction_set:
        return error_no_instruction_set_found()
    elif isinstance(instruction_set, dict) and \
            instruction_set.get('controller') == 'system':
        return error_illegal_system_portal()
    return jsonify(
        ewallet_session_manager.session_manager_controller(
            **instruction_set
        )
    )

# ERRORS


def error_no_instruction_set_found():
    error = 'No EWallet Server Core instruction set found.'
    log.error(error)
    return jsonify({
        'failed': True,
        'error': error,
    })


def error_illegal_system_portal():
    error = 'Illegal portal for (EWSC - Server Core) '\
            'system actions and events.'
    log.error(error)
    return jsonify({
        'failed': True,
        'error': error,
    })


if __name__ == '__main__':
    app.run()
