"""Tests for swing and custom groove timing."""
from __future__ import annotations

import music21
import pytest

from src.domain.groove_parser import (
    GrooveRule,
    apply_groove_rules,
    parse_groove_text,
    swing_intensity_to_long_ratio,
)
from src.domain.rhythm_config import RhythmConfig
from src.domain.score_rhythm_detection import resolve_rhythm_rules


def test_swing_intensity_endpoints() -> None:
    assert swing_intensity_to_long_ratio(0) == pytest.approx(0.5)
    assert swing_intensity_to_long_ratio(100) == pytest.approx(2 / 3)


def test_parse_groove_text_accepts_fractions() -> None:
    rules = parse_groove_text('8th: 2/3 1/3')
    assert rules == [GrooveRule(note_length=0.5, ratios=(2 / 3, 1 / 3))]


def test_parse_groove_text_ignores_comments() -> None:
    rules = parse_groove_text('# swing feel\n8th: 0.6 0.4')
    assert len(rules) == 1
    assert rules[0].ratios == (0.6, 0.4)


def test_apply_groove_rule_adjusts_eighth_pair() -> None:
    part = music21.stream.Part()
    first = music21.note.Note('C4', quarterLength=0.5)
    second = music21.note.Note('D4', quarterLength=0.5)
    part.insert(0, first)
    part.insert(0.5, second)

    apply_groove_rules(part, [GrooveRule(note_length=0.5, ratios=(2 / 3, 1 / 3))])
    assert first.quarterLength == pytest.approx(2 / 3)
    assert second.quarterLength == pytest.approx(1 / 3)


def test_resolve_rules_prefers_groove_when_marked() -> None:
    config = RhythmConfig(
        force_swing=True,
        swing_intensity=100,
        groove='16th: 0.6 0.4 0.4 0.6',
    )
    rules = resolve_rhythm_rules(config, has_swing_annotation=True, has_groove_annotation=True)
    assert len(rules) == 1
    assert rules[0].note_length == 0.25


def test_resolve_rules_force_swing_when_unmarked() -> None:
    config = RhythmConfig(force_swing=True, swing_intensity=100)
    rules = resolve_rhythm_rules(config, has_swing_annotation=False, has_groove_annotation=False)
    assert len(rules) == 1
    assert rules[0].ratios[0] == pytest.approx(2 / 3)


def test_resolve_rules_force_groove_when_unmarked() -> None:
    config = RhythmConfig(force_groove=True, groove='8th: 2/3 1/3')
    rules = resolve_rhythm_rules(config, has_swing_annotation=False, has_groove_annotation=False)
    assert len(rules) == 1
    assert rules[0].note_length == 0.5


def test_resolve_rules_disabled_returns_empty() -> None:
    config = RhythmConfig(rhythm_disabled=True, force_swing=True, swing_intensity=100)
    assert resolve_rhythm_rules(config, has_swing_annotation=True, has_groove_annotation=False) == []
