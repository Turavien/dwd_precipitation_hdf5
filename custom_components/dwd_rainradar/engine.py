"""Engine for DWD data processing."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant

from .backfill import Backfill
from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .products import (
    RS,
    RV,
    RW,
    SF,
)
from .state import State
from .storage import Storage


class Engine:
    """Coordinate download, storage and parsing."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the engine."""

        self._storage = Storage(
            hass,
        )

        self._decoder = Decoder()

        self._history = History(
            self._storage,
            self._decoder,
        )

        self._fetcher = Fetcher(
            hass,
        )

        self._backfill = Backfill(
            self._fetcher,
            self._history,
            self._decoder,
        )

        self._state = State()

        self._products = (
            RS,
            RV,
            RW,
            SF,
        )

    async def async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Update all configured DWD products."""

        decoded_products = {}

        updated = False

        for product in self._products:

            #
            # 1.
            # Read stored HTTP metadata.
            #

            metadata = await self._storage.async_read_metadata(
                product.key,
            )

            #
            # 2.
            # Download latest product.
            #

            result = await self._fetcher.async_download(
                product,
                metadata,
            )

            #
            # 3.
            # Use cached file if unchanged.
            #

            if not result.downloaded:

                try:

                    result = await self._history.product(
                        product,
                    ).read_latest()

                except FileNotFoundError:

                    result = await self._fetcher.async_download(
                        product,
                    )

            #
            # 4.
            # Decode product.
            #

            decoded = self._decoder.decode(
                result,
                grid_cell,
            )

            latest = decoded.values[-1]

            #
            # 5.
            # Persist updated product.
            #

            if result.downloaded:
                await self._history.product(
                    product,
                ).store(
                    result,
                )

                await self._backfill.async_backfill(
                    product,
                    latest.valid_until
                    - product.retention
                    + product.interval / 2,
                )

                updated = True

            decoded_products[
                product.key
            ] = decoded

        if updated:
            await self._history.prune()

        rw = decoded_products.get(
            "rw",
        )

        sf = decoded_products.get(
            "sf",
        )

        rolling: dict[str, float | None] = {}

        if (
            rw is not None
            and rw.values
            and sf is not None
            and sf.values
        ):

            rolling = await self._history.rolling_summaries(
                rw_anchor=rw.values[-1].valid_until,
                sf_anchor=sf.values[-1].valid_until,
                grid_cell=grid_cell,
            )

        self._state.update(
            decoded_products,
            rolling,
        )

        return self._state

