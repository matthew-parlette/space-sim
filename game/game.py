import logging
import os
import sys
import json
import yaml
import uuid
import datetime
import shutil
from random import randint, random
from objects import GameObject
from objects.manmade import ManMade
from objects.natural import Natural
from objects.commodity import Commodity, Ore, Organics, Equipment
from objects.coordinates import Coordinates
from objects.user import User
from objects.ship import Ship
from objects.sector import Sector
from objects.star import Star
from objects.planet import Planet
from objects.station import Station
from objects.port import Port

class Game(object):
    new_object_probability = {
        # Key must match object class name
        # Values between 0 and 1
        'Star': 0.5,
        'Planet': 0.5,
        'Station': 0.5,
        'Port': 0.5,
    }

    def __init__(self, data_dir = 'data', log = None, bigbang = False):
        self.log = log
        self.file = file
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

        self.log.debug("Verifying data directory exists (%s)..." % str(self.data_dir))
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        self.log.debug("Shared objects for all Game instances: %s" % str(self.shared_objects))
        for obj in self.shared_objects:
            self.load_shared_object(obj)

        self.logged_in_user = None

    @property
    def shared_objects(self):
        """Return a list of objects that are shared between all Game instances."""
        objects = [Sector().plural()]
        objects += [User().plural()]
        objects += [globals()[obj.__name__]().plural() for obj in ManMade.__subclasses__()]
        objects += [globals()[obj.__name__]().plural() for obj in Natural.__subclasses__()]
        return objects

    def save(self):
        self.log.info("Saving shared objects to disk")
        for obj in self.shared_objects:
            if getattr(Game, '_' + obj, None):
                self.log.debug("Saving shared object '%s'..." % str(obj))
                self.log.debug("Shared object '%s' is %s" % (str(obj),str(getattr(Game, '_' + obj))))
                with open(os.path.join(self.data_dir,obj + '.yaml'), 'w') as outfile:
                    outfile.write(yaml.dump(getattr(Game, '_' + obj),
                                            default_flow_style = False))
            else:
                self.log.debug("'%s' shared object is empty, skipping..." % str(obj))

    def load_shared_object(self, name):
        friendly_name = name
        object_name = '_' + name
        filename = os.path.join(self.data_dir,friendly_name + '.yaml')
        self.log.debug("Loading shared object '%s'" % str(friendly_name))
        # Do we need to initialize the shared object?
        if getattr(Game, object_name, None):
            self.log.debug("Shared object '%s' is available" % str(friendly_name))
        else:
            self.log.debug("Shared object '%s' is empty, initializing..." % str(friendly_name))
            # Shared object is empty, can we load it from a file?
            if os.path.isfile(filename):
                self.log.debug("Loading shared object '%s' from %s..." % (str(friendly_name),
                                                                         str(filename)))
                loaded_obj = yaml.load(open(filename))
                setattr(Game, object_name, loaded_obj)
            else:
                self.log.debug("File not found, creating a new shared object '%s'..." %
                    str(friendly_name))
                setattr(Game, object_name, {})

        self.log.debug("load_shared_object() done, shared object '%s' is %s" %
            (str(friendly_name),str(getattr(Game, object_name))))

    def location(self, of):
        """Return location object for the user's current location"""
        if hasattr(of, 'location_id'):
            if of.location_id in Game._ships.keys():
                return Game._ships[of.location_id]
        if hasattr(of, 'coordinates'):
            if of.coordinates in Game._sectors.keys():
                return Game._sectors[of.coordinates]
        if hasattr(of, 'location'):
            if isinstance(of.location,Coordinates):
                if of.location in Game._sectors.keys():
                    return Game._sectors[of.location]
            if isinstance(of.location,str):
                # Assume location is uuid, search objects for id
                return self.find_by_id(of.location)
        return None

    def find_by_id(self, id):
        """
        Find an object by its ID
        """
        self.log.debug("Searching for object with id %s" % str(id))
        found_obj = None
        possible_objects = [globals()[obj.__name__]().plural() for obj in ManMade.__subclasses__()]
        for shared_obj in possible_objects:
            self.log.debug("Searching %s for id %s" % (str(shared_obj),str(id)))
            if found_obj:
                break
            for key, value in getattr(Game,'_' + shared_obj,{}).iteritems():
                objects = []
                if isinstance(value,list):
                    objects += value
                else:
                    objects.append(value)
                for obj in objects:
                    self.log.debug("Processing %s" % str(obj))
                    self.log.debug("Testing %s (id: %s) for id %s" % (
                        str(obj.name),
                        str(obj.id),
                        str(id),
                    ))
                    if obj.id == id:
                        found_obj = obj
                        break

        if found_obj:
            self.log.debug("Found object of type %s: %s" % (str(found_obj.__class__.__name__),str(found_obj)))
        else:
            self.log.warning("No object found with id %s" % str(id))
        return found_obj

    def state(self):
        """Return the state and commands dictionary for the currently
        logged in user.

        The state must be returned as a dictionary, so it can be
        converted correctly to json. This means that objects must be
        converted to a dictionary before being returned.
        """

        self.log.debug("Generating state...")
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
        flags['docked'] = True if (
            flags['in_ship'] and
            ship_location and
            ship_location.__class__.__name__ in ['Port']
        ) else False
        # Flags are defined

        self.log.debug("State flags are %s" % str(flags))
        state = {} # Initialize
        commands = {} # Initialize

        self.log.debug("Processing state flag 'logged_in'...")
        if flags['logged_in']:
            # Return __dict__ for json
            state['user'] = self.logged_in_user.to_dict()
            if not flags['joined_game']:
                # New user needs to join the game
                commands['join_game'] = {'ship_name': None}

            self.log.debug("Processing state flag 'in_ship'...")
            if flags['in_ship']:
                state['user_location'] = user_location.to_dict()

            self.log.debug("Processing state flag 'in_sector'...")
            if flags['in_sector']:
                state['sector'] = ship_location.to_dict()
                state['sector']['coordinates'] = user_location.location.to_dict()
                contents = self.get_contents(user_location.location)
                for obj in contents:
                    heading = globals()[obj.__class__.__name__]().plural()
                    if heading in state['sector']:
                        state['sector'][heading].append(obj.to_dict())
                    else:
                        state['sector'][heading] = [obj.to_dict()]
                    if obj.dockable:
                        if 'dock' in commands:
                            commands['dock']['id'].append(obj.id)
                        else:
                            commands['dock'] = {'id': [obj.id]}
                commands['move'] = {'direction': ['n','s','e','w']}

            self.log.debug("Processing state flag 'docked'...")
            if flags['docked']:
                state['at'] = ship_location.to_dict()
                commands['undock'] = {}
                commands['buy'] = {
                    'item': [c.id for c in ship_location.cargo],
                    'quantity': None,
                }
                commands['sell'] = {
                    'item': [c.id for c in user_location.cargo],
                    'quantity': None,
                }
        else:
            # No user is logged in
            state['user'] = User().to_dict() # Emtpy user
            # Login takes user/pass
            commands['login'] = {'name': None, 'password': None}
            # Register takes user/pass
            commands['register'] = {'name': None, 'password': None}

        self.log.debug("Returning state of %s..." % str(state))
        self.log.debug("Returning commands of %s..." % str(commands))
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
                self.log.debug("Username '%s' found in user database" % str(name))
                self.log.debug("Password loaded for '%s' as '%s'" % (
                    Game._users[str(name)],
                    Game._users[str(name)].password,
                ))
                if password == Game._users[str(name)].password:
                    self.log.info("Login successful for %s" % str(name))
                    self.log.debug("Setting logged in user to %s..." % str(Game._users[str(name)]))
                    self.logged_in_user = Game._users[str(name)]
                    if Game._users[str(name)].token:
                        # Token exists
                        self.log.debug("Token reused. User state is %s" % Game._users[str(name)])
                        return True
                    else:
                        # Generate token
                        Game._users[str(name)].token = str(uuid.uuid4())
                        self.log.debug("Token generated. User state is %s" % Game._users[str(name)])
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
        ship.holds = 100
        Game._ships[ship.id] = ship

        # Put player in ship
        self.logged_in_user.location_id = ship.id

        # Mark player as not-new
        self.logged_in_user.status = 'alive'

        # Start player with 1000 credits
        self.logged_in_user.credits = 1000

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
        self.log.debug("Requesting sector at %s..." % str(coordinates))
        sector = self.sector(coordinates)
        self.log.info("Spawning ship '%s' in sector '%s' (%s)..." % (
            str(ship),
            str(sector),
            str(coordinates),
        ))
        ship.location = coordinates
        return True

    def move(self, cardinal_direction = None, coordinates = None):
        """
        Move the current player's ship in a cardinal direction (N-S-E-W)
        """
        if cardinal_direction:
            if cardinal_direction.lower() in ['n','s','e','w']:
                ship = self.location(of = self.logged_in_user)
                coordinates = ship.location.adjacent(cardinal_direction)

        if coordinates:
            ship.location = ship.location.adjacent(cardinal_direction)

            # Call self.sector() so the sector is generated, if necessary
            self.sector(ship.location)

    def sector(self, coordinates):
        """
        Return a sector (lookup by name)

        If the sector is not found, it will be generated
        """
        if coordinates in self._sectors.keys():
            sector = self._sectors[coordinates]
            self.log.debug("Sector at %s exists, returning %s..." % (
                str(coordinates),
                str(sector),
            ))
            return sector

        # Sector doesn't exit, create it
        self.log.info("Sector at (%s,%s) does not exist, generating new sector..." % (
            str(coordinates.x),
            str(coordinates.y)
        ))
        new_sector = Sector(name = 'M-' + str(randint(0,1000)))
        self._sectors[coordinates] = new_sector
        sector = self._sectors[coordinates]
        for object_name, probability in self.new_object_probability.iteritems():
            self.log.debug("Probability of %s to generate a %s" % (
                str(probability),
                str(object_name),
            ))
            while random() <= probability:
                # Create a new object
                self.log.debug("Roll passed, generating new %s in %s" % (
                    str(object_name),
                    str(coordinates),
                ))
                new_object = globals()[object_name]()
                new_object.location = coordinates
                shared_dict = getattr(Game,'_' + new_object.plural())
                if coordinates in shared_dict:
                    shared_dict[coordinates].append(new_object)
                else:
                    shared_dict[coordinates] = [new_object]
                self.log.debug("Generated new %s in %s: %s" % (
                    str(object_name),
                    str(coordinates),
                    str(new_object),
                ))

        if not sector:
            self.log.error("Sector at %s could not be created" % str(coordinates))
            return None
        self.log.info("Sector at (%s,%s) created" % (str(coordinates.x),str(coordinates.y)))
        self.log.debug("Returning %s" % (str(sector)))
        return sector

    def get_contents(self, coordinates = None):
        """
        Return a list of the contents of a sector at the provided coordinates.
        """
        if not coordinates or not isinstance(coordinates,Coordinates):
            self.log.warning("%s called without proper coordinates: %s (type %s)" % (
                "Game.get_contents()",
                str(coordinates),
                str(coordinates.__class__.__name__),
            ))
            return []

        contents = []
        # GameObject -> ManMade or Natural -> Object we want here
        for parent in GameObject.__subclasses__():
            for child in globals()[parent.__name__].__subclasses__():
                # subclasses returns full path, ex: objects.star.Star
                # child.__name__ returns Star
                shared_object = getattr(Game,'_' + globals()[child.__name__]().plural())
                if shared_object and coordinates in shared_object:
                    contents += shared_object[coordinates]
        self.log.debug("Coordinates %s contents: %s" % (str(coordinates),str(contents)))
        return contents

    def enter(self, id):
        """
        Move the current player's ship to the object (identified by id).
        """
        found_obj = self.find_by_id(id)
        # Move the ship to it
        if found_obj:
            ship = self.location(of = self.logged_in_user)
            ship.location = found_obj.id

    def leave(self):
        """
        Move the current player's ship from wherever they are landed to the sector.
        """
        ship = self.location(of = self.logged_in_user)
        location = self.location(of = ship)
        if hasattr(location,'location'):
            ship.location = location.location

    def trade(
        self,
        item,
        quantity = 0,
        for_what = None,
        seller = None,
        seller_cargo_location = None,
        buyer = None,
        buyer_cargo_location = None,
    ):
        """
        Move an item from the seller to the buyer for another item (usually credits).
        """
        # Determine seller and buyer, as well as the location of their cargo
        if buyer is 'current_user':
            buyer = self.logged_in_user
            if hasattr(self.logged_in_user, 'cargo'):
                buyer_cargo_location = self.logged_in_user
            else:
                buyer_cargo_location = buyer_cargo_location or self.location(of = buyer)
            seller = self.location(of = self.location(of = buyer))
            seller_cargo_location = seller_cargo_location or seller
        if seller is 'current_user':
            seller = self.logged_in_user
            if hasattr(self.logged_in_user, 'cargo'):
                seller_cargo_location = self.logged_in_user
            else:
                seller_cargo_location = seller_cargo_location or self.location(of = seller)
            buyer = self.location(of = self.location(of = seller))
            buyer_cargo_location = buyer_cargo_location or buyer
        if buyer is None:
            self.log.error("trade() could not determine the buyer, aborting trade...")
            return
        if seller is None:
            self.log.error("trade() could not determine the seller, aborting trade...")
            return

        # Make sure the quantity is valid
        try:
            quantity = int(quantity)
        except:
            self.log.error("trade() called with a non-integer quantity, aborting trade...")
            return
        if quantity == 0:
            self.log.error("trade() called with a quantity of 0, aborting trade...")
            return

        self.log.debug("Initiating trade from %s (cargo to %s) to %s (cargo to %s) for %s of %s..." % (
            str(seller.name),
            str(seller_cargo_location.name),
            str(buyer.name),
            str(buyer_cargo_location.name),
            str(quantity),
            str(item),
        ))

        # Determine cost of the item
        cost = -1
        if for_what:
            try:
                cost = int(for_what)
            except:
                self.log.error("trade() called with a non-integer cost, aborting trade...")
                return
        else:
            cost = (seller.get_price(item) if seller.is_business else buyer.get_price(item)) * quantity

        # Trade parameters are valid, proceed with trade
        if isinstance(item, str) or isinstance(item, unicode):
            # Assuming item was passed as a commodity id
            if str(item) in [c.id for c in seller_cargo_location.cargo]:
                # Seller has the item
                (item_obj,) = [c for c in seller_cargo_location.cargo if c.id == str(item)]
                if item_obj.count >= int(quantity):
                    # Seller has enough of the item, move the item and transfer credits
                    self._transfer_credits(buyer, seller, cost)
                    self._move_item(seller_cargo_location, buyer_cargo_location, item_obj, quantity)

    def _move_item(self, from_location, to_location, item, quantity):
        """
        Move an item from one place to another without exchanging credits.
        """
        self.log.debug("Moving item %s (quantity %s) from %s to %s" % (
            str(item.name),
            str(quantity),
            str(from_location.name),
            str(to_location.name),
        ))
        if isinstance(item, Commodity):
            if item.count >= int(quantity):
                # Remove item from from_location
                item.count -= int(quantity)
                # Add item to to_location
                if item.id in [i.id for i in to_location.cargo]:
                    # Item already exists on to_location
                    (to_item,) = [i for i in to_location.cargo if i.id == item.id]
                    to_item.count += int(quantity)
                else:
                    # Item needs to be created on to_location
                    self.log.debug("%s does not have a %s object, creating one" % (
                        str(to_location.name),
                        str(item.__class__.__name__),
                    ))
                    to_item = globals()[item.__class__.__name__](count = int(quantity))
                    to_location.cargo.append(to_item)

    def _transfer_credits(self, from_obj, to_obj, amount):
        """
        Transfer a number of credits (amount) from from_obj to to_obj
        """
        if from_obj.credits >= amount:
            self.log.debug("Transferring %s credits from %s to %s" % (
                str(amount),
                str(from_obj.name),
                str(to_obj.name),
            ))
            from_obj.credits -= amount
            to_obj.credits += amount
        else:
            self.log.error("_transfer_credits() called but from_obj (%s) doesn't have enough credits (%s < %s)" % (
                str(from_obj.name),
                str(from_obj.credits),
                str(amount),
            ))
