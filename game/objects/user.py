from objects import NamedEntity

class User(NamedEntity):
    yaml_tag = "!User"

    STATUS = [
        'new',
        'alive',
        'dead',
    ]

    def __init__(
        self,
        name = None,
        id = None,
        password = None,
        token = None,
        status = 'new',
        location_id = None,
        credits = 0,
        is_business = False,
    ):
        self.name = name
        self.id = id
        self.password = password
        self.token = token
        self.status = status
        self.location_id = location_id
        self.credits = 0
        self.is_business = is_business

        # Parent init should be called at end of __init__
        super(User,self).__init__(name, id)
