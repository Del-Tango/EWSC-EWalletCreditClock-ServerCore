import socket
import sys
import selectors
import types
import pysnooper


'''
    [ NOTE ]: Multiconn socket handler for both server and client sides.
'''
class SocketHandler():

    def __init__(self, *args, **kwargs):
        self.sock = kwargs.get('sock') or self.create_socket()
        self.host = kwargs.get('host') or '127.0.0.1'
        self.port = kwargs.get('port') or 65432
        self.sel = selectors.DefaultSelector()

    # FETCHERS

    def fetch_socket_values(self):
        _values = {
                'sock': self.sock,
                'host': self.host,
                'port': self.port,
                'sel': self.sel,
                }
        return _values

    def view_handler_values(self):
        print(str(self.fetch_socket_values))

    # SETTERS

    def set_socket(self, socket):
        self.sock = socket
        return True

    # GENERAL

    def create_socket(self, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    #@pysnooper.snoop()
    def bind_socket(self, sock, **kwargs):
        bind = sock.bind((self.host, self.port))
        listen = sock.listen()
        return True

    #@pysnooper.snoop()
    def accept_connection(self, sock, **kwargs):
        conn, addr = sock.accept()
        if kwargs.get('multiconn'):
            conn.setblocking(False)
        return {'conn': conn, 'addr': addr}

    @pysnooper.snoop()
    def accept_wrapper(self, sock):
        # Should be ready to read
        accept = self.accept_connection(sock, multiconn=True)
        set_socket = self.set_socket(accept['conn'])
        print("Accepted connection from", accept['addr'])
        data = types.SimpleNamespace(addr=accept['addr'], inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(accept['conn'], events, data=data)

#   @pysnooper.snoop()
    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print("Closing connection to", data.addr)
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print("Echoing", repr(data.outb), "to", data.addr)
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]


    # ACTIONS

    def destroy_socket(self, sock, **kwargs):
        sock.close()
        return True

    def send_data(self, conn, data, **kwargs):
        conn.sendall(data)
        return True

    def receive_data(self, conn, **kwargs):
        data = conn.recv(1024)
        return data

    def process_data(self, **kwargs):
        print('Data received : {}'.format(kwargs.get('data')))
        return True

    def incomming_transmission(self, conn, **kwargs):
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()
            self.destroy_socket(conn)

    #@pysnooper.snoop()
    def start_listener(self, **kwargs):
        with self.sock as s:
            self.bind_socket(s)
            accept = self.accept_connection(s)
            self.sel.register(s, selectors.EVENT_READ, data=None)
            transmission = self.incomming_transmission(**accept)

_socket_handler = SocketHandler()
_view = _socket_handler.view_handler_values()
_socket_handler.start_listener()

##############################################################################
# CODE DUMP
###############################################################################

# def send(self, msg):
#   totalsent = 0
#   MSGLEN = len(msg)
#   while totalsent < MSGLEN:
#     sent = self.sock.send(str.encode(msg[totalsent:]))
#     if sent == 0:
#       raise RuntimeError("socket connection broken")

#     totalsent = totalsent + sent

# def receive(self, EOFChar='\036'):
#   msg = ''
#   MSGLEN = 100
#   while len(msg) < MSGLEN:
#     chunk = self.sock.recv(MSGLEN-len(msg))
#     if chunk.find(EOFChar) != -1:
#       msg = msg + chunk
#       return msg

#     msg = msg + chunk
#     return msg

#       data = False
#       with conn:
#           print('Connected by', kwargs.get('addr'))
#           try:
#               while True:
#                   data = self.receive_data(conn)
#                   if not data:
#                       break
#                   self.send_data(conn, data)
#               self.destroy_socket(conn)
#           except KeyboardInterrupt:
#               print('Caught keyboard interrupt. Exit Alive.')
#       return True

###############################################################################
# SERVER

#   import sys
#   import socket
#   import selectors
#   import types

#   sel = selectors.DefaultSelector()


#   def accept_wrapper(sock):
#       conn, addr = sock.accept()  # Should be ready to read
#       print("accepted connection from", addr)
#       conn.setblocking(False)
#       data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
#       events = selectors.EVENT_READ | selectors.EVENT_WRITE
#       sel.register(conn, events, data=data)

#   def service_connection(key, mask):
#       sock = key.fileobj
#       data = key.data
#       if mask & selectors.EVENT_READ:
#           recv_data = sock.recv(1024)  # Should be ready to read
#           if recv_data:
#               data.outb += recv_data
#           else:
#               print("closing connection to", data.addr)
#               sel.unregister(sock)
#               sock.close()
#       if mask & selectors.EVENT_WRITE:
#           if data.outb:
#               print("echoing", repr(data.outb), "to", data.addr)
#               sent = sock.send(data.outb)  # Should be ready to write
#               data.outb = data.outb[sent:]


#   if len(sys.argv) != 3:
#       print("usage:", sys.argv[0], "<host> <port>")
#       sys.exit(1)

#   host, port = sys.argv[1], int(sys.argv[2])
#   lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#   lsock.bind((host, port))
#   lsock.listen()
#   print("listening on", (host, port))
#   lsock.setblocking(False)
#   sel.register(lsock, selectors.EVENT_READ, data=None)

#   try:
#       while True:
#           events = sel.select(timeout=None)
#           for key, mask in events:
#               if key.data is None:
#                   accept_wrapper(key.fileobj)
#               else:
#                   service_connection(key, mask)
#   except KeyboardInterrupt:
#       print("caught keyboard interrupt, exiting")
#   finally:
#       sel.close()


#
