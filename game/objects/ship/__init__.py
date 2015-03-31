import uuid
from objects import GameObject
from objects.coordinates import Coordinates

class Ship(GameObject):
    yaml_tag = "!Ship"

    def __init__(
        self,
        name = None,
        id = str(uuid.uuid4()),
        coordinates = Coordinates(0,0,0),
        holds = 10,
        cargo = [],
        warp = 1,
        weapons = None,
        hull = 0,
        shields = 0,
    ):
        self.name = name
        self.id = id
        self.coordinates = coordinates
        self.holds = holds
        self.cargo = cargo
        self.warp = warp
        self.weapons = weapons
        self.hull = hull
        self.shields = shields

        # Parent init should be called at end of __init__
        super(Ship,self).__init__()

    def to_dict(self):
        """Override to_dict to handle coordinates."""
        result = super(Ship,self).to_dict()
        result['coordinates'] = self.coordinates.to_dict()
        return result
