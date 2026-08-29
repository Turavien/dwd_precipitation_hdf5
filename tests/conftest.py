"""Fixtures for DWD Rain Radar tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations,
) -> Generator[None, None, None]:
    """Enable custom integrations in all tests."""

    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock integration setup during config-flow tests."""

    with patch(
        "custom_components.dwd_rainradar.async_setup_entry",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_dwd_connection() -> Generator[AsyncMock, None, None]:
    """Mock the DWD connection check."""

    with patch(
        "custom_components.dwd_rainradar.config_flow."
        "Fetcher.async_check_connection",
        new_callable=AsyncMock,
    ) as mock:
        yield mock
