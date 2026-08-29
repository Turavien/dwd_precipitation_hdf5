"""Definitions of supported DWD products."""

# Derived in part from DWD Precipitation by Hoffmann77.
# Substantially modified for DWD Rain Radar by Turavien, 2026.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from .const import (
    DWD_RADOLAN_URL,
    DWD_RADVOR_URL,
)

_PRODUCT_FRESHNESS_GRACE = timedelta(
    minutes=5,
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

    publication_interval: timedelta

    publication_delay: timedelta

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

    @property
    def freshness_window(
        self,
    ) -> timedelta:
        """Return how long one product timestamp remains current."""

        return (
            self.publication_interval
            + self.publication_delay
            + _PRODUCT_FRESHNESS_GRACE
        )


RW = Product(
    key="rw",
    base_url=DWD_RADOLAN_URL,
    file_type=FileType.HDF5,
    download_directory="rw",
    latest_filename="raa01-rw_10000-latest-dwd---bin.hdf5",
    file_extension="hdf5",
    interval=timedelta(hours=1),
    publication_interval=timedelta(minutes=10),
    publication_delay=timedelta(minutes=24),
    retention=timedelta(hours=49),
)

RS = Product(
    key="rs",
    base_url=DWD_RADVOR_URL,
    file_type=FileType.TAR,
    download_directory="rs",
    latest_filename="composite_rs_LATEST.tar",
    file_extension="tar",
    interval=timedelta(hours=1),
    publication_interval=timedelta(minutes=5),
    publication_delay=timedelta(minutes=3),
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
    publication_interval=timedelta(minutes=5),
    publication_delay=timedelta(minutes=3),
    retention=timedelta(hours=6),
)
