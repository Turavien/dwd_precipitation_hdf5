"""Decoder for DWD product files."""

from __future__ import annotations

from .extractor import Extractor
from .models import (
    DecodedProduct,
    FetchResult,
    ParsedValue,
)
from .parser import Parser
from .products import FileType


class Decoder:
    """Decode downloaded DWD product files."""

    def __init__(self) -> None:
        """Initialize decoder."""

        self._extractor = Extractor()
        self._parser = Parser()

    def decode(
        self,
        result: FetchResult,
        grid_cell: tuple[int, int],
    ) -> DecodedProduct:
        """Decode one DWD product for one grid cell."""

        if result.data is None:
            raise ValueError(
                "FetchResult contains no data.",
            )

        if result.product.file_type is FileType.HDF5:

            values = self._parser.read(
                result.data,
                grid_cell,
            )

            if not values:
                raise ValueError(
                    f"{result.product.key} contains no values."
                )

            if result.timestamp is None:
                result.timestamp = values[0].timestamp

            result.valid_from = values[0].valid_from
            result.valid_until = values[0].valid_until

            return self._build_decoded_product(
                result,
                values,
            )

        if result.product.file_type is FileType.TAR:
            return self._decode_tar(
                result,
                grid_cell,
            )

        raise ValueError(
            f"Unsupported file type: "
            f"{result.product.file_type}"
        )

    def decode_cells(
        self,
        result: FetchResult,
        grid_cells: tuple[
            tuple[int, int],
            ...
        ],
    ) -> dict[
        tuple[int, int],
        DecodedProduct,
    ]:
        """Decode one HDF5 product for multiple grid cells."""

        if result.data is None:
            raise ValueError(
                "FetchResult contains no data.",
            )

        if result.product.file_type is not FileType.HDF5:
            raise ValueError(
                "Multiple grid-cell decoding is only supported for HDF5."
            )

        values_by_cell = self._parser.read_cells(
            result.data,
            grid_cells,
        )

        if not values_by_cell:
            raise ValueError(
                f"{result.product.key} contains no values."
            )

        first_value = next(
            iter(
                values_by_cell.values(),
            ),
        )

        if result.timestamp is None:
            result.timestamp = first_value.timestamp

        result.valid_from = first_value.valid_from
        result.valid_until = first_value.valid_until

        return {
            grid_cell: self._build_decoded_product(
                result,
                (value,),
            )
            for grid_cell, value in values_by_cell.items()
        }

    def _decode_tar(
        self,
        result: FetchResult,
        grid_cell: tuple[int, int],
    ) -> DecodedProduct:
        """Decode one TAR product."""

        values: list[ParsedValue] = []

        files = self._extractor.extract(
            result.data,
        )

        for filename in sorted(files):

            values.extend(
                self._parser.read(
                    files[filename],
                    grid_cell,
                ),
            )

        if not values:
            raise ValueError(
                f"{result.product.key} contains no values."
            )

        if result.timestamp is None:
            result.timestamp = values[0].timestamp

        result.valid_from = values[0].valid_from
        result.valid_until = values[0].valid_until

        return self._build_decoded_product(
            result,
            tuple(values),
        )

    def _build_decoded_product(
        self,
        result: FetchResult,
        values: tuple[ParsedValue, ...],
    ) -> DecodedProduct:
        """Build a decoded product."""

        return DecodedProduct(
            product=result.product,
            metadata=result.metadata,
            values=values,
        )

