"""Sensor platform for Lookout."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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

    entities: list[SensorEntity] = [
        LookoutAverageCloudCover(coordinator, entry),
        LookoutAverageFogDensity(coordinator, entry),
        LookoutAverageRainIntensity(coordinator, entry),
        LookoutEffectiveSkyObstruction(coordinator, entry),
        LookoutCondition(coordinator, entry),
        LookoutLastUpdate(coordinator, entry),
    ]
    for index, camera in enumerate(coordinator.cameras):
        key = camera_key(index)
        entities.append(
            LookoutCameraCloudCover(coordinator, entry, key, camera["name"])
        )
        entities.append(
            LookoutCameraConfidence(coordinator, entry, key, camera["name"])
        )
        entities.append(
            LookoutCameraFogDensity(coordinator, entry, key, camera["name"])
        )
        entities.append(
            LookoutCameraRainIntensity(coordinator, entry, key, camera["name"])
        )

    async_add_entities(entities)


def _average_field(data: dict, field: str) -> float | None:
    values = [
        v.get(field)
        for v in data.values()
        if isinstance(v, dict) and v.get(field) is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


class _BaseSkyEntity(CoordinatorEntity[LookoutCoordinator], SensorEntity):
    # has_entity_name=False + an explicit suggested_object_id keeps the
    # resulting entity_id predictable (matches what dashboard.py
    # generates as a starting point) rather than being derived from a
    # device name + translated entity name combination.
    _attr_has_entity_name = False

    def __init__(self, coordinator: LookoutCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": "Lookout",
        }


class LookoutCameraCloudCover(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:camera-outline"

    def __init__(self, coordinator, entry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_cloud_cover"
        self._attr_suggested_object_id = f"lookout_{slug}_cloud_cover"
        self._attr_name = f"{camera_name} Cloud Cover"

    @property
    def native_value(self):
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("cloud_cover")


class LookoutCameraConfidence(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:check-decagram"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_confidence"
        self._attr_suggested_object_id = f"lookout_{slug}_confidence"
        self._attr_name = f"{camera_name} Confidence"

    @property
    def native_value(self):
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("confidence")


class LookoutAverageCloudCover(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-cloudy"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_average_cloud_cover"
        self._attr_suggested_object_id = "lookout_average_cloud_cover"
        self._attr_name = "Average Cloud Cover"

    @property
    def native_value(self):
        avg = _average_field(self.coordinator.data or {}, "cloud_cover")
        return round(avg) if avg is not None else None


class LookoutCameraFogDensity(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-fog"

    def __init__(self, coordinator, entry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_fog_density"
        self._attr_suggested_object_id = f"lookout_{slug}_fog_density"
        self._attr_name = f"{camera_name} Fog Density"

    @property
    def native_value(self):
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("fog_density")


class LookoutCameraRainIntensity(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator, entry, key: str, camera_name: str) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        slug = slugify(camera_name)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_rain_intensity"
        self._attr_suggested_object_id = f"lookout_{slug}_rain_intensity"
        self._attr_name = f"{camera_name} Rain Intensity"

    @property
    def native_value(self):
        camera_data = (self.coordinator.data or {}).get(self._key, {})
        return camera_data.get("rain_intensity")


class LookoutAverageFogDensity(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-fog"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_average_fog_density"
        self._attr_suggested_object_id = "lookout_average_fog_density"
        self._attr_name = "Average Fog Density"

    @property
    def native_value(self):
        avg = _average_field(self.coordinator.data or {}, "fog_density")
        return round(avg) if avg is not None else None


class LookoutAverageRainIntensity(_BaseSkyEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_average_rain_intensity"
        self._attr_suggested_object_id = "lookout_average_rain_intensity"
        self._attr_name = "Average Rain Intensity"

    @property
    def native_value(self):
        avg = _average_field(self.coordinator.data or {}, "rain_intensity")
        return round(avg) if avg is not None else None


class LookoutEffectiveSkyObstruction(_BaseSkyEntity):
    """Combined cloud+fog metric intended for automations like Adaptive
    Cover, which care about "how much is obscuring/diffusing direct
    light right now" rather than cloud cover specifically.

    Currently max(avg_cloud_cover, avg_fog_density) - whichever effect
    is stronger "wins" rather than summing, since summing risks
    double-counting when both are present (e.g. overcast + fog isn't
    necessarily "more obstruction" than either alone). This formula is
    a starting point and may be revisited once tested against more
    real conditions.
    """

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:weather-hazy"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_effective_sky_obstruction"
        self._attr_suggested_object_id = "lookout_effective_sky_obstruction"
        self._attr_name = "Effective Sky Obstruction"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        cloud = _average_field(data, "cloud_cover")
        fog = _average_field(data, "fog_density")
        candidates = [v for v in (cloud, fog) if v is not None]
        if not candidates:
            return None
        return round(max(candidates))


class LookoutCondition(_BaseSkyEntity):
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_sky_condition"
        self._attr_suggested_object_id = "lookout_sky_condition"
        self._attr_name = "Sky Condition"

    @property
    def native_value(self):
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is not None and sun_state.state == "below_horizon":
            return "Night"

        data = self.coordinator.data or {}
        camera_values = [v for v in data.values() if isinstance(v, dict)]
        if not camera_values:
            return None

        # Rain and fog take priority over the cloud-based label, since
        # a camera can show 0% cloud cover with fog or rain in front
        # of it (e.g. clear sky above ground-level morning mist).
        if any(v.get("rain_detected") for v in camera_values):
            return "Rainy"
        if any(v.get("fog_detected") for v in camera_values):
            return "Foggy"

        cloud = _average_field(data, "cloud_cover")
        if cloud is None:
            return None

        if cloud < 10:
            return "Clear"
        if cloud < 40:
            return "Mostly Clear"
        if cloud < 70:
            return "Partly Cloudy"
        if cloud < 90:
            return "Mostly Cloudy"
        return "Overcast"


class LookoutLastUpdate(_BaseSkyEntity):
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_last_update"
        self._attr_suggested_object_id = "lookout_last_update"
        self._attr_name = "Last Update"

    @property
    def native_value(self):
        # Only reflects the last time llmvision was actually called and
        # returned a valid response - not set on nights where the call
        # is skipped, or on failed calls, so it's a genuine
        # "last successful analysis" timestamp rather than a general
        # coordinator refresh time.
        return self.coordinator.last_success_time
