import music21


# file_path = './data/en_test.xml'
file_path = './data/jappo_test.xml'

music = music21.converter.parse(file_path)

for n in music.flat.notes:
    print(f"Note: {n.pitch.name}{n.pitch.octave} {n.duration.quarterLength:0.01f} - {n.lyric}")