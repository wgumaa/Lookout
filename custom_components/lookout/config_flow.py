"""Config flow for Lookout.

Setup flow shape:
  user            -> provider / model / scan interval
  add_camera      -> pick one camera entity + give it a name, loop
  dashboard       -> show generated dashboard card YAML, then finish

Options flow shape (mirrors setup rather than a raw object editor):
  init            -> provider / model / scan interval
  manage_cameras  -> keep/remove existing cameras, choose to add more
  add_camera      -> same loop as setup, only entered if adding more
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CAMERAS,
    CONF_LLMVISION_PROVIDER,
    CONF_MODEL,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_MODEL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .dashboard import build_dashboard_card_yaml

BASE_SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LLMVISION_PROVIDER): str,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
        vol.Optional(
            CONF_SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL_MINUTES
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=30, step=1, mode="slider", unit_of_measurement="min"
            )
        ),
    }
)


def _base_settings_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_LLMVISION_PROVIDER, default=defaults.get(CONF_LLMVISION_PROVIDER)
            ): str,
            vol.Optional(
                CONF_MODEL, default=defaults.get(CONF_MODEL, DEFAULT_MODEL)
            ): str,
            vol.Optional(
                CONF_SCAN_INTERVAL_MINUTES,
                default=defaults.get(
                    CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=30, step=1, mode="slider", unit_of_measurement="min"
                )
            ),
        }
    )


def _add_camera_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("entity_id"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="camera")
            ),
            vol.Required("name"): str,
            vol.Optional("add_another", default=True): bool,
        }
    )


def _manage_cameras_schema(cameras: list[dict[str, str]]) -> vol.Schema:
    options = [
        selector.SelectOptionDict(value=c["entity_id"], label=c["name"])
        for c in cameras
    ]
    return vol.Schema(
        {
            vol.Required(
                "keep_entity_ids", default=[c["entity_id"] for c in cameras]
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options, multiple=True, mode="list"
                )
            ),
            vol.Optional("add_more", default=False): bool,
        }
    )


class LookoutConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lookout."""

    VERSION = 2

    def __init__(self) -> None:
        self._base_data: dict[str, Any] = {}
        self._cameras: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._base_data = user_input
            return await self.async_step_add_camera()

        return self.async_show_form(
            step_id="user", data_schema=BASE_SETTINGS_SCHEMA, errors=errors
        )

    async def async_step_add_camera(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = user_input["entity_id"]
            name = user_input["name"].strip() or entity_id

            if any(c["entity_id"] == entity_id for c in self._cameras):
                errors["entity_id"] = "camera_already_added"
            else:
                self._cameras.append({"entity_id": entity_id, "name": name})

                if user_input.get("add_another"):
                    return self.async_show_form(
                        step_id="add_camera",
                        data_schema=_add_camera_schema(),
                        description_placeholders={
                            "camera_count": str(len(self._cameras))
                        },
                    )
                return await self.async_step_dashboard()

        return self.async_show_form(
            step_id="add_camera",
            data_schema=_add_camera_schema(),
            errors=errors,
            description_placeholders={"camera_count": str(len(self._cameras))},
        )

    async def async_step_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if not self._cameras:
            # Shouldn't happen given add_camera requires at least one
            # entry before reaching here, but guard just in case.
            return await self.async_step_add_camera()

        if user_input is not None:
            data = {**self._base_data, CONF_CAMERAS: self._cameras}
            return self.async_create_entry(title="Lookout", data=data)

        card_yaml = build_dashboard_card_yaml(self._cameras)
        return self.async_show_form(
            step_id="dashboard",
            data_schema=vol.Schema({}),
            description_placeholders={"dashboard_yaml": card_yaml},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LookoutOptionsFlow:
        return LookoutOptionsFlow(config_entry)


class LookoutOptionsFlow(config_entries.OptionsFlow):
    """Edit provider/model/interval, then manage cameras.

    Mirrors the setup flow's add-camera loop instead of the previous
    raw ObjectSelector editor: existing cameras are shown as a
    checklist to keep or remove, with an option to add more using the
    same one-at-a-time flow used during initial setup.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._base_data: dict[str, Any] = {}
        self._cameras: list[dict[str, str]] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            self._base_data = user_input
            self._cameras = list(
                self._config_entry.options.get(
                    CONF_CAMERAS, self._config_entry.data.get(CONF_CAMERAS, [])
                )
            )
            return await self.async_step_manage_cameras()

        return self.async_show_form(
            step_id="init", data_schema=_base_settings_schema(current)
        )

    async def async_step_manage_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            keep_ids = set(user_input.get("keep_entity_ids", []))
            self._cameras = [c for c in self._cameras if c["entity_id"] in keep_ids]

            if not self._cameras and not user_input.get("add_more"):
                errors["base"] = "no_cameras_selected"
            elif user_input.get("add_more"):
                return self.async_show_form(
                    step_id="add_camera",
                    data_schema=_add_camera_schema(),
                    description_placeholders={
                        "camera_count": str(len(self._cameras))
                    },
                )
            else:
                data = {**self._base_data, CONF_CAMERAS: self._cameras}
                return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="manage_cameras",
            data_schema=_manage_cameras_schema(self._cameras),
            errors=errors,
        )

    async def async_step_add_camera(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = user_input["entity_id"]
            name = user_input["name"].strip() or entity_id

            if any(c["entity_id"] == entity_id for c in self._cameras):
                errors["entity_id"] = "camera_already_added"
            else:
                self._cameras.append({"entity_id": entity_id, "name": name})

                if user_input.get("add_another"):
                    return self.async_show_form(
                        step_id="add_camera",
                        data_schema=_add_camera_schema(),
                        description_placeholders={
                            "camera_count": str(len(self._cameras))
                        },
                    )
                data = {**self._base_data, CONF_CAMERAS: self._cameras}
                return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="add_camera",
            data_schema=_add_camera_schema(),
            errors=errors,
            description_placeholders={"camera_count": str(len(self._cameras))},
        )
