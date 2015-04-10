import uuid
from objects import NamedEntity

class Sector(NamedEntity):
    yaml_tag = "!Sector"

    def __init__(
        self,
        name = None,
        id = None,
    ):
        self.name = str(name)

        # Parent init should be called at end of __init__
        super(Sector,self).__init__(name = name)
