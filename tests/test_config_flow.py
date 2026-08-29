"""Test the DWD Rain Radar config flow."""

from unittest.mock import AsyncMock

from aiohttp import ClientConnectionError
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dwd_rainradar.config_flow import _validate_location
from custom_components.dwd_rainradar.const import (
    CONF_COORDS,
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
)

TEST_NAME = "Berlin"
TEST_LATITUDE = 52.52
TEST_LONGITUDE = 13.405
TEST_GRID_CELL = (416, 784)

USER_INPUT = {
    "name": TEST_NAME,
    CONF_COORDS: {
        "latitude": TEST_LATITUDE,
        "longitude": TEST_LONGITUDE,
    },
}

ENTRY_DATA = {
    "name": TEST_NAME,
    "latitude": TEST_LATITUDE,
    "longitude": TEST_LONGITUDE,
    "grid_cell": TEST_GRID_CELL,
}


def test_validate_location_missing_coordinates() -> None:
    """Test validation when coordinates are missing."""

    data, errors = _validate_location(
        {
            "name": TEST_NAME,
            CONF_COORDS: None,
        }
    )

    assert data["name"] == TEST_NAME
    assert errors == {
        "base": "invalid_coordinates",
    }


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test a successful user config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "sensor_groups"
    mock_dwd_connection.assert_awaited_once()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME
    assert result["data"] == ENTRY_DATA
    assert result["options"] == {
        CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
    }

    await hass.async_block_till_done()
    mock_setup_entry.assert_awaited_once()


async def test_user_flow_invalid_name(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test rejecting an empty name."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **USER_INPUT,
            "name": "   ",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {
        "base": "invalid_name",
    }
    mock_dwd_connection.assert_not_awaited()


async def test_user_flow_outside_coverage(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test rejecting a location outside DWD radar coverage."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": TEST_NAME,
            CONF_COORDS: {
                "latitude": 0.0,
                "longitude": 0.0,
            },
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {
        "base": "outside_dwd_coverage",
    }
    mock_dwd_connection.assert_not_awaited()


async def test_user_flow_duplicate_location(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test aborting when the same location already exists."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title=TEST_NAME,
        data=ENTRY_DATA,
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_dwd_connection.assert_not_awaited()


async def test_user_flow_connection_error_and_retry(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test connection failure and a successful retry."""

    mock_dwd_connection.side_effect = [
        ClientConnectionError,
        None,
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {
        "base": "cannot_connect",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "sensor_groups"
    assert mock_dwd_connection.await_count == 2


@pytest.mark.no_fail_on_log_exception
async def test_user_flow_unknown_error(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test an unexpected connection-check error."""

    mock_dwd_connection.side_effect = RuntimeError(
        "Unexpected test error"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {
        "base": "unknown",
    }


async def test_options_flow_success(
    hass: HomeAssistant,
) -> None:
    """Test changing enabled sensor groups."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title=TEST_NAME,
        data=ENTRY_DATA,
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    selected_groups = [
        SENSOR_GROUP_CURRENT,
        SENSOR_GROUP_EVENT,
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SENSOR_GROUPS: selected_groups,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SENSOR_GROUPS: selected_groups,
    }

    assert entry.title == TEST_NAME
    assert entry.data == ENTRY_DATA
    assert entry.options == {
        CONF_SENSOR_GROUPS: selected_groups,
    }


async def test_reconfigure_flow_success(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test changing name and location through reconfigure."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title=TEST_NAME,
        data=ENTRY_DATA,
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "Munich",
            CONF_COORDS: {
                "latitude": 48.137,
                "longitude": 11.575,
            },
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert entry.title == "Munich"
    assert entry.data == {
        "name": "Munich",
        "latitude": 48.137,
        "longitude": 11.575,
        "grid_cell": (935, 669),
    }
    assert entry.options == {
        CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
    }

    mock_dwd_connection.assert_not_awaited()


async def test_reconfigure_flow_invalid_name(
    hass: HomeAssistant,
) -> None:
    """Test rejecting an empty name during reconfigure."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title=TEST_NAME,
        data=ENTRY_DATA,
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "   ",
            CONF_COORDS: {
                "latitude": TEST_LATITUDE,
                "longitude": TEST_LONGITUDE,
            },
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {
        "base": "invalid_name",
    }

    assert entry.title == TEST_NAME
    assert entry.data == ENTRY_DATA


async def test_reconfigure_flow_duplicate_location(
    hass: HomeAssistant,
    mock_dwd_connection: AsyncMock,
) -> None:
    """Test rejecting a location used by another entry."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title=TEST_NAME,
        data=ENTRY_DATA,
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    entry.add_to_hass(hass)

    other_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        title="Munich",
        data={
            "name": "Munich",
            "latitude": 48.137,
            "longitude": 11.575,
            "grid_cell": (935, 669),
        },
        options={
            CONF_SENSOR_GROUPS: DEFAULT_SENSOR_GROUPS,
        },
    )
    other_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "Munich",
            CONF_COORDS: {
                "latitude": 48.137,
                "longitude": 11.575,
            },
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    assert entry.title == TEST_NAME
    assert entry.data == ENTRY_DATA

    mock_dwd_connection.assert_not_awaited()
