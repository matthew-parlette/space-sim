#!/usr/bin/python

import argparse
import logging
import os
import datetime
import sys
import menu

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

    def quit(self):
        sys.exit(0)

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

    log.info("=========== START ============")
    log.info("  %s" % datetime.datetime.isoformat(datetime.datetime.today()))
    log.info("Initializing menu...")
    main = menu.MainMenu(log, Game(log))
    main.display()
