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
ewallet_session_manager = EWalletSessionManager()

app = Flask(__name__)

# TODO - Pass down ResUtils() object to EWallet Session Manager
# TODO - Pass down Config() object to EWallet Session Manager
# TODO - Pass down SqlAlchemy.orm_session() object tot EWallet Session Manager
# TODO - Implement Basi HTTP Authentication

def handle_display_ewallet_session_manager_instruction_set_option(**kwargs):
    log.debug('')
    return display_ewallet_session_manager_instruction_set_option(**kwargs)

@app.route('/ewallet', methods=['GET'])
def handle_ewallet_session_manager_get_requests():
    log.debug('')
    return jsonify({'Introduction': 'This EWallet Credit Clock Server says "Hello".'})

@app.route('/ewallet/instruction_set', methods=['GET'])
def handle_ewallet_session_manager_instruction_set_get_requests():
    log.debug('')
    if not request.json:
        return jsonify(
            display_ewallet_session_manager_instruction_set_options()
        )
    instruction_set = request.json
    return jsonify(
        handle_display_ewallet_session_manager_instruction_set_option(
            **instruction_set
        )
    )

@app.route('/ewallet/instruction_set', methods=['POST'])
def handle_ewallet_session_manager_instruction_set_post_requests():
    log.debug('')
    instruction_set = request.json or None
    return jsonify(
        ewallet_session_manager.session_manager_controller(
            **instruction_set
        )
    )


if __name__ == '__main__':
    app.run()
