class Voice:
    __slots__ = ('renderer', 'phonemizer', 'singer')

    def __init__(self, renderer: str, phonemizer: str, singer: str):
        self.renderer = renderer
        self.phonemizer = phonemizer
        self.singer = singer


