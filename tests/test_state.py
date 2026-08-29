"""Test real-time DWD Rain Radar state evaluation."""

from datetime import (
    UTC,
    datetime,
    timedelta,
)

import pytest

from custom_components.dwd_rainradar.models import (
    DecodedProduct,
    ParsedValue,
    ProductMetadata,
)
from custom_components.dwd_rainradar.products import (
    RS,
    RV,
    RW,
)
from custom_components.dwd_rainradar.state import State


BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)


def _rv_value(
    start_minutes: int,
    end_minutes: int,
    value: float | None,
) -> ParsedValue:
    """Create one synthetic RV interval."""

    return ParsedValue(
        timestamp=BASE_TIME,
        valid_from=(
            BASE_TIME
            + timedelta(
                minutes=start_minutes,
            )
        ),
        valid_until=(
            BASE_TIME
            + timedelta(
                minutes=end_minutes,
            )
        ),
        value=value,
    )


def _state(
    reference_time: datetime,
    values: tuple[
        ParsedValue,
        ...
    ],
) -> State:
    """Create one state with synthetic RV data."""

    return State(
        {
            RV.key: DecodedProduct(
                product=RV,
                metadata=ProductMetadata(),
                values=values,
            ),
        },
        {},
        reference_time,
    )


def test_rv_offsets_follow_real_time() -> None:
    """Test now and forecast offsets use real wall-clock time."""

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=3,
            seconds=30,
        ),
        (
            _rv_value(-5, 0, 0.1),
            _rv_value(0, 5, 0.2),
            _rv_value(5, 10, 0.3),
            _rv_value(10, 15, 0.4),
            _rv_value(15, 20, 0.5),
            _rv_value(20, 25, 0.6),
        ),
    )

    assert state.intensity_now == pytest.approx(
        2.4,
    )

    assert state.intensity_in_5min == pytest.approx(
        3.6,
    )

    assert state.intensity_in_10min == pytest.approx(
        4.8,
    )

    assert state.intensity_in_15min == pytest.approx(
        6.0,
    )

    assert state.precipitation_active is True

    assert state.maximum_precipitation_intensity == pytest.approx(
        7.2,
    )


def test_rv_state_advances_without_new_dwd_product() -> None:
    """Test an older RV run still advances with real time."""

    values = (
        _rv_value(-5, 0, 0.1),
        _rv_value(0, 5, 0.2),
        _rv_value(5, 10, 0.3),
        _rv_value(10, 15, 0.4),
        _rv_value(15, 20, 0.5),
        _rv_value(20, 25, 0.6),
    )

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=3,
            seconds=30,
        ),
        values,
    )

    later_state = state.with_reference_time(
        BASE_TIME
        + timedelta(
            minutes=8,
            seconds=30,
        )
    )

    assert later_state.intensity_now == pytest.approx(
        3.6,
    )

    assert later_state.intensity_in_5min == pytest.approx(
        4.8,
    )

    assert later_state.intensity_in_10min == pytest.approx(
        6.0,
    )

    assert later_state.intensity_in_15min == pytest.approx(
        7.2,
    )


def test_rv_interval_boundary_uses_new_interval() -> None:
    """Test exact interval boundaries use the following RV interval."""

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=5,
        ),
        (
            _rv_value(-5, 0, 0.1),
            _rv_value(0, 5, 0.2),
            _rv_value(5, 10, 0.3),
        ),
    )

    assert state.intensity_now == pytest.approx(
        3.6,
    )


def test_precipitation_start_uses_real_minutes() -> None:
    """Test precipitation start is measured from real current time."""

    values = (
        _rv_value(-5, 0, 0.0),
        _rv_value(0, 5, 0.0),
        _rv_value(5, 10, 0.4),
        _rv_value(10, 15, 0.0),
    )

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=3,
            seconds=30,
        ),
        values,
    )

    assert state.precipitation_start == 2

    active_state = state.with_reference_time(
        BASE_TIME
        + timedelta(
            minutes=5,
        )
    )

    assert active_state.precipitation_start == 0


def test_rv_returns_none_outside_available_forecast() -> None:
    """Test targets beyond the available RV horizon return no value."""

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=30,
        ),
        (
            _rv_value(-5, 0, 0.1),
            _rv_value(0, 5, 0.2),
            _rv_value(5, 10, 0.3),
        ),
    )

    assert state.intensity_now is None
    assert state.intensity_in_5min is None
    assert state.precipitation_active is None
    assert state.precipitation_start is None
    assert state.maximum_precipitation_intensity is None


def test_reference_time_accepts_naive_datetime() -> None:
    """Test naive reference times are interpreted as UTC."""

    state = _state(
        BASE_TIME,
        (),
    )

    updated = state.with_reference_time(
        datetime(
            2026,
            8,
            29,
            10,
            5,
        )
    )

    assert updated._reference_time == datetime(
        2026,
        8,
        29,
        10,
        5,
        tzinfo=UTC,
    )


def test_history_and_rs_properties() -> None:
    """Test RW history and RS forecast properties."""

    rw_value = ParsedValue(
        timestamp=BASE_TIME,
        valid_from=(
            BASE_TIME
            - timedelta(
                hours=1,
            )
        ),
        valid_until=BASE_TIME,
        value=1.25,
    )

    rs_first = ParsedValue(
        timestamp=BASE_TIME,
        valid_from=BASE_TIME,
        valid_until=(
            BASE_TIME
            + timedelta(
                hours=1,
            )
        ),
        value=2.0,
    )

    rs_second = ParsedValue(
        timestamp=BASE_TIME,
        valid_from=(
            BASE_TIME
            + timedelta(
                hours=1,
            )
        ),
        valid_until=(
            BASE_TIME
            + timedelta(
                hours=2,
            )
        ),
        value=3.0,
    )

    rolling = {
        "rw_2h": 2.0,
        "rw_3h": 3.0,
        "rw_6h": 6.0,
        "rw_9h": 9.0,
        "rw_12h": 12.0,
        "rw_24h": 24.0,
        "rw_36h": 36.0,
        "rw_48h": 48.0,
    }

    state = State(
        {
            RW.key: DecodedProduct(
                product=RW,
                metadata=ProductMetadata(),
                values=(
                    rw_value,
                ),
            ),
            RS.key: DecodedProduct(
                product=RS,
                metadata=ProductMetadata(),
                values=(
                    rs_first,
                    rs_second,
                ),
            ),
        },
        rolling,
        BASE_TIME,
    )

    assert state.precipitation_last_1h == 1.25
    assert state.precipitation_last_2h == 2.0
    assert state.precipitation_last_3h == 3.0
    assert state.precipitation_last_6h == 6.0
    assert state.precipitation_last_9h == 9.0
    assert state.precipitation_last_12h == 12.0
    assert state.precipitation_last_24h == 24.0
    assert state.precipitation_last_36h == 36.0
    assert state.precipitation_last_48h == 48.0

    assert state.precipitation_next_1h == 2.0
    assert state.precipitation_next_2h == 5.0

    assert state.rw == (
        rw_value,
    )


def test_missing_history_and_incomplete_rs_return_none() -> None:
    """Test missing RW and incomplete RS return no value."""

    rs_first = ParsedValue(
        timestamp=BASE_TIME,
        valid_from=BASE_TIME,
        valid_until=(
            BASE_TIME
            + timedelta(
                hours=1,
            )
        ),
        value=2.0,
    )

    state = State(
        {
            RS.key: DecodedProduct(
                product=RS,
                metadata=ProductMetadata(),
                values=(
                    rs_first,
                ),
            ),
        },
        {},
        BASE_TIME,
    )

    assert state.precipitation_last_1h is None
    assert state.precipitation_next_1h == 2.0
    assert state.precipitation_next_2h is None
    assert state.rw == ()


def test_unknown_rv_values_propagate_none() -> None:
    """Test unknown RV data does not produce false certainty."""

    state = _state(
        BASE_TIME
        + timedelta(
            minutes=1,
        ),
        (
            _rv_value(
                0,
                5,
                None,
            ),
            _rv_value(
                5,
                10,
                0.5,
            ),
        ),
    )

    assert state.intensity_now is None
    assert state.precipitation_active is None
    assert state.maximum_precipitation_intensity is None
    assert state.precipitation_start is None


def test_rv_without_relevant_values_has_no_maximum_or_start() -> None:
    """Test expired RV data has no current maximum or start."""

    state = _state(
        BASE_TIME
        + timedelta(
            hours=3,
        ),
        (
            _rv_value(
                0,
                5,
                0.5,
            ),
        ),
    )

    assert state.maximum_precipitation_intensity is None
    assert state.precipitation_start is None


def test_product_freshness_uses_publication_timing() -> None:
    """Test each DWD product becomes stale only after its grace window."""

    for product in (
        RW,
        RS,
        RV,
    ):

        value = ParsedValue(
            timestamp=BASE_TIME,
            valid_from=BASE_TIME,
            valid_until=(
                BASE_TIME
                + product.interval
            ),
            value=0.0,
        )

        state = State(
            {
                product.key: DecodedProduct(
                    product=product,
                    metadata=ProductMetadata(),
                    values=(
                        value,
                    ),
                ),
            },
            {},
            BASE_TIME,
        )

        deadline = (
            BASE_TIME
            + product.freshness_window
        )

        assert state.with_reference_time(
            deadline,
        ).is_product_fresh(
            product,
        )

        assert not state.with_reference_time(
            deadline
            + timedelta(
                seconds=1,
            ),
        ).is_product_fresh(
            product,
        )

    assert not State(
        {},
        {},
        BASE_TIME,
    ).is_product_fresh(
        RV,
    )
