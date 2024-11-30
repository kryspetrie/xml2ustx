from src.models.TrackEvent import TrackEvent


class Note(TrackEvent):
    __slots__ = ('position', 'duration', 'location', 'tone', 'lyric')

    def __init__(self, position: float, duration: float, tone: int, lyrics: str):
        super().__init__(position)
        self.duration = duration
        self.tone = tone
        self.lyric = lyrics
