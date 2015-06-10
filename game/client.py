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

class Screen(object):
    """
    A screen has three parts:
    * title
    * left screen (main section)
    * right screen (status section)
    """
    def __init__(self, left_screen_percent = 0.75, right_screen_enabled = False, log = None):
        """
        left_screen_percent: percent (from 0 to 1) of the screen taken up by the left screen
        """
        self.log = log
        self._left_screen = []
        self._right_screen = []
        self._title = None
        self._left_screen_percent = left_screen_percent
        self._right_screen_enabled = right_screen_enabled

    def _refresh_dimensions(self):
        self._height, self._width = os.popen('stty size', 'r').read().split()
        self._left_width = int(int(self._width) * self._left_screen_percent)
        self._main_display_height = int(self._height) - 5

    @property
    def height(self):
        self._refresh_dimensions()
        return self._height

    @property
    def width(self):
        self._refresh_dimensions()
        return self._width

    @property
    def dimensions(self):
        self._refresh_dimensions()
        return (self._height,self._width)

    def render(self):
        """
        Render the title and screens to the console.
        """
        self.log.debug("Rendering screen (right screen enabled? %s)" % str(self._enable_right_screen))
        self._render_bar()
        self._render_line(left = self._title, title = True)
        self._render_bar()
        for i in range(0,self._main_display_height):
            if self._enable_right_screen:
                if i < len(self._left_screen) and i < len(self._right_screen):
                    # Both left and right screens have values
                    left = self._left_screen[i]
                    right = self._right_screen[i]
                    self._render_line(left = left,right = right)
                elif i < len(self._left_screen):
                    # Left buffer has a value, right is empty
                    self._render_line(left = self._left_screen[i])
                elif i < len(self._right_screen):
                    # Left buffer is empty, right has a value
                    self._render_line(right = self._right_screen[i])
                else:
                    # Left and right buffers are empty
                    self._render_line()
            else:
                # Right screen is disabled
                if i < len(self._left_screen):
                    # Both left and right screens have values
                    left = self._left_screen[i]
                    self._render_line(left = left)
                else:
                    # Left buffer is empty
                    self._render_line()

        self._render_bar()

    def _render_bar(self, text = None):
        # Get the console dimensions
        print "-" * int(self.width)
        if text:
            self.render_line(text)
            print "-" * int(self.width)

    def _render_line(self, left = "", right = "", border = True, title = False):
        if self._enable_right_screen and not title:
            if border:
                print "| %s%s |" % (
                    left.ljust(int(self._left_width) - 6),
                    "| %s" % (right.ljust(int(self.width) - int(self._left_width))),
                )
            else:
                print left
        else:
            if border:
                print "| " + left.ljust(int(self.width) - 4) + " |"
            else:
                print left

class Menu(object):
    def __init__(self, state = {}, commands = {}, log = None):
        self.log = log
        self._state = state
        self._commands_from_server = commands
        self._state_cache = None
        self.screen = Screen(log = self.log)

    def parse_json(self, json_string):
        self.log.info("Loading state as json...")
        response = json.loads(json_string)
        self.log.info("State received from server: %s" % str(response))
        self._state = response['state']
        self._commands_from_server = response['commands']

    def display(self, state = None, commands = None):
        # Initialize the command to request state
        request_state_command = {'state': {} }

        if self._state:
            if not args.debug:
                # clear screen
                os.system('clear')

            self.update_state_cache()

            self.build_command_dict()

            self.render_state()

            user_command = self.parse_input(self.get_input())
            self.log.debug("user_command is %s" % str(user_command))
            return user_command

        # If there are no commands, then just request state
        return request_state_command

    def get_input(self):
        print "(? for menu) > ",
        user_input = getch()
        print ""
        return user_input

    def parse_input(self, user_input):
        # Handle user input
        command_menu = self._command_dict
        request_state_command = {'state': {} }
        if user_input in command_menu.keys():
            # Is the user trying to quit?
            if user_input == 'q':
                self.log.info("User is quitting...")
                self.log.debug("parse_input() returning %s" % str(None))
                return None
            if user_input == '?':
                self.log.info("User is requesting help...")
                self.render_state(help = True)
                self.log.debug("parse_input() returning %s" % str(request_state_command))
                return request_state_command

            # User is not quitting, must be a valid command
            command = command_menu[user_input]
            self.log.debug("user's command is %s" % str(command))
            # Default command to server is to simply request the state
            command_to_server = request_state_command
            # Do we need to get more input? Or just send the command?
            if isinstance(command, str) or isinstance(command, unicode):
                # Command is just a string, what does the server need for
                # this command?
                command_to_server = { command: {} }
                # The self.commands dictionary tells us what further
                # input is required. Login/Register is special
                # if command in ['login','register']:
                #     self.render_bar(str(command).upper())
                #     username = raw_input("%s: " % "Username")
                #     command_to_server[command]['name'] = username
                #     password = raw_input("%s: " % "Password")
                #     command_to_server[command]['password'] = password
                # elif command in ['join_game']:
                #     self.render_bar(str(command).replace('_',' ').upper())
                # else:
                    # Command is not login or register, fallback to generic
                    # command input
                for param in self._commands_from_server[command]:
                    self.log.debug("processing command parameter %s..." % str(param))
                    if isinstance(self._commands_from_server[command][param],list):
                        self.log.debug("parameter %s is a list" % str(param))
                        # Possible answers are provided, select one
                        user_choice = ""
                        options_as_dict = {}
                        for index, value in enumerate(self._commands_from_server[command][param]):
                            options_as_dict[str(index+1)] = value
                        self.log.debug("presenting parameter options to user as %s..." % str(options_as_dict))
                        self.render_options(options_as_dict, title=param)
                        while user_choice not in [str(s) for s in range(1,len(options_as_dict.keys()) + 1)]:
                            print "\nEnter to cancel\n%s > " % (
                                str(param),
                            ),
                            user_choice = getch().lower()
                            if user_choice == '\r':
                                # Cancelled command, return nothing
                                self.log.debug("parse_input() returning %s" % str(request_state_command))
                                return request_state_command
                        command_to_server[command][param] = options_as_dict[user_choice]
                    else:
                        # Possible answers are not provided, assume
                        # free form text
                        self.log.debug("asking user for free-form input for '%s' parameter..." % str(param))
                        entry = raw_input("%s: " % str(param))
                        command_to_server[command][param] = entry
            elif isinstance(command, dict):
                # command is already a dictionary, send it to server
                self.log.debug("command %s is a dictionary..." % str(command))
                command_to_server = command
            elif isinstance(command, list):
                self.log.info("command %s is a list" % str(command))
                # command is a list, convert it to a dictionary
                # command_dict = {}
                # for index, value in enumerate(command):
                #     command_dict[str(index)] = value
                # selection = self.render
                # command_to_server = {command: command_dict[str(selection)]}
            self.log.debug("parse_input() returning %s" % str(command_to_server))
            return command_to_server
        else:
            # Invalid input, try again
            self.log.debug("user input (%s) was not in command_menu's keys (%s)" % (
                str(user_input),
                str(command_menu.keys()),
            ))
            pass
        self.log.warning("parse_input() did not find a command, returning state request")
        return request_state_command

    def get_command_input(self, parameters = {}):
        """
        For each parameter of a command, get the user's input for that parameter.

        parameters should be a dictionary with a key of the parameter name and a value of the possible values for that parameter.

        Parameter value types:
        * empty string: free form text input
        * list: user must select one of the items in the list
        """

        pass

    def build_command_dict(self):
        """Return a dictionary with menu keys that correlate to commands."""
        result = {
            'q': 'quit', # Default to support quit on the client side
            '?': 'help', # Show help menu
        }

        # The move command is special, add the possible move
        # directions to the command dict
        if 'move' in self._commands_from_server and 'direction' in self._commands_from_server['move']:
            for direction in self._commands_from_server['move']['direction']:
                if direction not in result.keys():
                    result[direction] = {'move': {'direction': direction}}

        # Go through the rest of the commands
        for key,value in self._commands_from_server.iteritems():
            for char in key:
                if char not in result.keys():
                    result[char] = key
                    break

        self.log.info("command_dict loaded as %s" % str(result))
        self._command_dict = result

    def render_help(self):
        # print "\n%s\nCommands\n%s\n%s\n%s" % (
        #     '=' * 15,
        #     '-' * 8,
        #     '\n'.join(["%s - %s" % (key, value) for (key, value) in command_menu.items()]),
        #     '=' * 15,
        # )
        pass

    def render_state(self, help = False):
        # Get the console dimensions
        height, width = os.popen('stty size', 'r').read().split()

        if 'user' in self._state:
            if 'token' in self._state['user'] and self._state['user']['token']:
                # User is logged in
                # print "Player: %s" % state['user']['name']
                if 'user_location' in self._state:
                    if 'name' in self._state['user_location']:
                        # User is in the game
                        # print "In: %s (your ship)" % state['user_location']['name']
                        if 'sector' in self._state:
                            if 'name' in self._state['sector'] and 'coordinates' in self._state['sector']:
                                # User is in a sector
                                self.render_sector(self._state, self._commands_from_server)
                        elif 'at' in self._state:
                            self.render_location(self._state, self._commands_from_server)
                else:
                    # User not in game
                    self.render_options(
                        self._command_dict,
                        "Join Game"
                    )
            else:
                # User is not logged in
                # print "Player: Not logged in"
                self.render_options(
                    self._command_dict,
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
        height, width = self.screen.dimensions
        # title
        self.screen._title = title
        # main
        self.screen._enable_right_screen = False
        left = []
        for key in sorted(command_dict.keys()):
            if key not in ['q','?']:
                if key == command_dict[key][:1]:
                    # Key is the start of the option
                    # example: Key: R, Value: Ready
                    left.append("(%s)%s" % (
                        key.upper(),
                        command_dict[key][1:].replace('_',' ').ljust(int(width) - 7),
                    ))
                else:
                    # Key is not the start of the option
                    # example: Key: 1, Value: Ready

                    obj = self._state_cache[command_dict[key]] if command_dict[key] in self._state_cache else None
                    if obj and 'is_business' in obj and obj['is_business']:
                        # If the item is found in the state cache, then print a friendly name
                        left.append("(%s) %s" % (
                            key.upper(),
                            self.render_object(obj).ljust(int(width) - 8)
                        ))
                    else:
                        # Otherwise just print the command
                        left.append("(%s) %s" % (
                            key.upper(),
                            command_dict[key].replace('_',' ').ljust(int(width) - 8),
                        ))
        self.screen._left_screen = left
        self.screen.render()


    def render_sector(self, state, commands):
        # Get the console dimensions
        height, width = self.screen.dimensions

        # main
        self.screen._enable_right_screen = True
        # Get the console dimensions
        # height, width = os.popen('stty size', 'r').read().split()
        # left_section_width = int(int(width) * 0.75)
        main_display_height = self.screen._main_display_height

        # title
        self.screen._title = "Sector %s (%s,%s)" % (
            state['sector']['name'],
            state['sector']['coordinates']['x'],
            state['sector']['coordinates']['y'],
        )

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

        right_screen = self.render_info_panel(height = main_display_height)

        self.screen._left_screen = left_screen
        self.screen._right_screen = right_screen
        self.screen.render()

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
        line = 1
        # Show the cargo at this location
        if 'cargo' in state['at'] and state['at']['cargo']:
            for item in state['at']['cargo']:
                left_screen[line] = "%s (%s) (B: $%s, S: $%s)" % (
                    str(item['name']),
                    str(item['count']),
                    str(item['cost']['buying']),
                    str(item['cost']['selling']),
                )
                line += 1
        # Show the available commands
        for index, key in enumerate(commands):
            left_screen[-(index+1)] = "(%s)%s" % (
                str(key[:1]),
                str(key[1:])
            )

        right_screen = self.render_info_panel(height = main_display_height)



        self.render_bar()

    def render_info_panel(self, height):
        """
        Return a list of strings that will be printed on the right side of the screen.
        """
        info_panel = ["" for x in range(height)]
        # Player Info
        info_panel[1] = "Player Information"
        if 'credits' in self._state['user']:
            info_panel[2] = "Credits: %s" % self._state['user']['credits']

        # Ship Info
        info_panel[4] = "Ship Information"
        info_panel[5] = self._state['user_location']['name']
        holds_used = 0
        for item in self._state['user_location']['cargo']:
            holds_used += item['count'] if 'count' in item else 0
        if 'holds' in self._state['user_location']:
            info_panel[6] = "Cargo: %s/%s" % (
                holds_used,
                self._state['user_location']['holds'],
            )
        if 'warp' in self._state['user_location']:
            info_panel[7] = "Warp Speed: %s" % self._state['user_location']['warp']
        if 'weapons' in self._state['user_location'] and self._state['user_location']['weapons']:
            info_panel[8] = "Weapons: %s" % self._state['user_location']['weapons']
        if 'hull' in self._state['user_location']:
            info_panel[9] = "Hull: %s" % self._state['user_location']['hull']
        if 'shields' in self._state['user_location']:
            info_panel[10] = "Shields: %s" % self._state['user_location']['shields']
        return info_panel

    def render_object(self, obj):
        """
        Return a string representing this object.

        Object is expected to be a dictionary.
        """
        if obj and 'is_business' in obj and obj['is_business']:
            # only show that the business is buying if the player has something to sell
            player_selling = []
            for item in self._state['user_location']['cargo']:
                if item['count']:
                    player_selling.append(item['id'])

            business_buying = ""
            business_selling = " - ".join(["%s @ $%s" % (c['name'][0],c['cost']['selling']) for c in obj['cargo'] if c['count']])
            if player_selling:
                business_buying = " - ".join(["%s @ $%s" % (c['name'][0],c['cost']['buying']) for c in obj['cargo'] if c['id'] in player_selling])
            return "%s %s%s" % (
                str(obj['name']),
                "(Buying: %s) " % business_buying if business_buying else "",
                "(Selling: %s)" % business_selling,
            )
        return obj['name']

    def update_state_cache(self):
        """
        For every object in the state, update the state cache with that object.
        """
        if self._state:
            self.log.debug("Updating state cache...")
            self._state_cache = self._state_cache or dict()
            if 'sector' in self._state:
                self.log.debug("sector found in state")
                if 'ports' in self._state['sector']:
                    self.log.debug("processing ports %s..." % str(self._state['sector']['ports']))
                    for item in self._state['sector']['ports']:
                        self.log.debug("processing port %s..." % str(item))
                        if isinstance(item, dict):
                            if 'id' in item:
                                self.log.debug("updating cache at %s" % str(item['id']))
                                self._state_cache[item['id']] = item

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='0')
    parser.add_argument('-H','--host', default='localhost', help='Server name to connect to, default is localhost')
    parser.add_argument('-P','--port', default=10344, help='Port number for server, default is 10344')
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
    host = args.host
    port = args.port
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
            menu.parse_json(line)
        else:
            # User has quit
            log.info("Exiting game...")
            break

    socket.close()
