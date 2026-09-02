"""Coordinator for Lookout.

Calls llmvision.image_analyzer on a schedule, sends all configured
cameras in one request (in list order), and parses the structured
JSON response into a dict keyed by index-based camera_N keys.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_MAX_TOKENS,
    LLMVISION_DOMAIN,
    LLMVISION_SERVICE_IMAGE_ANALYZER,
    build_prompt,
    build_response_schema,
    camera_key,
)

_LOGGER = logging.getLogger(__name__)


class LookoutCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches sky analysis for all configured cameras on an interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: str,
        model: str,
        cameras: list[dict[str, str]],
        scan_interval_minutes: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Lookout",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )
        self._provider = provider
        self._model = model
        # cameras: [{"entity_id": "camera.front", "name": "Entry"}, ...]
        self._cameras = cameras
        # Timestamp of the last time llmvision was actually called and
        # returned a valid structured response - not set on nights
        # where the call is skipped, and not set on failures, so it
        # reflects genuine last-successful-analysis time.
        self.last_success_time: datetime | None = None

    @property
    def cameras(self) -> list[dict[str, str]]:
        return self._cameras

    async def _async_update_data(self) -> dict[str, Any]:
        # Only poll during daylight - mirrors the original package's
        # "conditions: sun after sunrise before sunset" behavior.
        # This gate only applies to the scheduled poll; async_run_now()
        # bypasses it deliberately for manual/test use.
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is not None and sun_state.state == "below_horizon":
            # Keep previous data rather than overwriting with stale
            # values, unless we have nothing yet.
            return self.data or {}

        return await self._fetch_analysis()

    async def async_run_now(self) -> None:
        """Force an immediate analysis, bypassing the daylight gate.

        Used by the "Run Now" button so testing doesn't require
        waiting for the next scheduled poll or for daylight hours.
        Pushes the result to all entities immediately and resets the
        coordinator's normal refresh schedule, same as a regular
        successful poll.
        """
        data = await self._fetch_analysis()
        self.async_set_updated_data(data)

    async def _fetch_analysis(self) -> dict[str, Any]:
        image_entities = [c["entity_id"] for c in self._cameras]
        schema = build_response_schema(len(self._cameras))
        prompt = build_prompt(self._cameras)

        try:
            result = await self.hass.services.async_call(
                LLMVISION_DOMAIN,
                LLMVISION_SERVICE_IMAGE_ANALYZER,
                {
                    "provider": self._provider,
                    "model": self._model,
                    "image_entity": image_entities,
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "response_format": "json",
                    "include_filename": True,
                    "structure": schema,
                    "message": prompt,
                },
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError as err:
            raise UpdateFailed(f"llmvision call failed: {err}") from err

        structured = (result or {}).get("response", {}).get(
            "structured_response"
        ) or (result or {}).get("structured_response")

        if not structured:
            # Some provider/model combinations (observed with local
            # Ollama vision models) don't honor the requested JSON
            # schema at all and fall back to their normal free-text
            # response shape (e.g. a "title"/"response_text" pair)
            # instead. Surface whatever was actually returned so this
            # is diagnosable instead of a bare "no structured_response"
            # message with no further information.
            fallback_text = None
            if isinstance(result, dict):
                response_obj = result.get("response", result)
                if isinstance(response_obj, dict):
                    fallback_text = (
                        response_obj.get("response_text")
                        or response_obj.get("title")
                        or str(response_obj)
                    )
            hint = (
                f" llmvision returned instead: {fallback_text!r}. "
                "This usually means the selected model does not "
                "support enforced JSON schema / structured output. "
                "Try a different model or provider."
                if fallback_text
                else ""
            )
            raise UpdateFailed(f"llmvision returned no structured_response.{hint}")

        expected_keys = [camera_key(i) for i in range(len(self._cameras))]
        missing = [k for k in expected_keys if k not in structured]
        if missing:
            raise UpdateFailed(f"Response missing keys: {missing}")

        self.last_success_time = dt_util.utcnow()
        return structured
