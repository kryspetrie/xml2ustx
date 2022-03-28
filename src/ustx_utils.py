def generate_ustx(traks_count, voice_parts):
    ustx_string = [boilerplate()]
    ustx_string += ["tracks:"] + [ generate_trak_line() for i in range(traks_count)]
    
    ustx_string += ["voice_parts:"]
    for i, p in enumerate(voice_parts):
        ustx_string += [generate_part(i)]
        for n in p:
            ustx_string += [generate_note(int(n['position'] * 100),int(n['duration'] * 100), n['tone'], n['lyric'])]

    ustx_string += [generate_wav_parts()]
    return '\n'.join(ustx_string)

def generate_part(i):
    return f"""- name: New Part
  comment: ''
  track_no: {i}
  position: 0
  notes:"""

def generate_note(position, duration, tone, lyric):
    return """  - position: %s
    duration: %s
    tone: %s
    lyric: %s
    pitch:
      data:
      - {x: -40, y: 0, shape: io}
      - {x: 25, y: 0, shape: io}
      snap_first: true
    vibrato: {length: 0, period: 175, depth: 25, in: 10, out: 10, shift: 0, drift: 0}
    note_expressions: []
    phoneme_expressions: []
    phoneme_overrides: []""" % (position, duration, tone, lyric)

def generate_trak_line():
    return """- phonemizer: OpenUtau.Core.DefaultPhonemizer
  mute: false
  solo: false
  volume: 0"""

def generate_wav_parts():
    return "wave_parts: []"

def boilerplate():
    return """name: New Project
comment: ''
output_dir: Vocal
cache_dir: UCache
ustx_version: 0.5
bpm: 120
beat_per_bar: 4
beat_unit: 4
resolution: 480
expressions:
  dyn:
    name: dynamics
    abbr: dyn
    type: Curve
    min: -240
    max: 120
    default_value: 0
    is_flag: false
    flag: ''
  pitd:
    name: pitch deviation
    abbr: pitd
    type: Curve
    min: -1200
    max: 1200
    default_value: 0
    is_flag: false
    flag: ''
  clr:
    name: voice color
    abbr: clr
    type: Options
    min: 0
    max: -1
    default_value: 0
    is_flag: false
    options: []
  eng:
    name: resampler engine
    abbr: eng
    type: Options
    min: 0
    max: 1
    default_value: 0
    is_flag: false
    options:
    - ''
    - worldline
  vel:
    name: velocity
    abbr: vel
    type: Numerical
    min: 0
    max: 200
    default_value: 100
    is_flag: false
    flag: ''
  vol:
    name: volume
    abbr: vol
    type: Numerical
    min: 0
    max: 200
    default_value: 100
    is_flag: false
    flag: ''
  atk:
    name: attack
    abbr: atk
    type: Numerical
    min: 0
    max: 200
    default_value: 100
    is_flag: false
    flag: ''
  dec:
    name: decay
    abbr: dec
    type: Numerical
    min: 0
    max: 100
    default_value: 0
    is_flag: false
    flag: ''
  gen:
    name: gender
    abbr: gen
    type: Numerical
    min: -100
    max: 100
    default_value: 0
    is_flag: true
    flag: g
  bre:
    name: breath
    abbr: bre
    type: Numerical
    min: 0
    max: 100
    default_value: 0
    is_flag: true
    flag: B
  lpf:
    name: lowpass
    abbr: lpf
    type: Numerical
    min: 0
    max: 100
    default_value: 0
    is_flag: true
    flag: H
  mod:
    name: modulation
    abbr: mod
    type: Numerical
    min: 0
    max: 100
    default_value: 0
    is_flag: false
    flag: ''
  alt:
    name: alternate
    abbr: alt
    type: Numerical
    min: 0
    max: 16
    default_value: 0
    is_flag: false
    flag: ''
  shft:
    name: tone shift
    abbr: shft
    type: Numerical
    min: -36
    max: 36
    default_value: 0
    is_flag: false
    flag: ''"""