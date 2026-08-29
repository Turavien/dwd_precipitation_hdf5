"""Test DWD Rain Radar HDF5 parser."""

from datetime import (
    UTC,
    datetime,
)
from io import BytesIO

import h5py
import numpy as np
import pytest

from custom_components.dwd_rainradar.parser import Parser


TIMESTAMP = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)

VALID_FROM = datetime(
    2026,
    8,
    29,
    10,
    0,
    tzinfo=UTC,
)

VALID_UNTIL = datetime(
    2026,
    8,
    29,
    10,
    5,
    tzinfo=UTC,
)


def _build_hdf5(
    values: list[list[int]],
    *,
    gain: float = 0.1,
    offset: float = -0.2,
    nodata: int = 65535,
    undetect: int = 0,
    text_attributes_as_bytes: bool = True,
    date_attribute: object | None = None,
) -> bytes:
    """Build a minimal DWD-like HDF5 file."""

    def text_attribute(
        value: str,
    ) -> object:
        """Build one HDF5 text attribute."""

        if text_attributes_as_bytes:
            return np.bytes_(
                value
            )

        return value

    buffer = BytesIO()

    with h5py.File(
        buffer,
        "w",
    ) as hdf5:

        product_what = hdf5.create_group(
            "what",
        )

        product_what.attrs[
            "date"
        ] = (
            date_attribute
            if date_attribute is not None
            else text_attribute(
                "20260829"
            )
        )

        product_what.attrs[
            "time"
        ] = text_attribute(
            "100000"
        )

        dataset = hdf5.create_group(
            "dataset1",
        )

        interval_what = dataset.create_group(
            "what",
        )

        interval_what.attrs[
            "startdate"
        ] = text_attribute(
            "20260829"
        )

        interval_what.attrs[
            "starttime"
        ] = text_attribute(
            "100000"
        )

        interval_what.attrs[
            "enddate"
        ] = text_attribute(
            "20260829"
        )

        interval_what.attrs[
            "endtime"
        ] = text_attribute(
            "100500"
        )

        data_group = dataset.create_group(
            "data1",
        )

        data_group.create_dataset(
            "data",
            data=values,
        )

        data_what = data_group.create_group(
            "what",
        )

        data_what.attrs[
            "gain"
        ] = gain

        data_what.attrs[
            "offset"
        ] = offset

        data_what.attrs[
            "nodata"
        ] = nodata

        data_what.attrs[
            "undetect"
        ] = undetect

    return buffer.getvalue()


def _build_unsupported_hdf5() -> bytes:
    """Build an HDF5 file without the expected DWD structure."""

    buffer = BytesIO()

    with h5py.File(
        buffer,
        "w",
    ) as hdf5:

        hdf5.create_group(
            "what",
        )

    return buffer.getvalue()


def test_read_cells_decodes_values_and_metadata() -> None:
    """Test normal, undetect, nodata and clamped HDF5 values."""

    parser = Parser()

    values = parser.read_cells(
        _build_hdf5(
            [
                [5, 0],
                [65535, 1],
            ],
        ),
        (
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ),
    )

    assert values[
        (0, 0)
    ].value == pytest.approx(
        0.3,
    )

    assert values[
        (0, 1)
    ].value == 0.0

    assert values[
        (1, 0)
    ].value is None

    assert values[
        (1, 1)
    ].value == 0.0

    for value in values.values():

        assert value.timestamp == TIMESTAMP
        assert value.valid_from == VALID_FROM
        assert value.valid_until == VALID_UNTIL


def test_read_returns_single_value_tuple() -> None:
    """Test the single-cell parser wrapper."""

    parser = Parser()

    values = parser.read(
        _build_hdf5(
            [
                [7],
            ],
            gain=0.5,
            offset=0.0,
        ),
        (0, 0),
    )

    assert len(
        values
    ) == 1

    assert values[
        0
    ].value == pytest.approx(
        3.5,
    )


def test_read_cells_accepts_string_attributes() -> None:
    """Test HDF5 text attributes already decoded by h5py."""

    parser = Parser()

    values = parser.read_cells(
        _build_hdf5(
            [
                [5],
            ],
            text_attributes_as_bytes=False,
        ),
        (
            (0, 0),
        ),
    )

    assert values[
        (0, 0)
    ].timestamp == TIMESTAMP

    assert values[
        (0, 0)
    ].valid_from == VALID_FROM

    assert values[
        (0, 0)
    ].valid_until == VALID_UNTIL


def test_read_cells_rejects_unsupported_text_attribute() -> None:
    """Test malformed HDF5 text attributes are rejected."""

    parser = Parser()

    with pytest.raises(
        ValueError,
        match="Unsupported DWD HDF5 text attribute",
    ):

        parser.read_cells(
            _build_hdf5(
                [
                    [5],
                ],
                date_attribute=20260829,
            ),
            (
                (0, 0),
            ),
        )


def test_read_cells_rejects_unsupported_structure() -> None:
    """Test malformed DWD HDF5 structures are rejected clearly."""

    parser = Parser()

    with pytest.raises(
        ValueError,
        match="Unsupported DWD HDF5 structure",
    ):

        parser.read_cells(
            _build_unsupported_hdf5(),
            (
                (0, 0),
            ),
        )
