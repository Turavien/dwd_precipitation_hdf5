"""Fetcher for DWD products."""

from __future__ import annotations

import logging

from datetime import (
    UTC,
    datetime,
)

from aiohttp import ClientError, ClientSession
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
)

_LOGGER = logging.getLogger(__name__)


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

    def _build_remote_product(
        self,
        product: Product,
        filename: str,
        timestamp: datetime,
    ) -> RemoteProduct:
        """Create one remote product."""

        return RemoteProduct(
            product=product,
            timestamp=timestamp,
            filename=filename,
        )

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

            return datetime.strptime(
                f"{parts[2]}{parts[3]}",
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

        _LOGGER.debug(
            "Downloading %s",
            url,
        )

        try:

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

                result = FetchResult(
                    product=product,
                    downloaded=response.status == 200,
                    timestamp=None,
                    data=data,
                    metadata=ProductMetadata(
                        etag=response.headers.get(
                            "ETag",
                        ),
                        last_modified=response.headers.get(
                            "Last-Modified",
                        ),
                    ),
                )

        except ClientError:

            _LOGGER.exception(
                "Download failed: %s",
                url,
            )

            raise

        if result.data is None:

            _LOGGER.debug(
                "Product %s not modified",
                product.key,
            )

        else:

            _LOGGER.debug(
                "Downloaded %s (%d bytes)",
                url,
                len(result.data),
            )

        return result

    async def async_download(
        self,
        product: Product,
        metadata: ProductMetadata | None = None,
    ) -> FetchResult:
        """Download latest product."""

        return await self._async_download(
            product=product,
            url=product.download_url(),
            metadata=metadata,
        )

    async def async_list_remote_products(
        self,
        product: Product,
        since: datetime,
    ) -> list[RemoteProduct]:
        """Return all products available on the DWD server since a given time."""

        _LOGGER.debug(
            "Listing remote products in %s",
            product.directory_url(),
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
                product.file_extension,
            ):
                continue

            timestamp = self._parse_remote_timestamp(
                product,
                filename,
            )

            if timestamp < since:
                continue

            remote_products.append(
                self._build_remote_product(
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

        _LOGGER.debug(
            "Found %d remote %s products",
            len(
                remote_products,
            ),
            product.key,
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

