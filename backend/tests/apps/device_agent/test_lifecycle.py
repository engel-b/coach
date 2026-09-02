import asyncio

import pytest
from bleak.exc import BleakError

from apps.device_agent.lifecycle import run_device_worker


@pytest.mark.asyncio
async def test_device_worker_retries_after_bleak_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Erwarteter BLE-Ausfall:

    Der Worker soll nicht sterben, sondern nach der Retry-Pause
    erneut versuchen.

    Java-Vergleich:
    ungefähr ein RetryTemplate um eine Device-Operation.
    """

    calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1

        if calls == 1:
            raise BleakError("device unavailable")

        raise asyncio.CancelledError

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert calls == 2


@pytest.mark.asyncio
async def test_device_worker_retries_after_os_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Auch ein temporärer I/O-Fehler soll einen Retry auslösen.
    """

    calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1

        if calls == 1:
            raise OSError("temporary I/O failure")

        raise asyncio.CancelledError

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert calls == 2


@pytest.mark.asyncio
async def test_device_worker_retries_after_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    TimeoutError ist ebenfalls ein erwartbarer technischer Fehler.
    """

    calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1

        if calls == 1:
            raise TimeoutError("telemetry timeout")

        raise asyncio.CancelledError

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert calls == 2


@pytest.mark.asyncio
async def test_device_worker_retries_when_operation_returns_normally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Eine langlebige Device-Operation sollte normalerweise nicht
    einfach regulär enden.

    Falls sie es doch tut, startet der Worker einen neuen Versuch.
    """

    calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1

        if calls == 1:
            return

        raise asyncio.CancelledError

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert calls == 2


@pytest.mark.asyncio
async def test_device_worker_propagates_cancellation_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Cancellation gehört zum kontrollierten Shutdown.

    Deshalb darf CancelledError nicht in einen Retry umgewandelt werden.
    """

    calls = 0
    sleep_calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1
        raise asyncio.CancelledError

    async def fake_sleep(_seconds: float) -> None:
        nonlocal sleep_calls
        sleep_calls += 1

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(asyncio.CancelledError):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert calls == 1
    assert sleep_calls == 0


@pytest.mark.asyncio
async def test_device_worker_does_not_swallow_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Programmierfehler oder unerwartete Integrationsfehler sollen
    sichtbar bleiben.

    Deshalb fängt run_device_worker() absichtlich nicht Exception
    pauschal ab.
    """

    sleep_calls = 0

    async def operation() -> None:
        raise ValueError("unexpected application error")

    async def fake_sleep(_seconds: float) -> None:
        nonlocal sleep_calls
        sleep_calls += 1

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(
        ValueError,
        match="unexpected application error",
    ):
        await run_device_worker(
            name="Test device",
            operation=operation,
            retry_delay_seconds=5.0,
        )

    assert sleep_calls == 0
