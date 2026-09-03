import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class BleDiscoveryCoordinator:
    """
    Serialisiert BLE-Discovery-Aufrufe innerhalb des Device-Agent-Prozesses.

    Hintergrund:
    BlueZ/Bleak reagiert empfindlich auf parallele Discovery-Aufrufe und kann
    dann mit org.bluez.Error.InProgress antworten.

    Java-Vergleich:
    ungefähr ein gemeinsamer ReentrantLock/Semaphore(1) um den kritischen
    Discovery-Abschnitt.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def run(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        async with self._lock:
            return await operation()
