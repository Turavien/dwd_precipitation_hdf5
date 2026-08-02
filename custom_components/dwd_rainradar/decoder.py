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
        """Decode one downloaded DWD product."""

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

        return self._decode_tar(
            result,
            grid_cell,
        )

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

