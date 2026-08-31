"""Test DWD Rain Radar sensor entities."""

from datetime import (
    UTC,
    datetime,
)
from unittest.mock import MagicMock

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceEntryType

from custom_components.dwd_rainradar.const import (
    CONF_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
)
from custom_components.dwd_rainradar.models import ParsedValue
from custom_components.dwd_rainradar.products import (
    RS,
    RV,
    RW,
)
from custom_components.dwd_rainradar.sensor import (
    EVENT_SENSORS,
    FORECAST_SENSORS,
    HISTORY_SENSORS,
    INTENSITY_SENSORS,
    ROLLING_SENSORS,
    DwdRainRadarSensor,
    PARALLEL_UPDATES,
    async_setup_entry,
)


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


def test_sensor_descriptions_and_platform_settings() -> None:
    """Test sensor metadata and platform settings."""

    assert PARALLEL_UPDATES == 0

    assert HISTORY_SENSORS[0].state_class is None

    assert all(
        description.state_class is None
        for description in ROLLING_SENSORS
    )

    assert all(
        description.state_class is None
        for description in FORECAST_SENSORS
    )

    assert (
        INTENSITY_SENSORS[0].state_class
        is SensorStateClass.MEASUREMENT
    )

    assert all(
        description.state_class is None
        for description in INTENSITY_SENSORS[1:]
    )

    assert EVENT_SENSORS[0].state_class is None

    assert (
        EVENT_SENSORS[0].device_class
        is SensorDeviceClass.DURATION
    )

    assert all(
        description.product is RW
        for description in (
            *HISTORY_SENSORS,
            *ROLLING_SENSORS,
        )
    )

    assert all(
        description.product is RS
        for description in FORECAST_SENSORS
    )

    assert all(
        description.product is RV
        for description in (
            *INTENSITY_SENSORS,
            *EVENT_SENSORS,
        )
    )


def test_sensor_unique_ids_and_device_info() -> None:
    """Test sensor unique IDs and device information."""

    coordinator = _mock_coordinator()

    descriptions = (
        *INTENSITY_SENSORS,
        *FORECAST_SENSORS,
        *EVENT_SENSORS,
        *HISTORY_SENSORS,
        *ROLLING_SENSORS,
    )

    entities = [
        DwdRainRadarSensor(
            coordinator,
            description,
        )
        for description in descriptions
    ]

    assert [
        entity.unique_id
        for entity in entities
    ] == [
        (
            f"test-entry-id_"
            f"{description.key}"
        )
        for description in descriptions
    ]

    for entity in entities:

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


async def test_sensor_setup_uses_options() -> None:
    """Test sensor groups are read from config-entry options."""

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

    assert [
        entity.entity_description.key
        for entity in entities
    ] == [
        description.key
        for description in INTENSITY_SENSORS
    ]


async def test_sensor_setup_legacy_data_fallback() -> None:
    """Test legacy sensor groups are still read from config-entry data."""

    coordinator = _mock_coordinator()

    entry = MagicMock()

    entry.runtime_data.coordinator = coordinator

    entry.options = {}

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

    assert [
        entity.entity_description.key
        for entity in entities
    ] == [
        description.key
        for description in EVENT_SENSORS
    ]


def test_sensor_values_and_attributes() -> None:
    """Test sensor values and optional attributes."""

    coordinator = _mock_coordinator()

    current = DwdRainRadarSensor(
        coordinator,
        INTENSITY_SENSORS[0],
    )

    assert current.native_value is None
    assert current.extra_state_attributes is None

    coordinator.data = MagicMock()
    coordinator.data.intensity_now = 1.5

    assert current.native_value == 1.5

    history = DwdRainRadarSensor(
        coordinator,
        HISTORY_SENSORS[0],
    )

    first = ParsedValue(
        timestamp=datetime(
            2026,
            8,
            29,
            10,
            0,
            tzinfo=UTC,
        ),
        valid_from=datetime(
            2026,
            8,
            29,
            9,
            0,
            tzinfo=UTC,
        ),
        valid_until=datetime(
            2026,
            8,
            29,
            10,
            0,
            tzinfo=UTC,
        ),
        value=1.0,
    )

    latest = ParsedValue(
        timestamp=datetime(
            2026,
            8,
            29,
            11,
            0,
            tzinfo=UTC,
        ),
        valid_from=datetime(
            2026,
            8,
            29,
            10,
            0,
            tzinfo=UTC,
        ),
        valid_until=datetime(
            2026,
            8,
            29,
            11,
            0,
            tzinfo=UTC,
        ),
        value=2.0,
    )

    coordinator.data.rw = (
        first,
        latest,
    )

    assert history.extra_state_attributes == {
        "product": "RW",
        "source": "RADOLAN",
        "latest_measurement": latest.valid_until,
    }

    coordinator.data.rw = ()

    assert history.extra_state_attributes == {
        "product": "RW",
        "source": "RADOLAN",
        "latest_measurement": None,
    }

    coordinator.data = None

    assert history.extra_state_attributes is None


def test_sensor_availability_uses_product_freshness() -> None:
    """Test coordinator and product freshness both control availability."""

    coordinator = _mock_coordinator()

    coordinator.data = MagicMock()
    coordinator.data.is_product_fresh.return_value = True

    entity = DwdRainRadarSensor(
        coordinator,
        INTENSITY_SENSORS[0],
    )

    assert entity.available is True

    coordinator.data.is_product_fresh.assert_called_once_with(
        RV,
    )

    coordinator.data.is_product_fresh.return_value = False

    assert entity.available is False

    coordinator.data.is_product_fresh.return_value = True
    coordinator.last_update_success = False

    assert entity.available is False

    coordinator.last_update_success = True
    coordinator.data = None

    assert entity.available is False
