import uuid
from objects import Entity

class Coordinates(Entity):
    """
    A Hashable set of coordinates that can be used as a dictionary key.

    This inherits from Entity since it has no name or id (it essentially acts
    as an id for other objects).
    """
    yaml_tag = "!Coordinates"

    def __init__(
        self,
        x = 0,
        y = 0,
        z = 0,
    ):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

        # Parent init should be called at end of __init__
        super(Coordinates,self).__init__()

    def __eq__(self, other):
        return other and self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self,other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def adjacent(self, cardinal_direction):
        if cardinal_direction.lower() == 'n':
            return Coordinates(self.x, self.y+1, self.z)
        if cardinal_direction.lower() == 's':
            return Coordinates(self.x, self.y-1, self.z)
        if cardinal_direction.lower() == 'e':
            return Coordinates(self.x+1, self.y, self.z)
        if cardinal_direction.lower() == 'w':
            return Coordinates(self.x-1, self.y, self.z)
        return None
