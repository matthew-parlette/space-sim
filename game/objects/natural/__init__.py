import uuid
from copy import deepcopy
from objects.coordinates import Coordinates
from objects import GameObject

class Natural(GameObject):
    yaml_tag = "!Natural"
