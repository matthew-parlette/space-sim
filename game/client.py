#!/usr/bin/python

import argparse
import logging
import os
import json
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

    # Create Client and connect
    host = 'localhost'
    port = 10344
    log.info("Connecting to %s:%s" % (str(host),str(port)))
    socket = socket.create_connection((host,port))
    log.info("Connected to %s:%s" % (str(host),str(port)))

    fileobj = socket.makefile()

    while True:
        # Send command
        data = {'state': {}}
        log.info("Sending command to server: %s" % str(data))
        fileobj.write(json.dumps(data))
        fileobj.write("\n")
        fileobj.flush()

        # Receive state
        log.info("Receiving from server...")
        line = fileobj.readline()
        if not line:
            log.info("Server disconnected")
            break

        log.info("Loading state as json...")
        state = json.loads(line)
        log.info("State received from server: %s" % str(state))
        log.info("Disconnecting")
        break

    socket.close()
