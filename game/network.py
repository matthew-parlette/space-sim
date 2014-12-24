#!/usr/bin/python

import argparse
import logging
import os
import sys
import socket

class Network(object):
    def __init__(self, hostname = None, port = None, log = None):
        self.log = log
        self.log.info("Initializing...")
        # Create socket to use for communication
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Define EOT character to denote when a message is complete
        self.eot = '|'

        # Initialize some variables
        self.hostname = hostname
        self.port = port
        self.connection = None
        self.client_address = None

    def connect(self):
        """Connect to a host, client mode.

        Returns boolean based on connection outcome."""
        raise NotImplementedError

    def listen(self):
        """Listen for connections, server mode.

        This sets the following variables:
            * self.connection
            * self.client_address

        Returns boolean based on bind command outcome."""
        raise NotImplementedError

    def send(self, data):
        """Send data on the socket.

        Returns boolean based on success of message being sent."""
        try:
            self.log.info("Sending data (%s)..." % str(data))
            if self.connection:
                self.connection.sendall(data + self.eot)
            else:
                self.socket.sendall(data + self.eot)
            return True
        except:
            self.log.error("Exception caught: %s" % str(sys.exc_info()))
            return False

    def receive(self):
        """Receive data on the socket.

        The data received is accessible through the last_response variable.

        Returns boolean based on success of a complete message received."""
        try:
            total_data = []
            data = ''
            self.log.info("Receiving data (eot is %s)..." % str(self.eot))
            while True:
                if self.connection:
                    data = self.connection.recv(16)
                else:
                    data = self.socket.recv(16)
                if self.eot in data:
                    total_data.append(data[:data.find(self.eot)])
                    break
                total_data.append(data)
                if len(total_data) > 1:
                    last_pair = total_data[-2] + total_data[-1]
                    if self.eot in last_pair:
                        total_data[-2] = last_pair[:last_pair.find(self.eot)]
                        total_data.pop()
                        break
            self.last_response = ''.join(total_data)
            self.log.info("Data received is '%s'" % str(self.last_response))
            return True
        except:
            self.log.error("Exception caught: %s" % str(sys.exc_info()))
            return False

    def close(self):
        """Close the existing connection."""
        self.log.info("Closing connection...")
        if self.connection:
            self.connection.close()
        else:
            self.socket.close()

        # Clear out the connection variables
        self.connection = None
        self.client_address = None
        return True

class Client(Network):
    def __init__(self, hostname, port, log = None):
        super(Client, self).__init__(hostname = hostname,
                                     port = port,
                                     log = log)
        # self.log.debug("Calling connect()...")
        # self.connect(hostname, port)

    def connect(self):
        self.log.info("Connecting to %s on port %s..." % (str(self.hostname),
                                                          str(self.port)))
        self.socket.connect((self.hostname,self.port))
        self.log.info("Connection established")
        return True

    def listen(self):
        self.log.error("listen() called from Client, this is a programming error")
        return False

class Server(Network):
    def __init__(self, hostname, port, log = None):
        super(Server, self).__init__(hostname = hostname,
                                     port = port,
                                     log = log)
        # self.log.debug("Calling listen()...")
        # self.listen(hostname, port)

    def connect(self):
        self.log.error("connect() called from Server, this is a programming error")
        return False

    def listen(self):
        self.log.info("Binding to %s at port %s..." % (str(self.hostname),
                                                       str(self.port)))
        self.socket.bind((self.hostname,self.port))

        self.log.info("Listening on port %s..." % str(self.port))
        self.socket.listen(5)

        self.log.info("Waiting for connection...")
        self.connection, self.client_address = self.socket.accept()
        self.log.info("Received connection from %s" % str(self.client_address))
        return True
