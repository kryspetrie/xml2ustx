class TimelineEvent:
    __slots__ = 'position'
    """
    Base class of all events that happen across all tracks
    """

    def __init__(self, position: int):
        self.position = position

