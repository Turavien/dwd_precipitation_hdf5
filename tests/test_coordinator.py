"""Test DWD Rain Radar coordinator settings."""

from datetime import timedelta
from unittest.mock import (
    AsyncMock,
    MagicMock,
)

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar.coordinator import (
    UPDATE_INTERVAL,
    UpdateCoordinator,
)
from custom_components.dwd_rainradar.state import State


GRID_CELL = (416, 784)


def _coordinator(
    hass: HomeAssistant,
) -> tuple[
    UpdateCoordinator,
    MagicMock,
    MagicMock,
]:
    """Create one coordinator with mocked entry and engine."""

    entry = MagicMock()

    entry.data = {
        "grid_cell": GRID_CELL,
    }

    engine = MagicMock()

    coordinator = UpdateCoordinator(
        hass,
        entry,
        engine,
    )

    return (
        coordinator,
        entry,
        engine,
    )


def test_update_interval() -> None:
    """Test the coordinator checks for updates every 30 seconds."""

    assert UPDATE_INTERVAL == timedelta(
        seconds=30,
    )


def test_coordinator_configuration(
    hass: HomeAssistant,
) -> None:
    """Test coordinator configuration."""

    coordinator, entry, engine = _coordinator(
        hass,
    )

    assert coordinator.config_entry is entry

    assert coordinator.always_update is True

    engine.register_grid_cell.assert_called_once_with(
        GRID_CELL,
    )

    engine.register_update_callback.assert_called_once_with(
        coordinator._handle_background_update,
    )


async def test_background_update_requests_refresh(
    hass: HomeAssistant,
) -> None:
    """Test completed background work requests a refresh."""

    coordinator, entry, _ = _coordinator(
        hass,
    )

    coordinator.async_request_refresh = AsyncMock()

    coordinator._handle_background_update()

    refresh_coro = (
        entry.async_create_task.call_args.args[
            1
        ]
    )

    assert (
        entry.async_create_task.call_args.args[
            0
        ]
        is hass
    )

    assert (
        entry.async_create_task.call_args.args[
            2
        ]
        == "DWD Rain Radar background refresh"
    )

    await refresh_coro

    coordinator.async_request_refresh.assert_awaited_once_with()


async def test_update_data_delegates_to_engine(
    hass: HomeAssistant,
) -> None:
    """Test updates are delegated to the shared engine."""

    coordinator, _, engine = _coordinator(
        hass,
    )

    expected = MagicMock(
        spec=State,
    )

    engine.async_update = AsyncMock(
        return_value=expected,
    )

    assert (
        await coordinator._async_update_data()
        is expected
    )

    engine.async_update.assert_awaited_once_with(
        grid_cell=GRID_CELL,
    )


def test_unregister_engine(
    hass: HomeAssistant,
) -> None:
    """Test coordinator registrations are removed."""

    coordinator, _, engine = _coordinator(
        hass,
    )

    coordinator.unregister_engine()

    engine.unregister_update_callback.assert_called_once_with(
        coordinator._handle_background_update,
    )

    engine.unregister_grid_cell.assert_called_once_with(
        GRID_CELL,
    )


def test_diagnostics_delegate_to_engine(
    hass: HomeAssistant,
) -> None:
    """Test coordinator diagnostics delegate to the shared engine."""

    coordinator, _, engine = _coordinator(
        hass,
    )

    coordinator.data = MagicMock(
        spec=State,
    )

    expected = {
        "runtime": "ok",
    }

    engine.get_diagnostics.return_value = expected

    assert coordinator.get_diagnostics() == expected

    engine.get_diagnostics.assert_called_once_with(
        coordinator.data,
    )
