"""Backfill for historical DWD products."""

from __future__ import annotations

import logging

from datetime import datetime

from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .products import Product

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
        product: Product,
        since: datetime,
    ) -> None:
        """Synchronize historical products."""

        remote_products = (
            await self._fetcher.async_list_remote_products(
                product,
                since,
            )
        )

        history = self._history.product(
            product,
        )

        local_valid_from = {
            interval.valid_from
            for interval in await history.intervals()
        }

        missing_products = [
            remote_product
            for remote_product in remote_products
            if (
                remote_product.timestamp
                not in local_valid_from
            )
        ]

        _LOGGER.debug(
            "Backfill found %d missing %s products",
            len(
                missing_products,
            ),
            product.key,
        )

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

                await history.store(
                    result,
                )

            except Exception:

                _LOGGER.exception(
                    "Failed to backfill %s %s",
                    product.key,
                    remote_product.filename,
                )

        await history.prune(
            product.retention,
        )

