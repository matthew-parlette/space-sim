import uuid
from copy import deepcopy
from objects.coordinates import Coordinates
from objects import GameObject

class ManMade(GameObject):
    yaml_tag = "!ManMade"
