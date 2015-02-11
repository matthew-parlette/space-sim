#!/usr/bin/python

import argparse
import logging
import os
import json
from game import Game
from gevent.server import StreamServer

global log
global args

class ServerGameAdapter(object):
    def __init__(self, log = None, bigbang = False):
        self.game = Game(log = log, bigbang = bigbang)

    def save(self):
        return self.game.save()

    def state(self, parameters = None):
        return self.game.state()

    def register(self, parameters):
        return self.game.register(parameters['name'], parameters['password'])

    def login(self, parameters):
        return self.game.login(parameters['name'], parameters['password'])

    def join_game(self, parameters):
        return self.game.join_game(parameters['ship_name'])

    def move(self, parameters):
        return self.game.move(parameters['direction'])

def json_repr(obj):
    """Represent instance of a class as JSON.
    Arguments:
    obj -- any object
    Return:
    String that reprent JSON-encoded object.
    """
    def serialize(obj):
        """Recursively walk object's hierarchy."""
        if isinstance(obj, (bool, int, long, float, basestring)):
            return obj
        elif isinstance(obj, dict):
            obj = obj.copy()
            for key in obj:
                obj[key] = serialize(obj[key])
            return obj
        elif isinstance(obj, list):
            return [serialize(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(serialize([item for item in obj]))
        elif hasattr(obj, '__dict__'):
            return serialize(obj.__dict__)
        else:
            return repr(obj) # Don't know how to handle, convert to string
    return json.dumps(serialize(obj))

def handle(socket, address):
    log.info("Connection received from %s" % str(address))
    log.info("Creating ServerGameAdapter...")
    game = ServerGameAdapter(log = log, bigbang = args.bigbang)
    fileobj = socket.makefile()

    while True:
        # Listen for commands
        line = fileobj.readline()
        if not line:
            log.info("Client disconnected, saving game...")
            game.save()
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
        fileobj.write(json.dumps(data, default=str))
        fileobj.write("\n")
        fileobj.flush()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--bigbang', action='store_true', help='Delete everything before starting')
    parser.add_argument('--version', action='version', version='0')
    global args
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
