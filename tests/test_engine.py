"""Test DWD Rain Radar engine caching."""

import asyncio
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar.engine import Engine
from custom_components.dwd_rainradar.models import (
    DecodedProduct,
    FetchResult,
    ParsedValue,
    ProductMetadata,
)
from custom_components.dwd_rainradar.products import (
    Product,
    RS,
    RV,
    RW,
)
from custom_components.dwd_rainradar.state import State


GRID_CELL = (416, 784)
OTHER_GRID_CELL = (417, 784)


def _remote_results(
    *,
    downloaded_product: Product | None = None,
) -> dict[str, FetchResult]:
    """Return remote results for all operational products."""

    return {
        product.key: FetchResult(
            product=product,
            downloaded=(
                product is downloaded_product
            ),
            timestamp=None,
            metadata=ProductMetadata(),
        )
        for product in (
            RS,
            RV,
            RW,
        )
    }


async def test_cached_state_refreshes_time_without_rebuilding_products() -> None:
    """Test unchanged products refresh real time without decoding again."""

    engine = object.__new__(
        Engine,
    )

    engine._update_lock = asyncio.Lock()

    cached_state = State(
        {},
        {},
        datetime(
            2020,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    engine._state_cache = {
        GRID_CELL: cached_state,
    }

    engine._async_fetch_latest_products = AsyncMock(
        return_value=_remote_results(),
    )

    engine._async_build_state = AsyncMock()

    result = await engine.async_update(
        GRID_CELL,
    )

    assert result is not cached_state

    assert result._products is cached_state._products
    assert result._rolling is cached_state._rolling

    assert (
        result._reference_time
        > cached_state._reference_time
    )

    assert engine._state_cache[
        GRID_CELL
    ] is result

    engine._async_build_state.assert_not_awaited()


async def test_cache_miss_builds_state_without_new_product() -> None:
    """Test an uncached grid cell is built from existing product data."""

    engine = object.__new__(
        Engine,
    )

    engine._update_lock = asyncio.Lock()
    engine._state_cache = {}

    remote_results = _remote_results()

    new_state = MagicMock(
        spec=State,
    )

    engine._async_fetch_latest_products = AsyncMock(
        return_value=remote_results,
    )

    engine._async_build_state = AsyncMock(
        return_value=new_state,
    )

    result = await engine.async_update(
        GRID_CELL,
    )

    assert result is new_state
    assert engine._state_cache == {
        GRID_CELL: new_state,
    }

    engine._async_build_state.assert_awaited_once_with(
        GRID_CELL,
        remote_results,
    )


async def test_new_product_invalidates_all_cached_states() -> None:
    """Test a new DWD product invalidates all per-location states."""

    engine = object.__new__(
        Engine,
    )

    engine._update_lock = asyncio.Lock()

    engine._state_cache = {
        GRID_CELL: MagicMock(
            spec=State,
        ),
        OTHER_GRID_CELL: MagicMock(
            spec=State,
        ),
    }

    remote_results = _remote_results(
        downloaded_product=RV,
    )

    new_state = MagicMock(
        spec=State,
    )

    engine._async_fetch_latest_products = AsyncMock(
        return_value=remote_results,
    )

    engine._async_build_state = AsyncMock(
        return_value=new_state,
    )

    result = await engine.async_update(
        GRID_CELL,
    )

    assert result is new_state
    assert engine._state_cache == {
        GRID_CELL: new_state,
    }


async def test_metadata_is_read_from_disk_only_once() -> None:
    """Test product metadata is cached in memory."""

    engine = object.__new__(
        Engine,
    )

    metadata = ProductMetadata(
        etag="test-etag",
    )

    engine._metadata_cache = {}
    engine._storage = MagicMock()
    engine._storage.async_read_metadata = AsyncMock(
        return_value=metadata,
    )

    assert await engine._async_get_metadata(
        RV,
    ) is metadata

    assert await engine._async_get_metadata(
        RV,
    ) is metadata

    engine._storage.async_read_metadata.assert_awaited_once_with(
        RV.key,
    )


async def test_fetch_passes_latest_product_timestamp() -> None:
    """Test fetch checks do not commit unpersisted product metadata."""

    engine = object.__new__(
        Engine,
    )

    old_metadata = ProductMetadata(
        etag="old-etag",
    )

    new_metadata = ProductMetadata(
        etag="new-etag",
    )

    latest_timestamp = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    engine._products = (
        RV,
    )
    engine._metadata_cache = {
        RV.key: old_metadata,
    }
    engine._latest_product_timestamps = {
        RV.key: latest_timestamp,
    }
    engine._storage = MagicMock()
    engine._fetcher = MagicMock()

    expected_result = FetchResult(
        product=RV,
        downloaded=True,
        timestamp=None,
        metadata=new_metadata,
    )

    engine._fetcher.async_download = AsyncMock(
        return_value=expected_result,
    )

    result = await engine._async_fetch_latest_products()

    assert result == {
        RV.key: expected_result,
    }

    assert engine._metadata_cache == {
        RV.key: old_metadata,
    }

    engine._fetcher.async_download.assert_awaited_once_with(
        RV,
        old_metadata,
        latest_timestamp,
    )


async def test_failed_store_does_not_commit_product_markers() -> None:
    """Test failed forecast storage does not advance runtime product markers."""

    engine = object.__new__(
        Engine,
    )

    old_timestamp = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    new_timestamp = datetime(
        2026,
        8,
        29,
        10,
        5,
        tzinfo=UTC,
    )

    old_metadata = ProductMetadata(
        etag="old-etag",
    )

    new_metadata = ProductMetadata(
        etag="new-etag",
    )

    engine._forecast_products = (
        RV,
    )

    engine._latest_product_timestamps = {
        RV.key: old_timestamp,
    }

    engine._metadata_cache = {
        RV.key: old_metadata,
    }

    engine._decoder = MagicMock()
    engine._decoder.async_decode = AsyncMock(
        return_value=DecodedProduct(
            product=RV,
            metadata=new_metadata,
            values=(
                ParsedValue(
                    timestamp=new_timestamp,
                    valid_from=new_timestamp,
                    valid_until=new_timestamp,
                    value=0.0,
                ),
            ),
        )
    )

    engine._storage = MagicMock()
    engine._storage.async_store_product = AsyncMock(
        side_effect=OSError(
            "Test storage error"
        ),
    )

    with pytest.raises(
        OSError,
        match="Test storage error",
    ):
        await engine._async_build_state(
            GRID_CELL,
            {
                RV.key: FetchResult(
                    product=RV,
                    downloaded=True,
                    timestamp=None,
                    data=b"test",
                    metadata=new_metadata,
                ),
            },
        )

    assert engine._latest_product_timestamps == {
        RV.key: old_timestamp,
    }

    assert engine._metadata_cache == {
        RV.key: old_metadata,
    }


async def test_failed_rw_store_does_not_commit_product_markers() -> None:
    """Test failed RW storage does not advance runtime product markers."""

    engine = object.__new__(
        Engine,
    )

    old_timestamp = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    new_timestamp = datetime(
        2026,
        8,
        29,
        10,
        10,
        tzinfo=UTC,
    )

    old_metadata = ProductMetadata(
        etag="old-etag",
    )

    new_metadata = ProductMetadata(
        etag="new-etag",
    )

    engine._forecast_products = ()
    engine._latest_product_timestamps = {
        RW.key: old_timestamp,
    }
    engine._metadata_cache = {
        RW.key: old_metadata,
    }
    engine._grid_cell_references = {
        GRID_CELL: 1,
    }

    decoded = DecodedProduct(
        product=RW,
        metadata=new_metadata,
        values=(
            ParsedValue(
                timestamp=new_timestamp,
                valid_from=new_timestamp,
                valid_until=new_timestamp,
                value=0.0,
            ),
        ),
    )

    engine._decoder = MagicMock()
    engine._decoder.async_decode_cells = AsyncMock(
        return_value={
            GRID_CELL: decoded,
        }
    )

    engine._history = MagicMock()
    engine._history.store = AsyncMock(
        side_effect=OSError(
            "Test RW storage error"
        ),
    )

    with pytest.raises(
        OSError,
        match="Test RW storage error",
    ):
        await engine._async_build_state(
            GRID_CELL,
            {
                RW.key: FetchResult(
                    product=RW,
                    downloaded=True,
                    timestamp=None,
                    data=b"test",
                    metadata=new_metadata,
                ),
            },
        )

    assert engine._latest_product_timestamps == {
        RW.key: old_timestamp,
    }

    assert engine._metadata_cache == {
        RW.key: old_metadata,
    }


async def test_backfill_change_invalidates_state_cache() -> None:
    """Test changed RW backfill data invalidates cached states."""

    engine = object.__new__(
        Engine,
    )

    engine._backfill = MagicMock()
    engine._backfill.async_backfill = AsyncMock(
        return_value=(
            True,
            True,
        ),
    )

    engine._backfill_anchor = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    engine._state_cache = {
        GRID_CELL: MagicMock(
            spec=State,
        ),
    }

    engine._rolling_cache_anchor = datetime(
        2026,
        8,
        29,
        9,
        0,
        tzinfo=UTC,
    )
    engine._rolling_cache_grid_cells = (
        GRID_CELL,
    )
    engine._rolling_cache = {
        GRID_CELL: {
            "rw_2h": 1.0,
        },
    }

    callback = MagicMock()
    engine._update_callbacks = {
        callback,
    }

    await engine._async_backfill(
        datetime(
            2026,
            8,
            27,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    assert engine._state_cache == {}
    assert engine._rolling_cache_anchor is None
    assert engine._rolling_cache_grid_cells == ()
    assert engine._rolling_cache == {}

    callback.assert_called_once_with()


def test_engine_initialization_wires_shared_services(
    hass: HomeAssistant,
) -> None:
    """Test engine initialization wires all shared services."""

    with (
        patch(
            "custom_components.dwd_rainradar.engine.Storage"
        ) as storage_class,
        patch(
            "custom_components.dwd_rainradar.engine.Decoder"
        ) as decoder_class,
        patch(
            "custom_components.dwd_rainradar.engine.History"
        ) as history_class,
        patch(
            "custom_components.dwd_rainradar.engine.Fetcher"
        ) as fetcher_class,
        patch(
            "custom_components.dwd_rainradar.engine.Backfill"
        ) as backfill_class,
    ):
        engine = Engine(
            hass,
        )

    storage_class.assert_called_once_with(
        hass,
    )

    decoder_class.assert_called_once_with(
        hass,
    )

    history_class.assert_called_once_with(
        storage_class.return_value,
        decoder_class.return_value,
    )

    fetcher_class.assert_called_once_with(
        hass,
    )

    backfill_class.assert_called_once_with(
        fetcher_class.return_value,
        history_class.return_value,
        decoder_class.return_value,
    )

    assert engine._forecast_products == (
        RS,
        RV,
    )

    assert engine._products == (
        RS,
        RV,
        RW,
    )

    assert engine._metadata_cache == {}
    assert engine._latest_product_timestamps == {}
    assert engine._state_cache == {}
    assert engine._grid_cell_references == {}
    assert engine._rolling_cache_anchor is None
    assert engine._rolling_cache_grid_cells == ()
    assert engine._rolling_cache == {}
    assert engine._update_callbacks == set()
    assert engine._backfill_anchor is None
    assert engine._backfill_tasks == set()


def test_grid_cell_and_callback_registration() -> None:
    """Test shared-engine reference counting and callbacks."""

    engine = object.__new__(
        Engine,
    )

    engine._grid_cell_references = {}

    engine._state_cache = {
        GRID_CELL: MagicMock(),
    }

    engine._rolling_cache_anchor = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    engine._rolling_cache_grid_cells = (
        GRID_CELL,
    )

    engine._rolling_cache = {
        GRID_CELL: {
            "rw_2h": 1.0,
        },
    }

    engine._update_callbacks = set()

    callback = MagicMock()

    engine.register_grid_cell(
        GRID_CELL,
    )

    engine.register_grid_cell(
        GRID_CELL,
    )

    assert engine._grid_cell_references == {
        GRID_CELL: 2,
    }

    engine.register_update_callback(
        callback,
    )

    assert callback in engine._update_callbacks

    engine.unregister_grid_cell(
        GRID_CELL,
    )

    assert engine._grid_cell_references == {
        GRID_CELL: 1,
    }

    assert GRID_CELL not in engine._state_cache
    assert engine._rolling_cache_anchor is None
    assert engine._rolling_cache_grid_cells == ()
    assert engine._rolling_cache == {}

    engine.unregister_grid_cell(
        GRID_CELL,
    )

    assert engine._grid_cell_references == {}

    engine.unregister_update_callback(
        callback,
    )

    assert callback not in engine._update_callbacks


def test_start_backfill_prevents_parallel_task() -> None:
    """Test only one backfill task is started at a time."""

    engine = object.__new__(
        Engine,
    )

    task = MagicMock()

    engine._hass = MagicMock()

    engine._hass.async_create_background_task.return_value = (
        task
    )

    engine._async_backfill = MagicMock(
        return_value="backfill-awaitable",
    )

    engine._backfill_tasks = set()

    since = datetime(
        2026,
        8,
        27,
        10,
        0,
        tzinfo=UTC,
    )

    assert engine._start_backfill(
        since,
    )

    assert engine._backfill_tasks == {
        task,
    }

    engine._hass.async_create_background_task.assert_called_once_with(
        "backfill-awaitable",
        "DWD Rain Radar RW backfill",
    )

    task.add_done_callback.assert_called_once()

    assert not engine._start_backfill(
        since,
    )


async def test_shutdown_cancels_background_tasks() -> None:
    """Test engine shutdown cancels background tasks."""

    engine = object.__new__(
        Engine,
    )

    task = asyncio.create_task(
        asyncio.sleep(
            60,
        )
    )

    engine._backfill_tasks = {
        task,
    }

    await engine.async_shutdown()

    assert task.cancelled()
    assert engine._backfill_tasks == set()


async def test_incomplete_unchanged_backfill_resets_anchor() -> None:
    """Test incomplete unchanged backfill is retried later."""

    engine = object.__new__(
        Engine,
    )

    engine._backfill = MagicMock()

    engine._backfill.async_backfill = AsyncMock(
        return_value=(
            False,
            False,
        )
    )

    engine._backfill_anchor = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    engine._state_cache = {}
    engine._rolling_cache_anchor = None
    engine._rolling_cache_grid_cells = ()
    engine._rolling_cache = {}

    callback = MagicMock()

    engine._update_callbacks = {
        callback,
    }

    await engine._async_backfill(
        datetime(
            2026,
            8,
            27,
            10,
            0,
            tzinfo=UTC,
        )
    )

    assert engine._backfill_anchor is None

    callback.assert_not_called()


async def test_build_state_recovers_missing_cached_products() -> None:
    """Test missing cached products are force-downloaded and fully committed."""

    engine = object.__new__(
        Engine,
    )

    base_time = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    rv_timestamp = base_time

    rw_valid_from = (
        base_time
        - timedelta(
            minutes=50,
        )
    )

    rw_valid_until = (
        rw_valid_from
        + timedelta(
            hours=1,
        )
    )

    rv_metadata = ProductMetadata(
        etag="rv-etag",
    )

    rw_metadata = ProductMetadata(
        etag="rw-etag",
    )

    rv_result = FetchResult(
        product=RV,
        downloaded=True,
        timestamp=None,
        valid_from=rv_timestamp,
        valid_until=(
            rv_timestamp
            + timedelta(
                minutes=5,
            )
        ),
        data=b"rv",
        metadata=rv_metadata,
    )

    rw_result = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        valid_from=rw_valid_from,
        valid_until=rw_valid_until,
        data=b"rw",
        metadata=rw_metadata,
    )

    rv_decoded = DecodedProduct(
        product=RV,
        metadata=rv_metadata,
        values=(
            ParsedValue(
                timestamp=rv_timestamp,
                valid_from=rv_timestamp,
                valid_until=(
                    rv_timestamp
                    + timedelta(
                        minutes=5,
                    )
                ),
                value=0.1,
            ),
        ),
    )

    rw_decoded = DecodedProduct(
        product=RW,
        metadata=rw_metadata,
        values=(
            ParsedValue(
                timestamp=rw_valid_until,
                valid_from=rw_valid_from,
                valid_until=rw_valid_until,
                value=1.0,
            ),
        ),
    )

    other_rw_decoded = DecodedProduct(
        product=RW,
        metadata=rw_metadata,
        values=(
            ParsedValue(
                timestamp=rw_valid_until,
                valid_from=rw_valid_from,
                valid_until=rw_valid_until,
                value=2.0,
            ),
        ),
    )

    engine._forecast_products = (
        RV,
    )

    engine._storage = MagicMock()

    engine._storage.async_read_latest_product = AsyncMock(
        side_effect=FileNotFoundError,
    )

    engine._storage.async_store_product = AsyncMock()

    engine._storage.async_delete_old_files = AsyncMock()

    engine._fetcher = MagicMock()

    engine._fetcher.async_download = AsyncMock(
        side_effect=[
            rv_result,
            rw_result,
        ]
    )

    engine._decoder = MagicMock()

    engine._decoder.async_decode = AsyncMock(
        return_value=rv_decoded,
    )

    engine._decoder.async_decode_cells = AsyncMock(
        return_value={
            GRID_CELL: rw_decoded,
            OTHER_GRID_CELL: other_rw_decoded,
        }
    )

    engine._history = MagicMock()

    engine._history.read_latest = AsyncMock(
        side_effect=FileNotFoundError,
    )

    engine._history.store = AsyncMock()

    engine._history.prune = AsyncMock()

    engine._history.rolling_summaries_cells = AsyncMock(
        return_value={
            GRID_CELL: {
                "rw_2h": 3.0,
            },
            OTHER_GRID_CELL: {
                "rw_2h": 4.0,
            },
        }
    )

    engine._grid_cell_references = {
        GRID_CELL: 1,
        OTHER_GRID_CELL: 1,
    }

    engine._latest_product_timestamps = {}

    engine._metadata_cache = {}

    engine._backfill_anchor = None

    engine._rolling_cache_anchor = None

    engine._rolling_cache_grid_cells = ()

    engine._rolling_cache = {}

    engine._start_backfill = MagicMock(
        return_value=True,
    )

    state = await engine._async_build_state(
        GRID_CELL,
        {
            RV.key: FetchResult(
                product=RV,
                downloaded=False,
                timestamp=None,
            ),
            RW.key: FetchResult(
                product=RW,
                downloaded=False,
                timestamp=None,
            ),
        },
    )

    assert state._products == {
        RV.key: rv_decoded,
        RW.key: rw_decoded,
    }

    assert state._rolling == {
        "rw_2h": 3.0,
    }

    assert engine._latest_product_timestamps == {
        RV.key: rv_timestamp,
        RW.key: rw_valid_until,
    }

    assert engine._metadata_cache == {
        RV.key: rv_metadata,
        RW.key: rw_metadata,
    }

    engine._storage.async_read_latest_product.assert_awaited_once_with(
        RV,
    )

    engine._storage.async_store_product.assert_awaited_once_with(
        rv_result,
    )

    engine._storage.async_delete_old_files.assert_awaited_once_with(
        RV,
        rv_result.valid_until,
    )

    engine._history.read_latest.assert_awaited_once_with()

    engine._history.store.assert_awaited_once_with(
        rw_result,
    )

    engine._history.prune.assert_awaited_once_with()

    assert engine._fetcher.async_download.await_count == 2

    engine._fetcher.async_download.assert_any_await(
        RV,
        force=True,
    )

    engine._fetcher.async_download.assert_any_await(
        RW,
        force=True,
    )

    engine._start_backfill.assert_called_once_with(
        rw_valid_until
        - RW.retention
        + RW.interval / 2,
    )

    assert engine._backfill_anchor == rw_valid_until

    engine._history.rolling_summaries_cells.assert_awaited_once_with(
        latest_rw={
            GRID_CELL: rw_decoded,
            OTHER_GRID_CELL: other_rw_decoded,
        }
    )

    assert engine._rolling_cache_anchor == rw_valid_from

    assert engine._rolling_cache_grid_cells == (
        GRID_CELL,
        OTHER_GRID_CELL,
    )


async def test_build_state_reuses_cached_products_and_rolling_data() -> None:
    """Test unchanged products use local files and cached rolling summaries."""

    engine = object.__new__(
        Engine,
    )

    base_time = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    rv_timestamp = base_time

    rw_valid_from = (
        base_time
        - timedelta(
            minutes=50,
        )
    )

    rw_valid_until = (
        rw_valid_from
        + timedelta(
            hours=1,
        )
    )

    rv_cached = FetchResult(
        product=RV,
        downloaded=False,
        timestamp=None,
        data=b"rv-cached",
        metadata=ProductMetadata(
            etag="rv-cached",
        ),
    )

    rw_cached = FetchResult(
        product=RW,
        downloaded=False,
        timestamp=None,
        data=b"rw-cached",
        metadata=ProductMetadata(
            etag="rw-cached",
        ),
    )

    rv_decoded = DecodedProduct(
        product=RV,
        metadata=rv_cached.metadata,
        values=(
            ParsedValue(
                timestamp=rv_timestamp,
                valid_from=rv_timestamp,
                valid_until=(
                    rv_timestamp
                    + timedelta(
                        minutes=5,
                    )
                ),
                value=0.0,
            ),
        ),
    )

    rw_decoded = DecodedProduct(
        product=RW,
        metadata=rw_cached.metadata,
        values=(
            ParsedValue(
                timestamp=rw_valid_until,
                valid_from=rw_valid_from,
                valid_until=rw_valid_until,
                value=1.0,
            ),
        ),
    )

    engine._forecast_products = (
        RV,
    )

    engine._storage = MagicMock()

    engine._storage.async_read_latest_product = AsyncMock(
        return_value=rv_cached,
    )

    engine._storage.async_store_product = AsyncMock()

    engine._storage.async_delete_old_files = AsyncMock()

    engine._fetcher = MagicMock()

    engine._fetcher.async_download = AsyncMock()

    engine._decoder = MagicMock()

    engine._decoder.async_decode = AsyncMock(
        return_value=rv_decoded,
    )

    engine._decoder.async_decode_cells = AsyncMock(
        return_value={
            GRID_CELL: rw_decoded,
        }
    )

    engine._history = MagicMock()

    engine._history.read_latest = AsyncMock(
        return_value=rw_cached,
    )

    engine._history.store = AsyncMock()

    engine._history.prune = AsyncMock()

    engine._history.rolling_summaries_cells = AsyncMock()

    engine._grid_cell_references = {
        GRID_CELL: 1,
    }

    engine._latest_product_timestamps = {}

    engine._metadata_cache = {}

    engine._backfill_anchor = rw_valid_until

    engine._rolling_cache_anchor = rw_valid_from

    engine._rolling_cache_grid_cells = (
        GRID_CELL,
    )

    engine._rolling_cache = {
        GRID_CELL: {
            "rw_2h": 5.0,
        }
    }

    engine._start_backfill = MagicMock()

    state = await engine._async_build_state(
        GRID_CELL,
        {
            RV.key: FetchResult(
                product=RV,
                downloaded=False,
                timestamp=None,
            ),
            RW.key: FetchResult(
                product=RW,
                downloaded=False,
                timestamp=None,
            ),
        },
    )

    assert state._rolling == {
        "rw_2h": 5.0,
    }

    engine._fetcher.async_download.assert_not_awaited()

    engine._storage.async_store_product.assert_not_awaited()

    engine._storage.async_delete_old_files.assert_not_awaited()

    engine._history.store.assert_not_awaited()

    engine._history.prune.assert_not_awaited()

    engine._history.rolling_summaries_cells.assert_not_awaited()

    engine._start_backfill.assert_not_called()


def test_engine_diagnostics_are_non_sensitive() -> None:
    """Test engine diagnostics expose status without grid-cell values."""

    engine = object.__new__(
        Engine,
    )

    reference_time = datetime(
        2026,
        8,
        29,
        10,
        0,
        tzinfo=UTC,
    )

    rw_value = ParsedValue(
        timestamp=reference_time,
        valid_from=(
            reference_time
            - timedelta(
                hours=1,
            )
        ),
        valid_until=reference_time,
        value=1.0,
    )

    state = State(
        {
            RW.key: DecodedProduct(
                product=RW,
                metadata=ProductMetadata(),
                values=(
                    rw_value,
                ),
            ),
        },
        {},
        reference_time,
    )

    engine._products = (
        RW,
        RS,
        RV,
    )

    engine._latest_product_timestamps = {
        RW.key: reference_time,
    }

    engine._metadata_cache = {
        RW.key: ProductMetadata(
            etag='"rw-etag"',
            last_modified="Sat, 29 Aug 2026 10:00:00 GMT",
        ),
    }

    engine._grid_cell_references = {
        GRID_CELL: 2,
        OTHER_GRID_CELL: 1,
    }

    engine._state_cache = {
        GRID_CELL: state,
    }

    engine._rolling_cache = {
        GRID_CELL: {
            "rw_2h": 2.0,
        },
    }

    engine._rolling_cache_anchor = reference_time

    engine._backfill_anchor = (
        reference_time
        - timedelta(
            hours=1,
        )
    )

    engine._backfill_tasks = {
        MagicMock(),
    }

    engine._update_callbacks = {
        MagicMock(),
        MagicMock(),
    }

    diagnostics = engine.get_diagnostics(
        state,
    )

    assert diagnostics[
        "registered_grid_cells"
    ] == 2

    assert diagnostics[
        "config_entry_references"
    ] == 3

    assert diagnostics[
        "state_cache_entries"
    ] == 1

    assert diagnostics[
        "rolling_cache_entries"
    ] == 1

    assert diagnostics[
        "rolling_cache_anchor"
    ] == reference_time.isoformat()

    assert diagnostics[
        "backfill_anchor"
    ] == (
        reference_time
        - timedelta(
            hours=1,
        )
    ).isoformat()

    assert diagnostics[
        "backfill_tasks"
    ] == 1

    assert diagnostics[
        "update_callbacks"
    ] == 2

    products = diagnostics[
        "products"
    ]

    assert products[
        RW.key
    ] == {
        "last_product_timestamp": reference_time.isoformat(),
        "fresh": True,
        "publication_interval_seconds": 600,
        "publication_delay_seconds": 1440,
        "freshness_window_seconds": 2340,
        "http_metadata": {
            "etag": '"rw-etag"',
            "last_modified": "Sat, 29 Aug 2026 10:00:00 GMT",
        },
    }

    assert products[
        RS.key
    ][
        "fresh"
    ] is False

    assert products[
        RV.key
    ][
        "last_product_timestamp"
    ] is None

    diagnostic_text = repr(
        diagnostics,
    )

    assert repr(
        GRID_CELL
    ) not in diagnostic_text

    assert repr(
        OTHER_GRID_CELL
    ) not in diagnostic_text
