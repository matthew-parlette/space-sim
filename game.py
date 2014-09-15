#!/usr/bin/python

import argparse
import logging
import os
import datetime
import sys
import menu
from uuid import uuid4

class Entity(object):
    """docstring for Entity"""
    def __init__(self, id):
        super(Entity, self).__init__()
        self.id = id

    def __repr__(self):
        return str(self.id)

class Sector(Entity):
    """docstring for Sector"""
    def __init__(self, id, warps = {}):
        super(Sector, self).__init__(id)
        self.warps = warps

    def __repr__(self):
        return "%s (warps to %s)" % (self.id,
            ','.join(str(warp) for warp in self.warps))

class Player(Entity):
    """docstring for Player"""
    def __init__(self, id):
        super(Player, self).__init__(id)
        self.name = id

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
        self.id = None
        self.sectors = None
        self.players = None
        self.log.debug("%s initialized" % self.__class__.__name__)

    def new(self):
        self.log.debug("Starting a new game...")
        self.id = uuid4()
        self.players = []
        self.log.info("Executing big bang...")
        self.big_bang()


    def big_bang(self):
        """Generate sectors for the universe"""
        self.log.debug("Executing big bang on game %s" % self.id)
        self.sectors = {
            Sector(int(1),warps = {int(2),int(3),int(4),int(5)}),
            Sector(int(2),warps = {int(1),int(3),int(4),int(5)}),
            Sector(int(3),warps = {int(1),int(2),int(4),int(5)}),
            Sector(int(4),warps = {int(1),int(2),int(3),int(5)}),
            Sector(int(5),warps = {int(1),int(2),int(3),int(4)})
        }

    def add_player(self, player_name):
        """Add a new player to this game"""
        self.log.debug("Player list before add: %s" % self.players)
        self.players.append(Player(player_name))
        self.log.debug("Player list after add: %s" % self.players)

    def start(self):
        """Start the game"""
        self.log.info("Starting game %s..." % self.id)
        self.log.info("Players:\n\t%s\nSector Map:\n\t%s\n" %
            (
                "\n\t".join(str(p) for p in self.players),
                "\n\t".join(str(s) for s in self.sectors)
            )
        )

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
