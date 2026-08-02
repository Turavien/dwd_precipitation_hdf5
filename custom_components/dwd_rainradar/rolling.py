"""Rolling calculations for historical DWD products."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def rolling_sum(
    history: Iterable[Any],
) -> float | None:
    """Return the sum of all valid precipitation values."""

    total = 0.0
    found = False

    for historical_product in history:

        if not historical_product.product.values:
            continue

        parsed = historical_product.product.values[0]

        value = parsed.value

        if value is None:
            continue

        total += value
        found = True

    if not found:
        return None

    return total

