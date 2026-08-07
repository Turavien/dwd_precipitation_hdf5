"""Backfill for historical DWD products."""

from __future__ import annotations

import logging

from datetime import datetime

from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .products import RW

_LOGGER = logging.getLogger(__name__)


class Backfill:
    """Synchronize missing historical products."""

    def __init__(
        self,
        fetcher: Fetcher,
        history: History,
        decoder: Decoder,
    ) -> None:
        """Initialize the backfill."""

        self._fetcher = fetcher
        self._history = history
        self._decoder = decoder

    async def async_backfill(
        self,
        since: datetime,
    ) -> None:
        """Synchronize historical RW products."""

        remote_products = (
            await self._fetcher.async_list_remote_products(
                RW,
                since,
            )
        )

        local_valid_from = {
            interval.valid_from
            for interval in await self._history.intervals()
        }

        missing_products = [
            remote_product
            for remote_product in remote_products
            if (
                remote_product.timestamp
                not in local_valid_from
            )
        ]

        max_backfill_products = 300

        missing_products = missing_products[
            :max_backfill_products
        ]

        for remote_product in missing_products:

            try:

                result = (
                    await self._fetcher.async_download_remote(
                        remote_product,
                    )
                )

                self._decoder.decode(
                    result,
                    (0, 0),
                )

                await self._history.store(
                    result,
                )

            except Exception:

                _LOGGER.exception(
                    "Failed to backfill %s %s",
                    RW.key,
                    remote_product.filename,
                )

        await self._history.prune()

