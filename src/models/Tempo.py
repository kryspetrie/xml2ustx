from src.models.Event import Event


class Tempo(Event):

    def __init__(self, position: int, beat_per_minute: int):
        super().__init__(position)
        self.beat_per_minute = beat_per_minute

    def __hash__(self):
        return hash((self.position, self.beat_per_minute))

    def __eq__(self, other):
        return (self.position == other.position and
                self.beat_per_minute == other.beat_per_minute)