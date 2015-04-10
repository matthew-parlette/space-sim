from random import choice, randint
from objects.manmade import ManMade

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
