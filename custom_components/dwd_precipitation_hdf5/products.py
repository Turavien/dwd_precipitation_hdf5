"""DWD RADOLAN and RADVOR products."""

import tarfile
import logging
import h5py
from io import BytesIO
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from functools import cached_property

import numpy as np
from homeassistant.util import dt as dt_util

from .utils import get_previous_multiple, async_get
from .radar import get_radolan_grid
from .const import DWD_RADOLAN_URL, DWD_RADVOR_URL

if TYPE_CHECKING:
    import httpx

_LOGGER = logging.getLogger(__name__)


class Product(ABC):
    """Base DWD radar product."""

    PRODUCT_KEY = "rq"

    RELEASE_INTERVAL = timedelta(minutes=15)

    RELEASE_DELAY = timedelta(minutes=5)

    RELEASE_OFFSET = timedelta()

    USE_LOCAL_TIME = False

    GRID_ROWS = 1200

    GRID_COLS = 1100

    def __init__(self, lat: float, lon: float) -> None:
        """Initialize Product."""
        self.lat = lat
        self.lon = lon
        self.data = None
        self.source = None
        self.curr_release = None

    @cached_property
    def index(self):
        """Return the index for the parsed radolan data."""
        grid = get_radolan_grid(
            self.GRID_ROWS,
            self.GRID_COLS,
            wgs84=True
        )
        lon_grid = grid[:,:,0]
        lat_grid = grid[:,:,1]

        # Compute the squared Euclidean distances
        dist_sq = (lat_grid - self.lat)**2 + (lon_grid - self.lon)**2

        return np.unravel_index(np.argmin(dist_sq), dist_sq.shape)

    @property
    def requires_update(self) -> bool:
        """Return if the product needs to be updated."""
        if self.curr_release is None:
            return True

        if self.curr_release < self.get_latest_release():
            return True

        return False

    def get_latest_release(self) -> datetime:
        """Return the latest release timestamp."""
        now = dt_util.now() if self.USE_LOCAL_TIME else dt_util.utcnow()

        prev_multiple = get_previous_multiple(
            now - self.RELEASE_DELAY,
            self.RELEASE_INTERVAL,
            self.RELEASE_OFFSET,
        )

        return dt_util.as_utc(prev_multiple)

    @abstractmethod
    def get_url(self, ts: datetime, *args, **kwargs) -> str | list[str]:
        """Return the url."""
        pass

    @abstractmethod
    def update(self, async_client) -> None:
        """Update the data."""
        pass


class RadvorRQ(Product):
    """DWD RS precipitation forecast."""

    PRODUCT_KEY = "rq"

    RELEASE_INTERVAL = timedelta(minutes=5)

    RELEASE_DELAY = timedelta(minutes=5)

    RELEASE_OFFSET = timedelta()

    def get_url(self, ts: datetime) -> str:
        """Return RS tar url."""
        ts = ts.strftime("%Y%m%d_%H%M")

        return (
            f"{DWD_RADVOR_URL}/"
            f"composite_rs_{ts}.tar"
        )

    async def update(self, async_client) -> None:
        """Update RS precipitation data."""

        latest = self.get_latest_release()

        release_candidates = [
            latest,
            latest - timedelta(minutes=5),
            latest - timedelta(minutes=10),
            latest - timedelta(minutes=15),
            latest - timedelta(minutes=20),
            latest - timedelta(minutes=25),
            latest - timedelta(minutes=30),
        ]

        for ts in release_candidates:

            try:

                url = self.get_url(ts)

                response = await async_get(url, async_client)

                tar_bytes = BytesIO(response.content)

                new_data = []

                with tarfile.open(fileobj=tar_bytes) as tar:

                    for suffix in [

                        "000",
                        "005",
                        "010",
                        "015",
                        "020",
                        "025",
                        "030",
                        "035",
                        "040",
                        "045",
                        "050",
                        "055",
                        "060",
                        "065",
                        "070",
                        "075",
                        "080",
                        "085",
                        "090",
                        "095",
                        "100",
                        "105",
                        "110",
                        "115",
                        "120",
                    ]:

                        member_name = (
                            f"composite_rs_"
                            f"{ts.strftime('%Y%m%d_%H%M')}_"
                            f"{suffix}-hd5"
                        )

                        member = tar.extractfile(member_name)

                        if member is None:
                            raise ValueError(
                                f"Missing RS member {member_name}"
                            )

                        with h5py.File(member, "r") as h5f:

                            data = (
                                h5f["dataset1"]["data1"]["data"]
                            )


                            raw_value = float(data[self.index])

                            gain = float(
                                h5f["dataset1"]["data1"]["what"].attrs["gain"]
                            )

                            offset = float(
                                h5f["dataset1"]["data1"]["what"].attrs["offset"]
                            )

                            nodata = float(
                                h5f["dataset1"]["data1"]["what"].attrs["nodata"]
                            )

                            undetect = float(
                                h5f["dataset1"]["data1"]["what"].attrs["undetect"]
                            )

                            if raw_value == nodata:

                                value = None

                            elif raw_value == undetect:

                                value = 0.0

                            else:

                                value = (raw_value * gain) + offset

                                if value < 0:
                                    value = 0.0

                            new_data.append(
                                0.0
                                if value is None
                                else value
                            )


                self.curr_release = ts

                self.data = [

                    new_data[0],

                    sum(new_data[0:2]),

                    sum(new_data[0:3]),

                    sum(new_data[0:6]),

                    sum(new_data[0:9]),

                    sum(new_data[0:12]),

                    sum(new_data[0:18]),

                    sum(new_data[0:24]),
                ]

                _LOGGER.info(
                    "RS update successful using release %s",
                    ts
                )

                return

            except Exception as err:

                _LOGGER.warning(
                    "RS release %s failed: %s",
                    ts,
                    err
                )

        _LOGGER.error("All RS release attempts failed")


class RadolanProduct(Product):
    """DWD radolan product."""

    async def update(self, async_client):
        """Update the data."""

        latest = self.get_latest_release()

        release_candidates = [
            latest,
            latest - self.RELEASE_INTERVAL,
            latest - (self.RELEASE_INTERVAL * 2),
        ]

        response = None

        for ts in release_candidates:

            url = self.get_url(ts)

            try:

                response = await async_get(
                    url,
                    async_client
                )

                self.curr_release = ts

                break

            except Exception as err:

                _LOGGER.warning(
                    "%s RELEASE %s FAILED: %s",
                    self.__class__.__name__,
                    ts,
                    err
                )

        if response is None:

            return

        response = BytesIO(response.content)

        try:

            with h5py.File(response, "r") as h5f:

                data = h5f["dataset1"]["data1"]["data"]

                raw_value = float(data[self.index])

                what = h5f["dataset1"]["data1"]["what"].attrs

                gain = float(what["gain"])

                offset = float(what["offset"])

                nodata = float(what["nodata"])

                undetect = float(what["undetect"])

                if raw_value == nodata:

                    value = None

                elif raw_value == undetect:

                    value = 0.0

                else:

                    value = (raw_value * gain) + offset

                    if value < 0:
                        value = 0.0

                self.data = value

        except Exception as err:

            _LOGGER.warning(
                "%s HDF5 PARSE ERROR %s",
                self.__class__.__name__,
                err
            )


class RadolanRW(RadolanProduct):
    """DWD radolan RW 1 hour precipitation analysis."""

    PRODUCT_KEY = "rw"

    RELEASE_INTERVAL = timedelta(hours=1)

    RELEASE_DELAY = timedelta(minutes=28)

    RELEASE_OFFSET = timedelta(minutes=50)

    def get_url(self, ts: datetime) -> str:
        """Return the urls."""
        ts = ts.strftime("%y%m%d%H%M")

        return (
            f"{DWD_RADOLAN_URL}/rw/raa01-rw_10000-{ts}-dwd---bin.hdf5"
        )


class RadolanSF(RadolanProduct):
    """DWD radolan SF 24 hour precipitation analysis."""

    PRODUCT_KEY = "sf"

    RELEASE_INTERVAL = timedelta(minutes=60)

    RELEASE_DELAY = timedelta(minutes=28)

    RELEASE_OFFSET = timedelta(minutes=50)

    def get_url(self, ts: datetime) -> str:
        """Return the urls."""
        ts = ts.strftime("%y%m%d%H%M")

        return (
            f"{DWD_RADOLAN_URL}/sf/raa01-sf_10000-{ts}-dwd---bin.hdf5"
        )
