from src.domain.models.Event import Event


class TempoDown(Event):
    def __init__(self, position: int, duration: float):
        super().__init__(position)
        self.duration = duration

    def __eq__(self, other):
        return (other is TempoDown
                and self.position == other.position
                and self.duration == other.duration)

    def __hash__(self):
        return hash((self.position, self.duration))
