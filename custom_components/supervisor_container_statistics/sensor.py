"""
Sensor platform for supervisor_container_statistics.

Exposes CPU, memory, network, and disk I/O statistics for every Supervisor
container (add-ons, Home Assistant Core, and the Supervisor itself) by
reusing the ``hassio`` integration's own :class:`HassioDataUpdateCoordinator`.
This avoids polling the Supervisor API a second time, but couples this
integration to ``hassio``'s internal (undocumented) data structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.hassio.const import (
    ADDONS_COORDINATOR,
    CONTAINER_STATS,
    CORE_CONTAINER,
    DATA_KEY_ADDONS,
    DATA_KEY_CORE,
    DATA_KEY_SUPERVISOR,
    SUPERVISOR_CONTAINER,
)
from homeassistant.components.hassio.const import (
    DOMAIN as HASSIO_DOMAIN,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_BLK_READ,
    ATTR_BLK_WRITE,
    ATTR_CPU_PERCENT,
    ATTR_MEMORY_USAGE,
    ATTR_NETWORK_RX,
    ATTR_NETWORK_TX,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.components.hassio.coordinator import HassioDataUpdateCoordinator
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


def _bytes_to_megabytes(value: Any) -> float | None:
    """Convert a raw byte count from the Supervisor API to decimal MB."""
    if value is None:
        return None
    return round(float(value) / 1_000_000, 1)


@dataclass(frozen=True, kw_only=True)
class ContainerStatSensorEntityDescription(SensorEntityDescription):
    """Describe a single Supervisor container statistic sensor."""

    value_fn: Callable[[dict[str, Any]], float | None]


SENSOR_DESCRIPTIONS: tuple[ContainerStatSensorEntityDescription, ...] = (
    ContainerStatSensorEntityDescription(
        key=ATTR_MEMORY_USAGE,
        translation_key="memory_usage",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: _bytes_to_megabytes(stats.get(ATTR_MEMORY_USAGE)),
    ),
    ContainerStatSensorEntityDescription(
        key=ATTR_CPU_PERCENT,
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: stats.get(ATTR_CPU_PERCENT),
    ),
    ContainerStatSensorEntityDescription(
        key=ATTR_NETWORK_RX,
        translation_key="network_received",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: _bytes_to_megabytes(stats.get(ATTR_NETWORK_RX)),
    ),
    ContainerStatSensorEntityDescription(
        key=ATTR_NETWORK_TX,
        translation_key="network_transmitted",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: _bytes_to_megabytes(stats.get(ATTR_NETWORK_TX)),
    ),
    ContainerStatSensorEntityDescription(
        key=ATTR_BLK_READ,
        translation_key="disk_read",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: _bytes_to_megabytes(stats.get(ATTR_BLK_READ)),
    ),
    ContainerStatSensorEntityDescription(
        key=ATTR_BLK_WRITE,
        translation_key="disk_write",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda stats: _bytes_to_megabytes(stats.get(ATTR_BLK_WRITE)),
    ),
)


def _addon_data_fn(slug: str) -> Callable[[dict[str, Any]], dict[str, Any] | None]:
    """Build a data getter for a single add-on's stats."""
    return lambda data: data.get(DATA_KEY_ADDONS, {}).get(slug)


def _core_data_fn(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the Home Assistant Core container's data."""
    return data.get(DATA_KEY_CORE)


def _supervisor_data_fn(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the Supervisor container's data."""
    return data.get(DATA_KEY_SUPERVISOR)


@dataclass(frozen=True, kw_only=True)
class ContainerTarget:
    """Identify one Supervisor container to create statistic sensors for."""

    container_id: str
    data_fn: Callable[[dict[str, Any]], dict[str, Any] | None]
    device_identifier: str
    unique_id_prefix: str


class ContainerStatSensor(
    CoordinatorEntity["HassioDataUpdateCoordinator"], SensorEntity
):
    """Sensor for a single statistic of a single Supervisor container."""

    _attr_has_entity_name = True
    entity_description: ContainerStatSensorEntityDescription

    def __init__(
        self,
        coordinator: HassioDataUpdateCoordinator,
        description: ContainerStatSensorEntityDescription,
        target: ContainerTarget,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._target = target
        self._attr_unique_id = f"{target.unique_id_prefix}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(HASSIO_DOMAIN, target.device_identifier)},
        )

    @property
    def _container_data(self) -> dict[str, Any] | None:
        """Return the current stats payload for this container, if any."""
        return self._target.data_fn(self.coordinator.data)

    @property
    def native_value(self) -> float | None:
        """Return the current value of this statistic."""
        data = self._container_data
        if data is None:
            return None
        return self.entity_description.value_fn(data)

    @property
    def available(self) -> bool:
        """Return True if the coordinator has stats for this container."""
        data = self._container_data
        return (
            super().available
            and data is not None
            and self.entity_description.key in data
        )

    async def async_added_to_hass(self) -> None:
        """Enable stats collection for this container while the entity exists."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_enable_container_updates(
                self._target.container_id,
                self.entity_id,
                {CONTAINER_STATS},
            )
        )
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,  # noqa: ARG001
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up container statistic sensors from a config entry."""
    coordinator: HassioDataUpdateCoordinator | None = hass.data.get(ADDONS_COORDINATOR)
    if coordinator is None:
        msg = (
            "The hassio integration is not available. This integration only "
            "works on Home Assistant Supervised or Home Assistant OS."
        )
        raise ConfigEntryNotReady(msg)

    targets = [
        ContainerTarget(
            container_id=slug,
            data_fn=_addon_data_fn(slug),
            device_identifier=slug,
            unique_id_prefix=slug,
        )
        for slug in coordinator.data.get(DATA_KEY_ADDONS, {})
    ]
    targets.append(
        ContainerTarget(
            container_id=CORE_CONTAINER,
            data_fn=_core_data_fn,
            device_identifier="core",
            unique_id_prefix="home_assistant_core",
        )
    )
    targets.append(
        ContainerTarget(
            container_id=SUPERVISOR_CONTAINER,
            data_fn=_supervisor_data_fn,
            device_identifier="supervisor",
            unique_id_prefix="home_assistant_supervisor",
        )
    )

    async_add_entities(
        ContainerStatSensor(coordinator, description, target)
        for target in targets
        for description in SENSOR_DESCRIPTIONS
    )
