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
        self.options = options
        self.prompt = prompt
        self.default = default
        self.getch = _Getch()
        self.log.debug("%s initialized" % self.__class__.__name__)

    def display(self):
        while True:
            self.pre_prompt_hook()
            print "%s\n%s" % (self.heading,'=' * len(self.heading))
            for key,value in self.options.iteritems():
                print "  %s: %s" % (key,value)
            print self.prompt,
            selection = self.getch()
            # Print a newline to separate the display more
            print "\n"
            # Is the function defined in the menu?
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
        self.game.quit()
        # SectorMenu(self.log,self.game).display()
