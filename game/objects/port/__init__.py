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
        self.is_business = True

        # If cargo is empty, then populate with some commodities
        if not self.cargo:
            self.holds = 100
            # How many holds should be filled at this port?
            holds_to_fill = randint(int(self.holds * 0.2),self.holds)
            ore = holds_to_fill - randint(0,holds_to_fill)
            holds_to_fill -= ore
            self.cargo.append(commodity.Ore(count=ore))
            org = holds_to_fill - randint(0,holds_to_fill)
            holds_to_fill -= org
            self.cargo.append(commodity.Organics(count=org))
            equ = holds_to_fill - randint(0,holds_to_fill)
            holds_to_fill -= equ
            self.cargo.append(commodity.Equipment(count=equ))
