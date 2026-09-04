"""Constants for the Lookout integration."""

DOMAIN = "lookout"

# Config / options keys
CONF_LLMVISION_PROVIDER = "llmvision_provider"
CONF_MODEL = "model"
CONF_CAMERAS = "cameras"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

# Defaults
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_SCAN_INTERVAL_MINUTES = 10
DEFAULT_MAX_TOKENS = 250

# Service used from the llmvision integration
LLMVISION_DOMAIN = "llmvision"
LLMVISION_SERVICE_IMAGE_ANALYZER = "image_analyzer"

import re


def slugify(value: str) -> str:
    """Lowercase, alphanumeric-and-underscore slug for use in unique_ids."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


# Internal per-image JSON keys are always index-based ("camera_1",
# "camera_2", ...) regardless of how many cameras are configured or
# what the user has named them. This keeps the schema/prompt
# deterministic. User-facing entity names come from the camera's
# configured "name" instead, matched back to the same index.
def camera_key(index: int) -> str:
    return f"camera_{index + 1}"


CAMERA_FIELDS = ["cloud_cover", "confidence", "sun_visible", "fog_detected", "fog_density", "rain_detected", "rain_intensity"]

_CAMERA_SCHEMA_PROPERTIES = {
    "cloud_cover": {"type": "integer"},
    "confidence": {"type": "integer"},
    "sun_visible": {"type": "boolean"},
    "fog_detected": {"type": "boolean"},
    "fog_density": {"type": "integer"},
    "rain_detected": {"type": "boolean"},
    "rain_intensity": {"type": "integer"},
}


def build_response_schema(camera_count: int) -> dict:
    """Build the structured JSON schema for the given number of cameras.

    For a single camera, the schema is flat (fields directly at the
    top level, no camera_1 wrapper). For two or more cameras, fields
    are nested per camera under camera_1, camera_2, and so on, so any
    number of images can be analyzed independently in one request.

    The flat single-camera case exists because some local/smaller
    vision models (observed with at least one Ollama model) can
    produce correct structured output against a flat schema but
    return an empty or malformed response when the same fields are
    requested nested under a dynamic key. Since a flat shape loses
    nothing when there is only one camera to describe anyway, this
    is a compatibility improvement with no real downside for the
    single-camera case.

    Includes "additionalProperties": false at every object level.
    This is required by OpenAI's structured-output (strict JSON
    schema) mode; without it, OpenAI rejects the request entirely
    with an "Invalid schema" error. Other providers, including
    Gemini, have been observed to accept schemas without this field,
    but including it is harmless for them and required for OpenAI.
    """
    camera_schema = {
        "type": "object",
        "properties": dict(_CAMERA_SCHEMA_PROPERTIES),
        "required": list(CAMERA_FIELDS),
        "additionalProperties": False,
    }

    if camera_count == 1:
        return camera_schema

    properties = {camera_key(i): camera_schema for i in range(camera_count)}
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


PROMPT_HEADER = """\
{camera_count} outdoor security camera images are provided, in this order:
{camera_list}

Analyze each image independently. Never average, compare, or infer
conditions in one image from another. Camera names are for context only
- they do not change how you should assess conditions.

For EACH image estimate:
{field_rules}

Rules:
- Analyze only the visible sky and scene.
- Ignore buildings, trees, vehicles and the ground EXCEPT where
  specifically relevant to fog_detected or rain_detected above.
- Thin cirrus clouds count toward cloud_cover.
- Blue sky = 0% cloud_cover. Completely overcast = 100%.
- sun_visible must NOT be true just because the scene is bright, shadows
  are visible, or there is glare/lens flare - only the actual solar disc
  counts.
- CRITICAL: water droplets, streaks, blur, or smudges on the camera
  LENS ITSELF (not in the scene) are a camera/lens condition, not
  weather. Do NOT set rain_detected or increase fog_density because of
  marks on the lens - if the lens appears dirty, wet, or obstructed,
  note this by keeping confidence LOW rather than reporting weather
  conditions you cannot actually verify through it.
- If the sun is below the horizon: cloud_cover = 0, confidence = 100,
  sun_visible = false. fog_detected/rain_detected may still be true if
  visible under available lighting; if visibility is too low to tell,
  set both false and keep confidence low.
- Return integers only for numeric fields.
- Return ONLY valid JSON matching the supplied schema{nesting_note}.
  No explanations, markdown or extra fields.
"""

FIELD_RULES = """\
- cloud_cover: cloud cover of the visible sky, 0-100 (integer)
- confidence: confidence in the cloud cover estimate, 0-100 (integer)
- sun_visible: true only if the solar disc is directly visible
- fog_detected: true if fog, mist, or haze is reducing visibility in
  the scene, whether or not the sky itself is cloudy
- fog_density: how much fog/mist/haze is reducing visibility, 0-100
  (integer). 0 = fully clear air, 100 = heavily obscured/whited out.
  This is about near-ground atmospheric haze, NOT cloud cover - a
  scene can have 0% cloud cover and high fog_density at the same time
  (e.g. a clear sky above ground-level morning mist), or the reverse.
- rain_detected: true if rain is visibly falling in the scene
  (streaks, splashes, visibly wet motion), OR if the sky in the same
  image is overcast or heavily clouded AND surfaces in the scene look
  distinctly wet, glossy, or reflective in a way consistent with
  active or very recent rainfall. Steady light to moderate rain often
  produces no visible streaks or splashes in a single still frame, so
  wet ground under a grey, overcast sky is real evidence, not just a
  guess.
  Do NOT set rain_detected true from wet looking surfaces alone if
  the sky in the same image is clear, mostly clear, or the sun is
  visible. That combination usually means rain has already stopped
  and what you are seeing is residual wetness while conditions clear,
  not active rain.
- rain_intensity: 0-100 (integer) if rain_detected is true, else 0"""


SINGLE_CAMERA_PROMPT = """\
One outdoor security camera image is provided.

{field_rules}

Rules:
- Analyze only the visible sky and scene.
- Ignore buildings, trees, vehicles and the ground EXCEPT where
  specifically relevant to fog_detected or rain_detected above.
- Thin cirrus clouds count toward cloud_cover.
- Blue sky = 0% cloud_cover. Completely overcast = 100%.
- sun_visible must NOT be true just because the scene is bright, shadows
  are visible, or there is glare/lens flare - only the actual solar disc
  counts.
- CRITICAL: water droplets, streaks, blur, or smudges on the camera
  LENS ITSELF (not in the scene) are a camera/lens condition, not
  weather. Do NOT set rain_detected or increase fog_density because of
  marks on the lens - if the lens appears dirty, wet, or obstructed,
  note this by keeping confidence LOW rather than reporting weather
  conditions you cannot actually verify through it.
- If the sun is below the horizon: cloud_cover = 0, confidence = 100,
  sun_visible = false. fog_detected/rain_detected may still be true if
  visible under available lighting; if visibility is too low to tell,
  set both false and keep confidence low.
- Return integers only for numeric fields.
- Return ONLY valid JSON matching the supplied schema, with the
  fields directly at the top level. No explanations, markdown or
  extra fields.
"""


def build_prompt(cameras: list[dict]) -> str:
    """Build the analysis prompt, listing each camera's given name.

    Uses a flat, single-image prompt when there is exactly one
    camera, matching the flat schema build_response_schema returns
    in that case (see its docstring for why).
    """
    if len(cameras) == 1:
        return SINGLE_CAMERA_PROMPT.format(field_rules=FIELD_RULES)

    camera_list = "\n".join(
        f"- Image {i + 1} ({camera_key(i)}): {c['name']}"
        for i, c in enumerate(cameras)
    )
    key_list = ", ".join(camera_key(i) for i in range(len(cameras)))
    return PROMPT_HEADER.format(
        camera_count=len(cameras),
        camera_list=camera_list,
        field_rules=FIELD_RULES,
        nesting_note=f", with all fields nested under {key_list}",
    )
