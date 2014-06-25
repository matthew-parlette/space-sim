#!/usr/bin/env python

import socket
import json

TCP_IP = '127.0.0.1'
TCP_PORT = 10344
BUFFER_SIZE = 1024
MESSAGE = json.dumps({'action': 'login','user':'matt'})

try:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((TCP_IP, TCP_PORT))
  print "sending message:", MESSAGE
  s.sendall(MESSAGE + "\n")
  data = s.recv(BUFFER_SIZE)
finally:
  s.close()

print "received data:", data
