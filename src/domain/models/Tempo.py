from src.domain.models.Event import Event


class Tempo(Event):

    def __init__(self, position: float, beats_per_minute: float):
        super().__init__(position)
        self.beats_per_minute = beats_per_minute

    def __hash__(self):
        return hash((self.position, self.beats_per_minute))

    def __eq__(self, other):
        return (other is Tempo
                and self.position == other.position
                and self.beats_per_minute == other.beats_per_minute)

    def __repr__(self):
        return f"Tempo(position={self.position}, beats_per_minute={self.beats_per_minute})";