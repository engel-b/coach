from __future__ import annotations

import asyncio
import logging

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakDBusError, BleakError


logger = logging.getLogger(__name__)


class BleDiscoveryCoordinator:
    """Serializes BLE discovery for all Bluetooth adapters.

    BlueZ only allows a limited number of concurrent discovery operations.
    In particular, two BleakScanner.find_device_by_address() calls may
    interfere with each other and result in
    org.bluez.Error.InProgress.

    All Bluetooth adapters therefore share one coordinator instance.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def find_device_by_address(
        self,
        address: str,
        *,
        timeout: float = 10.0,
    ) -> BLEDevice | None:
        """Find a BLE device while holding the shared discovery lock.

        The lock only protects discovery. It is released as soon as the
        device has been found (or the scan has timed out). Connections and
        notifications are not serialized.
        """

        async with self._lock:
            try:
                return await BleakScanner.find_device_by_address(
                    address,
                    timeout=timeout,
                )

            except BleakDBusError as exc:
                if exc.dbus_error == "org.bluez.Error.InProgress":
                    # This should become rare once all adapters use this
                    # coordinator. It can still happen if another process
                    # on the machine performs a BlueZ discovery.
                    logger.info(
                        "BLE discovery already in progress while looking "
                        "for %s",
                        address,
                    )
                    return None

                logger.warning(
                    "BLE discovery failed for %s: %s",
                    address,
                    exc,
                )
                return None

            except BleakError as exc:
                logger.warning(
                    "BLE discovery failed for %s: %s",
                    address,
                    exc,
                )
                return None