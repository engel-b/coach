from dataclasses import dataclass

from features.coaching.domain.live_coaching import HeartRateZoneStatus

MAX_CONTINUOUS_SAMPLE_GAP_SECONDS = 30.0


@dataclass(frozen=True)
class HeartRateDeviation:
    zone_status: HeartRateZoneStatus
    outside_target_seconds: float


class HeartRateDeviationTracker:
    """
    Verfolgt, wie lange die Herzfrequenz ununterbrochen außerhalb
    des Zielbereichs liegt.

    Ein Wechsel zwischen ABOVE_TARGET, IN_TARGET und BELOW_TARGET
    setzt die laufende Abweichungsdauer zurück.
    """

    def __init__(self) -> None:
        self._current_status: HeartRateZoneStatus | None = None
        self._deviation_started_at_seconds: float | None = None
        self._last_timestamp_seconds: float | None = None

    def reset(self) -> None:
        """Verwirft eine laufende Abweichung, z. B. nach Pause oder Sensorlücke."""

        self._current_status = None
        self._deviation_started_at_seconds = None
        self._last_timestamp_seconds = None

    def update(
        self,
        *,
        timestamp_seconds: float,
        heart_rate_bpm: int,
        target_min_bpm: int,
        target_max_bpm: int,
    ) -> HeartRateDeviation:
        self._validate(
            timestamp_seconds=timestamp_seconds,
            heart_rate_bpm=heart_rate_bpm,
            target_min_bpm=target_min_bpm,
            target_max_bpm=target_max_bpm,
        )

        if (
            self._last_timestamp_seconds is not None
            and timestamp_seconds < self._last_timestamp_seconds
        ):
            raise ValueError("timestamp_seconds must not move backwards")

        if (
            self._last_timestamp_seconds is not None
            and timestamp_seconds - self._last_timestamp_seconds > MAX_CONTINUOUS_SAMPLE_GAP_SECONDS
        ):
            # Eine groessere Sample-Luecke gilt als unterbrochene HR-Verbindung.
            # Alte Abweichungsdauer darf nach einem Sensor-Reconnect nicht
            # weitergezaehlt werden.
            self._current_status = None
            self._deviation_started_at_seconds = None

        self._last_timestamp_seconds = timestamp_seconds

        status = self._determine_status(
            heart_rate_bpm=heart_rate_bpm,
            target_min_bpm=target_min_bpm,
            target_max_bpm=target_max_bpm,
        )

        if status is HeartRateZoneStatus.IN_TARGET:
            self._current_status = status
            self._deviation_started_at_seconds = None

            return HeartRateDeviation(
                zone_status=status,
                outside_target_seconds=0.0,
            )

        if status is not self._current_status:
            self._current_status = status
            self._deviation_started_at_seconds = timestamp_seconds

            return HeartRateDeviation(
                zone_status=status,
                outside_target_seconds=0.0,
            )

        if self._deviation_started_at_seconds is None:
            self._deviation_started_at_seconds = timestamp_seconds

        return HeartRateDeviation(
            zone_status=status,
            outside_target_seconds=(timestamp_seconds - self._deviation_started_at_seconds),
        )

    @staticmethod
    def _determine_status(
        *,
        heart_rate_bpm: int,
        target_min_bpm: int,
        target_max_bpm: int,
    ) -> HeartRateZoneStatus:
        if heart_rate_bpm < target_min_bpm:
            return HeartRateZoneStatus.BELOW_TARGET

        if heart_rate_bpm > target_max_bpm:
            return HeartRateZoneStatus.ABOVE_TARGET

        return HeartRateZoneStatus.IN_TARGET

    @staticmethod
    def _validate(
        *,
        timestamp_seconds: float,
        heart_rate_bpm: int,
        target_min_bpm: int,
        target_max_bpm: int,
    ) -> None:
        if timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must not be negative")

        if heart_rate_bpm <= 0:
            raise ValueError("heart_rate_bpm must be positive")

        if target_min_bpm <= 0:
            raise ValueError("target_min_bpm must be positive")

        if target_max_bpm <= 0:
            raise ValueError("target_max_bpm must be positive")

        if target_min_bpm > target_max_bpm:
            raise ValueError("target_min_bpm must not be greater than target_max_bpm")
