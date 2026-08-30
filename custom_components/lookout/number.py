"""Number platform for Lookout - exposes scan interval as an adjustable entity."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)

DEVICE_NAME = "Lookout"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([LookoutScanInterval(hass, entry)])


class LookoutScanInterval(NumberEntity):
    """Adjustable scan interval, shown on the device page as a slider.

    Writes go through the same config entry options the Options flow
    uses, so this stays in sync with it and reuses the same reload
    behavior (the integration briefly reloads to apply the new
    interval, same as submitting the Options form).
    """

    _attr_has_entity_name = False
    _attr_native_min_value = 1
    _attr_native_max_value = 30
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:timer-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_scan_interval"
        self._attr_suggested_object_id = "lookout_scan_interval"
        self._attr_name = "Scan Interval"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": "Lookout",
        }

    @property
    def native_value(self) -> float:
        current = {**self._entry.data, **self._entry.options}
        return current.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES)

    async def async_set_native_value(self, value: float) -> None:
        current = {**self._entry.data, **self._entry.options}
        current[CONF_SCAN_INTERVAL_MINUTES] = int(value)
        self.hass.config_entries.async_update_entry(self._entry, options=current)
