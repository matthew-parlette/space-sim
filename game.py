#!/usr/bin/python

import argparse
import logging
import os
import date

## {{{ http://code.activestate.com/recipes/134892/ (r2)
class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
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

## end of http://code.activestate.com/recipes/134892/ }}}

class Manager(object):
    """The superclass for all objects that manage other objects.

    Ex: Game object manages the players and sectors."""
    def __init__(self, log = None):
        super(Manager, self).__init__()
        self.log = log
        self.log.debug("%s initializing..." % self.__class__.__name__)

class Game(Manager):
    """docstring for Game"""
    def __init__(self, log = None):
        super(Game, self).__init__(log)
        self.log.debug("%s initialized" % self.__class__.__name__)

class Menu(Manager):
    """docstring for Menu"""
    def __init__(self, log = None, game = None):
        super(Menu, self).__init__(log)
        if game:
            self.log.debug("Game %s provided on init")
            self.game = game
        else:
            self.log.warn("Game was not provided on init, creating new game...")
            Game(self.log)

        self.getch = _Getch()
        self.log.debug("%s initialized" % self.__class__.__name__)
        self.log.debug("Entering menu loop...")
        self.loop()

    def loop(self):
        heading = "Main Menu"
        print "%s\n%s" % (heading,str("=" * len(heading)))

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process command line options.')
    parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='0.0')
    args = parser.parse_args()

    # Setup logging options
    log_level = logging.DEBUG if args.debug else logging.INFO
    log = logging.getLogger(os.path.basename(__file__))
    log.setLevel(log_level)
    # TODO: change name to be class name
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

    log.info("========== START ==========")
    log.info("\t%s" % date)
    log.info("Initializing menu...")
    menu = Menu(log)
