from src.domain.models.Voice import Voice


class TrackConfig:

    def __init__(self, name: str, voice: Voice, pan: float, volume: float):
        self.name = name
        self.voice = voice
        self.pan = pan
        self.volume = volume
