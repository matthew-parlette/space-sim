from random import choice, randint
from objects.manmade import ManMade
import objects.commodity as commodity

class Port(ManMade):
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

    def post_init_hook(self):
        self.dockable = True

        # If cargo is empty, then populate with some commodities
        if not self.cargo:
            self.cargo.append(commodity.Ore(count=10))
            self.cargo.append(commodity.Organics(count=10))
            self.cargo.append(commodity.Equipment(count=10))
