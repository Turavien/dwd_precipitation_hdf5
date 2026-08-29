"""Test DWD Rain Radar config-entry lifecycle."""

from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar import (
    MyData,
    async_setup_entry,
    async_unload_entry,
    update_listener,
)
from custom_components.dwd_rainradar.const import (
    DOMAIN,
    PLATFORMS,
)
from custom_components.dwd_rainradar.engine import Engine


async def test_setup_entry_creates_shared_engine(
    hass: HomeAssistant,
) -> None:
    """Test setup creates and stores one shared engine."""

    entry = MagicMock()
    entry.entry_id = "test-entry-id"

    engine = MagicMock(
        spec=Engine,
    )

    coordinator = MagicMock()

    coordinator.async_config_entry_first_refresh = (
        AsyncMock()
    )

    unload_callback = MagicMock()

    entry.add_update_listener.return_value = (
        unload_callback
    )

    with (
        patch(
            "custom_components.dwd_rainradar."
            "async_remove_disabled_entities",
            new_callable=AsyncMock,
        ) as remove_disabled,
        patch(
            "custom_components.dwd_rainradar.Engine",
            return_value=engine,
        ) as engine_class,
        patch(
            "custom_components.dwd_rainradar."
            "UpdateCoordinator",
            return_value=coordinator,
        ) as coordinator_class,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(),
        ) as forward_setups,
    ):
        assert await async_setup_entry(
            hass,
            entry,
        )

    remove_disabled.assert_awaited_once_with(
        hass,
        entry,
    )

    engine_class.assert_called_once_with(
        hass,
    )

    coordinator_class.assert_called_once_with(
        hass,
        entry,
        engine,
    )

    coordinator.async_config_entry_first_refresh.assert_awaited_once_with()

    coordinator.unregister_engine.assert_not_called()

    assert hass.data[
        DOMAIN
    ][
        "engine"
    ] is engine

    assert entry.runtime_data == MyData(
        coordinator,
    )

    entry.add_update_listener.assert_called_once_with(
        update_listener,
    )

    entry.async_on_unload.assert_called_once_with(
        unload_callback,
    )

    forward_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


async def test_setup_entry_reuses_shared_engine(
    hass: HomeAssistant,
) -> None:
    """Test additional entries reuse the existing engine."""

    entry = MagicMock()

    engine = MagicMock(
        spec=Engine,
    )

    hass.data[
        DOMAIN
    ] = {
        "engine": engine,
    }

    coordinator = MagicMock()

    coordinator.async_config_entry_first_refresh = (
        AsyncMock()
    )

    with (
        patch(
            "custom_components.dwd_rainradar."
            "async_remove_disabled_entities",
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.dwd_rainradar.Engine",
        ) as engine_class,
        patch(
            "custom_components.dwd_rainradar."
            "UpdateCoordinator",
            return_value=coordinator,
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(),
        ),
    ):
        assert await async_setup_entry(
            hass,
            entry,
        )

    engine_class.assert_not_called()


async def test_setup_entry_unregisters_after_failed_first_refresh(
    hass: HomeAssistant,
) -> None:
    """Test failed first refresh unregisters the coordinator."""

    entry = MagicMock()

    engine = MagicMock(
        spec=Engine,
    )

    coordinator = MagicMock()

    coordinator.async_config_entry_first_refresh = (
        AsyncMock(
            side_effect=RuntimeError(
                "first refresh failed"
            )
        )
    )

    with (
        patch(
            "custom_components.dwd_rainradar."
            "async_remove_disabled_entities",
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.dwd_rainradar.Engine",
            return_value=engine,
        ),
        patch(
            "custom_components.dwd_rainradar."
            "UpdateCoordinator",
            return_value=coordinator,
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="first refresh failed",
        ):
            await async_setup_entry(
                hass,
                entry,
            )

    coordinator.unregister_engine.assert_called_once_with()


async def test_update_listener_reloads_entry(
    hass: HomeAssistant,
) -> None:
    """Test config-entry updates trigger one reload."""

    entry = MagicMock()
    entry.entry_id = "test-entry-id"

    with patch.object(
        hass.config_entries,
        "async_reload",
        new=AsyncMock(
            return_value=True,
        ),
    ) as reload_entry:

        await update_listener(
            hass,
            entry,
        )

    reload_entry.assert_awaited_once_with(
        "test-entry-id",
    )


async def test_unload_entry_failure_keeps_runtime_registered(
    hass: HomeAssistant,
) -> None:
    """Test failed platform unload keeps runtime registrations."""

    entry = MagicMock()

    coordinator = MagicMock()

    entry.runtime_data = MyData(
        coordinator,
    )

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new=AsyncMock(
            return_value=False,
        ),
    ):

        assert not await async_unload_entry(
            hass,
            entry,
        )

    coordinator.unregister_engine.assert_not_called()


async def test_unload_last_entry_shuts_down_shared_engine(
    hass: HomeAssistant,
) -> None:
    """Test unloading the last entry shuts down the shared engine."""

    entry = MagicMock()

    coordinator = MagicMock()

    entry.runtime_data = MyData(
        coordinator,
    )

    engine = object.__new__(
        Engine,
    )

    engine.async_shutdown = AsyncMock()

    hass.data[
        DOMAIN
    ] = {
        "engine": engine,
    }

    with (
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new=AsyncMock(
                return_value=True,
            ),
        ),
        patch.object(
            hass.config_entries,
            "async_loaded_entries",
            return_value=[],
        ),
    ):
        assert await async_unload_entry(
            hass,
            entry,
        )

    coordinator.unregister_engine.assert_called_once_with()

    engine.async_shutdown.assert_awaited_once_with()

    assert DOMAIN not in hass.data
