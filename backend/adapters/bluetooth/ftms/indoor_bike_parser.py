from dataclasses import dataclass


@dataclass(frozen=True)
class FtmsIndoorBikeData:
    """
    Werte, die in genau einer FTMS Indoor-Bike-Notification enthalten waren.

    Die Felder sind absichtlich optional:
    FTMS verteilt die Daten unseres MERACH auf mehrere Notifications.
    Eine Notification enthält also beispielsweise Cadence und Power,
    die nächste Speed und Elapsed Time.
    """

    speed_kmh: float | None = None
    cadence_rpm: float | None = None
    distance_m: int | None = None
    resistance: float | None = None
    power_w: int | None = None
    heart_rate_bpm: int | None = None
    elapsed_seconds: int | None = None


class FtmsParseError(ValueError):
    pass


def _require(data: bytes, offset: int, size: int) -> None:
    if offset + size > len(data):
        raise FtmsParseError(
            f"FTMS frame too short: "
            f"need {size} bytes at offset {offset}, "
            f"frame has {len(data)} bytes"
        )


def _u16(data: bytes, offset: int) -> int:
    _require(data, offset, 2)
    return int.from_bytes(
        data[offset : offset + 2],
        byteorder="little",
        signed=False,
    )


def _s16(data: bytes, offset: int) -> int:
    _require(data, offset, 2)
    return int.from_bytes(
        data[offset : offset + 2],
        byteorder="little",
        signed=True,
    )


def _u24(data: bytes, offset: int) -> int:
    _require(data, offset, 3)
    return int.from_bytes(
        data[offset : offset + 3],
        byteorder="little",
        signed=False,
    )


def parse_indoor_bike_data(data: bytes) -> FtmsIndoorBikeData:
    """
    Parse Bluetooth FTMS Characteristic 0x2AD2 "Indoor Bike Data".

    Wichtig bei FTMS:
    Bit 0 heißt "More Data".

    Ist Bit 0 NICHT gesetzt, befindet sich Instantaneous Speed direkt
    hinter den Flags.

    Unser MERACH nutzt dieses Verfahren tatsächlich und liefert die
    Messwerte abwechselnd über mehrere Notifications.
    """
    if len(data) < 2:
        raise FtmsParseError("FTMS Indoor Bike Data must contain at least the 2-byte flags")

    flags = _u16(data, 0)
    offset = 2

    speed_kmh: float | None = None
    cadence_rpm: float | None = None
    distance_m: int | None = None
    resistance: float | None = None
    power_w: int | None = None
    heart_rate_bpm: int | None = None
    elapsed_seconds: int | None = None

    more_data = bool(flags & (1 << 0))

    # Bit 0 ist invertiert gegenüber den üblichen "field present"-Bits:
    # More Data == 0 bedeutet, dass Instantaneous Speed enthalten ist.
    if not more_data:
        speed_kmh = _u16(data, offset) / 100.0
        offset += 2

    # Bit 1: Average Speed
    if flags & (1 << 1):
        _require(data, offset, 2)
        offset += 2

    # Bit 2: Instantaneous Cadence
    if flags & (1 << 2):
        cadence_rpm = _u16(data, offset) / 2.0
        offset += 2

    # Bit 3: Average Cadence
    if flags & (1 << 3):
        _require(data, offset, 2)
        offset += 2

    # Bit 4: Total Distance, uint24, Meter
    if flags & (1 << 4):
        distance_m = _u24(data, offset)
        offset += 3

    # Bit 5: Resistance Level
    if flags & (1 << 5):
        resistance = _s16(data, offset) / 10.0
        offset += 2

    # Bit 6: Instantaneous Power, Watt
    if flags & (1 << 6):
        power_w = _s16(data, offset)
        offset += 2

    # Bit 7: Average Power
    if flags & (1 << 7):
        _require(data, offset, 2)
        offset += 2

    # Bit 8: Expended Energy
    # Total Energy       uint16
    # Energy per Hour    uint16
    # Energy per Minute  uint8
    if flags & (1 << 8):
        _require(data, offset, 5)
        offset += 5

    # Bit 9: Heart Rate
    if flags & (1 << 9):
        _require(data, offset, 1)
        heart_rate_bpm = data[offset]
        offset += 1

    # Bit 10: Metabolic Equivalent
    if flags & (1 << 10):
        _require(data, offset, 1)
        offset += 1

    # Bit 11: Elapsed Time
    if flags & (1 << 11):
        elapsed_seconds = _u16(data, offset)
        offset += 2

    # Bit 12: Remaining Time
    if flags & (1 << 12):
        _require(data, offset, 2)
        offset += 2

    return FtmsIndoorBikeData(
        speed_kmh=speed_kmh,
        cadence_rpm=cadence_rpm,
        distance_m=distance_m,
        resistance=resistance,
        power_w=power_w,
        heart_rate_bpm=heart_rate_bpm,
        elapsed_seconds=elapsed_seconds,
    )
