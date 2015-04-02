from random import choice, randint
from objects.manmade import ManMade

class Station(ManMade):
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
