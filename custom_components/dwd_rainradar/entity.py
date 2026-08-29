"""Base entities for DWD Rain Radar."""

from __future__ import annotations

from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UpdateCoordinator
from .products import Product


class DwdRainRadarEntity(
    CoordinatorEntity[UpdateCoordinator],
):
    """Base entity for DWD Rain Radar."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UpdateCoordinator,
        entity_key: str,
        product: Product,
    ) -> None:
        """Initialize the entity."""

        super().__init__(coordinator)

        self._product = product

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_"
            f"{entity_key}"
        )

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (
                    DOMAIN,
                    coordinator.config_entry.entry_id,
                )
            },
            name=(
                coordinator.config_entry.title
                or "DWD Rain Radar"
            ),
        )

    @property
    def available(
        self,
    ) -> bool:
        """Return whether the underlying DWD product is current."""

        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.is_product_fresh(
                self._product,
            )
        )
