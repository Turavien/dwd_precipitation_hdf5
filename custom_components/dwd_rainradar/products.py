"""Definitions of supported DWD products."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .const import (
    DWD_RADOLAN_URL,
    DWD_RADVOR_URL,
)


class FileType(StrEnum):
    """Supported DWD file types."""

    HDF5 = "hdf5"
    TAR = "tar"


@dataclass(frozen=True, slots=True)
class Product:
    """Definition of one DWD product."""

    key: str

    base_url: str

    file_type: FileType

    download_directory: str

    latest_filename: str

    file_extension: str

    interval: timedelta

    retention: timedelta

    def directory_url(
        self,
    ) -> str:
        """Return the product directory URL."""

        return (
            f"{self.base_url}/"
            f"{self.download_directory}"
        )

    def download_url(
        self,
    ) -> str:
        """Return the download URL."""

        return (
            f"{self.directory_url()}/"
            f"{self.latest_filename}"
        )


RW = Product(
    key="rw",
    base_url=DWD_RADOLAN_URL,
    file_type=FileType.HDF5,
    download_directory="rw",
    latest_filename="raa01-rw_10000-latest-dwd---bin.hdf5",
    file_extension="hdf5",
    interval=timedelta(hours=1),
    retention=timedelta(hours=49),
)

RS = Product(
    key="rs",
    base_url=DWD_RADVOR_URL,
    file_type=FileType.TAR,
    download_directory="rs",
    latest_filename="composite_rs_LATEST.tar",
    file_extension="tar",
    interval=timedelta(minutes=5),
    retention=timedelta(hours=6),
)

RV = Product(
    key="rv",
    base_url=DWD_RADVOR_URL,
    file_type=FileType.TAR,
    download_directory="rv",
    latest_filename="composite_rv_LATEST.tar",
    file_extension="tar",
    interval=timedelta(minutes=5),
    retention=timedelta(hours=6),
)

PRODUCTS: tuple[Product, ...] = (
    RW,
    RS,
    RV,
)


PRODUCTS_BY_KEY: dict[str, Product] = {
    product.key: product
    for product in PRODUCTS
}

