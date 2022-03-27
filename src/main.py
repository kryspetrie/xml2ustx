import music21


# file_path = './data/en_test.xml'
# file_path = './data/jappo_test.xml'
file_path = './data/haendel_hallelujah.xml'

music = music21.converter.parse(file_path)

for part in music.parts:
    print('Part:', part.partName)

    for event in part.flat:
        for y in event.contextSites():
            if y[0] is part:
                offset=y[1]
        if getattr(event,'isNote',None) and event.isNote:
            print(f"\tNote: {event.pitch.name}{event.pitch.octave}, Duration: {event.quarterLength}, Midi pitch: {event.pitch.midi}, Offset: {offset}")
        if getattr(event,'isRest',None) and event.isRest:
            print(f"\tRest, Duration: {event.quarterLength}, Offset: {offset}")
    break