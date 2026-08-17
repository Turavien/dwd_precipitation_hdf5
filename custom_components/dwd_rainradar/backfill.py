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

    _MAX_BACKFILL_PRODUCTS = 300

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
    ) -> tuple[
        bool,
        bool,
    ]:
        """Synchronize historical RW products."""

        try:
            remote_products = (
                await self._fetcher.async_list_remote_products(
                    RW,
                    since,
                )
            )

        except Exception:

            _LOGGER.exception(
                "Failed to list remote %s products",
                RW.key,
            )

            return (
                False,
                False,
            )

        local_valid_from = {
            interval.valid_from
            for interval in await self._history.intervals()
        }

        missing_products = [
            remote_product
            for remote_product in remote_products
            if (
                remote_product.timestamp - RW.interval
                not in local_valid_from
            )
        ]

        missing_products = missing_products[
            :self._MAX_BACKFILL_PRODUCTS
        ]

        completed = True
        changed = False

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
                    update_metadata=False,
                )

                changed = True

            except Exception:

                completed = False

                _LOGGER.exception(
                    "Failed to backfill %s %s",
                    RW.key,
                    remote_product.filename,
                )

        try:
            await self._history.prune()

        except Exception:

            completed = False

            _LOGGER.exception(
                "Failed to prune %s history",
                RW.key,
            )

        return (
            completed,
            changed,
        )
