"""Test sensor module for supervisor_container_statistics integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

import pytest
from homeassistant.components.hassio.const import (
    ADDONS_COORDINATOR,
    CONTAINER_STATS,
    DATA_KEY_ADDONS,
    DATA_KEY_CORE,
    DATA_KEY_SUPERVISOR,
)
from homeassistant.components.hassio.const import DOMAIN as HASSIO_DOMAIN
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.supervisor_container_statistics.sensor import (
    SENSOR_DESCRIPTIONS,
    ContainerStatSensor,
    ContainerStatSensorEntityDescription,
    ContainerTarget,
    _addon_data_fn,
    async_setup_entry,
)

if TYPE_CHECKING:
    from homeassistant.components.hassio.coordinator import HassioDataUpdateCoordinator

ADDON_STATS: dict[str, Any] = {
    "cpu_percent": 12.3,
    "memory_usage": 104_857_600,
    "network_rx": 2_000_000,
    "network_tx": 1_000_000,
    "blk_read": 500_000,
    "blk_write": 250_000,
}


class FakeCoordinator:
    """Minimal stand-in for hassio's HassioDataUpdateCoordinator."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize with a coordinator.data payload."""
        self.data = data
        self.last_update_success = True
        self.enabled: list[tuple[str, str | None, set[str]]] = []
        self.refresh_requested = False

    def async_add_listener(self, _update_callback: Any, _context: Any = None) -> Any:
        """Pretend to subscribe to coordinator updates."""
        return lambda: None

    def async_enable_container_updates(
        self, container_id: str, entity_id: str | None, types: set[str]
    ) -> Any:
        """Record that stats collection was enabled for a container."""
        self.enabled.append((container_id, entity_id, types))
        return lambda: self.enabled.remove((container_id, entity_id, types))

    async def async_request_refresh(self) -> None:
        """Record that a refresh was requested."""
        self.refresh_requested = True


def _description(key: str) -> ContainerStatSensorEntityDescription:
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


def _addon_target(slug: str) -> ContainerTarget:
    return ContainerTarget(
        container_id=slug,
        data_fn=_addon_data_fn(slug),
        device_identifier=slug,
        unique_id_prefix=slug,
    )


def _make_sensor(
    coordinator: FakeCoordinator, key: str, slug: str
) -> ContainerStatSensor:
    real_coordinator = cast("HassioDataUpdateCoordinator", coordinator)
    return ContainerStatSensor(real_coordinator, _description(key), _addon_target(slug))


def _device_id(sensor: ContainerStatSensor) -> tuple[str, str]:
    info = sensor.device_info
    assert info is not None
    return next(iter(info["identifiers"]))


def test_native_value_converts_bytes_to_megabytes() -> None:
    """Test byte-based stats are exposed as decimal MB."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {"myaddon": ADDON_STATS}})
    sensor = _make_sensor(coordinator, "memory_usage", "myaddon")

    assert sensor.native_value == pytest.approx(104.9, rel=1e-3)
    assert sensor.unique_id == "myaddon_memory_usage"
    assert _device_id(sensor) == (HASSIO_DOMAIN, "myaddon")


def test_native_value_percent_not_converted() -> None:
    """Test percent-based stats are passed through unchanged."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {"myaddon": ADDON_STATS}})
    sensor = _make_sensor(coordinator, "cpu_percent", "myaddon")

    assert sensor.native_value == 12.3


def test_native_value_none_when_container_missing() -> None:
    """Test the sensor is unavailable if its container has no data yet."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {}})
    sensor = _make_sensor(coordinator, "memory_usage", "missing")

    assert sensor.native_value is None
    assert sensor.available is False


def test_available_false_when_stat_not_yet_collected() -> None:
    """Test the sensor is unavailable before stats collection is enabled."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {"myaddon": {}}})
    sensor = _make_sensor(coordinator, "memory_usage", "myaddon")

    assert sensor.available is False


def test_available_false_when_coordinator_update_failed() -> None:
    """Test the sensor is unavailable when the coordinator itself failed."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {"myaddon": ADDON_STATS}})
    coordinator.last_update_success = False
    sensor = _make_sensor(coordinator, "memory_usage", "myaddon")

    assert sensor.available is False


async def test_async_added_to_hass_enables_container_stats() -> None:
    """Test the sensor enables stats collection for its container."""
    coordinator = FakeCoordinator({DATA_KEY_ADDONS: {"myaddon": ADDON_STATS}})
    sensor = _make_sensor(coordinator, "memory_usage", "myaddon")

    await sensor.async_added_to_hass()

    assert coordinator.enabled == [("myaddon", None, {CONTAINER_STATS})]
    assert coordinator.refresh_requested is True


async def test_async_setup_entry_creates_sensors_for_all_containers() -> None:
    """Test setup creates sensors for every add-on plus Core and Supervisor."""
    coordinator = FakeCoordinator(
        {
            DATA_KEY_ADDONS: {"addon_one": ADDON_STATS, "addon_two": ADDON_STATS},
            DATA_KEY_CORE: ADDON_STATS,
            DATA_KEY_SUPERVISOR: ADDON_STATS,
        }
    )

    class FakeHass:
        data: ClassVar[dict[str, Any]] = {ADDONS_COORDINATOR: coordinator}

    added: list[ContainerStatSensor] = []
    await async_setup_entry(
        cast("Any", FakeHass()), cast("Any", None), cast("Any", added.extend)
    )

    assert len(added) == 4 * len(SENSOR_DESCRIPTIONS)

    unique_ids = {sensor.unique_id for sensor in added}
    assert "addon_one_memory_usage" in unique_ids
    assert "addon_two_cpu_percent" in unique_ids
    assert "home_assistant_core_cpu_percent" in unique_ids
    assert "home_assistant_supervisor_network_rx" in unique_ids

    device_ids = {_device_id(sensor) for sensor in added}
    assert (HASSIO_DOMAIN, "addon_one") in device_ids
    assert (HASSIO_DOMAIN, "core") in device_ids
    assert (HASSIO_DOMAIN, "supervisor") in device_ids


async def test_async_setup_entry_raises_not_ready_without_hassio() -> None:
    """Test setup fails cleanly when hassio hasn't loaded (e.g. no Supervisor)."""

    class FakeHass:
        data: ClassVar[dict[str, Any]] = {}

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(
            cast("Any", FakeHass()), cast("Any", None), cast("Any", None)
        )
