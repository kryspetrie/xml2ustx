import sys
import music21
from src.ustx_utils import generate_ustx

# file_path = './data/en_test.xml'
# file_path = './data/jappo_test.xml'
# file_path = './data/haendel_hallelujah.xml'
file_path = sys.argv[1]
print(file_path)

music = music21.converter.parse(file_path)

traks_number = 0 
parts_list = []

for part in music.parts:
    print('Part:', part.partName)
    traks_number += 1

    part_notes = []
    for event in part.flat:
        for y in event.contextSites():
            if y[0] is part:
                offset=y[1]
        if getattr(event,'isNote',None) and event.isNote:
            print(f"\tNote: {event.pitch.name}{event.pitch.octave}, Duration: {event.quarterLength}, Midi pitch: {event.pitch.midi}, Offset: {offset}")
            part_notes.append({
                'position': offset,
                'duration': event.quarterLength,
                'tone': event.pitch.midi,
                'lyric': event.lyric
            })
        if getattr(event,'isRest',None) and event.isRest:
            print(f"\tRest, Duration: {event.quarterLength}, Offset: {offset}")
        
    parts_list.append(part_notes)

text_ustx = generate_ustx(traks_number, parts_list)
print(text_ustx)
with open('test.ustx', 'w') as f:
    f.write(text_ustx)