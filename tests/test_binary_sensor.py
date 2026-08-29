"""Test DWD Rain Radar binary sensor entities."""

from unittest.mock import MagicMock

from homeassistant.helpers.device_registry import DeviceEntryType

from custom_components.dwd_rainradar.binary_sensor import (
    BINARY_SENSORS,
    DwdRainRadarBinarySensor,
    PARALLEL_UPDATES,
    async_setup_entry,
)
from custom_components.dwd_rainradar.const import (
    CONF_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
)
from custom_components.dwd_rainradar.products import RV


def _mock_coordinator() -> MagicMock:
    """Return a mock coordinator."""

    coordinator = MagicMock()

    coordinator.config_entry.entry_id = (
        "test-entry-id"
    )

    coordinator.config_entry.title = (
        "Berlin"
    )

    coordinator.data = None
    coordinator.last_update_success = True

    return coordinator


def test_parallel_updates_disabled() -> None:
    """Test the coordinator controls platform update concurrency."""

    assert PARALLEL_UPDATES == 0
    assert BINARY_SENSORS[0].product is RV


def test_binary_sensor_unique_id_and_device_info() -> None:
    """Test binary sensor unique ID and device information."""

    coordinator = _mock_coordinator()

    entity = DwdRainRadarBinarySensor(
        coordinator,
        BINARY_SENSORS[0],
    )

    assert entity.unique_id == (
        "test-entry-id_radvor_rv_active"
    )

    assert entity.has_entity_name is True

    assert entity.device_info is not None

    assert entity.device_info[
        "entry_type"
    ] is DeviceEntryType.SERVICE

    assert entity.device_info[
        "identifiers"
    ] == {
        (
            DOMAIN,
            "test-entry-id",
        )
    }

    assert entity.device_info[
        "name"
    ] == "Berlin"


async def test_binary_sensor_setup_uses_options() -> None:
    """Test binary sensor groups are read from config-entry options."""

    coordinator = _mock_coordinator()

    entry = MagicMock()

    entry.runtime_data.coordinator = coordinator

    entry.options = {
        CONF_SENSOR_GROUPS: [
            SENSOR_GROUP_CURRENT,
        ],
    }

    entry.data = {
        CONF_SENSOR_GROUPS: [
            SENSOR_GROUP_EVENT,
        ],
    }

    entities = []

    def async_add_entities(
        new_entities,
    ) -> None:
        """Collect added entities."""

        entities.extend(
            list(
                new_entities
            )
        )

    await async_setup_entry(
        MagicMock(),
        entry,
        async_add_entities,
    )

    assert entities == []


async def test_binary_sensor_setup_event_group() -> None:
    """Test precipitation-active entity is created for the event group."""

    coordinator = _mock_coordinator()

    entry = MagicMock()

    entry.runtime_data.coordinator = coordinator

    entry.options = {
        CONF_SENSOR_GROUPS: [
            SENSOR_GROUP_EVENT,
        ],
    }

    entry.data = {}

    entities = []

    def async_add_entities(
        new_entities,
    ) -> None:
        """Collect added entities."""

        entities.extend(
            list(
                new_entities
            )
        )

    await async_setup_entry(
        MagicMock(),
        entry,
        async_add_entities,
    )

    assert len(
        entities
    ) == 1

    assert entities[
        0
    ].entity_description.key == (
        "radvor_rv_active"
    )

    assert entities[
        0
    ].unique_id == (
        "test-entry-id_radvor_rv_active"
    )


def test_binary_sensor_value() -> None:
    """Test binary sensor value handling."""

    coordinator = _mock_coordinator()

    entity = DwdRainRadarBinarySensor(
        coordinator,
        BINARY_SENSORS[0],
    )

    assert entity.is_on is None

    coordinator.data = MagicMock()

    coordinator.data.precipitation_active = True

    assert entity.is_on is True


def test_binary_sensor_availability_uses_rv_freshness() -> None:
    """Test precipitation-active availability follows RV freshness."""

    coordinator = _mock_coordinator()

    coordinator.data = MagicMock()
    coordinator.data.is_product_fresh.return_value = True

    entity = DwdRainRadarBinarySensor(
        coordinator,
        BINARY_SENSORS[0],
    )

    assert entity.available is True

    coordinator.data.is_product_fresh.assert_called_once_with(
        RV,
    )

    coordinator.data.is_product_fresh.return_value = False

    assert entity.available is False
