"""Helpers for comparing USTX YAML documents in tests."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import pytest
import yaml


@dataclass(frozen=True)
class UstxNoteTiming:
    """One exported note's timing in ticks and quarter-note beats."""

    position_ticks: int
    duration_ticks: int
    position_beats: float
    duration_beats: float


def load_ustx_document(text: str) -> dict[str, Any]:
    """Parse USTX YAML text into a Python mapping.

    Args:
        text: Raw USTX file contents.

    Returns:
        Parsed document root mapping.

    Raises:
        AssertionError: If the parsed root is not a mapping.
    """
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        raise AssertionError('USTX root must be a mapping')
    return document


def normalize_ustx_document(document: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy export quirks for stable semantic comparison.

    Args:
        document: Parsed USTX document mapping.

    Returns:
        Deep copy of the document with legacy ``None`` representations normalized.
    """
    normalized = copy.deepcopy(document)
    if isinstance(normalized.get('ustx_version'), str):
        normalized['ustx_version'] = float(normalized['ustx_version'])

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if item is None and key in {'name', 'track_name'}:
                    value[key] = 'None'
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(normalized)
    return normalized


def assert_ustx_documents_equal(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    """Assert two parsed USTX documents are semantically equivalent.

    Args:
        actual: Parsed document produced by the exporter under test.
        expected: Parsed golden/reference document.

    Raises:
        AssertionError: If the normalized documents differ.
    """
    assert normalize_ustx_document(actual) == normalize_ustx_document(expected)


def ustx_resolution(document: dict[str, Any]) -> int:
    """Return project tick resolution (ticks per quarter note)."""
    resolution = document.get('resolution', 480)
    if not isinstance(resolution, int):
        raise AssertionError(f'Expected integer resolution, got {resolution!r}')
    return resolution


def voice_part_note_timings(
        document: dict[str, Any],
        *,
        part_index: int = 0) -> list[UstxNoteTiming]:
    """Extract note position/duration from a parsed USTX document."""
    voice_parts = document.get('voice_parts')
    if not isinstance(voice_parts, list) or not voice_parts:
        raise AssertionError('USTX document has no voice_parts')

    part = voice_parts[part_index]
    if not isinstance(part, dict):
        raise AssertionError('voice_part must be a mapping')

    notes = part.get('notes')
    if not isinstance(notes, list):
        raise AssertionError('voice_part.notes must be a list')

    resolution = ustx_resolution(document)
    timings: list[UstxNoteTiming] = []
    for note in notes:
        if not isinstance(note, dict):
            raise AssertionError('Each note must be a mapping')
        position_ticks = int(note['position'])
        duration_ticks = int(note['duration'])
        timings.append(UstxNoteTiming(
            position_ticks=position_ticks,
            duration_ticks=duration_ticks,
            position_beats=position_ticks / resolution,
            duration_beats=duration_ticks / resolution,
        ))
    return timings


def assert_note_durations_beats(
        document: dict[str, Any],
        expected_durations: list[float],
        *,
        part_index: int = 0) -> None:
    """Assert exported note durations in quarter-note beats."""
    timings = voice_part_note_timings(document, part_index=part_index)
    assert len(timings) == len(expected_durations), (
        f'Expected {len(expected_durations)} notes, got {len(timings)}'
    )
    for index, (timing, expected) in enumerate(zip(timings, expected_durations, strict=True)):
        assert timing.duration_beats == pytest.approx(expected), (
            f'Note {index}: expected duration {expected} beats, '
            f'got {timing.duration_beats} ({timing.duration_ticks} ticks)'
        )


def assert_consecutive_notes_abut(document: dict[str, Any], *, part_index: int = 0) -> None:
    """Assert each note starts where the previous note ends (no gaps/overlaps)."""
    timings = voice_part_note_timings(document, part_index=part_index)
    for index in range(len(timings) - 1):
        current = timings[index]
        nxt = timings[index + 1]
        expected_next_position = current.position_ticks + current.duration_ticks
        assert nxt.position_ticks == expected_next_position, (
            f'Gap/overlap between notes {index} and {index + 1}: '
            f'expected next position {expected_next_position}, got {nxt.position_ticks}'
        )
