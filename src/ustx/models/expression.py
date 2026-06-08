"""OpenUtau expression definitions embedded in USTX project files."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Mapping, Self

import yaml

UstxExpressionType = Literal['Curve', 'Options', 'Numerical']


@dataclass(frozen=True)
class UstxExpression:
    """Single expression parameter definition (dynamics, pitch deviation, etc.)."""

    name: str
    abbr: str
    type: UstxExpressionType
    min: int | float
    max: int | float
    default_value: int | float
    is_flag: bool
    flag: str | None = None
    options: tuple[str, ...] | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        """Create an expression from a YAML mapping."""
        options = data.get('options')
        parsed_options: tuple[str, ...] | None = None
        if options is not None:
            parsed_options = tuple(str(option) for option in options)
        flag = str(data['flag']) if 'flag' in data else None
        return cls(
            name=str(data['name']),
            abbr=str(data['abbr']),
            type=str(data['type']),  # type: ignore[arg-type]
            min=data['min'],
            max=data['max'],
            default_value=data['default_value'],
            is_flag=bool(data['is_flag']),
            flag=flag,
            options=parsed_options,
        )

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        mapping: dict[str, Any] = {
            'name': self.name,
            'abbr': self.abbr,
            'type': self.type,
            'min': self.min,
            'max': self.max,
            'default_value': self.default_value,
            'is_flag': self.is_flag,
        }
        if self.flag is not None:
            mapping['flag'] = self.flag
        if self.options is not None:
            mapping['options'] = list(self.options)
        return mapping


@dataclass(frozen=True)
class UstxExpressionCatalog:
    """Catalog of default OpenUtau expression definitions keyed by abbreviation."""

    expressions: Mapping[str, UstxExpression]

    @classmethod
    @lru_cache(maxsize=1)
    def load_default(cls) -> UstxExpressionCatalog:
        """Load the bundled default expression catalog from ``ustx_expressions.yml``."""
        expressions_path = (
            Path(__file__).resolve().parents[2] / 'resources' / 'ustx_expressions.yml'
        )
        loaded = yaml.safe_load(expressions_path.read_text(encoding='utf-8'))
        if not isinstance(loaded, dict):
            raise RuntimeError(f'Invalid expressions template: {expressions_path}')
        parsed = {
            key: UstxExpression.from_mapping(value)
            for key, value in loaded.items()
            if isinstance(value, dict)
        }
        return cls(expressions=parsed)

    def to_mapping(self) -> dict[str, Any]:
        """Convert the catalog to a mapping keyed by expression abbreviation."""
        return {key: expression.to_mapping() for key, expression in self.expressions.items()}
