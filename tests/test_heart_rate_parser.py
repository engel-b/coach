import pytest

from adapters.bluetooth.heart_rate_parser import parse_heart_rate


def test_parse_8_bit_heart_rate() -> None:
    """
    Standardfall für typische Pulswerte.

    Flags = 0x00
    BPM   = 72
    """

    data = bytes([0x00, 72])

    assert parse_heart_rate(data) == 72


def test_parse_16_bit_heart_rate() -> None:
    """
    Testet die laut BLE-Spezifikation ebenfalls mögliche 16-Bit-Variante.

    300 dezimal = 0x012C
    Little Endian -> 0x2C 0x01
    """

    data = bytes([0x01, 0x2C, 0x01])

    assert parse_heart_rate(data) == 300


def test_rejects_too_short_payload() -> None:
    with pytest.raises(ValueError):
        parse_heart_rate(bytes([0x00]))
