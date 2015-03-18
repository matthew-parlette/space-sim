import uuid
from base import GameObject
from coordinates import Coordinates
from random import choice, randint

class Station(GameObject):
    yaml_tag = "!Station"

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
        super(Station,self).__init__()

    def to_dict(self):
        """Override to_dict to handle coordinates."""
        result = super(Station,self).to_dict()
        result['coordinates'] = self.coordinates.to_dict()
        return result

    def generate_name(self):
        """
        Return a randomly generated name for this object.

        Names for stars come from http://simbad.u-strasbg.fr/simbad
        """
        return "Starbase %s%s%s" % (
            str(randint(1,9)),
            str(randint(0,9)),
            str(randint(0,9)),
        )
