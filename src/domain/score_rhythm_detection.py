"""Detect Swing/Groove score annotations and decide rhythm application."""
from __future__ import annotations

import re

import music21

from src.domain.groove_parser import GrooveRule, parse_groove_text, swing_intensity_to_long_ratio
from src.domain.rhythm_config import RhythmConfig

_SWING_PATTERN = re.compile(
    r'^(?:apply\s+)?swing(?:\s+(?P<percent>\d{1,3})\s*%)?(?:\s|$)',
)
_GROOVE_PATTERN = re.compile(
    r'^(?:apply\s+)?groove(?:\s|$)',
)


def score_has_swing_annotation(
        stream: music21.stream.Score | music21.stream.Part | music21.stream.Stream,
        flattened: music21.stream.Stream) -> bool:
    """Return True when a Swing text expression exists outside title and lyrics."""
    excluded = _excluded_title_and_lyric_text(stream)
    for event in flattened:
        if not isinstance(event, music21.expressions.TextExpression):
            continue
        content = event.content or ''
        if not _is_swing_annotation_text(content):
            continue
        if _is_excluded_rhythm_text(content, excluded):
            continue
        return True
    return False


def score_has_groove_annotation(
        stream: music21.stream.Score | music21.stream.Part | music21.stream.Stream,
        flattened: music21.stream.Stream) -> bool:
    """Return True when a Groove text expression exists outside title and lyrics."""
    excluded = _excluded_title_and_lyric_text(stream)
    for event in flattened:
        if not isinstance(event, music21.expressions.TextExpression):
            continue
        content = event.content or ''
        if not _is_groove_annotation_text(content):
            continue
        if _is_excluded_rhythm_text(content, excluded):
            continue
        return True
    return False


def parse_swing_intensity_from_score(
        stream: music21.stream.Score | music21.stream.Part | music21.stream.Stream,
        flattened: music21.stream.Stream) -> int | None:
    """Return swing intensity from a ``Swing NN%`` score marking, if present."""
    excluded = _excluded_title_and_lyric_text(stream)
    for event in flattened:
        if not isinstance(event, music21.expressions.TextExpression):
            continue
        content = event.content or ''
        if _is_excluded_rhythm_text(content, excluded):
            continue
        normalized = _normalize_text(content)
        match = _SWING_PATTERN.match(normalized)
        if not match or match.group('percent') is None:
            continue
        return max(0, min(100, int(match.group('percent'))))
    return None


def resolve_rhythm_rules(
        rhythm_config: RhythmConfig,
        *,
        has_swing_annotation: bool,
        has_groove_annotation: bool,
        score_swing_intensity: int | None = None) -> list[GrooveRule]:
    """Decide which rhythm rules to apply from config and score annotations."""
    if rhythm_config.rhythm_disabled:
        return []

    apply_groove = has_groove_annotation or rhythm_config.force_groove
    if rhythm_config.groove.strip() and apply_groove:
        return parse_groove_text(rhythm_config.groove)

    apply_swing = has_swing_annotation or rhythm_config.force_swing
    if not apply_swing:
        return []

    intensity = score_swing_intensity if score_swing_intensity is not None else rhythm_config.swing_intensity
    if intensity <= 0:
        return []

    long_ratio = swing_intensity_to_long_ratio(intensity)
    return [GrooveRule(note_length=0.5, ratios=(long_ratio, 1 - long_ratio))]


def is_rhythm_annotation_text(text: str) -> bool:
    """Return True when text is a Swing or Groove score annotation."""
    return _is_swing_annotation_text(text) or _is_groove_annotation_text(text)


def _is_swing_annotation_text(text: str) -> bool:
    normalized = _normalize_text(text)
    return normalized == 'swing' or bool(_SWING_PATTERN.match(normalized))


def _is_groove_annotation_text(text: str) -> bool:
    normalized = _normalize_text(text)
    return normalized == 'groove' or bool(_GROOVE_PATTERN.match(normalized))


def _excluded_title_and_lyric_text(
        stream: music21.stream.Score | music21.stream.Part | music21.stream.Stream) -> set[str]:
    excluded: set[str] = set()

    metadata = getattr(stream, 'metadata', None)
    if metadata is not None and metadata.title:
        excluded.add(_normalize_text(str(metadata.title)))

    for text_box in stream.recurse().getElementsByClass(music21.text.TextBox):
        content = getattr(text_box, 'content', None)
        if content:
            excluded.add(_normalize_text(str(content)))

    for note in stream.recurse().notes:
        if not isinstance(note, music21.note.Note):
            continue
        if note.lyric:
            excluded.add(_normalize_text(note.lyric))
        for lyric in note.lyrics or []:
            if lyric.text:
                excluded.add(_normalize_text(lyric.text))

    return excluded


def _is_excluded_rhythm_text(text: str, excluded: set[str]) -> bool:
    return _normalize_text(text) in excluded


def _normalize_text(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = cleaned.replace('’', "'")
    cleaned = re.sub(r'[.!?:;]+$', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned
