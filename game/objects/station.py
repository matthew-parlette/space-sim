import uuid
from coordinates import Coordinates
from random import choice, randint
from sector import SectorObject

class Station(SectorObject):
    yaml_tag = "!Station"

    def generate_name(self):
        """
        Return a randomly generated name for this object.
        """
        return "Starbase %s%s%s" % (
            str(randint(1,9)),
            str(randint(0,9)),
            str(randint(0,9)),
        )
