"""
This file is BAD and is remnants of the original implementation.
We should NOT be generating this file using string templates and string concatenation.
TODO: Generate USTX file via the imported yaml library
"""


TRACKS_LABEL = 'tracks:'
VOICE_PARTS_LABEL = 'voice_parts:'
TEMPOS_LABEL = 'tempos:'
TIME_SIGNATURES_LABEL = 'time_signatures:'
EMPTY_WAVE_PARTS = 'wave_parts: []'


def generate_part(
        track_number: int,
        track_name: str):
    return f"""- name: {track_name}
  comment: ''
  track_no: {track_number}
  position: 0
  notes:"""


def format_note(
        tick_position: int,
        tick_duration: int,
        tone: int,
        lyric: str):
    if lyric is not None:
        lyric = lyric.replace("\n", "")

    return f"""  - position: {tick_position}
    duration: {tick_duration}
    tone: {tone}
    lyric: "{lyric}"
    pitch:
      data:
      - {{x: -40, y: 0, shape: io}}
      - {{x: 25, y: 0, shape: io}}
      snap_first: true
    vibrato: {{length: 0, period: 175, depth: 25, in: 10, out: 10, shift: 0, drift: 0}}
    note_expressions: []
    phoneme_expressions: []
    phoneme_overrides: []"""


def format_track_header(
        name: str,
        phonemizer: str,
        singer: str,
        renderer: str,
        volume: float = 0.0,
        pan: float = 0.0):
    ustx: str = f"""- mute: false
  solo: false
  volume: {volume}
  pan: {pan}"""

    if phonemizer is not None:
        ustx += f'\n  phonemizer: {phonemizer}';

    if renderer is not None:
        ustx += f'''\n  renderer_settings:
    renderer: DIFFSINGER'''

    if singer is not None:
        ustx += f'\n  singer: {singer}'

    if name is not None or name != "":
        ustx += f'\n  track_name: {name}'

    return ustx


def format_time_signature(position: int, beat_per_bar: int, beat_unit: int):
    return f'- bar_position: {position}\n  beat_per_bar: {beat_per_bar}\n  beat_unit: {beat_unit}'


def format_tempo(position: int, bpm: int):
    return f'- position: {position}\n  bpm: {bpm}'


def format_file_header(name: str, resolution: int):
    return f"""
name: {name}
output_dir: Vocal
cache_dir: UCache
ustx_version: 0.6
resolution: {resolution}
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
    flag: ''
"""
