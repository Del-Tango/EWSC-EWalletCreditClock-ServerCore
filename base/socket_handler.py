from .config import Config

import socket
# import sys
import selectors
import types
import logging
import pysnooper
# import json

config = Config()
log_config = config.log_config
log = logging.getLogger(log_config['log_name'])


class EWalletSocketHandler():
    '''
    [ NOTE ]: Multiconn socket handler for both server and client sides.
    '''

    def __init__(self, *args, **kwargs):
        self.session_manager = kwargs.get('session_manager')
        self.in_sock = kwargs.get('in_sock') or self.create_socket()
        self.out_sock = kwargs.get('out_sock') or self.create_socket()
        self.host = kwargs.get('host') or '127.0.0.1'
        self.in_port = kwargs.get('in_port') or 8080
        self.out_port = kwargs.get('out_port') or 8081
        self.sel = selectors.DefaultSelector()

    # FETCHERS

    #@pysnooper.snoop()
    def fetch_socket_values(self):
        log.debug('')
        values = {
            'in_sock': self.in_sock,
            'out_sock': self.out_sock,
            'host': self.host,
            'in_port': self.in_port,
            'out_port': self.out_port,
            'sel': self.sel,
        }
        return values

    # SETTERS

    #@pysnooper.snoop()
    def set_input_socket(self, socket):
        log.debug('')
        self.in_sock = socket
        return True

    def set_output_socket(self, socket):
        log.debug('')
        self.out_sock = socket
        return True

    # GENERAL

    #@pysnooper.snoop()
    def create_socket(self, **kwargs):
        log.debug('')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    #@pysnooper.snoop()
    def bind_input_socket(self, sock, **kwargs):
        log.debug('')
        bind = sock.bind((self.host, self.in_port))
        listen = sock.listen()
        return True

    def bind_output_socket(self, sock, **kwargs):
        log.debug('')
        bind = sock.bind((self.host, self.out_port))
        return True

    def connect_output_socket(self, sock, **kwargs):
        log.debug('')
        conn = self.out_sock.connect((self.host, self.out_port))
        return True

    #@pysnooper.snoop()
    def accept_connection(self, sock, **kwargs):
        log.debug('')
        conn, addr = sock.accept()
        if kwargs.get('multiconn'):
            conn.setblocking(False)
        return {'conn': conn, 'addr': addr}

    #@pysnooper.snoop()
    def accept_wrapper(self, sock):
        log.debug('')
        # Should be ready to read
        accept = self.accept_connection(sock, multiconn=True)
        set_socket = self.set_input_socket(accept['conn'])
        log.info('Accepted connection from {}'.format(accept['addr']))
        data = types.SimpleNamespace(addr=accept['addr'], inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(accept['conn'], events, data=data)

    @pysnooper.snoop()
    def service_connection(self, key, mask):
        log.debug('')
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = self.receive_data(sock)
            if recv_data:
                data.outb += recv_data
            else:
                log.info('Closing connection to {}.'.format(data.addr))
                self.destroy_socket(sock)
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                self.process_data(data=data)

    # ACTIONS

    #@pysnooper.snoop()
    def destroy_socket(self, sock, **kwargs):
        log.debug('')
        try:
            self.sel.unregister(sock)
        except Exception as e:
            log.error(e)
        sock.close()
        return True

    #@pysnooper.snoop()
    def send_data(self, conn, data, **kwargs):
        log.debug('')
        # Should be ready to write
        conn.sendall(data)
        return True

    #@pysnooper.snoop()
    def receive_data(self, conn, **kwargs):
        log.debug('')
        # Should be ready to read
        data = conn.recv(1024)
        return data

    #@pysnooper.snoop()
    def process_data(self, **kwargs):
        log.debug('')
        data = kwargs.get('data')
        if not data:
            return self.error_no_data_found()
        try:
            decoded_data = eval(str(data.outb.decode('utf-8')))
        except Exception as e:
            log.warning(e)
            return self.warning_invalid_command_chain_instruction_set(str(data.outb.decode('utf-8')))
        if not decoded_data:
            return self.warning_no_data_received()
        if not isinstance(decoded_data, dict):
            return self.warning_invalid_command_chain_instruction_set(decoded_data)
        reply_data = self.session_manager.session_manager_controller(**decoded_data)
        encoded_data = str(reply_data).encode('utf-8')
        return self.issue_reply(reply=encoded_data)

    @pysnooper.snoop()
    def incomming_transmission(self, conn, **kwargs):
        log.debug('')
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            log.info('Caught keyboard interrupt, exiting.')
        finally:
            self.sel.close()
            self.destroy_socket(conn)

#   @pysnooper.snoop()
    def issue_reply(self, **kwargs):
        log.debug('')
        try:
            sock = self.create_socket()
            try:
                sock.connect((self.host, self.out_port))
            except Exception as e:
                log.error(e)
            self.send_data(sock, kwargs.get('reply'))
            sock.close()
        except:
            return self.warning_could_not_send_reply_to_socket(
                    repr(kwargs.get('reply')), self.out_port
                    )
        return True

    #@pysnooper.snoop()
    def start_listener(self, **kwargs):
        log.debug('')
        with self.in_sock as s:
            self.bind_input_socket(s)
            accept = self.accept_connection(s)
            self.sel.register(s, selectors.EVENT_READ, data=None)
            transmission = self.incomming_transmission(**accept)

    # DISPLAY

    def view_handler_values(self):
        log.debug('')
        values = (str(self.fetch_socket_values()))
        return values

    # WARNINGS

    def warning_invalid_command_chain_instruction_set(self, instruction_set):
        log.warning(
                'Could not process command. Invalid command chain instruction set {}.'\
                .format(instruction_set)
                )
        return False

    def warning_no_data_received(self):
        log.warning('No data received.')
        return False

    def warning_could_not_send_reply_to_socket(self, reply, port):
        log.warning('Could not send reply {} to port {}.'.format(reply, port))
        return False

    # ERRORS

    def error_no_data_found(self):
        log.error('No data found.')
        return False


if __name__ == "__main__":
    _socket_handler = EWalletSocketHandler()
    _view = _socket_handler.view_handler_values()
    _socket_handler.start_listener()

##############################################################################
# CODE DUMP
###############################################################################

