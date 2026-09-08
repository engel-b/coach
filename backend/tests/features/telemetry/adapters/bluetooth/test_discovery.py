import asyncio

import pytest

from features.telemetry.adapters.bluetooth.discovery import BleDiscoveryCoordinator


@pytest.mark.asyncio
async def test_discovery_operations_are_serialized() -> None:
    """
    Zwei konkurrierende BLE-Discovery-Aufrufe dürfen nicht gleichzeitig
    ausgeführt werden.

    BlueZ kann parallele Scans mit org.bluez.Error.InProgress ablehnen.
    Der Coordinator stellt deshalb genau einen aktiven Discovery-Aufruf
    gleichzeitig sicher.
    """

    coordinator = BleDiscoveryCoordinator()

    first_operation_started = asyncio.Event()
    allow_first_operation_to_finish = asyncio.Event()

    active_operations = 0
    maximum_active_operations = 0

    async def first_operation() -> str:
        nonlocal active_operations
        nonlocal maximum_active_operations

        active_operations += 1
        maximum_active_operations = max(
            maximum_active_operations,
            active_operations,
        )

        first_operation_started.set()

        await allow_first_operation_to_finish.wait()

        active_operations -= 1
        return "first"

    async def second_operation() -> str:
        nonlocal active_operations
        nonlocal maximum_active_operations

        active_operations += 1
        maximum_active_operations = max(
            maximum_active_operations,
            active_operations,
        )

        active_operations -= 1
        return "second"

    first_task = asyncio.create_task(
        coordinator.run(first_operation),
    )

    await first_operation_started.wait()

    second_task = asyncio.create_task(
        coordinator.run(second_operation),
    )

    # Dem zweiten Task die Möglichkeit geben anzulaufen.
    # Ohne Lock würde er jetzt parallel in second_operation() gelangen.
    await asyncio.sleep(0)

    assert active_operations == 1

    allow_first_operation_to_finish.set()

    first_result, second_result = await asyncio.gather(
        first_task,
        second_task,
    )

    assert first_result == "first"
    assert second_result == "second"
    assert maximum_active_operations == 1
