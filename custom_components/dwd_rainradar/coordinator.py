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
    seconds=30,
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
            config_entry=entry,
            name="dwd_rainradar",
            update_interval=UPDATE_INTERVAL,
            always_update=True,
        )

        self._engine = engine

        self._grid_cell = tuple(
            self.config_entry.data[
                "grid_cell"
            ]
        )

        self._engine.register_grid_cell(
            self._grid_cell,
        )

        self._engine.register_update_callback(
            self._handle_background_update,
        )

    def _handle_background_update(
        self,
    ) -> None:
        """Request an update after background data changed."""

        self.config_entry.async_create_task(
            self.hass,
            self.async_request_refresh(),
            "DWD Rain Radar background refresh",
        )

    def get_diagnostics(
        self,
    ) -> dict[str, object]:
        """Return non-sensitive runtime diagnostics."""

        return self._engine.get_diagnostics(
            self.data,
        )

    def unregister_engine(
        self,
    ) -> None:
        """Unregister this coordinator from the shared engine."""

        self._engine.unregister_update_callback(
            self._handle_background_update,
        )

        self._engine.unregister_grid_cell(
            self._grid_cell,
        )

    async def _async_update_data(
        self,
    ) -> State:
        """Fetch and decode all configured products."""

        return await self._engine.async_update(
            grid_cell=self._grid_cell,
        )
