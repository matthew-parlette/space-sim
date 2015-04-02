import uuid
from objects import NamedEntity

class Commodity(NamedEntity):
    yaml_tag = "!Commodity"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        value = 0,
    ):
        self.name = name
        self.id = id
        self.value = value

        # Parent init should be called at end of __init__
        super(Commodity,self).__init__(name = name, id = id)

class Ore(Commodity):
    def __init__(
        self,
    ):
        super(Ore,self).__init__(
            name = "Fuel Ore",
            id = "ore",
            value = 10,
        )

class Organics(Commodity):
    def __init__(
        self,
    ):
        super(Organics,self).__init__(
            name = "Organics",
            id = "organics",
            value = 20,
        )

class Equipment(Commodity):
    def __init__(
        self,
    ):
        super(Equipment,self).__init__(
            name = "Equipment",
            id = "equipment",
            value = 30,
        )
