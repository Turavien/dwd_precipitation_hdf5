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

        self.sf_entries: list[RainHistoryEntry] = []

    async def async_load(self) -> None:
        """Load history."""

        data = await self._store.async_load()

        if not data:

            self.entries = []
            self.sf_entries = []
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

        self.sf_entries = [

            RainHistoryEntry(
                timestamp=datetime.fromisoformat(
                    item["timestamp"]
                ),
                value=item["value"],
            )

            for item in data.get(
                "sf_entries",
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
                ],
                "sf_entries": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "value": entry.value,
                    }
                    for entry in self.sf_entries
                ],
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

    def add_sf_entry(
        self,
        timestamp: datetime,
        value: float,
    ) -> bool:
        """Add a new SF value.

        Returns True if history changed.
        """

        if self.sf_entries:

            last = self.sf_entries[-1]

            if last.timestamp == timestamp:

                if last.value == value:
                    return False

                last.value = value

                return True

        self.sf_entries.append(
            RainHistoryEntry(
                timestamp=timestamp,
                value=value,
            )
        )

        self.sf_entries.sort(
            key=lambda item: item.timestamp
        )

        self.prune_sf()

        return True

    def prune(
        self,
        hours: int = 37,
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

    def prune_sf(
        self,
        hours: int = 73,
    ) -> None:
        """Keep only the recent SF history."""

        if not self.sf_entries:
            return

        newest = self.sf_entries[-1].timestamp

        limit = newest - timedelta(hours=hours)

        self.sf_entries = [

            entry

            for entry in self.sf_entries

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

    def sum_rw_range(
        self,
        start_hours_ago: int,
        end_hours_ago: int,
    ) -> float | None:
        """Return RW sum for a historical hour range."""

        if not self.entries:
            return None

        newest = self.entries[-1].timestamp

        total = 0.0
        found = 0

        shift_used = False

        for hour in range(
            start_hours_ago,
            end_hours_ago + 1,
        ):

            target = newest - timedelta(hours=hour)

            matched = False

            for entry in reversed(self.entries):

                delta = abs(
                    (
                        entry.timestamp
                        - target
                    ).total_seconds()
                )

                if delta <= 5 * 60:

                    total += entry.value
                    found += 1
                    matched = True
                    break

                if (
                    not shift_used
                    and 55 * 60 <= delta <= 65 * 60
                ):

                    total += entry.value
                    found += 1
                    shift_used = True
                    matched = True
                    break

            if not matched:
                return None

        if found != (
            end_hours_ago
            - start_hours_ago
            + 1
        ):
            return None

        return total

    def get_sf_value(
        self,
        hours_ago: int,
    ) -> float | None:
        """Return stored SF value from approximately hours_ago."""

        if not self.sf_entries:
            return None

        newest = self.sf_entries[-1].timestamp

        target = newest - timedelta(hours=hours_ago)

        for entry in reversed(self.sf_entries):

            delta = abs(
                (
                    entry.timestamp
                    - target
                ).total_seconds()
            )

            if delta <= 5 * 60:

                return entry.value

        return None

    @property
    def latest_timestamp(self) -> datetime | None:
        """Return the newest stored timestamp."""

        if not self.entries:
            return None

        return self.entries[-1].timestamp

    @property
    def latest_sf_timestamp(
        self,
    ) -> datetime | None:
        """Return the newest stored SF timestamp."""

        if not self.sf_entries:
            return None

        return self.sf_entries[-1].timestamp
