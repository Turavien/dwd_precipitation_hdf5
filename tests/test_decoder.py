"""Test DWD Rain Radar decoder execution."""

from dataclasses import replace
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from unittest.mock import MagicMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar.decoder import Decoder
from custom_components.dwd_rainradar.models import (
    DecodedProduct,
    FetchResult,
    ParsedValue,
    ProductMetadata,
)
from custom_components.dwd_rainradar.products import (
    RV,
    RW,
)


GRID_CELL = (416, 784)

GRID_CELLS = (
    GRID_CELL,
    (417, 784),
)

BASE_TIME = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)


def _value(
    start_minutes: int,
    end_minutes: int,
    value: float = 1.0,
) -> ParsedValue:
    """Create one parsed value."""

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


async def test_async_decode_uses_executor(
    hass: HomeAssistant,
) -> None:
    """Test single-cell decoding is executed outside the event loop."""

    decoder = Decoder(
        hass,
    )

    result = FetchResult(
        product=RV,
        downloaded=True,
        timestamp=None,
        data=b"test",
        metadata=ProductMetadata(),
    )

    expected = MagicMock(
        spec=DecodedProduct,
    )

    decoder.decode = MagicMock(
        return_value=expected,
    )

    decoded = await decoder.async_decode(
        result,
        GRID_CELL,
    )

    assert decoded is expected

    decoder.decode.assert_called_once_with(
        result,
        GRID_CELL,
    )


async def test_async_decode_cells_uses_executor(
    hass: HomeAssistant,
) -> None:
    """Test multi-cell decoding is executed outside the event loop."""

    decoder = Decoder(
        hass,
    )

    result = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        data=b"test",
        metadata=ProductMetadata(),
    )

    expected = {
        grid_cell: MagicMock(
            spec=DecodedProduct,
        )
        for grid_cell in GRID_CELLS
    }

    decoder.decode_cells = MagicMock(
        return_value=expected,
    )

    decoded = await decoder.async_decode_cells(
        result,
        GRID_CELLS,
    )

    assert decoded is expected

    decoder.decode_cells.assert_called_once_with(
        result,
        GRID_CELLS,
    )


def test_decode_hdf5_sets_product_interval() -> None:
    """Test single-cell HDF5 decoding builds product metadata."""

    decoder = Decoder(
        MagicMock(),
    )

    parsed = _value(
        0,
        5,
    )

    decoder._parser.read = MagicMock(
        return_value=(
            parsed,
        ),
    )

    result = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        data=b"hdf5",
        metadata=ProductMetadata(
            etag="test-etag",
        ),
    )

    decoded = decoder.decode(
        result,
        GRID_CELL,
    )

    assert decoded.product is RW
    assert decoded.metadata == result.metadata

    assert decoded.values == (
        parsed,
    )

    assert result.timestamp == BASE_TIME
    assert result.valid_from == parsed.valid_from
    assert result.valid_until == parsed.valid_until


def test_decode_hdf5_rejects_empty_values() -> None:
    """Test empty HDF5 products are rejected."""

    decoder = Decoder(
        MagicMock(),
    )

    decoder._parser.read = MagicMock(
        return_value=(),
    )

    with pytest.raises(
        ValueError,
        match="rw contains no values",
    ):

        decoder.decode(
            FetchResult(
                product=RW,
                downloaded=True,
                timestamp=None,
                data=b"hdf5",
            ),
            GRID_CELL,
        )


def test_decode_tar_sorts_values_and_uses_full_interval() -> None:
    """Test TAR products are ordered by validity and span all forecasts."""

    decoder = Decoder(
        MagicMock(),
    )

    earlier = _value(
        0,
        5,
        1.0,
    )

    later = _value(
        5,
        10,
        2.0,
    )

    decoder._extractor.extract = MagicMock(
        return_value={
            "a_later.h5": b"later",
            "z_earlier.h5": b"earlier",
        },
    )

    decoder._parser.read = MagicMock(
        side_effect=lambda data, _grid_cell: (
            (
                later,
            )
            if data == b"later"
            else (
                earlier,
            )
        ),
    )

    result = FetchResult(
        product=RV,
        downloaded=True,
        timestamp=None,
        data=b"tar",
        metadata=ProductMetadata(),
    )

    decoded = decoder.decode(
        result,
        GRID_CELL,
    )

    assert decoded.values == (
        earlier,
        later,
    )

    assert result.timestamp == BASE_TIME
    assert result.valid_from == earlier.valid_from
    assert result.valid_until == later.valid_until


def test_decode_tar_rejects_empty_archive() -> None:
    """Test TAR products without values are rejected."""

    decoder = Decoder(
        MagicMock(),
    )

    decoder._extractor.extract = MagicMock(
        return_value={},
    )

    with pytest.raises(
        ValueError,
        match="rv contains no values",
    ):

        decoder.decode(
            FetchResult(
                product=RV,
                downloaded=True,
                timestamp=None,
                data=b"tar",
            ),
            GRID_CELL,
        )


def test_decode_rejects_missing_data() -> None:
    """Test decoding without downloaded bytes is rejected."""

    decoder = Decoder(
        MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="FetchResult contains no data",
    ):

        decoder.decode(
            FetchResult(
                product=RW,
                downloaded=False,
                timestamp=None,
                data=None,
            ),
            GRID_CELL,
        )


def test_decode_rejects_unsupported_file_type() -> None:
    """Test unsupported product file types are rejected."""

    decoder = Decoder(
        MagicMock(),
    )

    unsupported = replace(
        RW,
        file_type="unsupported",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):

        decoder.decode(
            FetchResult(
                product=unsupported,
                downloaded=True,
                timestamp=None,
                data=b"test",
            ),
            GRID_CELL,
        )


def test_decode_cells_hdf5_sets_interval_for_all_cells() -> None:
    """Test multi-cell HDF5 decoding builds one product per grid cell."""

    decoder = Decoder(
        MagicMock(),
    )

    first = _value(
        0,
        5,
        1.0,
    )

    second = _value(
        0,
        5,
        2.0,
    )

    decoder._parser.read_cells = MagicMock(
        return_value={
            GRID_CELLS[0]: first,
            GRID_CELLS[1]: second,
        },
    )

    result = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        data=b"hdf5",
        metadata=ProductMetadata(),
    )

    decoded = decoder.decode_cells(
        result,
        GRID_CELLS,
    )

    assert decoded[
        GRID_CELLS[0]
    ].values == (
        first,
    )

    assert decoded[
        GRID_CELLS[1]
    ].values == (
        second,
    )

    assert result.timestamp == BASE_TIME
    assert result.valid_from == first.valid_from
    assert result.valid_until == first.valid_until


def test_decode_cells_rejects_missing_data() -> None:
    """Test multi-cell decoding requires downloaded bytes."""

    decoder = Decoder(
        MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="FetchResult contains no data",
    ):

        decoder.decode_cells(
            FetchResult(
                product=RW,
                downloaded=False,
                timestamp=None,
                data=None,
            ),
            GRID_CELLS,
        )


def test_decode_cells_rejects_tar_product() -> None:
    """Test multi-cell decoding accepts only HDF5 products."""

    decoder = Decoder(
        MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="only supported for HDF5",
    ):

        decoder.decode_cells(
            FetchResult(
                product=RV,
                downloaded=True,
                timestamp=None,
                data=b"tar",
            ),
            GRID_CELLS,
        )


def test_decode_cells_rejects_empty_values() -> None:
    """Test empty multi-cell HDF5 products are rejected."""

    decoder = Decoder(
        MagicMock(),
    )

    decoder._parser.read_cells = MagicMock(
        return_value={},
    )

    with pytest.raises(
        ValueError,
        match="rw contains no values",
    ):

        decoder.decode_cells(
            FetchResult(
                product=RW,
                downloaded=True,
                timestamp=None,
                data=b"hdf5",
            ),
            GRID_CELLS,
        )
