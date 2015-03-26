import uuid
from objects import GameObject
from objects.coordinates import Coordinates

class Sector(GameObject):
    yaml_tag = "!Sector"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
    ):
        self.name = str(name)
        self.id = id

        # Parent init should be called at end of __init__
        super(Sector,self).__init__()

class SectorObject(GameObject):
    """Parent class for objects that exist in sectors."""
    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        coordinates = Coordinates(0,0,0),
    ):
        self.name = name if name else self.generate_name()
        self.id = id
        self.coordinates = coordinates

        # Parent init should be called at end of __init__
        super(SectorObject,self).__init__()

    def to_dict(self):
        """Override to_dict to handle coordinates."""
        result = super(SectorObject,self).to_dict()
        result['coordinates'] = self.coordinates.to_dict()
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
