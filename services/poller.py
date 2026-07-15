import asyncio
import time
from dataclasses import dataclass

from config import POLL_INTERVAL_SEC, STATUS_DEBOUNCE_MINUTES, logger
from database import Database
from parsers import all_parsers
from services.notifier import NotificationQueue, StatusChange, dispatch_changes


@dataclass
class _PendingChange:
    status_key: str
    first_seen: float


class SourcePoller:
    def __init__(self, db: Database, queue: NotificationQueue):
        self.db = db
        self.queue = queue
        self._task: asyncio.Task | None = None
        self._pending: dict[tuple[str, str], _PendingChange] = {}

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("poll cycle error")
            await asyncio.sleep(POLL_INTERVAL_SEC)

    def _debounce_ready(self, station_id: str, fuel_key: str, status_key: str) -> bool:
        key = (station_id, fuel_key)
        now = time.monotonic()
        debounce_sec = STATUS_DEBOUNCE_MINUTES * 60
        pending = self._pending.get(key)
        if pending is None or pending.status_key != status_key:
            self._pending[key] = _PendingChange(status_key, now)
            return False
        if now - pending.first_seen >= debounce_sec:
            del self._pending[key]
            return True
        return False

    async def poll_once(self) -> int:
        changes: list[StatusChange] = []
        for parser in all_parsers():
            result = await parser.fetch()
            for st in result.stations:
                sid = f"{result.source}:{st.external_id}"
                self.db.upsert_station(
                    id=sid,
                    source=result.source,
                    name=st.name,
                    address=st.address,
                    area_key=st.area_key,
                    network_key=st.network_key,
                    lat=st.lat,
                    lon=st.lon,
                )
            for st in result.statuses:
                sid = f"{result.source}:{st.station_external_id}"
                old = self.db.upsert_status(
                    station_id=sid,
                    fuel_key=st.fuel_key,
                    status_key=st.status_key,
                    queue_hint=st.queue_hint,
                    limit_hint=st.limit_hint,
                    source_status=st.source_status,
                )
                if old == st.status_key:
                    continue
                if not self._debounce_ready(sid, st.fuel_key, st.status_key):
                    continue
                snapshot = self.db.get_station_snapshot(sid, st.fuel_key)
                if not snapshot:
                    continue
                changes.append(
                    StatusChange(
                        station_id=sid,
                        fuel_key=st.fuel_key,
                        old_status=old,
                        new_status=st.status_key,
                        station=snapshot,
                    )
                )

        queued = await dispatch_changes(self.db, self.queue, changes)
        if changes:
            logger.info("poll: %s changes, %s pushes queued", len(changes), queued)
        return queued