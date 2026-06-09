"""Lyric extraction and merging for MusicXML parts."""
from __future__ import annotations

import music21

from src.domain.models.Note import Note
from src.domain.models.Track import Track

_CONTINUATION_LYRIC = '+'
DEFAULT_LYRIC = 'doo'


def extract_note_lyric(note: music21.note.Note) -> str:
    """Return lyric text from a music21 note, preferring structured lyric objects."""
    if note.lyrics:
        parts = [(ly.text or '').strip() for ly in note.lyrics if ly.text]
        if parts:
            return ''.join(parts)
    return (note.lyric or '').strip()


def primary_syllabic(note: music21.note.Note) -> str | None:
    """Return the syllabic marker for the primary lyric, if present."""
    if not note.lyrics:
        return None
    syllabic = note.lyrics[0].syllabic
    return str(syllabic) if syllabic else None


def merge_tied_lyrics_in_place(
        stream: music21.stream.Score | music21.stream.Part | music21.stream.Stream) -> None:
    """Merge lyrics across tie chains onto the first note; mark continuations with ``+``."""
    notes = [
        note for note in stream.recurse().notes
        if isinstance(note, music21.note.Note)
    ]
    visited: set[int] = set()

    for note in notes:
        if id(note) in visited:
            continue
        tie = note.tie
        if tie is None or tie.type != 'start':
            continue

        chain = _tie_chain_from_start(note)
        for chained in chain:
            visited.add(id(chained))

        merged = _merge_lyric_texts(extract_note_lyric(n) for n in chain)
        if merged:
            chain[0].lyric = merged
            for chained in chain[1:]:
                chained.lyric = _CONTINUATION_LYRIC


def merge_syllabic_lyrics_in_part(part: music21.stream.Part) -> None:
    """Merge begin/middle/end syllable groups across consecutive notes in one part."""
    notes = [
        note for note in part.flatten().notes
        if isinstance(note, music21.note.Note)
    ]

    index = 0
    while index < len(notes):
        syllabic = primary_syllabic(notes[index])
        if syllabic != 'begin':
            index += 1
            continue

        parts = [extract_note_lyric(notes[index])]
        end_index = index
        cursor = index + 1
        while cursor < len(notes):
            next_syllabic = primary_syllabic(notes[cursor])
            parts.append(extract_note_lyric(notes[cursor]))
            end_index = cursor
            if next_syllabic == 'end':
                break
            if next_syllabic != 'middle':
                end_index = index
                break
            cursor += 1

        if end_index > index:
            merged = _merge_lyric_texts(parts)
            notes[index].lyric = merged
            for continuation_index in range(index + 1, end_index + 1):
                notes[continuation_index].lyric = _CONTINUATION_LYRIC
            index = end_index + 1
            continue

        index += 1


def fill_missing_lyrics(tracks: list[Track], default_lyric: str) -> None:
    """Fill missing lyrics from aligned notes on other parts, then the default lyric."""
    lyric_by_beat: dict[float, str] = {}
    for track in tracks:
        for event in track.events:
            if not isinstance(event, Note):
                continue
            lyric = (event.lyric or '').strip()
            if lyric and lyric != _CONTINUATION_LYRIC:
                lyric_by_beat[_beat_key(event.position)] = lyric

    default = (default_lyric or '').strip() or DEFAULT_LYRIC
    for track in tracks:
        for event in track.events:
            if not isinstance(event, Note):
                continue
            lyric = (event.lyric or '').strip()
            if lyric:
                continue
            key = _beat_key(event.position)
            if key in lyric_by_beat:
                event.lyric = lyric_by_beat[key]
            else:
                event.lyric = default


def is_continuation_lyric(lyric: str | None) -> bool:
    """Return ``True`` when the lyric marks a continuation note in OpenUtau."""
    return (lyric or '').strip() == _CONTINUATION_LYRIC


def _beat_key(position: float) -> float:
    return round(position, 4)


def _merge_lyric_texts(parts: list[str]) -> str:
    merged = ''.join(part for part in parts if part)
    return merged.rstrip('-_')


def _tie_chain_from_start(start: music21.note.Note) -> list[music21.note.Note]:
    chain = [start]
    current = start
    while current.tie and current.tie.type in ('start', 'continue'):
        next_note = _find_next_tied_note(current)
        if next_note is None:
            break
        chain.append(next_note)
        current = next_note
    return chain


def _find_next_tied_note(note: music21.note.Note) -> music21.note.Note | None:
    part = note.activeSite
    if part is None:
        return None

    target_offset = note.offset + note.quarterLength
    for candidate in part.flatten().notes:
        if not isinstance(candidate, music21.note.Note):
            continue
        if candidate.pitch != note.pitch:
            continue
        if abs(candidate.offset - target_offset) > 0.001:
            continue
        tie = candidate.tie
        if tie is not None and tie.type in ('continue', 'stop'):
            return candidate
    return None
