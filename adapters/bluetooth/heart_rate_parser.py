def parse_heart_rate(data: bytes) -> int:
    """
    Liest den BPM-Wert aus der BLE Heart Rate Measurement Characteristic.

    Der Bluetooth Heart Rate Standard erlaubt zwei Varianten:

    - 8 Bit Herzfrequenz
    - 16 Bit Herzfrequenz

    Das niederwertigste Bit im ersten Byte gibt an,
    welche Variante verwendet wird.

    Java-artig gedacht:

        byte flags = data[0];

        if ((flags & 0x01) != 0) {
            // 16 Bit
        } else {
            // 8 Bit
        }
    """

    if len(data) < 2:
        raise ValueError("Heart-rate payload is too short")

    flags = data[0]

    is_16_bit = (flags & 0x01) != 0

    if is_16_bit:
        if len(data) < 3:
            raise ValueError("16-bit heart-rate payload is too short")

        return int.from_bytes(
            data[1:3],
            byteorder="little",
        )

    return data[1]
