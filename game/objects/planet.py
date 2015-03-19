import uuid
from coordinates import Coordinates
from random import choice
from sector import SectorObject

class Planet(SectorObject):
    yaml_tag = "!Planet"

    def generate_name(self):
        """
        Return a randomly generated name for this object.

        Names for planets come from http://fantasynamegenerators.com/planet_names.php
        """
        return choice([
            'Latania',
            'Efryria',
            'Glaonides',
            'Uewhiuq',
            'Skoyotania',
            'Oxfrion',
            'Wheyayama',
            'Auflhone',
            'Thiokeiliv',
            'Oiwuichiri',
        ])
