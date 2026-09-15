from dataclasses import dataclass
from enum import StrEnum


class WeightTrendDirection(StrEnum):
    UNKNOWN = "unknown"
    DOWN = "down"
    STABLE = "stable"
    UP = "up"


@dataclass(frozen=True)
class WeightTrendRules:
    """
    Explizite Produktregeln für die Berechnung des Gewichtstrends.

    Die Werte steuern nur die Glättung und Klassifikation des Trends.
    Sie sind keine medizinischen Grenzwerte und definieren insbesondere
    noch kein Solltempo für Gewichtsabnahme.
    """

    window_days: int = 30
    min_sample_count: int = 3
    min_span_days: float = 7.0
    stable_threshold_kg_per_week: float = 0.10

    def __post_init__(self) -> None:
        if self.window_days < 1:
            raise ValueError("window_days must be positive")
        if self.min_sample_count < 2:
            raise ValueError("min_sample_count must be at least 2")
        if self.min_span_days <= 0:
            raise ValueError("min_span_days must be positive")
        if self.window_days < self.min_span_days:
            raise ValueError("window_days must not be smaller than min_span_days")
        if self.stable_threshold_kg_per_week < 0:
            raise ValueError("stable_threshold_kg_per_week must not be negative")


@dataclass(frozen=True)
class WeightTrend:
    """Geglätteter Gewichtstrend aus mehreren Check-in-Messungen."""

    direction: WeightTrendDirection
    weekly_change_kg: float | None
    sample_count: int
    span_days: float
