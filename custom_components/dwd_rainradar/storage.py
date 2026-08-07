"""Persistent storage for original DWD product files."""

from __future__ import annotations

import json
import logging

from datetime import UTC, datetime

_LOGGER = logging.getLogger(__name__)

from pathlib import Path

from homeassistant.core import HomeAssistant

from .models import (
    FetchResult,
    ProductMetadata,
)
from .products import Product

_METADATA_FILENAME = "metadata.json"


class Storage:
    """Manage original DWD product files.

    This class is responsible only for:

    - creating product directories
    - storing original DWD files
    - listing stored files
    - deleting stored files

    It intentionally contains no product logic, no sensor logic,
    no history handling and no precipitation calculations.
    """

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize storage."""

        self._hass = hass

        self._base_directory = (
            Path(hass.config.config_dir)
            / "dwd_rainradar"
        )

        self._file_cache: dict[
            str,
            list[Path],
        ] = {}

    def get_product_directory(
        self,
        product_key: str,
    ) -> Path:
        """Return the directory for one DWD product."""

        return (
            self._base_directory
            / product_key.lower()
        )

    def _build_filename(
        self,
        product: Product,
        valid_from: datetime,
        valid_until: datetime,
    ) -> str:
        """Build the storage filename for one DWD product."""

        valid_from = valid_from.astimezone(
            UTC,
        )

        valid_until = valid_until.astimezone(
            UTC,
        )

        return (
            f"{product.key}"
            f"{valid_from:%Y%m%d%H%M}"
            "_"
            f"{valid_until:%Y%m%d%H%M}"
            f".{product.file_extension}"
        )

    def _parse_product_interval(
        self,
        product: Product,
        path: Path,
    ) -> tuple[datetime, datetime]:
        """Extract the validity interval from a stored filename."""

        filename = path.name.removesuffix(
            f".{product.file_extension}",
        )

        interval = filename.removeprefix(
            product.key,
        )

        start, end = interval.split(
            "_",
        )

        return (
            datetime.strptime(
                start,
                "%Y%m%d%H%M",
            ).replace(
                tzinfo=UTC,
            ),
            datetime.strptime(
                end,
                "%Y%m%d%H%M",
            ).replace(
                tzinfo=UTC,
            ),
        )

    def _get_file_path(
        self,
        product_key: str,
        filename: str,
    ) -> Path:
        """Return the path of one stored DWD file."""

        return (
            self.get_product_directory(
                product_key,
            )
            / filename
        )

    def _get_metadata_path(
        self,
        product_key: str,
    ) -> Path:
        """Return the metadata file for one DWD product."""

        return (
            self.get_product_directory(
                product_key,
            )
            / _METADATA_FILENAME
        )

    async def async_ensure_product_directory(
        self,
        product_key: str,
    ) -> Path:
        """Ensure that the directory for a product exists."""

        return await self._hass.async_add_executor_job(
            self._ensure_product_directory,
            product_key,
        )

    async def async_store_file(
        self,
        result: FetchResult,
    ) -> Path:
        """Store one original DWD file."""

        if (
            result.valid_from is None
            or result.valid_until is None
        ):
            raise ValueError(
                "Validity interval missing."
            )

        return await self._hass.async_add_executor_job(
            self._store_file,
            result,
        )

    async def async_list_files(
        self,
        product_key: str,
    ) -> list[Path]:
        """Return all stored files for one product."""

        return await self._hass.async_add_executor_job(
            self._list_files,
            product_key,
        )

    async def async_get_product_interval(
        self,
        product: Product,
        path: Path,
    ) -> tuple[datetime, datetime]:
        """Return the validity interval encoded in a stored filename."""

        return await self._hass.async_add_executor_job(
            self._parse_product_interval,
            product,
            path,
        )

    async def async_list_intervals(
        self,
        product: Product,
    ) -> list[tuple[datetime, datetime]]:
        """Return all validity intervals for a product."""

        return await self._hass.async_add_executor_job(
            self._list_intervals,
            product,
        )

    async def async_read_product(
        self,
        product: Product,
        valid_from: datetime,
    ) -> FetchResult:
        """Read one stored DWD file."""

        return await self._hass.async_add_executor_job(
            self._read_product,
            product,
            valid_from,
        )

    async def async_read_latest_product(
        self,
        product: Product,
    ) -> FetchResult:
        """Read the newest stored DWD file."""

        return await self._hass.async_add_executor_job(
            self._read_latest_product,
            product,
        )

    async def async_delete_product(
        self,
        product: Product,
        valid_from: datetime,
    ) -> None:
        """Delete one stored file."""

        await self._hass.async_add_executor_job(
            self._delete_product,
            product,
            valid_from,
        )

    async def async_delete_old_files(
        self,
        product: Product,
        cutoff: datetime,
    ) -> None:
        """Delete all products older than the cutoff timestamp."""

        await self._hass.async_add_executor_job(
            self._delete_old_files,
            product,
            cutoff,
        )

    async def async_read_metadata(
        self,
        product_key: str,
    ) -> ProductMetadata:
        """Read metadata for one product."""

        return await self._hass.async_add_executor_job(
            self._read_metadata,
            product_key,
        )

    async def async_write_metadata(
        self,
        product_key: str,
        metadata: ProductMetadata,
    ) -> None:
        """Write metadata for one product."""

        await self._hass.async_add_executor_job(
            self._write_metadata,
            product_key,
            metadata,
        )

    async def async_store_product(
        self,
        result: FetchResult,
    ) -> None:
        """Store one downloaded product including metadata."""

        if (
            result.valid_from is None
            or result.valid_until is None
        ):
            raise ValueError(
                "Validity interval missing."
            )

        await self.async_store_file(
            result,
        )

        await self.async_write_metadata(
            result.product.key,
            result.metadata,
        )

    def _ensure_product_directory(
        self,
        product_key: str,
    ) -> Path:
        """Ensure that the directory for a product exists."""

        directory = self.get_product_directory(
            product_key,
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def _list_files(
        self,
        product_key: str,
    ) -> list[Path]:
        """Return all stored files for one product."""

        cached = self._file_cache.get(
            product_key,
        )

        if cached is not None:
            return cached

        directory = self._ensure_product_directory(
            product_key,
        )

        files = sorted(
            (
                path
                for path in directory.iterdir()
                if (
                    path.is_file()
                    and path.name != _METADATA_FILENAME
                )
            ),
            key=lambda path: path.name,
        )

        self._file_cache[
            product_key
        ] = files

        _LOGGER.debug(
            "Storage[%s]: directory=%s files=%d first=%s last=%s",
            product_key,
            directory,
            len(files),
            files[0].name if files else "-",
            files[-1].name if files else "-",
        )

        return files

    def _invalidate_file_cache(
        self,
        product_key: str,
    ) -> None:
        """Invalidate cached file list."""

        self._file_cache.pop(
            product_key,
            None,
        )

    def _list_intervals(
        self,
        product: Product,
    ) -> list[tuple[datetime, datetime]]:
        """Return all stored validity intervals for a product."""

        intervals = [
            (
                valid_from,
                valid_until,
            )
            for (
                _,
                valid_from,
                valid_until,
            ) in self._iter_product_files(
                product,
                skip_invalid=True,
            )
        ]

        _LOGGER.debug(
            "Storage[%s]: parsed %d intervals",
            product.key,
            len(intervals),
        )

        if intervals:

            _LOGGER.debug(
                "Storage[%s]: first interval %s -> %s",
                product.key,
                intervals[0][0],
                intervals[0][1],
            )

            _LOGGER.debug(
                "Storage[%s]: last interval %s -> %s",
                product.key,
                intervals[-1][0],
                intervals[-1][1],
            )

        return intervals

    def _store_file(
        self,
        result: FetchResult,
    ) -> Path:
        """Store one original DWD file."""

        if result.data is None:
            raise ValueError(
                "FetchResult contains no data.",
            )

        directory = self._ensure_product_directory(
            result.product.key,
        )

        filename = self._build_filename(
            result.product,
            result.valid_from,
            result.valid_until,
        )

        file_path = directory / filename

        file_path.write_bytes(
            result.data,
        )

        _LOGGER.debug(
            "Storage[%s]: stored %s (%s -> %s)",
            result.product.key,
            file_path.name,
            result.valid_from,
            result.valid_until,
        )

        self._invalidate_file_cache(
            result.product.key,
        )

        return file_path

    def _iter_product_files(
        self,
        product: Product,
        *,
        skip_invalid: bool = False,
    ):
        """Yield stored files together with their validity interval."""

        for file_path in self._list_files(
            product.key,
        ):

            try:

                valid_from, valid_until = (
                    self._parse_product_interval(
                        product,
                        file_path,
                    )
                )

            except ValueError:

                if not skip_invalid:
                    raise

                _LOGGER.warning(
                    "Storage[%s]: cannot parse filename %s",
                    product.key,
                    file_path.name,
                )

                continue

            yield (
                file_path,
                valid_from,
                valid_until,
            )

    def _read_product(
        self,
        product: Product,
        valid_from: datetime,
    ) -> FetchResult:
        """Read one stored DWD file."""

        for (
            file_path,
            start,
            end,
        ) in self._iter_product_files(
            product,
        ):

            if start != valid_from:
                continue

            return self._build_cached_result(
                product,
                start,
                end,
                file_path.read_bytes(),
                self._read_metadata(
                    product.key,
                ),
            )

        raise FileNotFoundError(
            f"No stored file for {product.key} at {valid_from}."
        )

    def _read_latest_product(
        self,
        product: Product,
    ) -> FetchResult:
        """Read the newest stored DWD file."""

        files = self._list_files(
            product.key,
        )

        if not files:
            raise FileNotFoundError(
                f"No stored file for {product.key}"
            )

        file_path = files[-1]

        valid_from, valid_until = (
            self._parse_product_interval(
                product,
                file_path,
            )
        )

        return self._build_cached_result(
            product,
            valid_from,
            valid_until,
            file_path.read_bytes(),
            self._read_metadata(
                product.key,
            ),
        )

    def _delete_product(
        self,
        product: Product,
        valid_from: datetime,
    ) -> None:
        """Delete one stored file."""

        for (
            file_path,
            start,
            _,
        ) in self._iter_product_files(
            product,
        ):

            if start != valid_from:
                continue

            file_path.unlink(
                missing_ok=True,
            )

            self._invalidate_file_cache(
                product.key,
            )

            return

    def _read_metadata(
        self,
        product_key: str,
    ) -> ProductMetadata:
        """Read metadata for one product."""

        metadata_path = self._get_metadata_path(
            product_key,
        )

        if not metadata_path.exists():
            return ProductMetadata()

        data = json.loads(
            metadata_path.read_text(
                encoding="utf-8",
            ),
        )

        return ProductMetadata(
            etag=data.get(
                "etag",
            ),
            last_modified=data.get(
                "last_modified",
            ),
        )

    def _write_metadata(
        self,
        product_key: str,
        metadata: ProductMetadata,
    ) -> None:
        """Write metadata for one product."""

        directory = self._ensure_product_directory(
            product_key,
        )

        metadata_path = (
            directory
            / _METADATA_FILENAME
        )

        metadata_path.write_text(
            json.dumps(
                {
                    "etag": metadata.etag,
                    "last_modified": metadata.last_modified,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def _build_cached_result(
        self,
        product: Product,
        valid_from: datetime,
        valid_until: datetime,
        data: bytes,
        metadata: ProductMetadata,
    ) -> FetchResult:
        """Build a FetchResult from cached product data."""

        return FetchResult(
            product=product,
            downloaded=False,
            timestamp=valid_until,
            valid_from=valid_from,
            valid_until=valid_until,
            data=data,
            metadata=metadata,
        )

    def _delete_old_files(
        self,
        product: Product,
        cutoff: datetime,
    ) -> None:
        """Delete all products older than the cutoff timestamp."""

        deleted = 0

        for (
            file_path,
            valid_from,
            valid_until,
        ) in self._iter_product_files(
            product,
        ):

            if valid_until < cutoff:

                _LOGGER.debug(
                    "Storage[%s]: deleting %s (%s -> %s), cutoff=%s",
                    product.key,
                    file_path.name,
                    valid_from,
                    valid_until,
                    cutoff,
                )

                file_path.unlink(
                    missing_ok=True,
                )

                deleted += 1

                self._invalidate_file_cache(
                    product.key,
                )

        _LOGGER.debug(
            "Storage[%s]: prune finished, deleted=%d",
            product.key,
            deleted,
        )

