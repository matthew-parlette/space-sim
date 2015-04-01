import yaml
import uuid
from copy import deepcopy

class Entity(yaml.YAMLObject):
    __metaclass__ = yaml.YAMLObjectMetaclass

    def __init__(self, name, id):
        super(Entity,self).__init__()
        self.name = name
        self.id = id
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
        return str(self.__dict__)

    # This method is used by json.dumps() when sending it to a client
    def __str__(self):
        return str(self.__dict__)

    def plural(self, capitalized = False):
        """Return the plural form of this object."""
        return self.__class__.__name__.lower() + "s"

    def to_dict(self):
        return deepcopy(self.__dict__)

class GameObject(Entity):
    yaml_tag = "!GameObject"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        location = None,
        holds = 0,
        cargo = [],
        warp = 0,
        weapons = None,
        hull = 0,
        shields = 0,
    ):
        self.name = name
        self.id = id
        self.location = location
        self.holds = holds
        self.cargo = cargo
        self.warp = warp
        self.weapons = weapons
        self.hull = hull
        self.shields = shields

        # Parent init should be called at end of __init__
        super(GameObject,self).__init__(name = name, id = id)
