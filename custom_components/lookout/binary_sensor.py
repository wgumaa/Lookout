"""Binary sensor platform for Lookout."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, camera_key, slugify
from .coordinator import LookoutCoordinator

DEVICE_NAME = "Lookout"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: LookoutCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for i, camera in enumerate(coordinator.cameras):
        key = camera_key(i)
        entities.append(LookoutSunVisible(coordinator, entry, key, camera["name"]))
        entities.append(LookoutFogDetected(coordinator, entry, key, camera["name"]))
        entities.append(LookoutRainDetected(coordinator, entry, key, camera["name"]))
    async_add_entities(entities)


class _BaseBinarySkyEntity(CoordinatorEntity[LookoutCoordinator], BinarySensorEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": "Lookout",
        }


class LookoutSunVisible(_BaseBinarySkyEntity):
    def __init__(self, coordinator, entry: ConfigEntry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_sun_visible"
        self._attr_suggested_object_id = f"lookout_{slug}_sun_visible"
        self._attr_name = f"{camera_name} Sun Visible"

    @property
    def is_on(self) -> bool | None:
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("sun_visible")

    @property
    def icon(self) -> str:
        return "mdi:white-balance-sunny" if self.is_on else "mdi:weather-cloudy"


class LookoutFogDetected(_BaseBinarySkyEntity):
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_icon = "mdi:weather-fog"

    def __init__(self, coordinator, entry: ConfigEntry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_fog_detected"
        self._attr_suggested_object_id = f"lookout_{slug}_fog_detected"
        self._attr_name = f"{camera_name} Fog Detected"

    @property
    def is_on(self) -> bool | None:
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("fog_detected")


class LookoutRainDetected(_BaseBinarySkyEntity):
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator, entry: ConfigEntry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_rain_detected"
        self._attr_suggested_object_id = f"lookout_{slug}_rain_detected"
        self._attr_name = f"{camera_name} Rain Detected"

    @property
    def is_on(self) -> bool | None:
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("rain_detected")
