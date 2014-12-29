#!/usr/bin/python

import argparse
import logging
import os
import json
from network import Client

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
    client = Client(hostname = host, port = port, log = log)

    if client.connect():
        if client.receive():
            log.info("State from server: '%s'" % str(client.last_response))

            # raw_input("Press enter to send registration to server...")

            command = {'register': {'name': 'matt', 'password': 'matt'}}
            if client.send(json.dumps(command)):
                log.info("Command sent to server, sending login...")
                command = {'login': {'name': 'matt', 'password': 'matt'}}
                if client.receive():
                    if client.send(json.dumps(command)):
                        log.info("Command sent to server, disconnecting...")
                    else:
                        log.error("client.send() returned False")
                else:
                    log.error("client.receive() returned False")
            else:
                log.error("client.send() returned False")
        else:
            log.error("client.receive() returned False")
    client.close()
