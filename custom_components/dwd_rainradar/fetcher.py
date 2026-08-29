"""Fetcher for DWD products."""

from __future__ import annotations

import logging

from datetime import (
    UTC,
    datetime,
    timedelta,
)

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOWNLOAD_TIMEOUT,
)
from .directory import (
    DirectoryParser,
)
from .models import (
    FetchResult,
    ProductMetadata,
    RemoteProduct,
)
from .products import (
    FileType,
    Product,
    RV,
)

_LOGGER = logging.getLogger(__name__)

_FAST_RETRY_INTERVAL = timedelta(
    seconds=30,
)
_FAST_RETRY_WINDOW = timedelta(
    minutes=5,
)
_SLOW_RETRY_INTERVAL = timedelta(
    minutes=2,
)


def _as_utc(
    timestamp: datetime,
) -> datetime:
    """Return one timestamp as timezone-aware UTC."""

    if timestamp.tzinfo is None:
        return timestamp.replace(
            tzinfo=UTC,
        )

    return timestamp.astimezone(
        UTC,
    )


def _remote_check_due(
    product: Product,
    latest_product_timestamp: datetime | None,
    last_remote_check: datetime | None,
    now: datetime,
) -> bool:
    """Return whether the DWD product should be checked remotely."""

    now = _as_utc(
        now,
    )

    retry_interval = _FAST_RETRY_INTERVAL

    if latest_product_timestamp is not None:
        latest_product_timestamp = _as_utc(
            latest_product_timestamp,
        )

        if latest_product_timestamp <= now:

            next_product_timestamp = (
                latest_product_timestamp
                + product.publication_interval
            )

            expected_publication = (
                next_product_timestamp
                + product.publication_delay
            )

            if now < expected_publication:
                return False

            if (
                now
                >= expected_publication
                + _FAST_RETRY_WINDOW
            ):
                retry_interval = (
                    _SLOW_RETRY_INTERVAL
                )

    if last_remote_check is None:
        return True

    last_remote_check = _as_utc(
        last_remote_check,
    )

    if last_remote_check > now:
        return True

    return (
        now
        >= last_remote_check
        + retry_interval
    )


class Fetcher:
    """Fetch DWD product files."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the fetcher."""

        self._session: ClientSession = async_get_clientsession(
            hass,
        )

        self._directory_cache: dict[
            str,
            tuple[
                datetime,
                str,
            ]
        ] = {}

        self._last_remote_checks: dict[
            str,
            datetime,
        ] = {}

    def _build_headers(
        self,
        metadata: ProductMetadata | None,
    ) -> dict[str, str]:
        """Build HTTP headers for one request."""

        headers: dict[str, str] = {}

        if metadata is None:
            return headers

        if metadata.etag:
            headers["If-None-Match"] = (
                metadata.etag
            )

        if metadata.last_modified:
            headers["If-Modified-Since"] = (
                metadata.last_modified
            )

        return headers

    def _parse_remote_timestamp(
        self,
        product: Product,
        filename: str,
    ) -> datetime:
        """Extract the timestamp from one historical DWD filename."""

        if product.file_type is FileType.HDF5:

            parts = filename.split(
                "-",
            )

            for part in parts:

                if (
                    len(part) == 10
                    and part.isdigit()
                ):
                    return datetime.strptime(
                        part,
                        "%y%m%d%H%M",
                    ).replace(
                        tzinfo=UTC,
                    )

        else:

            stem = filename.removesuffix(
                f".{product.file_extension}",
            )

            parts = stem.split(
                "_",
            )

            if len(parts) >= 4:

                date_part = parts[2]
                time_part = parts[3]

                if (
                    len(date_part) == 8
                    and date_part.isdigit()
                    and len(time_part) == 4
                    and time_part.isdigit()
                ):
                    return datetime.strptime(
                        f"{date_part}{time_part}",
                        "%Y%m%d%H%M",
                    ).replace(
                        tzinfo=UTC,
                    )

        raise ValueError(
            f"Unable to parse timestamp from '{filename}'."
        )

    async def _async_download(
        self,
        product: Product,
        url: str,
        metadata: ProductMetadata | None = None,
    ) -> FetchResult:
        """Download one DWD product."""

        async with self._session.get(
            url,
            headers=self._build_headers(
                metadata,
            ),
            timeout=DOWNLOAD_TIMEOUT,
        ) as response:

            if response.status not in (
                200,
                304,
            ):
                response.raise_for_status()

            data: bytes | None = None

            if response.status == 200:
                data = await response.read()

            return FetchResult(
                product=product,
                downloaded=response.status == 200,
                timestamp=None,
                data=data,
                metadata=ProductMetadata(
                    etag=(
                        response.headers.get(
                            "ETag",
                        )
                        or (
                            metadata.etag
                            if metadata is not None
                            else None
                        )
                    ),
                    last_modified=(
                        response.headers.get(
                            "Last-Modified",
                        )
                        or (
                            metadata.last_modified
                            if metadata is not None
                            else None
                        )
                    ),
                ),
            )

    async def async_download(
        self,
        product: Product,
        metadata: ProductMetadata | None = None,
        latest_product_timestamp: datetime | None = None,
        *,
        force: bool = False,
    ) -> FetchResult:
        """Download the latest product when a newer one can be expected."""

        now = datetime.now(
            UTC,
        )

        if (
            not force
            and not _remote_check_due(
                product,
                latest_product_timestamp,
                self._last_remote_checks.get(
                    product.key,
                ),
                now,
            )
        ):
            return FetchResult(
                product=product,
                downloaded=False,
                timestamp=None,
                metadata=(
                    metadata
                    if metadata is not None
                    else ProductMetadata()
                ),
            )

        self._last_remote_checks[
            product.key
        ] = now

        return await self._async_download(
            product=product,
            url=product.download_url(),
            metadata=metadata,
        )

    async def async_check_connection(
        self,
    ) -> None:
        """Check whether the DWD radar service is reachable."""

        async with self._session.get(
            RV.directory_url(),
            timeout=DOWNLOAD_TIMEOUT,
        ) as response:
            response.raise_for_status()
            await response.read()

    async def async_list_remote_products(
        self,
        product: Product,
        since: datetime,
    ) -> list[RemoteProduct]:
        """Return all products available on the DWD server since a given time."""

        since = _as_utc(
            since,
        )

        now = datetime.now(
            UTC,
        )

        cached = self._directory_cache.get(
            product.key,
        )

        if (
            cached is not None
            and (
                now - cached[0]
            ).total_seconds() < 60
        ):

            listing = cached[1]

        else:

            async with self._session.get(
                product.directory_url(),
                timeout=DOWNLOAD_TIMEOUT,
            ) as response:

                response.raise_for_status()

                listing = await response.text()

            self._directory_cache[
                product.key
            ] = (
                now,
                listing,
            )

        remote_products: list[
            RemoteProduct
        ] = []

        for filename in DirectoryParser.parse(
            listing,
        ):

            if filename == product.latest_filename:
                continue

            if not filename.endswith(
                f".{product.file_extension}",
            ):
                continue

            try:
                timestamp = self._parse_remote_timestamp(
                    product,
                    filename,
                )

            except ValueError:

                _LOGGER.warning(
                    "Ignoring unexpected %s filename: %s",
                    product.key,
                    filename,
                )

                continue

            if timestamp < since:
                continue

            remote_products.append(
                RemoteProduct(
                    product=product,
                    filename=filename,
                    timestamp=timestamp,
                ),
            )

        remote_products.sort(
            key=lambda remote_product: (
                remote_product.timestamp,
            ),
        )

        return remote_products

    async def async_download_remote(
        self,
        remote_product: RemoteProduct,
    ) -> FetchResult:
        """Download one specific product from the DWD server."""

        result = await self._async_download(
            product=remote_product.product,
            url=(
                f"{remote_product.product.directory_url()}/"
                f"{remote_product.filename}"
            ),
        )

        result.timestamp = remote_product.timestamp

        result.valid_until = (
            remote_product.timestamp
        )

        result.valid_from = (
            remote_product.timestamp
            - remote_product.product.interval
        )

        return result

