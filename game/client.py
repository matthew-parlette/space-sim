#!/usr/bin/python

import argparse
import logging
import os
import json
import socket
import pprint

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
args = None

class Menu(object):
    def __init__(self, state = {}, commands = {}, log = None):
        self.log = log
        self.state = state
        self.commands = commands

    def display(self, state = None, commands = None):
        self.state = state or self.state
        # Commands can be empty from the server (for development)
        self.commands = commands or self.commands

        # Initialize the command to request state
        request_state_command = {'state': {} }

        if self.state:
            if not args.debug:
                # clear screen
                os.system('clear')

            command_menu = self.command_dict(self.commands)
            self.render_state(self.state, self.commands, command_menu)
            # print "Commands\n%s\n%s" % (
            #     '=' * 8,
            #     '\n'.join(["%s - %s" % (key, value) for (key, value) in command_menu.items()])
            # )

            print "(? for menu) > ",
            input_string = getch()
            print ""

            # Handle user input
            if input_string in command_menu.keys():
                # Is the user trying to quit?
                if input_string == 'q':
                    return None
                if input_string == '?':
                    print "\n%s\nCommands\n%s\n%s\n%s" % (
                        '=' * 15,
                        '-' * 8,
                        '\n'.join(["%s - %s" % (key, value) for (key, value) in command_menu.items()]),
                        '=' * 15,
                    )
                    return request_state_command

                # User is not quitting, must be a valid command
                command = command_menu[input_string]
                # Default command to server is to simply request the state
                command_to_server = request_state_command
                # Do we need to get more input? Or just send the command?
                if isinstance(command, str) or isinstance(command, unicode):
                    # Command is just a string, what does the server need for
                    # this command?
                    command_to_server = { command: {} }
                    # The self.commands dictionary tells us what further
                    # input is required. Login/Register is special
                    if command in ['login','register']:
                        self.render_bar(str(command).upper())
                        username = raw_input("%s: " % "Username")
                        command_to_server[command]['name'] = username
                        password = raw_input("%s: " % "Password")
                        command_to_server[command]['password'] = password
                    else:
                        # Command is not login or register, fallback to generic
                        # command input
                        for param in self.commands[command]:
                            if isinstance(self.commands[command][param],list):
                                # Possible answers are provided, select one
                                user_choice = ""
                                options_as_dict = {}
                                for index, value in enumerate(self.commands[command][param]):
                                    options_as_dict[str(index+1)] = value
                                self.render_options(options_as_dict, title=param)
                                while user_choice not in [str(s) for s in range(1,len(options_as_dict.keys()) + 1)]:
                                    # print "\nEnter to cancel\n%s (%s) > " % (
                                    #     str(param),
                                    #     ",".join(self.commands[command][param])
                                    # ),
                                    print "\nEnter to cancel\n%s > " % (
                                        str(param),
                                    ),
                                    user_choice = getch().lower()
                                    if user_choice == '\r':
                                        # Cancelled command, return nothing
                                        return request_state_command
                                command_to_server[command][param] = options_as_dict[user_choice]
                            else:
                                # Possible answers are not provided, assume
                                # free form text
                                entry = raw_input("%s: " % str(param))
                                command_to_server[command][param] = entry
                elif isinstance(command, dict):
                    # command is already a dictionary, send it to server
                    command_to_server = command
                elif isinstance(command, list):
                    self.log.info("command %s is a list" % str(command))
                    # command is a list, convert it to a dictionary
                    # command_dict = {}
                    # for index, value in enumerate(command):
                    #     command_dict[str(index)] = value
                    # selection = self.render
                    # command_to_server = {command: command_dict[str(selection)]}
                return command_to_server
            else:
                # Invalid input, try again
                pass

        # If there are no commands, then just request state
        return request_state_command

    def command_dict(self, commands):
        """Return a dictionary with menu keys that correlate to commands."""
        result = {
            'q': 'quit', # Default to support quit on the client side
            '?': 'help', # Show help menu
        }

        # The move command is special, add the possible move
        # directions to the command dict
        if 'move' in commands and 'direction' in commands['move']:
            for direction in commands['move']['direction']:
                if direction not in result.keys():
                    result[direction] = {'move': {'direction': direction}}

        # Go through the rest of the commands
        for key,value in commands.iteritems():
            for char in key:
                if char not in result.keys():
                    result[char] = key
                    break

        self.log.info("command_dict loaded as %s" % str(result))
        return result

    def render_state(self, state, commands, command_dict):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()

        if 'user' in state:
            if 'token' in state['user'] and state['user']['token']:
                # User is logged in
                # print "Player: %s" % state['user']['name']
                if 'user_location' in state:
                    if 'name' in state['user_location']:
                        # User is in the game
                        # print "In: %s (your ship)" % state['user_location']['name']
                        if 'sector' in state:
                            if 'name' in state['sector'] and 'coordinates' in state['sector']:
                                # User is in a sector
                                self.render_sector(state, commands)
                        elif 'at' in state:
                            self.render_location(state, commands)
                    else:
                        # User not in game
                        pass
            else:
                # User is not logged in
                # print "Player: Not logged in"
                self.render_options(
                    command_dict,
                    "Welcome"
                )

    def render_options(self, command_dict, title = None):
        """
        Render all available options on the screen.

        This skips the quit and help (?) commands, since they are common.

        The display assumes the first character of each option string is the
        command (single character that is the key for the command in
        command_dict).
        """
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()
        # title
        self.render_bar(title)
        # main
        print "| " + "".ljust(int(width) - 4) + " |"
        for key in command_dict.keys():
            if key not in ['q','?']:
                if key == command_dict[key][:1]:
                    # Key is the start of the option
                    # example: Key: R, Value: Ready
                    print "| (%s)%s |" % (
                        key.upper(),
                        command_dict[key][1:].ljust(int(width) - 7),
                    )
                else:
                    # Key is not the start of the option
                    # example: Key: 1, Value: Ready
                    print "| (%s) %s |" % (
                        key.upper(),
                        command_dict[key].ljust(int(width) - 8),
                    )
        print "| " + "".ljust(int(width) - 4) + " |"
        # footer
        self.render_bar()

    def render_bar(self, text = None):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()
        print "-" * int(width)
        if text:
            self.render_line(text)
            print "-" * int(width)

    def render_line(self, text = "", border = True):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()
        if border:
            print "| " + text.ljust(int(width) - 4) + " |"
        else:
            print text

    def render_sector(self, state, commands):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()
        left_section_width = int(int(width) * 0.75)
        main_display_height = int(height) - 5

        self.render_bar("Sector %s (%s,%s)" % (
            state['sector']['name'],
            state['sector']['coordinates']['x'],
            state['sector']['coordinates']['y'],
        ))

        # self.render_line("".ljust(left_section_width) + "| ")

        left_screen = ["" for x in range(main_display_height)]
        if 'stars' in state['sector'] and state['sector']['stars']:
            left_screen[1]   = "Stars: "
            left_screen[1]  += " - ".join([star['name'] for star in state['sector']['stars']])
        if 'planets' in state['sector'] and state['sector']['planets']:
            left_screen[3]   = "Planets: "
            left_screen[3]  += " - ".join([planet['name'] for planet in state['sector']['planets']])
        if 'stations' in state['sector'] and state['sector']['stations']:
            left_screen[5]   = "Stations: "
            left_screen[5]  += " - ".join([station['name'] for station in state['sector']['stations']])
        if 'ports' in state['sector'] and state['sector']['ports']:
            left_screen[7]   = "Ports: "
            left_screen[7]  += " - ".join([port['name'] for port in state['sector']['ports']])
        left_screen[-1]  = "Warps to: "
        left_screen[-1] += " - ".join(commands['move']['direction'])

        right_screen = ["" for x in range(main_display_height)]
        right_screen[1] = "Ship Information"
        right_screen[2] = state['user_location']['name']
        if 'holds' in state['user_location']:
            right_screen[3] = "Cargo: %s/%s" % (
                0,
                state['user_location']['holds'],
            )
        if 'warp' in state['user_location']:
            right_screen[4] = "Warp Speed: %s" % state['user_location']['warp']
        if 'weapons' in state['user_location'] and state['user_location']['weapons']:
            right_screen[5] = "Weapons: %s" % state['user_location']['weapons']
        if 'hull' in state['user_location']:
            right_screen[6] = "Hull: %s" % state['user_location']['hull']
        if 'shields' in state['user_location']:
            right_screen[7] = "Shields: %s" % state['user_location']['shields']

        for i in range(0,main_display_height):
            left = left_screen[i]
            right = right_screen[i]
            self.render_line(
                "%s| %s" % (
                    left.ljust(left_section_width),
                    right,
                )
            )

        self.render_bar()

    def render_location(self, state, commands):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()
        left_section_width = int(int(width) * 0.75)
        main_display_height = int(height) - 5

        self.render_bar("%s (%s,%s)" % (
            state['at']['name'],
            state['at']['location']['x'],
            state['at']['location']['y'],
        ))

        left_screen = ["" for x in range(main_display_height)]
        for index, key in enumerate(commands):
            left_screen[-(index+1)] = "(%s)%s" % (
                str(key[:1]),
                str(key[1:])
            )

        right_screen = ["" for x in range(main_display_height)]
        right_screen[1] = "Ship Information"
        right_screen[2] = state['user_location']['name']
        if 'holds' in state['user_location']:
            right_screen[3] = "Cargo: %s/%s" % (
                0,
                state['user_location']['holds'],
            )
        if 'warp' in state['user_location']:
            right_screen[4] = "Warp Speed: %s" % state['user_location']['warp']
        if 'weapons' in state['user_location'] and state['user_location']['weapons']:
            right_screen[5] = "Weapons: %s" % state['user_location']['weapons']
        if 'hull' in state['user_location']:
            right_screen[6] = "Hull: %s" % state['user_location']['hull']
        if 'shields' in state['user_location']:
            right_screen[7] = "Shields: %s" % state['user_location']['shields']

        for i in range(0,main_display_height):
            left = left_screen[i]
            right = right_screen[i]
            self.render_line(
                "%s| %s" % (
                    left.ljust(left_section_width),
                    right,
                )
            )

        self.render_bar()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='0')
    global args
    args = parser.parse_args()

    # Setup logging options
    log_level = logging.DEBUG if args.debug else logging.INFO
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(funcName)s(%(lineno)i):%(message)s')

    ## Console Logging
    if args.debug:
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

    menu = Menu(log = log)

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
