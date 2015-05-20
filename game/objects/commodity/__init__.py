import uuid
from objects import NamedEntity

class Commodity(NamedEntity):
    yaml_tag = "!Commodity"

    def __init__(
        self,
        name = None,
        id = None,
        value = 0,
        count = 0,
    ):
        self.name = name
        self.id = id or str(uuid.uuid4())
        self.value = value
        self.count = count

        # Parent init should be called at end of __init__
        super(Commodity,self).__init__(name = name, id = id)

        self.post_init_hook()

    def post_init_hook(self):
        """Function to be run after __init__()."""
        pass

class Ore(Commodity):
    def post_init_hook(self):
        self.name = "Fuel Ore"
        self.id = "ore"
        self.value = 10

class Organics(Commodity):
    def post_init_hook(self):
        self.name = "Organics"
        self.id = "organics"
        self.value = 20

class Equipment(Commodity):
    def post_init_hook(self):
        self.name = "Equipment"
        self.id = "equipment"
        self.value = 30
