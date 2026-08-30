# Lookout (HACS integration scaffold)

![Lookout banner](images/banner.png)

v0.3.0 — renamed from AI Sky Observer to Lookout; confirmed working
against a live Home Assistant instance including multi-camera setup
and multi-day storm testing.

## Structure

```
hacs.json
custom_components/lookout/
├── __init__.py       # entry point, sets up coordinator + platforms
├── manifest.json      # integration metadata, depends on llmvision
├── const.py            # domain, defaults, prompt + schema builder
├── config_flow.py      # UI setup wizard (provider, model, interval, add-camera loop)
├── coordinator.py       # polls llmvision.image_analyzer on a schedule
├── dashboard.py          # generates ready-to-paste Lovelace card YAML
├── sensor.py              # cloud cover / confidence / condition sensors
├── binary_sensor.py        # sun-visible sensors
└── strings.json              # UI text for the config flow and entity names
```

## Design notes / what's still stubbed

- **Depends on the `llmvision` integration** being installed, with a
  provider already configured there. This isn't a Gemini-specific
  dependency — `llmvision` itself supports multiple providers,
  including local vision models (e.g. Ollama), OpenAI, Anthropic, and
  others. Gemini is just what this project's testing has used so far
  because it's free. Switching to a different provider, including a
  fully local one, is a matter of configuring it in `llmvision` and
  updating the `model` field here — no code changes needed. A future
  version could still call a provider's API directly to drop the
  `llmvision` dependency entirely, but that would trade away this
  built-in provider flexibility, so it's not an obvious win.
- **Cameras are a list, not hardcoded to two, and are user-named.**
  The setup flow lets you add any number of cameras one at a time,
  each with a name you choose (e.g. "Front", "Garden") — this
  replaces the old `camera_1`/`camera_2` package limitation. Names
  drive both the entity naming and the auto-generated dashboard card.
- **Daylight-only polling** is handled inside the coordinator by
  checking `sun.sun` before calling the LLM, rather than as an
  automation condition.
- **No history/trends yet.** Sensors are declared normally, so HA's
  built-in long-term statistics will start accumulating automatically
  once installed — no extra code needed for basic history. Dedicated
  "observation trends" entities are a later roadmap item.
- **Camera health checks (spiderweb, dirty lens, etc.) intentionally
  left out.** Per the roadmap discussion, these likely deserve a
  separate prompt/schema from sky analysis rather than being bolted
  onto this one, to avoid diluting either prompt's accuracy.
- **Confirmed working on a live Home Assistant instance**, including
  a multi-day test through storm conditions: config flow setup, the
  llmvision.image_analyzer call and structured-response parsing,
  daylight gating, single- and multi-camera polling, and the
  generated dashboard YAML all tested against real data.
- **The options flow (editing cameras after initial setup) is still
  clunky** — it currently uses a raw YAML/JSON object editor instead
  of the nicer one-at-a-time add-camera flow used during setup. On
  the to-do list to bring it in line with the setup flow.

## Local dev / testing

1. Copy `custom_components/lookout/` into your HA config's
   `custom_components/` folder.
2. Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → search
   "Lookout".
4. Once you're happy with it, this repo can be added to HACS as a
   custom repository for easier install/update.
