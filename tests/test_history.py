"""Test DWD Rain Radar RW history calculations."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.dwd_rainradar.history import History
from custom_components.dwd_rainradar.models import (
    DecodedProduct,
    ParsedValue,
    ProductMetadata,
    TimeInterval,
)
from custom_components.dwd_rainradar.products import RW


BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    10,
    tzinfo=UTC,
)

GRID_CELL = (416, 784)
OTHER_GRID_CELL = (417, 784)


def _interval(
    start_hours: int,
) -> TimeInterval:
    """Create one one-hour RW interval."""

    valid_from = (
        BASE_TIME
        + timedelta(
            hours=start_hours,
        )
    )

    return TimeInterval(
        valid_from=valid_from,
        valid_until=(
            valid_from
            + timedelta(
                hours=1,
            )
        ),
    )


def _decoded(
    valid_from: datetime,
    value: float | None,
) -> DecodedProduct:
    """Create one decoded RW value."""

    return DecodedProduct(
        product=RW,
        metadata=ProductMetadata(),
        values=(
            ParsedValue(
                timestamp=(
                    valid_from
                    + timedelta(
                        hours=1,
                    )
                ),
                valid_from=valid_from,
                valid_until=(
                    valid_from
                    + timedelta(
                        hours=1,
                    )
                ),
                value=value,
            ),
        ),
    )


def _history() -> History:
    """Create history with a mocked series."""

    history = History(
        MagicMock(),
        MagicMock(),
    )

    history._series = MagicMock()
    history._series.intervals = AsyncMock()
    history._series.read_interval_cells = AsyncMock()

    return history


async def test_history_delegates_series_operations() -> None:
    """Test public history wrappers delegate to the RW series."""

    history = _history()

    latest = MagicMock()
    result = MagicMock()

    history._series.read_latest = AsyncMock(
        return_value=latest,
    )
    history._series.store = AsyncMock()
    history._series.prune = AsyncMock()

    intervals = [
        _interval(
            -1,
        )
    ]

    history._series.intervals.return_value = intervals

    assert await history.read_latest() is latest

    await history.store(
        result,
        update_metadata=False,
    )

    assert await history.intervals() is intervals

    await history.prune()

    history._series.read_latest.assert_awaited_once_with()

    history._series.store.assert_awaited_once_with(
        result,
        update_metadata=False,
    )

    history._series.prune.assert_awaited_once_with(
        RW.retention,
    )


async def test_intervals_before_returns_exact_continuous_chain() -> None:
    """Test overlapping RW products do not disturb an exact hourly chain."""

    history = _history()

    exact_old = _interval(
        -2,
    )

    overlapping_old = TimeInterval(
        valid_from=(
            BASE_TIME
            - timedelta(
                hours=2,
            )
            + timedelta(
                minutes=10,
            )
        ),
        valid_until=(
            BASE_TIME
            - timedelta(
                hours=1,
            )
            + timedelta(
                minutes=10,
            )
        ),
    )

    exact_recent = _interval(
        -1,
    )

    overlapping_recent = TimeInterval(
        valid_from=(
            BASE_TIME
            - timedelta(
                hours=1,
            )
            - timedelta(
                minutes=10,
            )
        ),
        valid_until=(
            BASE_TIME
            - timedelta(
                minutes=10,
            )
        ),
    )

    history._series.intervals.return_value = sorted(
        [
            overlapping_old,
            exact_recent,
            exact_old,
            overlapping_recent,
        ],
        key=lambda interval: interval.valid_until,
    )

    assert await history.intervals_before(
        BASE_TIME,
        2,
    ) == [
        exact_old,
        exact_recent,
    ]


async def test_intervals_before_accepts_subminute_filename_precision() -> None:
    """Test sub-minute timestamp loss in stored filenames stays usable."""

    history = _history()

    candidate = TimeInterval(
        valid_from=(
            BASE_TIME
            - timedelta(
                hours=1,
                seconds=30,
            )
        ),
        valid_until=(
            BASE_TIME
            - timedelta(
                seconds=30,
            )
        ),
    )

    history._series.intervals.return_value = [
        candidate,
    ]

    assert await history.intervals_before(
        BASE_TIME,
        1,
    ) == [
        candidate,
    ]


async def test_intervals_before_rejects_gap_at_anchor() -> None:
    """Test rolling history does not bridge a missing immediate interval."""

    history = _history()

    history._series.intervals.return_value = [
        TimeInterval(
            valid_from=(
                BASE_TIME
                - timedelta(
                    hours=1,
                    minutes=10,
                )
            ),
            valid_until=(
                BASE_TIME
                - timedelta(
                    minutes=10,
                )
            ),
        )
    ]

    assert await history.intervals_before(
        BASE_TIME,
        2,
    ) == []


async def test_intervals_before_stops_at_internal_gap() -> None:
    """Test a partial chain ends when an exact predecessor is missing."""

    history = _history()

    exact_recent = _interval(
        -1,
    )

    older_with_gap = TimeInterval(
        valid_from=(
            BASE_TIME
            - timedelta(
                hours=2,
                minutes=10,
            )
        ),
        valid_until=(
            BASE_TIME
            - timedelta(
                hours=1,
                minutes=10,
            )
        ),
    )

    history._series.intervals.return_value = [
        older_with_gap,
        exact_recent,
    ]

    assert await history.intervals_before(
        BASE_TIME,
        3,
    ) == [
        exact_recent,
    ]


async def test_intervals_before_empty_history() -> None:
    """Test empty history returns no chain."""

    history = _history()

    history._series.intervals.return_value = []

    assert await history.intervals_before(
        BASE_TIME,
        2,
    ) == []


async def test_rolling_summaries_for_multiple_cells() -> None:
    """Test rolling sums, missing values and insufficient history."""

    history = _history()

    history._ROLLING_WINDOWS = (
        ("rw_2h", 2),
        ("rw_3h", 3),
        ("rw_4h", 4),
    )

    older = _interval(
        -2,
    )

    recent = _interval(
        -1,
    )

    history.intervals_before = AsyncMock(
        return_value=[
            older,
            recent,
        ]
    )

    history._series.read_interval_cells.side_effect = (
        {
            GRID_CELL: _decoded(
                recent.valid_from,
                2.0,
            ),
            OTHER_GRID_CELL: _decoded(
                recent.valid_from,
                None,
            ),
        },
        {
            GRID_CELL: _decoded(
                older.valid_from,
                3.0,
            ),
            OTHER_GRID_CELL: _decoded(
                older.valid_from,
                30.0,
            ),
        },
    )

    latest_rw = {
        GRID_CELL: _decoded(
            BASE_TIME,
            1.0,
        ),
        OTHER_GRID_CELL: _decoded(
            BASE_TIME,
            10.0,
        ),
    }

    summaries = await history.rolling_summaries_cells(
        latest_rw,
    )

    assert summaries[
        GRID_CELL
    ] == {
        "rw_2h": 3.0,
        "rw_3h": 6.0,
        "rw_4h": None,
    }

    assert summaries[
        OTHER_GRID_CELL
    ] == {
        "rw_2h": None,
        "rw_3h": None,
        "rw_4h": None,
    }


async def test_rolling_summaries_reject_mismatched_latest_intervals() -> None:
    """Test all current grid cells must use the same RW interval."""

    history = _history()

    with pytest.raises(
        ValueError,
        match="do not share the same validity interval",
    ):

        await history.rolling_summaries_cells(
            {
                GRID_CELL: _decoded(
                    BASE_TIME,
                    1.0,
                ),
                OTHER_GRID_CELL: _decoded(
                    BASE_TIME
                    + timedelta(
                        minutes=10,
                    ),
                    2.0,
                ),
            }
        )


async def test_rolling_summaries_empty_or_missing_latest_values() -> None:
    """Test incomplete latest data cannot produce rolling summaries."""

    history = _history()

    assert await history.rolling_summaries_cells(
        {},
    ) == {}

    empty = DecodedProduct(
        product=RW,
        metadata=ProductMetadata(),
        values=(),
    )

    assert await history.rolling_summaries_cells(
        {
            GRID_CELL: empty,
        }
    ) == {}

    assert await history.rolling_summaries_cells(
        {
            GRID_CELL: _decoded(
                BASE_TIME,
                1.0,
            ),
            OTHER_GRID_CELL: empty,
        }
    ) == {}
