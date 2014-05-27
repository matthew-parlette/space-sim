#!/usr/bin/env python

import socket

TCP_IP = '127.0.0.1'
TCP_PORT = 10344
BUFFER_SIZE = 1024
MESSAGE = "test client message"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print "sending message:", MESSAGE
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print "received data:", data
