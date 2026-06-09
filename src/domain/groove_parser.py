"""Parse and apply custom groove timing rules."""
from __future__ import annotations

import re
from dataclasses import dataclass

import music21

NOTE_LENGTH_ALIASES: dict[str, float] = {
    'quarter': 1.0,
    '4th': 1.0,
    'half': 2.0,
    '2nd': 2.0,
    '8th': 0.5,
    'eighth': 0.5,
    '16th': 0.25,
    'sixteenth': 0.25,
    '32nd': 0.125,
    'thirty-second': 0.125,
}

RULE_PATTERN = re.compile(
    r'^\s*(?P<unit>[A-Za-z0-9-]+)\s*:\s*(?P<ratios>.+?)\s*$',
)


@dataclass(frozen=True)
class GrooveRule:
    """One repeating duration pattern applied to consecutive notes."""

    note_length: float
    ratios: tuple[float, ...]


def swing_intensity_to_long_ratio(intensity: int) -> float:
    """Map swing intensity (0–100) to the long-note share of a pair.

    0% is straight (50/50). 100% is triplet swing (2/3, 1/3).
    See https://viva.pressbooks.pub/openmusictheory/chapter/swing-rhythms/
    """
    clamped = max(0, min(100, intensity))
    straight = 0.5
    triplet_swing = 2 / 3
    return straight + (clamped / 100) * (triplet_swing - straight)


def parse_groove_text(text: str) -> list[GrooveRule]:
    """Parse groove definition text into rules.

    One rule per line (or semicolon-separated), comments start with ``#``.

    Examples::

        8th: 2/3 1/3
        16th: 0.6 0.4 0.4 0.6
    """
    rules: list[GrooveRule] = []
    for chunk in re.split(r'[;\n]+', text):
        line = chunk.strip()
        if not line or line.startswith('#'):
            continue
        comment_index = line.find('#')
        if comment_index >= 0:
            line = line[:comment_index].strip()
        if not line:
            continue

        match = RULE_PATTERN.match(line)
        if not match:
            raise ValueError(f'Invalid groove rule: {line!r}. Expected format like "8th: 2/3 1/3".')

        note_length = _parse_note_length(match.group('unit'))
        ratios = _parse_ratios(match.group('ratios'))
        if len(ratios) < 2:
            raise ValueError(f'Groove rule must include at least two ratios: {line!r}')
        rules.append(GrooveRule(note_length=note_length, ratios=ratios))

    return rules


def apply_groove_rules(
        part: music21.stream.Part,
        rules: list[GrooveRule],
        *,
        start: float | None = None,
        end: float | None = None) -> None:
    """Apply groove rules to notes in a part, optionally within a beat range."""
    if not rules:
        return

    notes = [
        note for note in part.flatten().notes
        if isinstance(note, music21.note.Note)
    ]
    notes.sort(key=lambda note: note.offset)

    if start is not None:
        notes = [note for note in notes if note.offset >= start - 0.001]
    if end is not None:
        notes = [note for note in notes if note.offset < end - 0.001]

    for rule in rules:
        _apply_rule(notes, rule)


def _apply_rule(notes: list[music21.note.Note], rule: GrooveRule) -> None:
    index = 0
    group_size = len(rule.ratios)
    ratio_sum = sum(rule.ratios)
    if ratio_sum <= 0:
        raise ValueError('Groove ratios must sum to a positive value.')

    while index < len(notes):
        group: list[music21.note.Note] = []
        cursor = index
        while cursor < len(notes) and len(group) < group_size:
            note = notes[cursor]
            if abs(note.quarterLength - rule.note_length) > 0.001:
                break
            if group and abs(note.offset - (group[-1].offset + group[-1].quarterLength)) > 0.001:
                break
            group.append(note)
            cursor += 1

        if len(group) == group_size:
            total = sum(note.quarterLength for note in group)
            cursor_offset = group[0].offset
            for note_index, (note, ratio) in enumerate(zip(group, rule.ratios, strict=True)):
                note.quarterLength = total * (ratio / ratio_sum)
                if note_index > 0:
                    _set_note_offset(note, cursor_offset)
                cursor_offset += note.quarterLength
            index = cursor
            continue

        index += 1


def _parse_note_length(token: str) -> float:
    normalized = token.strip().lower()
    if normalized in NOTE_LENGTH_ALIASES:
        return NOTE_LENGTH_ALIASES[normalized]

    if normalized.isdigit():
        denominator = int(normalized)
        if denominator <= 0:
            raise ValueError(f'Invalid note length: {token!r}')
        return 4.0 / denominator

    raise ValueError(
        f'Unknown note length {token!r}. Use values like 8th, 16th, quarter, or a number (4=quarter).',
    )


def _parse_ratios(text: str) -> tuple[float, ...]:
    tokens = [token for token in re.split(r'[\s,]+', text.strip()) if token]
    if not tokens:
        raise ValueError('Groove rule is missing ratios.')
    return tuple(_parse_ratio_token(token) for token in tokens)


def _parse_ratio_token(token: str) -> float:
    cleaned = token.strip()
    if '/' in cleaned:
        numerator, denominator = cleaned.split('/', 1)
        return float(numerator) / float(denominator)
    return float(cleaned)


def _set_note_offset(note: music21.note.Note, absolute_offset: float) -> None:
    """Update a note's written offset in its containing measure or part."""
    measure = note.getContextByClass(music21.stream.Measure)
    if measure is not None:
        measure.setElementOffset(note, absolute_offset - measure.offset)
        return

    part = note.getContextByClass(music21.stream.Part)
    if part is not None:
        part.setElementOffset(note, absolute_offset)
        return

    note.offset = absolute_offset
