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
    host = 'localhost'
    port = 10344

    log.info("Connecting to %s on port %s..." % (str(host),str(port)))
    s.connect((host,port))

    try:
        data = "here's a message"
        log.info("Sending data to server...")
        s.sendall(data)

        eot = '|'
        total_data = []
        data = ''
        log.info("Reading data from server (eot is %s)..." % str(eot))
        while True:
            data = s.recv(16)
            if eot in data:
                total_data.append(data[:data.find(eot)])
                break
            total_data.append(data)
            if len(total_data) > 1:
                last_pair = total_data[-2] + total_data[-1]
                if eot in last_pair:
                    total_data[-2] = last_pair[:last_pair.find(eot)]
                    total_data.pop()
                    break
        response = ''.join(total_data)
        log.info("Response from server is '%s'" % str(response))
    finally:
        log.info("Closing connection...")
        s.close()
