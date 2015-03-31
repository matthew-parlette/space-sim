import uuid
from random import choice
from objects.sector import SectorObject
from objects.coordinates import Coordinates

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
