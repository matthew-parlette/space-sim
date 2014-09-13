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
        self.log.debug("Game %s provided on init")
        self.game = game
        self.heading = heading
        self.options = options
        self.prompt = prompt
        self.default = default
        self.getch = _Getch()
        self.log.debug("%s initialized" % self.__class__.__name__)

    def display(self):
        print "%s\n%s" % (self.heading,'=' * len(self.heading))
        for key,value in self.options.iteritems():
            print "  %s: %s" % (key,value)
        print self.prompt,
        selection = self.getch()
        func = getattr(self.game, self.options[selection])
        func()

    def pre_prompt_hook(self):
        pass

class MainMenu(Menu):
    """docstring for MainMenu"""
    def __init__(self, log, game):
        super(MainMenu, self).__init__(log = log,
                                       game = game,
                                       heading = "Main Menu",
                                       options = {'q': "quit"})
