import uuid
from coordinates import Coordinates
from random import choice
from sector import SectorObject

class Star(SectorObject):
    yaml_tag = "!Star"

    def generate_name(self):
        """
        Return a randomly generated name for this object.

        Names for stars come from http://simbad.u-strasbg.fr/simbad
        """
        return choice([
            'Al Dhanab',
            'Arneb',
            'Alrescha',
            'Gacrux',
            'Matar',
            'Mizar',
            'Okda',
            'Phact',
            'Rigel',
            'Sabik',
        ])
