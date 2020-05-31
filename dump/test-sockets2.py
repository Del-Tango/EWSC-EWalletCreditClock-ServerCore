import socket

class SocketHandler:

  def __init__(self, sock=None):
    if sock is None:
      self.sock = socket.socket(
      socket.AF_INET, socket.SOCK_STREAM)
    else:
      self.sock = sock

  def connect(self, host, port):
    self.sock.connect((host, port))

  def send(self, msg):
    totalsent = 0
    MSGLEN = len(msg)
    while totalsent < MSGLEN:
      sent = self.sock.send(str.encode(msg[totalsent:]))
      if sent == 0:
        raise RuntimeError("socket connection broken")

      totalsent = totalsent + sent

  def receive(self, EOFChar='\036'):
    msg = ''
    MSGLEN = 100
    while len(msg) < MSGLEN:
      chunk = self.sock.recv(MSGLEN-len(msg))
      if chunk.find(EOFChar) != -1:
        msg = msg + chunk
        return msg

      msg = msg + chunk
      return msg

_socket = SocketHandler()
print(_socket)
_socket.connect('127.0.0.1', 8080)
#   _send = _socket.send('hello')
#   print(_send)
_recv = _socket.receive()
print(_recv)

