import asyncio
import logging

from features.workout.service.video_catalog_sync_service import (
    VideoCatalogSyncService,
)

logger = logging.getLogger(__name__)


class VideoCatalogLifecycle:
    def __init__(
        self,
        *,
        sync_service: VideoCatalogSyncService,
        interval_seconds: float = 300.0,
    ) -> None:
        self._sync_service = sync_service
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._run_sync()
        if self._interval_seconds > 0:
            self._task = asyncio.create_task(self._run_periodically())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    def _run_sync(self) -> None:
        result = self._sync_service.sync()
        logger.info(
            "Workout video catalog synced: added=%s reactivated=%s deactivated=%s directory=%s",
            result.added,
            result.reactivated,
            result.deactivated,
            self._sync_service.video_directory,
        )

    async def _run_periodically(self) -> None:
        while True:
            await asyncio.sleep(self._interval_seconds)
            self._run_sync()
