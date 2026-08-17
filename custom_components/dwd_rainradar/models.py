"""Shared data models for DWD products."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .products import Product


@dataclass(frozen=True, slots=True)
class TimeInterval:
    """Validity interval of one stored product."""

    valid_from: datetime

    valid_until: datetime


@dataclass(frozen=True, slots=True)
class ParsedValue:
    """One parsed precipitation value."""

    timestamp: datetime

    valid_from: datetime

    valid_until: datetime

    value: float | None


@dataclass(frozen=True, slots=True)
class ProductMetadata:
    """HTTP metadata for one DWD product."""

    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True, slots=True)
class RemoteProduct:
    """One product available on the DWD server."""

    product: Product

    timestamp: datetime

    filename: str


@dataclass(slots=True)
class FetchResult:
    """Downloaded DWD product."""

    product: Product

    downloaded: bool

    timestamp: datetime | None

    valid_from: datetime | None = None

    valid_until: datetime | None = None

    data: bytes | None = None

    metadata: ProductMetadata = ProductMetadata()


@dataclass(frozen=True, slots=True)
class DecodedProduct:
    """Decoded DWD product."""

    product: Product

    metadata: ProductMetadata

    values: tuple[ParsedValue, ...]

