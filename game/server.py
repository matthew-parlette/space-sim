#!/usr/bin/python

import argparse
import logging
import os
import json
from network import Server
from game import Game

class ServerGameAdapter(object):
    def __init__(self, log = None):
        self.game = Game(log = log)

    def save(self):
        return self.game.save()

    def state(self):
        return self.game.state()

    def register(self, parameters):
        return self.game.register(parameters['name'], parameters['password'])

    def login(self, parameters):
        return self.game.login(parameters['name'], parameters['password'])

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

    # Create Server and start listening
    server = Server(hostname = '', port = 10344, log = log)
    if server.listen():
        # Client has connected, create game and send state
        connected = True
        game = ServerGameAdapter(log = log)
        state, commands = game.state()
        data = {'state': state, 'commands': commands}
        while connected:
            if server.send(json.dumps(data)):
                if server.receive():
                    command_dict = json.loads(server.last_response)
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

                    # For now, the client will disconnect here
                    # connected = False
                else:
                    log.error("server.receive() returned False")
            else:
                log.error("server.send() returned False")
                connected = False
        game.save()
    server.close()
