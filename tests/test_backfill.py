"""Test DWD Rain Radar historical backfill."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import AsyncMock, MagicMock

from custom_components.dwd_rainradar.backfill import Backfill
from custom_components.dwd_rainradar.models import (
    FetchResult,
    RemoteProduct,
    TimeInterval,
)
from custom_components.dwd_rainradar.products import RW


BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)


def _remote(
    hours: int,
) -> RemoteProduct:
    """Create one remote RW product."""

    timestamp = (
        BASE_TIME
        + timedelta(
            hours=hours,
        )
    )

    return RemoteProduct(
        product=RW,
        timestamp=timestamp,
        filename=(
            "raa01-rw_10000-"
            f"{timestamp:%y%m%d%H%M}"
            "-dwd---bin.hdf5"
        ),
    )


def _result(
    remote_product: RemoteProduct,
) -> FetchResult:
    """Create one downloaded historical RW result."""

    return FetchResult(
        product=RW,
        downloaded=True,
        timestamp=remote_product.timestamp,
        valid_from=(
            remote_product.timestamp
            - RW.interval
        ),
        valid_until=remote_product.timestamp,
        data=b"rw",
    )


def _backfill() -> tuple[
    Backfill,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    """Create a backfill service with mocked dependencies."""

    fetcher = MagicMock()
    history = MagicMock()
    decoder = MagicMock()

    fetcher.async_list_remote_products = AsyncMock()
    fetcher.async_download_remote = AsyncMock()

    history.intervals = AsyncMock(
        return_value=[]
    )

    history.store = AsyncMock()
    history.prune = AsyncMock()

    decoder.async_decode = AsyncMock()

    return (
        Backfill(
            fetcher,
            history,
            decoder,
        ),
        fetcher,
        history,
        decoder,
    )


async def test_backfill_listing_failure() -> None:
    """Test a failed directory listing marks the backfill incomplete."""

    backfill, fetcher, history, _ = _backfill()

    fetcher.async_list_remote_products.side_effect = RuntimeError(
        "listing failed"
    )

    assert await backfill.async_backfill(
        BASE_TIME,
    ) == (
        False,
        False,
    )

    history.prune.assert_not_awaited()


async def test_backfill_skips_already_stored_products() -> None:
    """Test products already represented by local validity starts are skipped."""

    backfill, fetcher, history, decoder = _backfill()

    stored = _remote(
        1,
    )

    missing = _remote(
        2,
    )

    fetcher.async_list_remote_products.return_value = [
        stored,
        missing,
    ]

    history.intervals.return_value = [
        TimeInterval(
            valid_from=(
                stored.timestamp
                - RW.interval
            ),
            valid_until=stored.timestamp,
        )
    ]

    downloaded = _result(
        missing,
    )

    fetcher.async_download_remote.return_value = downloaded

    assert await backfill.async_backfill(
        BASE_TIME,
    ) == (
        True,
        True,
    )

    fetcher.async_download_remote.assert_awaited_once_with(
        missing,
    )

    decoder.async_decode.assert_awaited_once_with(
        downloaded,
        (0, 0),
    )

    history.store.assert_awaited_once_with(
        downloaded,
        update_metadata=False,
    )

    history.prune.assert_awaited_once_with()


async def test_backfill_continues_after_one_product_failure() -> None:
    """Test one corrupt historical product does not prevent later products."""

    backfill, fetcher, history, decoder = _backfill()

    first = _remote(
        1,
    )

    second = _remote(
        2,
    )

    fetcher.async_list_remote_products.return_value = [
        first,
        second,
    ]

    first_result = _result(
        first,
    )

    second_result = _result(
        second,
    )

    fetcher.async_download_remote.side_effect = [
        first_result,
        second_result,
    ]

    decoder.async_decode.side_effect = [
        ValueError(
            "invalid RW"
        ),
        MagicMock(),
    ]

    assert await backfill.async_backfill(
        BASE_TIME,
    ) == (
        False,
        True,
    )

    assert fetcher.async_download_remote.await_count == 2

    history.store.assert_awaited_once_with(
        second_result,
        update_metadata=False,
    )

    history.prune.assert_awaited_once_with()


async def test_backfill_prune_failure_marks_run_incomplete() -> None:
    """Test pruning failure is reported without losing backfill completion state."""

    backfill, fetcher, history, _ = _backfill()

    fetcher.async_list_remote_products.return_value = []

    history.prune.side_effect = RuntimeError(
        "prune failed"
    )

    assert await backfill.async_backfill(
        BASE_TIME,
    ) == (
        False,
        False,
    )


async def test_backfill_limits_work_per_run() -> None:
    """Test a single backfill run respects its work limit."""

    backfill, fetcher, history, _ = _backfill()

    remote_products = [
        _remote(
            index,
        )
        for index in range(
            1,
            backfill._MAX_BACKFILL_PRODUCTS + 2,
        )
    ]

    fetcher.async_list_remote_products.return_value = remote_products

    fetcher.async_download_remote.side_effect = [
        _result(
            remote_product,
        )
        for remote_product in remote_products
    ]

    assert await backfill.async_backfill(
        BASE_TIME,
    ) == (
        True,
        True,
    )

    assert fetcher.async_download_remote.await_count == (
        backfill._MAX_BACKFILL_PRODUCTS
    )

    assert history.store.await_count == (
        backfill._MAX_BACKFILL_PRODUCTS
    )
