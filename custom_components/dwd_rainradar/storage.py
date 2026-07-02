"""Persistent storage for rolling DWD rainfall history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.helpers.storage import Store

STORAGE_VERSION = 1
STORAGE_KEY = "dwd_rainradar_history"


@dataclass(slots=True)
class RainHistoryEntry:
    """One stored RW measurement."""

    timestamp: datetime
    value: float


class RainHistoryStorage:
    """Persistent RW history."""

    def __init__(self, hass) -> None:

        self._store = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
        )

        self.entries: list[RainHistoryEntry] = []

    async def async_load(self) -> None:
        """Load history."""

        data = await self._store.async_load()

        if not data:

            self.entries = []
            return

        self.entries = [

            RainHistoryEntry(
                timestamp=datetime.fromisoformat(
                    item["timestamp"]
                ),
                value=item["value"],
            )

            for item in data.get(
                "entries",
                []
            )
        ]

    async def async_save(self) -> None:
        """Save history."""

        await self._store.async_save(
            {
                "entries": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "value": entry.value,
                    }
                    for entry in self.entries
                ]
            }
        )

    def add_entry(
        self,
        timestamp: datetime,
        value: float,
    ) -> bool:
        """Add a new RW value.

        Returns True if history changed.
        """

        if self.entries:

            last = self.entries[-1]

            if last.timestamp == timestamp:

                if last.value == value:
                    return False

                last.value = value

                return True

        self.entries.append(
            RainHistoryEntry(
                timestamp=timestamp,
                value=value,
            )
        )

        self.entries.sort(
            key=lambda item: item.timestamp
        )

        self.prune()

        return True

    def prune(
        self,
        hours: int = 13,
    ) -> None:
        """Keep only the recent history."""

        if not self.entries:
            return

        newest = self.entries[-1].timestamp

        limit = newest - timedelta(hours=hours)

        self.entries = [

            entry

            for entry in self.entries

            if entry.timestamp >= limit
        ]

    def rolling_sum(
        self,
        timestamp: datetime | None,
        hours: int,
    ) -> float | None:
        """Return rolling precipitation sum.

        Allows one missing hourly RW value.
        """

        if timestamp is None:
            return None

        if not self.entries:
            return None

        current = next(

            (
                index

                for index, entry

                in reversed(list(enumerate(self.entries)))

                if entry.timestamp == timestamp
            ),

            None,
        )

        if current is None:
            return None

        total = self.entries[current].value

        shift_used = False

        current_time = self.entries[current].timestamp

        for _ in range(hours - 1):

            found = False

            for candidate in range(current - 1, -1, -1):

                candidate_time = self.entries[candidate].timestamp

                delta = (
                    current_time
                    - candidate_time
                ).total_seconds()

                if 55 * 60 <= delta <= 65 * 60:

                    total += self.entries[candidate].value

                    current = candidate

                    current_time = candidate_time

                    found = True

                    break

                if (
                    not shift_used
                    and 115 * 60 <= delta <= 125 * 60
                ):

                    total += self.entries[candidate].value

                    current = candidate

                    current_time = candidate_time

                    shift_used = True

                    found = True

                    break

                if delta > 125 * 60:

                    break

            if not found:

                return None

        return total

    @property
    def latest_timestamp(self) -> datetime | None:
        """Return the newest stored timestamp."""

        if not self.entries:
            return None

        return self.entries[-1].timestamp

