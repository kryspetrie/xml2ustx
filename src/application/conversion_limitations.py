"""Detect unsupported score features and enforce conversion limitations."""
from __future__ import annotations

import music21

from src.application.conversion_log import LogFn, emit_log
from src.domain.score_rhythm_detection import is_rhythm_annotation_text


def _warn(message: str, log_fn: LogFn | None) -> None:
    emit_log(f'Warning: {message}', log_fn=log_fn)


def warn_unsupported_score_features(
        flattened: music21.stream.Stream,
        log_fn: LogFn | None = None) -> None:
    """Log warnings for score markings that are still ignored during conversion."""
    seen: set[str] = set()

    def once(key: str, message: str) -> None:
        if key not in seen:
            seen.add(key)
            _warn(message, log_fn)

    for event in flattened:
        if isinstance(event, music21.expressions.TextExpression):
            content = (event.content or '').strip().lower()
            if not content:
                continue
            if is_rhythm_annotation_text(event.content or ''):
                continue
            if content.startswith('rit') or content.startswith('accel'):
                continue
            once(
                'tempo-text',
                'Only MuseScore-style rit. and accel. tempo text is interpreted; '
                'other expressions are ignored.',
            )

