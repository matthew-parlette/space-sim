import logging
from game import Manager
from getch import _Getch

class Menu(object):
    """docstring for Menu"""
    def __init__(self,
                 log = None,
                 game = None,
                 heading = "Menu",
                 options = {},
                 prompt = ">",
                 default = None):
        super(Menu, self).__init__()
        self.log = log
        self.log.debug("Game %s provided on init" % game.id)
        self.game = game
        self.heading = heading
        self.options = dict(options.items() + {'?':"help"}.items())
        self.prompt = "%s > " % self.heading
        self.default = default
        self.getch = _Getch()
        self.log.debug("%s initialized" % self.__class__.__name__)

    def display(self):
        while True:
            self.pre_prompt_hook()
            print self.prompt,
            selection = ""
            selection_not_valid = True
            while selection_not_valid:
                selection_part = self.getch()
                print selection_part,
                selection += str(selection_part)

                # Check input
                if selection in self.options:
                    # Complete match for an option
                    selection_not_valid = False
                elif any(selection in o for o in self.options):
                    # Partial match for an option, keep accepting input
                    selection_not_valid = True
                else:
                    # Selection is invalid
                    self.log.debug("User input '%s' is invalid" % (
                        selection
                    ))
                    selection_not_valid = True
                    print "\nInvalid input"
                    selection = ""
                    self.pre_prompt_hook()
                    print self.prompt,

            # Print a newline to separate the display more
            print "\n"

            # Is the function defined in the menu?
            self.log.debug("Checking %s for %s function" % (
                self.__class__.__name__,
                self.options[selection]
            ))
            if hasattr(self,self.options[selection]):
                func = getattr(self, self.options[selection])
            elif hasattr(self.game,self.options[selection]):
                func = getattr(self.game, self.options[selection])
            else:
                self.log.error(
                    "Function %s was not found in menu %s or Game" % (
                        str(self.options[selection]),
                        str(self.__class__.__name__)
                    )
                )
            func()

    def pre_prompt_hook(self):
        pass

    def help(self):
        print "%s\n%s" % (self.heading,'=' * len(self.heading))
        for key,value in self.options.iteritems():
            print "  %s: %s" % (key,value)

class MainMenu(Menu):
    """docstring for MainMenu"""
    def __init__(self, log, game):
        options = {
            'q': "quit",
            'n': "new"
        }
        super(MainMenu, self).__init__(
            log = log,
            game = game,
            heading = "Main Menu",
            options = options
        )

    def new(self):
        NewGameMenu(self.log,self.game).display()

    def pre_prompt_hook(self):
        self.help()

class NewGameMenu(Menu):
    """docstring for NewGameMenu"""
    def __init__(self, log, game):
        options = {
            'q': "quit",
            's': "start",
            'a': "add_player"
        }
        game.new()
        super(NewGameMenu, self).__init__(
            log = log,
            game = game,
            heading = "New Game",
            options = options
        )

    def add_player(self):
        player_name = raw_input("Enter new player name: ")
        self.game.add_player(player_name)

    def start(self):
        self.game.start()
        SectorMenu(self.log,self.game).display()

    def pre_prompt_hook(self):
        self.help()

class SectorMenu(Menu):
    """docstring for SectorMenu"""
    def __init__(self, log, game):
        options = {
            'q': "quit",
            'm': "move"
        }
        super(SectorMenu, self).__init__(
            log = log,
            game = game,
            heading = "Sector",
            options = options
        )

    def pre_prompt_hook(self):
        padding = 8
        player = self.game.players[0]
        self.log.debug("Using player %s" % str(player))
        current = self.game.get(player.sector)[0]
        self.log.debug("Current sector is %s" % str(current.id))
        print "%s: %s" % (
            "Sector".ljust(padding),
            str(current.id)
        )
        print "%s: %s" % (
            "Warps".ljust(padding),
            ", ".join(str(w) for w in current.warps)
        )
