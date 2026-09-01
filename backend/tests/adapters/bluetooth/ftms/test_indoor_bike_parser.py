import pytest

from adapters.bluetooth.ftms.indoor_bike_parser import (
    FtmsParseError,
    parse_indoor_bike_data,
)


def test_parses_merach_cadence_distance_resistance_and_power() -> None:
    # Reales Frame vom MRK-S26:
    #
    # 75 00
    # a8 00        cadence = 168 / 2 = 84 rpm
    # b3 00 00     distance = 179 m
    # 00 00        resistance = 0
    # 50 01        power = 336 W
    data = bytes.fromhex("75 00 a8 00 b3 00 00 00 00 50 01")

    result = parse_indoor_bike_data(data)

    assert result.speed_kmh is None
    assert result.cadence_rpm == 84.0
    assert result.distance_m == 179
    assert result.resistance == 0.0
    assert result.power_w == 336


def test_parses_merach_speed_and_elapsed_time() -> None:
    # Reales zweites Frame:
    #
    # 00 0b
    # 66 0a        speed = 2662 / 100 = 26.62 km/h
    # 03 00 00 00 00
    # 00
    # 1f 00        elapsed = 31 s
    #
    # Die Zwischenfelder ergeben sich aus den gesetzten Flags.
    data = bytes.fromhex("00 0b 66 0a 03 00 00 00 00 00 1f 00")

    result = parse_indoor_bike_data(data)

    assert result.speed_kmh == 26.62
    assert result.elapsed_seconds == 31


def test_rejects_truncated_frame() -> None:
    with pytest.raises(FtmsParseError):
        parse_indoor_bike_data(bytes.fromhex("75"))


def test_rejects_frame_missing_declared_fields() -> None:
    # Flags sagen unter anderem Cadence/Distance/Power voraus,
    # aber die Nutzdaten fehlen.
    with pytest.raises(FtmsParseError):
        parse_indoor_bike_data(bytes.fromhex("75 00"))
