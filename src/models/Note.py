from src.models.Event import Event


class Note(Event):

    def __init__(self, position: float, duration: float, tone: int, lyrics: str):
        super().__init__(position)
        self.duration = duration
        self.tone = tone
        self.lyric = lyrics
