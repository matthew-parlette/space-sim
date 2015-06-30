#!/usr/bin/python

import argparse
import logging
import os
import json
import socket
import pprint
import re
import colorama as color

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
    def __init__(self, left_screen_percent = 0.75, right_screen_enabled = False, full_screen = True, prompt = None, log = None):
        """
        left_screen_percent: percent (from 0 to 1) of the screen taken up by the left screen
        """
        self.log = log
        self._left_screen = []
        self._right_screen = []
        self._title = None
        self._left_screen_percent = left_screen_percent
        self._right_screen_enabled = right_screen_enabled
        self._full_screen = full_screen
        self._prompt = prompt
        self._color_border = color.Fore.WHITE
        self._color_title = color.Fore.MAGENTA

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
        # Empty line to make sure we start all the way on the left
        print ""
        self._render_bar()
        self._render_line(left = self._title, title = True)
        self._render_bar()
        if self._full_screen:
            for i in range(0,self._main_display_height):
                self._render_line(
                    left = self._left_screen[i] if i < len(self._left_screen) else "",
                    right = self._right_screen[i] if i < len(self._right_screen) else "",
                )
        else:
            for i in range(0,max(len(self._left_screen),len(self._right_screen))):
                self._render_line(
                    left = self._left_screen[i] if i < len(self._left_screen) else "",
                    right = self._right_screen[i] if i < len(self._right_screen) else "",
                )

        # Only render the bottom bar if there was something printed on either screen
        if len(self._left_screen) or len(self._right_screen): self._render_bar()
        self._render_prompt()

    def _render_bar(self, text = None):
        # Get the console dimensions
        print self._color_border + "-" * int(self.width)
        if text:
            self.render_line(text)
            print "-" * int(self.width)

    def _render_line(self, left = "", right = "", border = True, title = False):
        """
        Print a line of the screen.

        This function takes into account colors by searching the string for the esacpe sequence \033
          to line everything up properly.
        
        The left line will be truncated if it is too long to fit into the window.
        """
        if self._enable_right_screen and not title:
            if border:
                # Before printing, we may need to truncate the line if it is too long
                # Check the length, but remove color codes before doing so
                if len(left) - self._count_color_characters(left) > self._left_width - 7:
                    self.log.debug("Truncating line...")
                    left = left[0:(self._left_width + self._count_color_characters(left) - 10)]
                    left = left + self._color_border + "..."
                print "%s| %s%s %s|" % (
                    self._color_border,
                    left.ljust(int(self._left_width) - 6 + self._count_color_characters(left)),
                    self._color_border + "| %s" % (right.ljust(int(self.width) - int(self._left_width) + self._count_color_characters(right))),
                    self._color_border,
                )
            else:
                print left
        else:
            if border:
                if title:
                    # For titles, print the text in color
                    print self._color_border + "| " + self._color_title + left.ljust(int(self.width) - 4 ) + self._color_border + " |"
                else:
                    print self._color_border + "| " + left.ljust(int(self.width) - 4) + self._color_border + " |"
            else:
                print left

    def _render_prompt(self):
        if self._prompt:
            print self._prompt + " > ",
        else:
            print color.Style.DIM + color.Fore.MAGENTA + "(? for menu) " + color.Style.BRIGHT + color.Fore.WHITE + "> ",

        # Reset prompt
        self._prompt = None

    def _count_color_characters(self,string):
        """
        Helper function to return the number of characters in color codes in this line.

        This is useful for lining up borders on lines with color.
        """
        count = 0
        matches = re.findall('(\\033\[\d+m)',string)
        if matches:
            for s in matches:
                count += len(s)
            self.log.debug("Processing line '%s', found %s characters in color codes" % (
                string[:8] + '...',
                str(count),
            ))
        return count

class Menu(object):
    def __init__(self, state = {}, commands = {}, log = None):
        self.log = log
        self._state = state
        self._commands_from_server = commands
        self._state_cache = None
        self.screen = Screen(log = self.log)
        self._color_none = color.Fore.WHITE
        self._color_title = color.Fore.MAGENTA
        self._color_heading = color.Fore.YELLOW
        self._color_list = color.Fore.CYAN
        self._color_good = color.Fore.GREEN
        self._color_normal = color.Style.BRIGHT + color.Fore.BLUE + color.Style.NORMAL
        self._color_bad = color.Fore.RED
        self._color_option_key = color.Fore.GREEN
        self._color_option_value = color.Fore.WHITE
        self._color_credits = color.Fore.GREEN
        self._color_item_name = color.Fore.BLUE
        self._color_item_quantity = color.Fore.CYAN

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
        # print "(? for menu) > ",
        user_input = getch()
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
                self.render_options(command_menu, title = "Help")
                return self.parse_input(self.get_input())

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
                if command in ['login','register']:
                    self.log.debug("Displaying user/pass screen to user...")
                    self.screen._title = "Login"
                    self.screen._left_screen = []
                    self.screen._enable_right_screen = False
                    self.screen._full_screen = False
                    self.screen._prompt = color.Fore.BLUE + "Username"
                    self.screen.render()
                    username = raw_input()
                    command_to_server[command]['name'] = username
                    self.screen._prompt = color.Fore.BLUE + "Password"
                    self.screen.render()
                    password = raw_input()
                    command_to_server[command]['password'] = password
                    self.screen._full_screen = True
                # elif command in ['join_game']:
                #     self.render_bar(str(command).replace('_',' ').upper())
                else:
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
                            self.render_options(options_as_dict, title=param, user_can_cancel = True)
                            while user_choice not in [str(s) for s in range(1,len(options_as_dict.keys()) + 1)]:
                                # print "\nEnter to cancel\n%s > " % (
                                #     str(param),
                                # ),
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
                            self.screen._title = str(command).replace('_',' ').title()
                            self.screen._left_screen = []
                            self.screen._enable_right_screen = False
                            self.screen._full_screen = False
                            self.screen._prompt = str(param).replace('_',' ').title()
                            self.screen.render()
                            entry = raw_input()
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
                        "Join Game",
                        user_can_cancel = False,
                    )
            else:
                # User is not logged in
                # print "Player: Not logged in"
                self.render_options(
                    self._command_dict,
                    "Welcome",
                    user_can_cancel = False,
                )

    def render_options(self, command_dict, title = None, user_can_cancel = True):
        """
        Render all available options on the screen.

        This skips the quit and help (?) commands, since they are common.

        The display assumes the first character of each option string is the
        command (single character that is the key for the command in
        command_dict).
        """
        self.log.debug("Rendering options dictionary %s..." % str(command_dict))

        # Get the console dimensions
        height, width = self.screen.dimensions
        main_display_height = self.screen._main_display_height

        # title
        self.screen._title = title
        # main
        self.screen._enable_right_screen = False

        left = ["" for x in range(main_display_height)]
        index = 0
        for key in sorted(command_dict.keys()):
            if key not in ['q','?']:
                self.log.debug("Processing option dictionary key %s..." % str(key))
                if isinstance(command_dict[key],str) and key == command_dict[key][:1]:
                    # Key is the start of the option
                    # example: Key: R, Value: Ready
                    left[index] = "%s(%s%s%s)%s%s" % (
                        self._color_none,
                        self._color_option_key,
                        key.upper(),
                        self._color_none,
                        self._color_option_value,
                        command_dict[key][1:].replace('_',' ').ljust(int(width) - 7),
                    )
                else:
                    # Key is not the start of the option
                    # example: Key: 1, Value: Ready
                    #   or
                    # example: Key: e, Value: {'move': {'direction': 'e'}}

                    if isinstance(command_dict[key],str) or isinstance(command_dict[key],unicode):
                        obj = self._state_cache[command_dict[key]] if command_dict[key] in self._state_cache else None
                        if obj and 'is_business' in obj and obj['is_business']:
                            # If the item is found in the state cache, then print a friendly name
                            left[index] = "%s(%s%s%s) %s%s" % (
                                self._color_none,
                                self._color_option_key,
                                key.upper(),
                                self._color_none,
                                self._color_option_value,
                                self.render_object(obj).ljust(int(width) - 8)
                            )
                        else:
                            # Otherwise just print the command
                            left[index] = "%s(%s%s%s) %s%s" % (
                                self._color_none,
                                self._color_option_key,
                                key.upper(),
                                self._color_none,
                                self._color_option_value,
                                command_dict[key].replace('_',' ').ljust(int(width) - 8),
                            )
                    else:
                        # This key's value is a dictionary or list
                        left[index] = "%s(%s%s%s) %s%s" % (
                            self._color_none,
                            self._color_option_key,
                            key.upper(),
                            self._color_none,
                            self._color_option_value,
                            str(command_dict[key]).ljust(int(width) - 8),
                        )
                index += 1
        if user_can_cancel: left[-1] = "(Enter to cancel)"

        self.screen._left_screen = left
        self.screen.render()


    def render_sector(self, state, commands):
        # Get the console dimensions
        height, width = self.screen.dimensions

        # main
        self.screen._enable_right_screen = True
        main_display_height = self.screen._main_display_height

        # title
        self.screen._title = "Sector %s (%s,%s)" % (
            state['sector']['name'],
            state['sector']['coordinates']['x'],
            state['sector']['coordinates']['y'],
        )

        left_screen = ["" for x in range(main_display_height)]
        if 'stars' in state['sector'] and state['sector']['stars']:
            left_screen[1]   = self._color_heading + "Stars: "
            left_screen[1]  += self._color_list + " - ".join([star['name'] for star in state['sector']['stars']])
        if 'planets' in state['sector'] and state['sector']['planets']:
            left_screen[3]   = self._color_heading + "Planets: "
            left_screen[3]  += self._color_list + " - ".join([planet['name'] for planet in state['sector']['planets']])
        if 'stations' in state['sector'] and state['sector']['stations']:
            left_screen[5]   = self._color_heading + "Stations: "
            left_screen[5]  += self._color_list + " - ".join([station['name'] for station in state['sector']['stations']])
        if 'ports' in state['sector'] and state['sector']['ports']:
            left_screen[7]   = self._color_heading + "Ports: "
            left_screen[7]  += self._color_list + " - ".join([port['name'] for port in state['sector']['ports']])
        if 'ships' in state['sector'] and state['sector']['ships']:
            left_screen[9]   = self._color_heading + "Ships: "
            left_screen[9]  += self._color_list + " - ".join([ship['name'] for ship in state['sector']['ships']])
        left_screen[-1]  = self._color_heading + "Warps to: "
        left_screen[-1] += self._color_list + " - ".join(commands['move']['direction'])

        right_screen = self.render_info_panel(height = main_display_height)

        self.screen._left_screen = left_screen
        self.screen._right_screen = self.render_info_panel(height = main_display_height)
        self.screen.render()

    def render_location(self, state, commands):
        # Get the console dimensions
        height, width = self.screen.dimensions

        # main
        self.screen._enable_right_screen = True
        main_display_height = self.screen._main_display_height

        # title
        self.screen._title = "%s (%s,%s)" % (
            state['at']['name'],
            state['at']['location']['x'],
            state['at']['location']['y'],
        )

        left_screen = ["" for x in range(main_display_height)]
        line = 1
        # Show the cargo at this location
        if 'cargo' in state['at'] and state['at']['cargo']:
            for item in state['at']['cargo']:
                left_screen[line] = "%s%s %s(%s%s%s) %s(B: %s$%s%s, S: %s$%s%s)" % (
                    self._color_item_name,
                    str(item['name']),
                    self._color_none,
                    self._color_item_quantity,
                    str(item['count']),
                    self._color_none,
                    self._color_none,
                    self._color_credits,
                    str(item['cost']['buying']),
                    self._color_none,
                    self._color_credits,
                    str(item['cost']['selling']),
                    self._color_none,
                )
                line += 1
        # Show the available commands
        for index, key in enumerate(commands):
            left_screen[-(index+1)] = "(%s)%s" % (
                self._color_option_key + str(key[:1]) + self._color_none,
                self._color_option_value + str(key[1:])
            )

        self.screen._left_screen = left_screen
        self.screen._right_screen = self.render_info_panel(height = main_display_height)
        self.screen.render()

    def render_info_panel(self, height):
        """
        Return a list of strings that will be printed on the right side of the screen.
        """
        info_panel = ["" for x in range(height)]
        # Player Info
        info_panel[1] = color.Fore.MAGENTA + "Player Information"
        if 'credits' in self._state['user']:
            info_panel[2] = self._color_heading + "Credits: " + self._color_normal + "%s" % self._state['user']['credits']

        # Ship Info
        info_panel[4] = color.Fore.MAGENTA + "Ship Information"
        info_panel[5] = self._color_normal + self._state['user_location']['name']
        holds_used = 0
        for item in self._state['user_location']['cargo']:
            holds_used += item['count'] if 'count' in item else 0
        if 'holds' in self._state['user_location']:
            info_panel[6] = self._color_heading + "Cargo: " + self._color_normal + "%s/%s" % (
                holds_used,
                self._state['user_location']['holds'],
            )
        if 'warp' in self._state['user_location']:
            info_panel[7] = self._color_heading + "Warp Speed: " + self._color_normal + "%s" % self._state['user_location']['warp']
        if 'weapons' in self._state['user_location'] and self._state['user_location']['weapons']:
            info_panel[8] = self._color_heading + "Weapons: " + self._color_normal + "%s" % self._state['user_location']['weapons']
        if 'hull' in self._state['user_location']:
            info_panel[9] = self._color_heading + "Hull: " + self._color_normal + "%s" % self._state['user_location']['hull']
        if 'shields' in self._state['user_location']:
            info_panel[10] = self._color_heading + "Shields: " + self._color_normal + "%s" % self._state['user_location']['shields']
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
            business_selling = " - ".join(["%s%s%s @ %s$%s%s" % (
                self._color_normal,
                c['name'][0],
                self._color_none,
                self._color_credits,
                c['cost']['selling'],
                self._color_none,
            ) for c in obj['cargo'] if c['count']])
            if player_selling:
                business_buying = " - ".join(["%s%s%s @ %s$%s%s" % (
                    self._color_normal,
                    c['name'][0],
                    self._color_none,
                    self._color_credits,
                    c['cost']['buying'],
                    self._color_none,
                ) for c in obj['cargo'] if c['id'] in player_selling])
            return "%s%s%s %s%s" % (
                self._color_list,
                str(obj['name']),
                self._color_none,
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

    log.info("Initializing coloring...")
    color.init(autoreset=True)

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
