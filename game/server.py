#!/usr/bin/python

import argparse
import logging
import os
import socket

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='0')
    args = parser.parse_args()

    # Setup logging options
    log_level = logging.DEBUG if args.debug else logging.INFO
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(funcName)s(%(lineno)i):%(message)s')

    ## Console Logging
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    ## File Logging
    fh = logging.FileHandler(os.path.basename(__file__) + '.log')
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    log.info("Initializing...")

    log.info("Initializing network...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "0.0.0.0"
    port = 10344
    s.bind((host,port))

    log.info("Listening on port %s..." % str(port))
    s.listen(5)

    eot = '|'
    while True:
        log.info("Waiting for connection...")
        connection, client_addr = s.accept()

        try:
            log.info("Received connection from %s" % str(client_addr))
            while True:
                data = connection.recv(16)
                if data:
                    log.info("Received data: '%s'" % str(data))
                    log.info("Sending response to client...")
                    response = "Server received '%s'" % str(data)
                    connection.sendall(data + eot)
                else:
                    log.info("No more data from %s" % str(client_addr))
                    break
        finally:
            log.info("Closing connection...")
            connection.close()
