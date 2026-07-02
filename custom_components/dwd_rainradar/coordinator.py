"""Data update coordinator for DWD Rain Radar."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .rolling import RainRollingCalculator
from .storage import RainHistoryStorage

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=90)


class UpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator."""

    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
            async_client,
            products,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=entry.data[CONF_NAME],
            update_interval=UPDATE_INTERVAL,
        )
        self.config_entry = entry
        self.async_client = async_client
        self.products = products

        self.history = RainHistoryStorage(hass)

        self.rolling = RainRollingCalculator(
            self.history
        )

        self._history_loaded = False

    async def _async_update_data(self) -> dict:
        """Update the data and the signal."""

        if not self._history_loaded:

            await self.history.async_load()

            self._history_loaded = True

        data = {}

        for product in self.products:

            if product.requires_update:

                await product.update(
                    self.async_client
                )

            history_value = product.history_value

            if history_value is not None:

                timestamp, value = history_value

                if self.history.add_entry(
                    timestamp,
                    value,
                ):

                    await self.history.async_save()

            data[
                product.PRODUCT_KEY
            ] = product.data

        data.update(
            self.rolling.calculate()
        )

        return data
