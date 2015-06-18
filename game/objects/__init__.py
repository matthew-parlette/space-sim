import yaml
import uuid
import pprint
from copy import deepcopy
from random import randint

class Entity(yaml.YAMLObject):
    """The lowest level base object.

    This handles to/from yaml conversion, pluralization, and dict rendering.
    """
    __metaclass__ = yaml.YAMLObjectMetaclass

    def __init__(self):
        super(Entity,self).__init__()
        # Call byteify to make sure all unicode variables are saved as strings
        # This makes it easier to save in yaml
        self.__dict__ = self.byteify(self.__dict__)

    def byteify(self, data):
        """Make sure everything in data is a string, not unicode (for nicer yaml)."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.iteritems():
                if isinstance(key, unicode):
                    key = key.encode('utf-8')
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                if isinstance(value, dict) or isinstance(value, list):
                    value = self.byteify(value)
                result[key] = value
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, unicode):
                    item = item.encode('utf-8')
                if isinstance(item, dict) or isinstance(item, list):
                    item = self.byteify(value)
                result.append(item)
        else:
            result = None

        return result

    def __repr__(self):
        return str(pprint.pformat(self.__dict__))

    # This method is used by json.dumps() when sending it to a client
    def __str__(self):
        return str(self.__dict__)

    def plural(self, capitalized = False):
        """Return the plural form of this object."""
        return self.__class__.__name__.lower() + "s"

    def to_dict(self):
        return deepcopy(self.__dict__)

class NamedEntity(Entity):
    """The base class for anything in the game that has a name and ID.

    That covers mostly everything.
    """
    def __init__(self, name, id = None):
        super(NamedEntity,self).__init__()
        self.name = name
        self.id = id or str(uuid.uuid4())
        # Call byteify to make sure all unicode variables are saved as strings
        # This makes it easier to save in yaml
        self.__dict__ = self.byteify(self.__dict__)

class GameObject(NamedEntity):
    yaml_tag = "!GameObject"

    def __init__(
        self,
        name = None,
        id = None,
        location = None,
        holds = 0,
        cargo = [],
        warp = 0,
        weapons = None,
        hull = 0,
        shields = 0,
        credits = 0,
        dockable = False,
        is_business = False,
    ):
        self.name = name if name else self.generate_name()
        self.id = id
        self.location = location
        self.holds = holds
        self.cargo = cargo
        self.warp = warp
        self.weapons = weapons
        self.hull = hull
        self.shields = shields
        self.credits = credits
        self.dockable = dockable
        self.is_business = is_business

        # Parent init should be called at end of __init__
        super(GameObject,self).__init__(name = self.name, id = self.id)

        self.post_init_hook()

    def post_init_hook(self):
        """Function to be run after __init__()."""
        pass

    def to_dict(self):
        """Override to_dict to handle subobjects."""
        result = super(GameObject,self).to_dict()
        if isinstance(self.location,Entity):
            result['location'] = self.location.to_dict()
        if self.cargo:
            result['cargo'] = []
            for item in self.cargo:
                item_dict = item.to_dict()

                # Only determine price for businesses
                if self.is_business:
                    item_dict['cost'] = self.get_price(item.id)
                result['cargo'].append(item_dict)
        return result

    def generate_name(self):
        """
        Return a randomly generated name for this object.
        """
        return "Object %s%s%s" % (
            str(randint(1,9)),
            str(randint(0,9)),
            str(randint(0,9)),
        )

    def get_price(self, item_id):
        """
        Return a price for a given item (in the cargo of this object).

        The price returned is a dictionary with 'buying' and 'selling' costs with respect to this object.

        Price is determined by the equation y=mx + b, where m is the slope and b is the y-intercept.

        x is the percentage of the total cargo capacity taken up by the item (between 0 and 1)
        y is the variance on the average value of the item (+/- 50%)

        Given two points (x1,y1) and (x2,y2):

          m = (y2 - y1) / (x2 - x1)
        """
        point1 = (0,-0.5)
        point2 = (1,0.5)
        (item,) = [i for i in self.cargo if i.id == item_id]
        m = float(point2[1] - point1[1]) / float(point2[0] - point1[0])
        b = point1[1] - (m * point1[0])
        x = float(item.count) / float(self.holds)
        return {
            'selling': item.value * (1 - ((m * x) + b)),
            'buying': item.value * (1 + ((m * x) + b)),
        }
