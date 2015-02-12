import logging
import os
import sys
import json
import yaml
import uuid
import datetime
import shutil
from random import randint
from user import User
from ship import Ship
from sector import Sector
from coordinates import Coordinates

class Game(object):
    # Objects shared between all instances of Game
    _users = {}
    _ships = {}
    _sectors = {}
    shared_objects = ['users','ships','sectors']

    def __init__(self, data_dir = 'data', log = None, bigbang = False):
        self.log = log
        self.file = file
        self.size = 10
        self.data_dir = data_dir

        if bigbang:
            # Delete data directory if bigbang is True
            self.log.warning("Performing big bang...")
            if os.path.isdir(self.data_dir):
                self.log.info("Deleting data directory '%s'..." % str(self.data_dir))
                shutil.rmtree(self.data_dir)
            # Set bigbang to False to make sure we don't delete data on next login
            self.log.info("Big Bang complete, it will not be run again until the game is restarted")
            self.bigbang = False

        self.log.info("Verifying data directory exists (%s)..." % str(self.data_dir))
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        for obj in Game.shared_objects:
            self.load_shared_object(obj)

        self.logged_in_user = None

    def save(self):
        self.log.info("Saving shared objects to disk")
        for obj in Game.shared_objects:
            if getattr(Game, '_' + obj, None):
                self.log.info("Saving shared object '%s'..." % str(obj))
                self.log.info("Shared object '%s' is %s" % (str(obj),str(getattr(Game, '_' + obj))))
                with open(os.path.join(self.data_dir,obj + '.yaml'), 'w') as outfile:
                    outfile.write(yaml.dump(getattr(Game, '_' + obj),
                                            default_flow_style = False))
            else:
                self.log.info("'%s' shared object is empty, skipping..." % str(obj))

    def load_shared_object(self, name):
        friendly_name = name
        object_name = '_' + name
        filename = os.path.join(self.data_dir,friendly_name + '.yaml')
        self.log.info("Loading shared object '%s'" % str(friendly_name))
        # Do we need to initialize the shared object?
        if getattr(Game, object_name, None):
            self.log.info("Shared object '%s' is available" % str(friendly_name))
        else:
            self.log.info("Shared object '%s' is empty, initializing..." % str(friendly_name))
            # Shared object is empty, can we load it from a file?
            if os.path.isfile(filename):
                self.log.info("Loading shared object '%s' from %s..." % (str(friendly_name),
                                                                         str(filename)))
                loaded_obj = yaml.load(open(filename))
                # for key, value in loaded_obj.iteritems():

                    # self.log.info("Loaded %s of type %s" % (str(loaded_obj),str(loaded_obj.__class__.__name__)))
                setattr(Game, object_name, loaded_obj)
            else:
                self.log.info("File not found, creating a new shared object '%s'..." %
                    str(friendly_name))

        self.log.info("load_shared_object() done, shared object '%s' is %s" %
            (str(friendly_name),str(getattr(Game, object_name))))

    def location(self, of):
        """Return location object for the user's current location"""
        if hasattr(of, 'location_id'):
            if of.location_id in Game._ships.keys():
                return Game._ships[of.location_id]
        if hasattr(of, 'coordinates'):
            if of.coordinates in Game._sectors.keys():
                return Game._sectors[of.coordinates]
        return None

    def state(self):
        """Return the state and commands dictionary for the currently
        logged in user.
        """

        self.log.info("Generating state...")
        # Define Flags
        flags = {}
        flags['logged_in'] = True if self.logged_in_user else False
        flags['joined_game'] = True if (
            flags['logged_in'] and
            self.logged_in_user.status != 'new'
        ) else False
        user_location = self.location(of = self.logged_in_user) if flags['joined_game'] else None
        flags['in_ship'] = True if (
            flags['logged_in'] and
            user_location and
            user_location.__class__.__name__ == 'Ship'
        ) else False
        ship_location = self.location(of = user_location) if flags['in_ship'] else None
        flags['in_sector'] = True if (
            flags['in_ship'] and
            ship_location and
            ship_location.__class__.__name__ == 'Sector'
        ) else False
        # Flags are defined

        self.log.info("State flags are %s" % str(flags))
        state = {} # Initialize
        commands = {} # Initialize

        if flags['logged_in']:
            # Return __dict__ for json
            state['user'] = self.logged_in_user
            if not flags['joined_game']:
                # New user needs to join the game
                commands['join_game'] = {'ship_name': None}

            if flags['in_ship']:
                state['user_location'] = user_location

            if flags['in_sector']:
                state['sector'] = ship_location
                # state['sector']['coordinates'] = user_location.coordinates
                commands['move'] = {'direction': ['n','s','e','w']}
        else:
            # No user is logged in
            state['user'] = User() # Emtpy user
            # Login takes user/pass
            commands['login'] = {'name': None, 'password': None}
            # Register takes user/pass
            commands['register'] = {'name': None, 'password': None}

        self.log.info("Returning state of %s..." % str(state))
        return state, commands

    def register(self, name, password):
        if name and password:
            if name in Game._users.keys():
                self.log.error("Username '%s' already found in user database" % str(name))
                return False
            else:
                self.log.info("Adding new user '%s'..." % str(name))
                Game._users[str(name)] = User(name = name, password = password)
                # Automatically login the user that was just created
                return self.login(name, password)
        self.log.error("Name or password is missing")
        return False

    def login(self, name, password):
        if name and password:
            if name in Game._users.keys():
                self.log.info("Username '%s' found in user database" % str(name))
                self.log.info("Password loaded for '%s' as '%s'" % (
                    Game._users[str(name)],
                    Game._users[str(name)].password,
                ))
                if password == Game._users[str(name)].password:
                    self.log.info("Login successful, setting logged in user to %s..." % str(Game._users[str(name)]))
                    self.logged_in_user = Game._users[str(name)]
                    if Game._users[str(name)].token:
                        # Token exists
                        self.log.info("Token reused. User state is %s" % Game._users[str(name)])
                        return True
                    else:
                        # Generate token
                        Game._users[str(name)].token = str(uuid.uuid4())
                        self.log.info("Token generated. User state is %s" % Game._users[str(name)])
                        return True
                else:
                    self.log.error("Login failed, incorrect password for '%s'" % str(name))
                    return False
            else:
                self.log.error("Login failed, username '%s' not found in user database" % str(name))
                return False
        self.log.error("Login failed, Name or password is missing")
        return False

    def join_game(self, ship_name):
        self.log.info("Creating new ship '%s' for user %s..." % (
            str(ship_name),
            str(self.logged_in_user.name),
        ))

        # Create ship
        ship = Ship(name = ship_name)
        Game._ships[ship.id] = ship

        # Put player in ship
        self.logged_in_user.location_id = ship.id

        # Mark player as not-new
        self.logged_in_user.status = 'alive'

        # Spawn the ship
        self.spawn(ship)

        # Return result
        self.log.info("Ship '%s' created" % (str(ship.name)))
        return True

    def spawn(self, ship):
        """
        Spawn a ship in sector (0,0,0)
        """
        coordinates = Coordinates(0,0,0)
        self.log.info("Requesting sector at %s..." % str(coordinates))
        sector = self.sector(coordinates)
        self.log.info("Spawning ship '%s' in sector '%s' (%s)..." % (
            str(ship),
            str(sector),
            str(coordinates),
        ))
        ship.coordinates = coordinates
        return True

    def move(self, cardinal_direction):
        """
        Move the current player's ship in a cardinal direction (N-S-E-W)
        """
        if cardinal_direction.lower() in ['n','s','e','w']:
            ship = self.location(of = self.logged_in_user)
            ship.coordinates = ship.coordinates.adjacent(cardinal_direction)

            # Call self.sector() so the sector is generated, if necessary
            self.sector(ship.coordinates)

    def sector(self, coordinates):
        """
        Return a sector (lookup by name)

        If the sector is not found, it will be generated
        """
        if coordinates in self._sectors.keys():
            sector = self._sectors[coordinates]
            self.log.info("Sector at %s exists, returning %s..." % (
                str(coordinates),
                str(sector),
            ))
            return sector

        # Sector doesn't exit, create it
        self.log.info("Sector at %s does not exist, generating new sector..." % str(coordinates))
        new_sector = Sector(name = 'M-' + str(randint(0,1000)))
        self._sectors[coordinates] = new_sector
        sector = self._sectors[coordinates]
        if not sector:
            self.log.error("Sector at %s could not be created" % str(coordinates))
            return None
        self.log.info("Sector at %s created, returning %s" % (str(coordinates),str(sector)))
        return sector
