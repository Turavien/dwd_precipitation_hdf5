"""DWD RADOLAN and RADVOR products."""

import tarfile
import logging
import h5py
import httpx
from io import BytesIO
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from functools import cached_property

from homeassistant.util import dt as dt_util

from .utils import get_previous_multiple, async_get
from .radar import (
    get_dwd_grid_index,
)
from .const import DWD_RADOLAN_URL, DWD_RADVOR_URL

if TYPE_CHECKING:
    import httpx

_LOGGER = logging.getLogger(__name__)

RV_RAIN_THRESHOLD = 0.1
RV_RAIN_GAP_MINUTES = 10
RV_RAIN_GAP_STEPS = RV_RAIN_GAP_MINUTES // 5


def _extract_rain_events(
    forecast: list[float],
) -> list[dict]:
    """Extract continuous rain events from a forecast."""

    events = []

    start = None
    peak = 0.0
    peak_index = None
    dry_steps = 0

    for index, value in enumerate(forecast):

        if value >= RV_RAIN_THRESHOLD:

            if start is None:

                start = index
                peak = value
                peak_index = index

            elif value > peak:

                peak = value
                peak_index = index

            dry_steps = 0

        elif start is not None:

            dry_steps += 1

            if dry_steps >= RV_RAIN_GAP_STEPS:

                end = index - RV_RAIN_GAP_STEPS

                events.append(
                    {
                        "start": start * 5,
                        "end": end * 5,
                        "duration": (end - start + 1) * 5,
                        "peak": peak,
                        "peak_at": peak_index * 5,
                        "open": False,
                    }
                )

                start = None
                peak = 0.0
                peak_index = None
                dry_steps = 0

    if start is not None:

        end = len(forecast) - 1

        events.append(
            {
                "start": start * 5,
                "end": end * 5,
                "duration": (end - start + 1) * 5,
                "peak": peak,
                "peak_at": peak_index * 5,
                "open": True,
            }
        )

    return events


class Product(ABC):
    """Base DWD radar product."""

    PRODUCT_KEY = ""

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

        return get_dwd_grid_index(
            self.lat,
            self.lon
        )

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


class RadvorRS(Product):
    """DWD RS precipitation forecast."""

    PRODUCT_KEY = "rs"

    RELEASE_INTERVAL = timedelta(minutes=5)

    RELEASE_DELAY = timedelta(minutes=5)

    RELEASE_OFFSET = timedelta()

    def get_url(self, ts: datetime) -> str:
        """Return RS tar url."""
        ts = ts.strftime("%Y%m%d_%H%M")

        return (
            f"{DWD_RADVOR_URL}/rs/"
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
                        "060",
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

                    new_data[0] + new_data[1],

                    new_data[0] + new_data[1] + new_data[2],
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


class RadvorRV(Product):
    """DWD RV precipitation intensity forecast."""

    PRODUCT_KEY = "rv"

    RELEASE_INTERVAL = timedelta(minutes=5)

    RELEASE_DELAY = timedelta(minutes=5)

    RELEASE_OFFSET = timedelta()

    def get_url(self, ts: datetime) -> str:
        """Return RV tar url."""
        ts = ts.strftime("%Y%m%d_%H%M")

        return (
            f"{DWD_RADVOR_URL}/rv/"
            f"composite_rv_{ts}.tar"
        )

    async def update(self, async_client) -> None:
        """Update RV precipitation data."""

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

                response = await async_get(
                    url,
                    async_client
                )

                tar_bytes = BytesIO(response.content)

                new_data = []

                with tarfile.open(fileobj=tar_bytes) as tar:

                    for minute in range(0, 125, 5):

                        suffix = f"{minute:03d}"

                        member_name = (
                            f"composite_rv_"
                            f"{ts.strftime('%Y%m%d_%H%M')}_"
                            f"{suffix}-hd5"
                        )

                        member = tar.extractfile(member_name)

                        if member is None:
                            raise ValueError(
                                f"Missing RV member {member_name}"
                            )

                        with h5py.File(member, "r") as h5f:

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

                            new_data.append(
                                0.0
                                if value is None
                                else value
                            )

                events = _extract_rain_events(new_data)

                next_event = (
                    events[0]
                    if events
                    else None
                )

                self.curr_release = ts

                release_time = dt_util.as_local(ts)

                forecast_max = max(new_data)
                forecast_max_index = new_data.index(
                    forecast_max
                )

                self.data = {
                    "forecast": new_data,

                    "events": events,

                    "rain_active": (
                        new_data[0] >= RV_RAIN_THRESHOLD
                    ),

                    "rain_now": new_data[0],
                    "rain_5": new_data[1],
                    "rain_10": new_data[2],
                    "rain_15": new_data[3],

                    "rain_start": (
                        next_event["start"]
                        if next_event
                        else None
                    ),

                    "rain_start_time": (
                        release_time
                        + timedelta(
                            minutes=next_event["start"]
                        )
                        if next_event
                        else None
                    ),

                    "rain_end": (
                        next_event["end"]
                        if (
                            next_event
                            and not next_event["open"]
                        )
                        else None
                    ),

                    "rain_end_time": (
                        release_time
                        + timedelta(
                            minutes=next_event["end"]
                        )
                        if (
                            next_event
                            and not next_event["open"]
                        )
                        else None
                    ),

                    "rain_duration": (
                        next_event["duration"]
                        if (
                            next_event
                            and not next_event["open"]
                        )
                        else None
                    ),

                    "max_intensity": (
                        next_event["peak"]
                        if next_event
                        else 0.0
                    ),

                    "max_intensity_at": (
                        next_event["peak_at"]
                        if next_event
                        else None
                    ),

                    "max_intensity_time": (
                        release_time
                        + timedelta(
                            minutes=next_event["peak_at"]
                        )
                        if next_event
                        else None
                    ),

                    "forecast_max_intensity": (
                        forecast_max
                    ),

                    "forecast_max_intensity_at": (
                        forecast_max_index * 5
                    ),

                    "forecast_max_intensity_time": (
                        release_time
                        + timedelta(
                            minutes=forecast_max_index * 5
                        )
                    ),
                }

                _LOGGER.info(
                    "RV update successful using release %s",
                    ts
                )

                return

            except Exception as err:

                _LOGGER.warning(
                    "RV release %s failed: %s",
                    ts,
                    err
                )

        _LOGGER.error("All RV release attempts failed")


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

            except httpx.HTTPStatusError as err:

                if err.response.status_code == 404:
                    continue

                _LOGGER.warning(
                    "%s RELEASE %s FAILED: %s",
                    self.__class__.__name__,
                    ts,
                    err
                )

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
