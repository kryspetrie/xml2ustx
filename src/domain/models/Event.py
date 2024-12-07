class Event:
    """
    Base class of all events that will generate track output
    """

    def __init__(self, position: float):
        self.position = position

