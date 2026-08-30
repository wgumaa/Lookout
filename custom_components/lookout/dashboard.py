"""Builds a Lovelace dashboard card matching this integration's real entity IDs.

Generated at the end of setup so the user never has to hand-guess or
hand-type entity IDs into a dashboard card (the exact mismatch problem
that came up with the original YAML package's manually-written card).
"""
from __future__ import annotations

from .const import slugify


def build_dashboard_card_yaml(cameras: list[dict[str, str]]) -> str:
    """Return an entities-card YAML string for the given camera list.

    Entity IDs here are a *best-effort preview* - the actual entity_id
    Home Assistant assigns depends on the entity registry (name
    collisions get "_2" etc. appended). This is shown to the user as a
    starting point to paste into a dashboard and adjust if needed, not
    as a guaranteed-exact copy of the real registry.
    """
    lines = [
        "type: entities",
        "title: Lookout",
        "show_header_toggle: false",
        "entities:",
        "  - entity: sensor.lookout_sky_condition",
        "    name: Sky Condition",
        "  - entity: sensor.lookout_average_cloud_cover",
        "    name: Average Cloud Cover",
        "  - entity: sensor.lookout_average_fog_density",
        "    name: Average Fog Density",
        "  - entity: sensor.lookout_average_rain_intensity",
        "    name: Average Rain Intensity",
        "  - entity: sensor.lookout_effective_sky_obstruction",
        "    name: Effective Sky Obstruction",
        "  - type: section",
        "    label: Camera Analysis",
    ]

    for camera in cameras:
        slug = slugify(camera["name"])
        display_name = camera["name"]
        lines += [
            f"  - entity: sensor.lookout_{slug}_cloud_cover",
            f"    name: {display_name} Cloud Cover",
            f"  - entity: binary_sensor.lookout_{slug}_sun_visible",
            f"    name: {display_name} Sun Visible",
            f"  - entity: sensor.lookout_{slug}_confidence",
            f"    name: {display_name} Confidence",
            f"  - entity: sensor.lookout_{slug}_fog_density",
            f"    name: {display_name} Fog Density",
            f"  - entity: sensor.lookout_{slug}_rain_intensity",
            f"    name: {display_name} Rain Intensity",
        ]

    lines += [
        "  - type: section",
        "    label: Observer Status",
        "  - entity: sensor.lookout_last_update",
        "    name: Last Update",
    ]

    return "\n".join(lines)
