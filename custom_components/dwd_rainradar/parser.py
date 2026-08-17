"""Parser for DWD HDF5 files."""

from __future__ import annotations

from datetime import (
    UTC,
    datetime,
)

from io import BytesIO

import h5py

from .models import ParsedValue


class Parser:
    """Read values from DWD HDF5 files."""

    def read(
        self,
        data: bytes,
        grid_cell: tuple[int, int],
    ) -> tuple[ParsedValue, ...]:
        """Read one precipitation value from a DWD HDF5 file."""

        return (
            self.read_cells(
                data,
                (grid_cell,),
            )[grid_cell],
        )

    def read_cells(
        self,
        data: bytes,
        grid_cells: tuple[
            tuple[int, int],
            ...
        ],
    ) -> dict[
        tuple[int, int],
        ParsedValue,
    ]:
        """Read precipitation values for multiple grid cells."""

        with h5py.File(
            BytesIO(data),
            "r",
        ) as hdf5:

            try:
                dataset = hdf5["dataset1"]["data1"]
            except KeyError as err:
                raise ValueError(
                    "Unsupported DWD HDF5 structure."
                ) from err

            return {
                grid_cell: self._read_dataset(
                    hdf5,
                    dataset,
                    grid_cell,
                )
                for grid_cell in grid_cells
            }

    def _read_dataset(
        self,
        hdf5: h5py.File,
        dataset: h5py.Group,
        grid_cell: tuple[int, int],
    ) -> ParsedValue:
        """Read one value from a DWD dataset."""

        selection = dataset["data"][grid_cell]

        raw_value = float(
            selection
        )

        dataset_what = dataset["what"].attrs
        interval_what = hdf5["dataset1"]["what"].attrs
        product_what = hdf5["what"].attrs

        gain = float(
            dataset_what["gain"]
        )

        offset = float(
            dataset_what["offset"]
        )

        nodata = float(
            dataset_what["nodata"]
        )

        undetect = float(
            dataset_what["undetect"]
        )

        date = product_what["date"].decode()

        time = product_what["time"].decode()

        start_date = interval_what["startdate"].decode()

        start_time = interval_what["starttime"].decode()

        end_date = interval_what["enddate"].decode()

        end_time = interval_what["endtime"].decode()

        timestamp = datetime.strptime(
            f"{date}{time}",
            "%Y%m%d%H%M%S",
        ).replace(
            tzinfo=UTC,
        )

        valid_from = datetime.strptime(
            f"{start_date}{start_time}",
            "%Y%m%d%H%M%S",
        ).replace(
            tzinfo=UTC,
        )

        valid_until = datetime.strptime(
            f"{end_date}{end_time}",
            "%Y%m%d%H%M%S",
        ).replace(
            tzinfo=UTC,
        )

        if raw_value == nodata:
            value = None

        elif raw_value == undetect:
            value = 0.0

        else:
            value = max(
                (raw_value * gain) + offset,
                0.0,
            )

        return ParsedValue(
            timestamp=timestamp,
            valid_from=valid_from,
            valid_until=valid_until,
            value=value,
        )

