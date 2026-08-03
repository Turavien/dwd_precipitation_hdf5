"""Data update coordinator for DWD Rain Radar."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .engine import Engine
from .state import State

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(
    seconds=90,
)


class UpdateCoordinator(
    DataUpdateCoordinator[
        State
    ]
):
    """Coordinate DWD product updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        engine: Engine,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name="dwd_rainradar",
            update_interval=UPDATE_INTERVAL,
        )

        self.config_entry = entry

        self._engine = engine

    async def _async_update_data(
        self,
    ) -> State:
        """Fetch and decode all configured products."""

        return await self._engine.async_update(
            grid_cell=tuple(
                self.config_entry.data[
                    "grid_cell"
                ]
            ),
        )

