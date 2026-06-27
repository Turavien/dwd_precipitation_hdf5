"""Utility helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx


def get_previous_multiple(
    timestamp: datetime,
    interval: timedelta,
    offset: timedelta,
    include: bool = True,
) -> datetime:
    """Return previous aligned timestamp."""

    shifted = timestamp - offset

    seconds = shifted.timestamp()
    interval_seconds = interval.total_seconds()

    remainder = seconds % interval_seconds

    if remainder == 0 and not include:
        seconds -= interval_seconds
    else:
        seconds -= remainder

    return datetime.fromtimestamp(
        seconds,
        tz=timestamp.tzinfo
    ) + offset


async def async_get(
    url: str,
    client: httpx.AsyncClient,
    attempts: int = 2,
    **kwargs,
) -> httpx.Response:
    """Execute async HTTP GET request."""

    last_error = None

    for attempt in range(attempts):

        try:

            response = await client.get(
                url,
                **kwargs
            )

            response.raise_for_status()

            return response

        except httpx.TransportError as err:

            last_error = err

            if attempt < (attempts - 1):

                await asyncio.sleep(
                    (attempt + 1) * 0.1
                )

    raise last_error
