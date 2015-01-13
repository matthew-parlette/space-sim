#!/usr/bin/python

import argparse
import logging
import os
import json
import socket

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

class Menu(object):
    def __init__(self, state = {}, commands = {}, log = None):
        self.log = log
        self.state = state
        self.commands = commands

    def display(self, state = None, commands = None):
        self.state = state or self.state
        # Commands can be empty from the server (for development)
        self.commands = commands or self.commands

        if self.state:
            print "State\n%s\n%s" % (
                '=' * 5,
                str(self.state)
            )

            command_menu = self.command_dict(self.commands)
            print "Commands\n%s\n%s" % (
                '=' * 8,
                '\n'.join(["%s - %s" % (key, value) for (key, value) in command_menu.items()])
            )

            print "> ",
            input_string = getch()

            # Handle user input
            if input_string in command_menu.keys():
                # Is the user trying to quit?
                if input_string == 'q':
                    return None

                # User is not quitting, must be a valid command
                command = command_menu[input_string]
                command_to_server = { command: {} }
                # Get additional input for this command
                for param in self.commands[command]:
                    entry = raw_input("%s: " % str(param))
                    command_to_server[command][param] = entry
                return command_to_server
            else:
                # Invalid input, try again
                pass

        # If there are no commands, then just request state
        return {'state': {} }

    def command_dict(self, commands):
        """Return a dictionary with menu keys that correlate to commands."""
        result = {
            'q': 'quit', # Default to support quit on the client side
        }

        for key,value in commands.iteritems():
            for c in key:
                if c not in result.keys():
                    result[c] = key
                    break

        return result

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

    menu = Menu()

    while True:
        command = menu.display()

        if command:
            # Send command
            log.info("Sending command to server: %s" % str(command))
            fileobj.write(json.dumps(command))
            fileobj.write("\n")
            fileobj.flush()

            # Receive state
            log.info("Receiving from server...")
            line = fileobj.readline()
            if not line:
                log.info("Server disconnected")
                break

            log.info("Loading state as json...")
            response = json.loads(line)
            log.info("State received from server: %s" % str(response))
            menu.state = response['state']
            menu.commands = response['commands']
        else:
            # User has quit
            log.info("Exiting game...")
            break

    socket.close()
