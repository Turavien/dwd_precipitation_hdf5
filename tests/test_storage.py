"""Test DWD Rain Radar persistent storage."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar.models import (
    FetchResult,
    ProductMetadata,
)
from custom_components.dwd_rainradar.products import RW
from custom_components.dwd_rainradar.storage import Storage


BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)


def _result(
    valid_from: datetime,
    valid_until: datetime,
    data: bytes = b"test-data",
) -> FetchResult:
    """Create one stored RW result."""

    return FetchResult(
        product=RW,
        downloaded=True,
        timestamp=valid_until,
        valid_from=valid_from,
        valid_until=valid_until,
        data=data,
        metadata=ProductMetadata(
            etag='"test-etag"',
            last_modified="Sat, 29 Aug 2026 11:00:00 GMT",
        ),
    )


def _write_text(
    path: Path,
    content: str,
) -> None:
    """Write text for one storage test."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )


@pytest.fixture
def isolated_storage(
    hass: HomeAssistant,
    tmp_path: Path,
) -> Storage:
    """Return storage using a per-test temporary directory."""

    storage = Storage(
        hass,
    )

    storage._base_directory = (
        tmp_path
        / "dwd_rainradar"
    )

    return storage


async def test_store_read_list_and_metadata(
    isolated_storage: Storage,
) -> None:
    """Test a product can be stored and read back completely."""

    storage = isolated_storage

    valid_from = BASE_TIME
    valid_until = (
        BASE_TIME
        + timedelta(
            hours=1,
        )
    )

    result = _result(
        valid_from,
        valid_until,
    )

    await storage.async_store_product(
        result,
    )

    assert await storage.async_list_intervals(
        RW,
    ) == [
        (
            valid_from,
            valid_until,
        )
    ]

    stored = await storage.async_read_product(
        RW,
        valid_from,
    )

    assert stored.product is RW
    assert stored.downloaded is False
    assert stored.timestamp is None
    assert stored.valid_from == valid_from
    assert stored.valid_until == valid_until
    assert stored.data == b"test-data"
    assert stored.metadata == result.metadata

    latest = await storage.async_read_latest_product(
        RW,
    )

    assert latest.valid_from == valid_from
    assert latest.valid_until == valid_until

    assert await storage.async_read_metadata(
        RW.key,
    ) == result.metadata


async def test_store_rejects_missing_interval_or_data(
    isolated_storage: Storage,
) -> None:
    """Test invalid storage results are rejected."""

    storage = isolated_storage

    missing_interval = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        data=b"test",
    )

    with pytest.raises(
        ValueError,
        match="Validity interval missing",
    ):
        await storage.async_store_file(
            missing_interval,
        )

    with pytest.raises(
        ValueError,
        match="Validity interval missing",
    ):
        await storage.async_store_product(
            missing_interval,
        )

    missing_data = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        valid_from=BASE_TIME,
        valid_until=(
            BASE_TIME
            + timedelta(
                hours=1,
            )
        ),
        data=None,
    )

    with pytest.raises(
        ValueError,
        match="FetchResult contains no data",
    ):
        await storage.async_store_file(
            missing_data,
        )


async def test_read_missing_product_raises(
    isolated_storage: Storage,
) -> None:
    """Test missing stored products raise FileNotFoundError."""

    storage = isolated_storage

    with pytest.raises(
        FileNotFoundError,
        match="No stored file",
    ):
        await storage.async_read_product(
            RW,
            BASE_TIME,
        )

    with pytest.raises(
        FileNotFoundError,
        match="No stored file",
    ):
        await storage.async_read_latest_product(
            RW,
        )


async def test_invalid_metadata_is_ignored(
    hass: HomeAssistant,
    isolated_storage: Storage,
) -> None:
    """Test malformed metadata never reaches HTTP request headers."""

    storage = isolated_storage

    metadata_path = (
        storage.get_product_directory(
            RW.key,
        )
        / "metadata.json"
    )

    assert await storage.async_read_metadata(
        RW.key,
    ) == ProductMetadata()

    for content in (
        "{invalid",
        '["not", "a", "mapping"]',
        '{"etag": 123, "last_modified": null}',
        '{"etag": null, "last_modified": 123}',
    ):

        await hass.async_add_executor_job(
            _write_text,
            metadata_path,
            content,
        )

        assert await storage.async_read_metadata(
            RW.key,
        ) == ProductMetadata()


async def test_invalid_storage_filename_is_ignored(
    hass: HomeAssistant,
    isolated_storage: Storage,
) -> None:
    """Test malformed product filenames do not break the interval index."""

    storage = isolated_storage

    invalid_path = (
        storage.get_product_directory(
            RW.key,
        )
        / "rw_invalid.hdf5"
    )

    await hass.async_add_executor_job(
        _write_text,
        invalid_path,
        "invalid",
    )

    assert await storage.async_list_intervals(
        RW,
    ) == []


async def test_delete_old_files_preserves_cutoff_and_newer(
    isolated_storage: Storage,
) -> None:
    """Test pruning removes only intervals strictly older than cutoff."""

    storage = isolated_storage

    first = _result(
        BASE_TIME,
        BASE_TIME
        + timedelta(
            hours=1,
        ),
        b"first",
    )

    second = _result(
        BASE_TIME
        + timedelta(
            hours=1,
        ),
        BASE_TIME
        + timedelta(
            hours=2,
        ),
        b"second",
    )

    third = _result(
        BASE_TIME
        + timedelta(
            hours=2,
        ),
        BASE_TIME
        + timedelta(
            hours=3,
        ),
        b"third",
    )

    for result in (
        first,
        second,
        third,
    ):
        await storage.async_store_product(
            result,
        )

    cutoff = (
        BASE_TIME
        + timedelta(
            hours=2,
        )
    )

    await storage.async_delete_old_files(
        RW,
        cutoff,
    )

    assert await storage.async_list_intervals(
        RW,
    ) == [
        (
            second.valid_from,
            second.valid_until,
        ),
        (
            third.valid_from,
            third.valid_until,
        ),
    ]


def test_partial_prune_invalidates_storage_caches() -> None:
    """Test a partial deletion never leaves stale file indexes cached."""

    hass = MagicMock()

    hass.config.config_dir = "/tmp"

    storage = Storage(
        hass,
    )

    first_path = MagicMock()
    first_path.name = "first.hdf5"

    second_path = MagicMock()
    second_path.name = "second.hdf5"

    second_path.unlink.side_effect = OSError(
        "test delete failure"
    )

    storage._file_cache[
        RW.key
    ] = [
        first_path,
        second_path,
    ]

    storage._interval_cache[
        RW.key
    ] = {
        BASE_TIME: (
            first_path,
            BASE_TIME
            + timedelta(
                hours=1,
            ),
        )
    }

    storage._iter_product_files = MagicMock(
        return_value=iter(
            (
                (
                    first_path,
                    BASE_TIME,
                    BASE_TIME
                    + timedelta(
                        hours=1,
                    ),
                ),
                (
                    second_path,
                    BASE_TIME
                    + timedelta(
                        hours=1,
                    ),
                    BASE_TIME
                    + timedelta(
                        hours=2,
                    ),
                ),
            )
        )
    )

    with pytest.raises(
        OSError,
        match="test delete failure",
    ):
        storage._delete_old_files(
            RW,
            BASE_TIME
            + timedelta(
                hours=3,
            ),
        )

    assert RW.key not in storage._file_cache
    assert RW.key not in storage._interval_cache


def test_file_cache_and_invalid_filename_error(
    isolated_storage: Storage,
) -> None:
    """Test file caching, unrelated files and strict filename parsing."""

    storage = isolated_storage

    directory = storage.get_product_directory(
        RW.key,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    valid_path = (
        directory
        / "rw202608291000_202608291100.hdf5"
    )

    valid_path.write_bytes(
        b"valid",
    )

    unrelated_path = (
        directory
        / "notes.txt"
    )

    unrelated_path.write_text(
        "ignore",
        encoding="utf-8",
    )

    invalid_path = (
        directory
        / "rw_invalid.hdf5"
    )

    invalid_path.write_text(
        "invalid",
        encoding="utf-8",
    )

    first = storage._list_files(
        RW.key,
    )

    second = storage._list_files(
        RW.key,
    )

    assert second is first

    with pytest.raises(
        ValueError,
    ):
        list(
            storage._iter_product_files(
                RW,
                skip_invalid=False,
            )
        )


def test_store_file_cleans_temporary_file_on_replace_failure(
    isolated_storage: Storage,
) -> None:
    """Test failed atomic product replacement removes temporary data."""

    storage = isolated_storage

    result = _result(
        BASE_TIME,
        BASE_TIME
        + timedelta(
            hours=1,
        ),
    )

    directory = storage.get_product_directory(
        RW.key,
    )

    filename = storage._build_filename(
        RW,
        result.valid_from,
        result.valid_until,
    )

    file_path = directory / filename

    temporary_path = file_path.with_suffix(
        f"{file_path.suffix}.tmp"
    )

    with patch.object(
        Path,
        "replace",
        side_effect=OSError(
            "replace failed"
        ),
    ):
        with pytest.raises(
            OSError,
            match="replace failed",
        ):
            storage._store_file(
                result,
            )

    assert not temporary_path.exists()
    assert not file_path.exists()


def test_write_metadata_cleans_temporary_file_on_replace_failure(
    isolated_storage: Storage,
) -> None:
    """Test failed atomic metadata replacement removes temporary data."""

    storage = isolated_storage

    directory = storage.get_product_directory(
        RW.key,
    )

    temporary_path = (
        directory
        / "metadata.tmp"
    )

    with patch.object(
        Path,
        "replace",
        side_effect=OSError(
            "metadata replace failed"
        ),
    ):
        with pytest.raises(
            OSError,
            match="metadata replace failed",
        ):
            storage._write_metadata(
                RW.key,
                ProductMetadata(
                    etag='"etag"',
                ),
            )

    assert not temporary_path.exists()
