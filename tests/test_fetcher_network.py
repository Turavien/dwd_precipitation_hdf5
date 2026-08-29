"""Test DWD Rain Radar network fetch paths."""

from datetime import (
    UTC,
    datetime,
)
from unittest.mock import AsyncMock

import pytest

from custom_components.dwd_rainradar.const import DOWNLOAD_TIMEOUT
from custom_components.dwd_rainradar.fetcher import Fetcher
from custom_components.dwd_rainradar.models import (
    FetchResult,
    ProductMetadata,
    RemoteProduct,
)
from custom_components.dwd_rainradar.products import (
    RS,
    RV,
    RW,
)


class _FakeResponse:
    """Minimal async HTTP response used by fetcher tests."""

    def __init__(
        self,
        *,
        status: int = 200,
        data: bytes = b"",
        text: str = "",
        headers: dict[str, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        """Initialize the fake response."""

        self.status = status
        self.headers = headers or {}
        self._data = data
        self._text = text
        self._error = error

        self.raise_calls = 0
        self.read_calls = 0
        self.text_calls = 0

    async def __aenter__(
        self,
    ):
        """Enter the asynchronous context manager."""

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> bool:
        """Exit the asynchronous context manager."""

        return False

    def raise_for_status(
        self,
    ) -> None:
        """Raise the configured HTTP error."""

        self.raise_calls += 1

        if self._error is not None:
            raise self._error

    async def read(
        self,
    ) -> bytes:
        """Return response bytes."""

        self.read_calls += 1

        return self._data

    async def text(
        self,
    ) -> str:
        """Return response text."""

        self.text_calls += 1

        return self._text


class _FakeSession:
    """Minimal queued aiohttp client session."""

    def __init__(
        self,
        *responses: _FakeResponse,
    ) -> None:
        """Initialize the fake session."""

        self._responses = list(
            responses,
        )

        self.calls: list[
            tuple[
                str,
                dict[str, object],
            ]
        ] = []

    def get(
        self,
        url: str,
        **kwargs,
    ) -> _FakeResponse:
        """Return the next queued response."""

        self.calls.append(
            (
                url,
                kwargs,
            )
        )

        return self._responses.pop(
            0,
        )


def _fetcher(
    session: _FakeSession,
) -> Fetcher:
    """Create a fetcher with a fake session."""

    fetcher = object.__new__(
        Fetcher,
    )

    fetcher._session = session
    fetcher._directory_cache = {}
    fetcher._last_remote_checks = {}

    return fetcher


def test_build_headers() -> None:
    """Test conditional request headers."""

    fetcher = object.__new__(
        Fetcher,
    )

    assert fetcher._build_headers(
        None,
    ) == {}

    assert fetcher._build_headers(
        ProductMetadata(
            etag='"etag"',
            last_modified="Sat, 29 Aug 2026 14:35:42 GMT",
        )
    ) == {
        "If-None-Match": '"etag"',
        "If-Modified-Since": "Sat, 29 Aug 2026 14:35:42 GMT",
    }


def test_parse_remote_timestamps() -> None:
    """Test historical RW and RS filename timestamps."""

    fetcher = object.__new__(
        Fetcher,
    )

    assert fetcher._parse_remote_timestamp(
        RW,
        "raa01-rw_10000-2608291410-dwd---bin.hdf5",
    ) == datetime(
        2026,
        8,
        29,
        14,
        10,
        tzinfo=UTC,
    )

    assert fetcher._parse_remote_timestamp(
        RS,
        "composite_rs_20260829_1410.tar",
    ) == datetime(
        2026,
        8,
        29,
        14,
        10,
        tzinfo=UTC,
    )


@pytest.mark.parametrize(
    ("product", "filename"),
    (
        (
            RW,
            "rw_invalid.hdf5",
        ),
        (
            RS,
            "broken.tar",
        ),
        (
            RS,
            "composite_rs_invalid_1410.tar",
        ),
    ),
)
def test_parse_remote_timestamp_rejects_malformed_names(
    product,
    filename: str,
) -> None:
    """Test malformed filenames consistently raise ValueError."""

    fetcher = object.__new__(
        Fetcher,
    )

    with pytest.raises(
        ValueError,
        match="Unable to parse timestamp",
    ):
        fetcher._parse_remote_timestamp(
            product,
            filename,
        )


async def test_async_download_200_uses_conditional_headers() -> None:
    """Test a changed product is downloaded with conditional headers."""

    response = _FakeResponse(
        status=200,
        data=b"new-product",
        headers={
            "ETag": '"new-etag"',
            "Last-Modified": "Sat, 29 Aug 2026 14:35:42 GMT",
        },
    )

    session = _FakeSession(
        response,
    )

    fetcher = _fetcher(
        session,
    )

    old_metadata = ProductMetadata(
        etag='"old-etag"',
        last_modified="Sat, 29 Aug 2026 14:25:33 GMT",
    )

    result = await fetcher._async_download(
        RW,
        RW.download_url(),
        old_metadata,
    )

    assert result.downloaded is True
    assert result.data == b"new-product"

    assert result.metadata == ProductMetadata(
        etag='"new-etag"',
        last_modified="Sat, 29 Aug 2026 14:35:42 GMT",
    )

    assert len(
        session.calls
    ) == 1

    url, kwargs = session.calls[0]

    assert url == RW.download_url()

    assert kwargs == {
        "headers": {
            "If-None-Match": '"old-etag"',
            "If-Modified-Since": "Sat, 29 Aug 2026 14:25:33 GMT",
        },
        "timeout": DOWNLOAD_TIMEOUT,
    }

    assert response.read_calls == 1
    assert response.raise_calls == 0


async def test_async_download_304_preserves_metadata() -> None:
    """Test an unchanged product keeps previously known HTTP metadata."""

    response = _FakeResponse(
        status=304,
    )

    session = _FakeSession(
        response,
    )

    fetcher = _fetcher(
        session,
    )

    metadata = ProductMetadata(
        etag='"etag"',
        last_modified="Sat, 29 Aug 2026 14:35:42 GMT",
    )

    result = await fetcher._async_download(
        RW,
        RW.download_url(),
        metadata,
    )

    assert result.downloaded is False
    assert result.data is None
    assert result.metadata == metadata
    assert response.read_calls == 0


async def test_async_download_error_is_propagated() -> None:
    """Test unexpected HTTP status failures propagate to the coordinator."""

    response = _FakeResponse(
        status=503,
        error=RuntimeError(
            "service unavailable"
        ),
    )

    fetcher = _fetcher(
        _FakeSession(
            response,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="service unavailable",
    ):
        await fetcher._async_download(
            RW,
            RW.download_url(),
        )

    assert response.raise_calls == 1


async def test_check_connection_reads_directory() -> None:
    """Test connection checks consume the DWD directory response."""

    response = _FakeResponse(
        status=200,
        data=b"directory",
    )

    session = _FakeSession(
        response,
    )

    fetcher = _fetcher(
        session,
    )

    await fetcher.async_check_connection()

    assert session.calls[0][0] == RV.directory_url()
    assert response.raise_calls == 1
    assert response.read_calls == 1


async def test_list_remote_products_filters_sorts_and_caches() -> None:
    """Test DWD directory discovery filters, sorts and caches RW products."""

    listing = """
    <a href="../">../</a>
    <a href="raa01-rw_10000-latest-dwd---bin.hdf5">latest</a>
    <a href="raa01-rw_10000-2608291300-dwd---bin.hdf5">old</a>
    <a href="raa01-rw_10000-2608291410-dwd---bin.hdf5">newer</a>
    <a href="rw_invalid.hdf5">invalid</a>
    <a href="raa01-rw_10000-2608291400-dwd---bin.hdf5">new</a>
    <a href="raa01-rw_10000-2608291420-dwd---bin.bz2">wrong type</a>
    """

    response = _FakeResponse(
        status=200,
        text=listing,
    )

    session = _FakeSession(
        response,
    )

    fetcher = _fetcher(
        session,
    )

    since = datetime(
        2026,
        8,
        29,
        13,
        30,
    )

    products = await fetcher.async_list_remote_products(
        RW,
        since,
    )

    assert [
        product.timestamp
        for product in products
    ] == [
        datetime(
            2026,
            8,
            29,
            14,
            0,
            tzinfo=UTC,
        ),
        datetime(
            2026,
            8,
            29,
            14,
            10,
            tzinfo=UTC,
        ),
    ]

    cached_products = await fetcher.async_list_remote_products(
        RW,
        since,
    )

    assert cached_products == products

    assert len(
        session.calls
    ) == 1

    assert response.raise_calls == 1
    assert response.text_calls == 1


async def test_download_remote_sets_historical_interval() -> None:
    """Test historical downloads receive the interval implied by filename time."""

    fetcher = object.__new__(
        Fetcher,
    )

    timestamp = datetime(
        2026,
        8,
        29,
        14,
        10,
        tzinfo=UTC,
    )

    remote_product = RemoteProduct(
        product=RW,
        timestamp=timestamp,
        filename="raa01-rw_10000-2608291410-dwd---bin.hdf5",
    )

    downloaded = FetchResult(
        product=RW,
        downloaded=True,
        timestamp=None,
        data=b"historical",
        metadata=ProductMetadata(),
    )

    fetcher._async_download = AsyncMock(
        return_value=downloaded,
    )

    result = await fetcher.async_download_remote(
        remote_product,
    )

    assert result is downloaded

    assert result.timestamp == timestamp
    assert result.valid_until == timestamp

    assert result.valid_from == (
        timestamp
        - RW.interval
    )

    fetcher._async_download.assert_awaited_once_with(
        product=RW,
        url=(
            f"{RW.directory_url()}/"
            f"{remote_product.filename}"
        ),
    )
