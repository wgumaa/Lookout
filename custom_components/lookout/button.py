"""Button platform for Lookout - manual 'Run Now' trigger."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LookoutCoordinator

DEVICE_NAME = "Lookout"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: LookoutCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LookoutRunNow(coordinator, entry)])


class LookoutRunNow(ButtonEntity):
    """Manual trigger for an immediate analysis.

    Bypasses the coordinator's daylight gate (see
    LookoutCoordinator.async_run_now), so this works for testing at
    any time of day/night rather than only during the scheduled
    daylight polling window.
    """

    _attr_has_entity_name = False
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: LookoutCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_run_now"
        self._attr_suggested_object_id = "lookout_run_now"
        self._attr_name = "Run Now"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": "Lookout",
        }

    async def async_press(self) -> None:
        try:
            await self._coordinator.async_run_now()
        except Exception as err:
            raise HomeAssistantError(f"Lookout analysis failed: {err}") from err
