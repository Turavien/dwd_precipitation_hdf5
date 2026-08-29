"""Test DWD Rain Radar time series."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import AsyncMock, MagicMock

from custom_components.dwd_rainradar.models import (
    FetchResult,
    ProductMetadata,
    TimeInterval,
)
from custom_components.dwd_rainradar.products import RW
from custom_components.dwd_rainradar.series import Series


BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)


def _series() -> tuple[
    Series,
    MagicMock,
    MagicMock,
]:
    """Create one series with mocked dependencies."""

    storage = MagicMock()
    decoder = MagicMock()

    storage.async_list_intervals = AsyncMock()
    storage.async_read_product = AsyncMock()
    storage.async_read_latest_product = AsyncMock()
    storage.async_store_product = AsyncMock()
    storage.async_delete_old_files = AsyncMock()

    decoder.async_decode_cells = AsyncMock()

    return (
        Series(
            storage,
            decoder,
            RW,
        ),
        storage,
        decoder,
    )


async def test_intervals_are_sorted_and_cached() -> None:
    """Test intervals are sorted by validity end and cached."""

    series, storage, _ = _series()

    first = (
        BASE_TIME,
        BASE_TIME
        + timedelta(
            hours=1,
        ),
    )

    second = (
        BASE_TIME
        + timedelta(
            hours=1,
        ),
        BASE_TIME
        + timedelta(
            hours=2,
        ),
    )

    storage.async_list_intervals.return_value = [
        second,
        first,
    ]

    result = await series.intervals()

    assert result == [
        TimeInterval(
            valid_from=first[0],
            valid_until=first[1],
        ),
        TimeInterval(
            valid_from=second[0],
            valid_until=second[1],
        ),
    ]

    assert await series.intervals() is result

    storage.async_list_intervals.assert_awaited_once_with(
        RW,
    )


async def test_read_interval_cells_delegates_to_storage_and_decoder() -> None:
    """Test one stored interval is decoded for all requested cells."""

    series, storage, decoder = _series()

    interval = TimeInterval(
        valid_from=BASE_TIME,
        valid_until=(
            BASE_TIME
            + timedelta(
                hours=1,
            )
        ),
    )

    grid_cells = (
        (416, 784),
        (417, 784),
    )

    stored = FetchResult(
        product=RW,
        downloaded=False,
        timestamp=None,
        data=b"stored",
        metadata=ProductMetadata(),
    )

    expected = {
        grid_cell: MagicMock()
        for grid_cell in grid_cells
    }

    storage.async_read_product.return_value = stored
    decoder.async_decode_cells.return_value = expected

    assert await series.read_interval_cells(
        interval,
        grid_cells,
    ) is expected

    storage.async_read_product.assert_awaited_once_with(
        RW,
        interval.valid_from,
    )

    decoder.async_decode_cells.assert_awaited_once_with(
        stored,
        grid_cells,
    )


async def test_read_latest_delegates_to_storage() -> None:
    """Test reading the newest product delegates to storage."""

    series, storage, _ = _series()

    expected = MagicMock()

    storage.async_read_latest_product.return_value = expected

    assert await series.read_latest() is expected

    storage.async_read_latest_product.assert_awaited_once_with(
        RW,
    )


async def test_store_invalidates_interval_cache() -> None:
    """Test storing a product invalidates cached intervals."""

    series, storage, _ = _series()

    series._intervals = [
        MagicMock()
    ]

    result = MagicMock()

    await series.store(
        result,
        update_metadata=False,
    )

    storage.async_store_product.assert_awaited_once_with(
        result,
        update_metadata=False,
    )

    assert series._intervals is None


async def test_prune_empty_series_does_nothing() -> None:
    """Test pruning an empty series does not call storage deletion."""

    series, storage, _ = _series()

    storage.async_list_intervals.return_value = []

    await series.prune(
        timedelta(
            hours=49,
        )
    )

    storage.async_delete_old_files.assert_not_awaited()


async def test_prune_uses_latest_interval_and_invalidates_cache() -> None:
    """Test pruning uses the newest validity end as retention anchor."""

    series, storage, _ = _series()

    first = (
        BASE_TIME,
        BASE_TIME
        + timedelta(
            hours=1,
        ),
    )

    latest = (
        BASE_TIME
        + timedelta(
            hours=10,
        ),
        BASE_TIME
        + timedelta(
            hours=11,
        ),
    )

    storage.async_list_intervals.return_value = [
        first,
        latest,
    ]

    max_age = timedelta(
        hours=5,
    )

    await series.prune(
        max_age,
    )

    storage.async_delete_old_files.assert_awaited_once_with(
        RW,
        latest[1] - max_age,
    )

    assert series._intervals is None
