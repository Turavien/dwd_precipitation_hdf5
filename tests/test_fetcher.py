"""Test DWD Rain Radar fetcher."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import AsyncMock

from custom_components.dwd_rainradar.fetcher import (
    Fetcher,
    _remote_check_due,
)
from custom_components.dwd_rainradar.models import (
    FetchResult,
    ProductMetadata,
)
from custom_components.dwd_rainradar.products import (
    RS,
    RV,
    RW,
)


def test_product_publication_timing() -> None:
    """Test configured DWD product publication timing."""

    assert RW.publication_interval == timedelta(
        minutes=10,
    )
    assert RW.publication_delay == timedelta(
        minutes=24,
    )
    assert RW.freshness_window == timedelta(
        minutes=39,
    )

    assert RS.publication_interval == timedelta(
        minutes=5,
    )
    assert RS.publication_delay == timedelta(
        minutes=3,
    )
    assert RS.freshness_window == timedelta(
        minutes=13,
    )

    assert RV.publication_interval == timedelta(
        minutes=5,
    )
    assert RV.publication_delay == timedelta(
        minutes=3,
    )
    assert RV.freshness_window == timedelta(
        minutes=13,
    )


def test_remote_check_due_without_product_timestamp() -> None:
    """Test unknown product timestamps are checked with retry throttling."""

    now = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    assert _remote_check_due(
        RV,
        None,
        None,
        now,
    )

    assert not _remote_check_due(
        RV,
        None,
        now,
        now + timedelta(
            seconds=29,
        ),
    )

    assert _remote_check_due(
        RV,
        None,
        now,
        now + timedelta(
            seconds=30,
        ),
    )


def test_remote_check_due_uses_product_timeline() -> None:
    """Test remote checks follow the DWD product timeline."""

    rv_timestamp = datetime(
        2026,
        8,
        29,
        13,
        45,
        tzinfo=UTC,
    )

    assert not _remote_check_due(
        RV,
        rv_timestamp,
        None,
        datetime(
            2026,
            8,
            29,
            13,
            52,
            59,
            tzinfo=UTC,
        ),
    )

    assert _remote_check_due(
        RV,
        rv_timestamp,
        None,
        datetime(
            2026,
            8,
            29,
            13,
            53,
            tzinfo=UTC,
        ),
    )

    rw_timestamp = datetime(
        2026,
        8,
        29,
        5,
        0,
        tzinfo=UTC,
    )

    assert not _remote_check_due(
        RW,
        rw_timestamp,
        None,
        datetime(
            2026,
            8,
            29,
            5,
            33,
            59,
            tzinfo=UTC,
        ),
    )

    assert _remote_check_due(
        RW,
        rw_timestamp,
        None,
        datetime(
            2026,
            8,
            29,
            5,
            34,
            tzinfo=UTC,
        ),
    )


def test_remote_check_fast_retry_interval() -> None:
    """Test delayed products are retried every 30 seconds initially."""

    latest_timestamp = datetime(
        2026,
        8,
        29,
        13,
        45,
        tzinfo=UTC,
    )

    last_remote_check = datetime(
        2026,
        8,
        29,
        13,
        53,
        tzinfo=UTC,
    )

    assert not _remote_check_due(
        RV,
        latest_timestamp,
        last_remote_check,
        datetime(
            2026,
            8,
            29,
            13,
            53,
            29,
            tzinfo=UTC,
        ),
    )

    assert _remote_check_due(
        RV,
        latest_timestamp,
        last_remote_check,
        datetime(
            2026,
            8,
            29,
            13,
            53,
            30,
            tzinfo=UTC,
        ),
    )


def test_remote_check_slow_retry_interval() -> None:
    """Test unusually late products use a two-minute retry interval."""

    latest_timestamp = datetime(
        2026,
        8,
        29,
        13,
        45,
        tzinfo=UTC,
    )

    last_remote_check = datetime(
        2026,
        8,
        29,
        14,
        0,
        tzinfo=UTC,
    )

    assert not _remote_check_due(
        RV,
        latest_timestamp,
        last_remote_check,
        datetime(
            2026,
            8,
            29,
            14,
            1,
            59,
            tzinfo=UTC,
        ),
    )

    assert _remote_check_due(
        RV,
        latest_timestamp,
        last_remote_check,
        datetime(
            2026,
            8,
            29,
            14,
            2,
            tzinfo=UTC,
        ),
    )


def test_remote_check_due_accepts_naive_timestamp() -> None:
    """Test naive product timestamps are interpreted as UTC."""

    assert not _remote_check_due(
        RV,
        datetime(
            2026,
            8,
            29,
            10,
            0,
        ),
        None,
        datetime(
            2026,
            8,
            29,
            10,
            7,
            59,
            tzinfo=UTC,
        ),
    )


def test_remote_check_due_with_future_timestamp() -> None:
    """Test future product timestamps still use retry throttling."""

    product_timestamp = datetime(
        2026,
        8,
        29,
        10,
        5,
        tzinfo=UTC,
    )

    now = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    assert _remote_check_due(
        RV,
        product_timestamp,
        None,
        now,
    )

    assert not _remote_check_due(
        RV,
        product_timestamp,
        now,
        now + timedelta(
            seconds=29,
        ),
    )

    assert _remote_check_due(
        RV,
        product_timestamp,
        now,
        now + timedelta(
            seconds=30,
        ),
    )


async def test_async_download_skips_before_publication_window() -> None:
    """Test no HTTP request is made before a new product can be expected."""

    fetcher = object.__new__(
        Fetcher,
    )

    fetcher._last_remote_checks = {}
    fetcher._async_download = AsyncMock()

    now = datetime.now(
        UTC,
    )

    metadata = ProductMetadata(
        etag="test-etag",
        last_modified="Sat, 29 Aug 2026 10:00:00 GMT",
    )

    result = await fetcher.async_download(
        RV,
        metadata,
        now,
    )

    assert result == FetchResult(
        product=RV,
        downloaded=False,
        timestamp=None,
        metadata=metadata,
    )

    fetcher._async_download.assert_not_awaited()
    assert fetcher._last_remote_checks == {}


async def test_async_download_checks_in_publication_window() -> None:
    """Test an expected newer product is checked remotely."""

    fetcher = object.__new__(
        Fetcher,
    )

    fetcher._last_remote_checks = {}

    expected_result = FetchResult(
        product=RV,
        downloaded=False,
        timestamp=None,
        metadata=ProductMetadata(
            etag="test-etag",
        ),
    )

    fetcher._async_download = AsyncMock(
        return_value=expected_result,
    )

    metadata = ProductMetadata(
        etag="test-etag",
    )

    result = await fetcher.async_download(
        RV,
        metadata,
        datetime.now(
            UTC,
        ) - timedelta(
            minutes=9,
        ),
    )

    assert result is expected_result
    assert RV.key in fetcher._last_remote_checks

    fetcher._async_download.assert_awaited_once_with(
        product=RV,
        url=RV.download_url(),
        metadata=metadata,
    )


async def test_async_download_force_bypasses_retry_throttle() -> None:
    """Test a forced fallback download bypasses the retry throttle."""

    fetcher = object.__new__(
        Fetcher,
    )

    now = datetime.now(
        UTC,
    )

    fetcher._last_remote_checks = {
        RV.key: now,
    }

    expected_result = FetchResult(
        product=RV,
        downloaded=True,
        timestamp=None,
        metadata=ProductMetadata(),
    )

    fetcher._async_download = AsyncMock(
        return_value=expected_result,
    )

    result = await fetcher.async_download(
        RV,
        force=True,
    )

    assert result is expected_result

    fetcher._async_download.assert_awaited_once_with(
        product=RV,
        url=RV.download_url(),
        metadata=None,
    )


def test_remote_check_due_with_future_last_check() -> None:
    """Test clock rollback does not suppress the next remote check."""

    now = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    assert _remote_check_due(
        RV,
        None,
        now + timedelta(
            minutes=1,
        ),
        now,
    )
