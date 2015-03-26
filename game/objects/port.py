import uuid
from random import choice, randint
from objects.sector import SectorObject
from objects.coordinates import Coordinates

class Port(SectorObject):
    yaml_tag = "!Port"

    def generate_name(self):
        """
        Return a randomly generated name for this object.
        """
        return "Port %s%s%s" % (
            str(randint(1,9)),
            str(randint(0,9)),
            str(randint(0,9)),
        )