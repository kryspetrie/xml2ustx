from src.models.Event import Event


class TimeSignature(Event):
    __slots__ = ('beat_per_bar', 'beat_unit')

    def __init__(self, position: int, beat_per_bar: int, beat_unit: int):
        super().__init__(position)
        self.beat_per_bar = beat_per_bar
        self.beat_unit = beat_unit

    def __hash__(self):
        return hash((self.position, self.beat_per_bar, self.beat_unit))

    def __eq__(self, other):
        return (self.position == other.position and
                self.beat_per_bar == other.beat_per_bar and
                self.beat_unit == other.beat_unit)

