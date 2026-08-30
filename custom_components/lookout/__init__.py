"""The Lookout integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CAMERAS,
    CONF_LLMVISION_PROVIDER,
    CONF_MODEL,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_MODEL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .coordinator import LookoutCoordinator

PLATFORMS = ["sensor", "binary_sensor", "number", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lookout from a config entry."""
    data = {**entry.data, **entry.options}

    # data[CONF_CAMERAS] is a list of {"entity_id": ..., "name": ...}
    # dicts, in the order the user added them during setup.
    coordinator = LookoutCoordinator(
        hass,
        provider=data[CONF_LLMVISION_PROVIDER],
        model=data.get(CONF_MODEL, DEFAULT_MODEL),
        cameras=data[CONF_CAMERAS],
        scan_interval_minutes=data.get(
            CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change (e.g. cameras edited)."""
    await hass.config_entries.async_reload(entry.entry_id)
