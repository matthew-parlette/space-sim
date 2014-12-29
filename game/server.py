#!/usr/bin/python

import argparse
import logging
import os
import json
from game import Game
from gevent.server import StreamServer

log = None

class ServerGameAdapter(object):
    def __init__(self, log = None):
        self.game = Game(log = log)

    def save(self):
        return self.game.save()

    def state(self, parameters = None):
        return self.game.state()

    def register(self, parameters):
        return self.game.register(parameters['name'], parameters['password'])

    def login(self, parameters):
        return self.game.login(parameters['name'], parameters['password'])

def handle(socket, address):
    log.info("Connection received from %s" % str(address))
    log.info("Creating ServerGameAdapter...")
    game = ServerGameAdapter(log = log)
    fileobj = socket.makefile()

    while True:
        # Listen for commands
        line = fileobj.readline()
        if not line:
            log.info("Client disconnected")
            break
        # Process line as a command
        command_dict = json.loads(line)
        log.info("Command from client: '%s'" % str(command_dict))
        if len(command_dict.keys()) is 1:
            command = command_dict.keys()[0]
            method = getattr(game, str(command), None)
            if method:
                log.info("Command is '%s'" % str(command))
                method(command_dict[command])
            else:
                log.error("Command '%s' not found in ServerGameAdapter" % str(command))
        else:
            log.error("Command dictionary from client includes multiple keys")

        # Respond to command
        state, commands = game.state()
        data = {'state': state, 'commands': commands}
        fileobj.write(json.dumps(data))
        fileobj.write("\n")
        fileobj.flush()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='0')
    args = parser.parse_args()

    # Setup logging options
    global log
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

    host = '0.0.0.0'
    port = 10344
    server = StreamServer((host, port), handle)
    log.info("Server initialized on %s:%s, listening..." % (str(host),str(port)))
    server.serve_forever()
