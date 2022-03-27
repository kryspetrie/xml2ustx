import music21


# file_path = './data/en_test.xml'
# file_path = './data/jappo_test.xml'
file_path = './data/haendel_hallelujah.xml'

music = music21.converter.parse(file_path)

for part in music.parts:
    print('Part:', part._partName)
    for n in part.flat.notes:
        print(f"\tNote: {n.pitch.name}{n.pitch.octave} {n.duration.quarterLength:0.01f} - {n.lyric}")