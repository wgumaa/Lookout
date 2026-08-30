# Lookout

![Lookout banner](images/banner.png)

Hyperlocal sky and camera observation for Home Assistant, powered by
[LLM Vision](https://github.com/valentinfrlch/ha-llmvision). Lookout
reads your own outdoor cameras, not a regional forecast API, to
estimate cloud cover, fog, rain, and sun visibility for whatever spot
your cameras actually cover.

Runs entirely inside your Home Assistant instance. No account is
required beyond whatever LLM Vision provider you choose to use.

## Why hyperlocal

Standard weather integrations pull from a regional forecast covering
your whole area. Lookout looks at what your own cameras can actually
see right now, which can differ from the regional forecast: ground
fog with a technically clear sky, or one side of a property in full
sun while the other side is shaded by cloud.

## Features

- Cloud cover, per camera and averaged across all cameras
- Fog and haze detection, tracked separately from cloud cover, since a
  scene can have 0 percent cloud cover with heavy ground fog at the
  same time, or the reverse
- Rain detection, requiring actual visible rain in the scene (streaks,
  splashes, rippling puddles), not just a wet looking or dark image.
  The prompt also distinguishes water on the camera lens itself from
  rain in the scene, so a dirty or wet lens does not get reported as
  weather
- Sun visibility, true only when the actual solar disc is visible, not
  just a bright or glary scene
- Confidence scoring, per camera, lower when the view is limited,
  poorly lit, or obscured
- Effective Sky Obstruction sensor, combining cloud cover and fog into
  one number meant as the input for automations like Adaptive Cover
- Any number of cameras, each named by you, analyzed independently in
  a single LLM call per poll
- Daylight only polling, skips calling the LLM while the sun is below
  the horizon
- Adjustable scan interval, a slider from 1 to 30 minutes right on the
  device page
- Run Now button, forces an immediate analysis at any time, including
  at night
- Last Update sensor, the timestamp of the last time the LLM was
  actually successfully called
- Auto generated dashboard card at the end of setup, using the exact
  entity IDs Lookout just created

## Requirements

- Home Assistant 2025.7 or newer
- The LLM Vision integration, installed and with at least one provider
  configured
- At least one outdoor camera entity with a view of the sky

## Installing LLM Vision

Lookout depends on the LLM Vision integration to actually call a
vision model. Install and configure it first.

1. Install HACS if you do not already have it. See
   [hacs.xyz](https://hacs.xyz) for instructions.
2. In Home Assistant, go to HACS, search for LLM Vision, and install
   it.
3. Restart Home Assistant.
4. Go to Settings, then Devices and Services, then Add Integration,
   and search for LLM Vision.
5. Choose a provider. Google Gemini has a free tier and is a common
   starting point, but LLM Vision also supports OpenAI, Anthropic,
   local models through Ollama, and others.
6. If you choose Google Gemini, you will need an API key from
   [Google AI Studio](https://aistudio.google.com/apikey). Paste it
   into the provider setup screen.
7. Set a default model. Check your provider's current model list
   before picking one, since models are periodically retired. As of
   this writing, Gemini 1.5 and 2.0 Flash have both been retired by
   Google; a current Gemini 3.x model is a safer choice.
8. Submit the form. If you see an Invalid API key error, this
   sometimes means the specific model you entered is no longer
   available rather than an actual problem with the key itself. Try a
   different, currently supported model.

Once LLM Vision is installed and a provider is configured, you are
ready to install Lookout.

## Installing Lookout

### Via HACS, custom repository

1. In HACS, open the menu and choose Custom repositories.
2. Add this repository's URL, category Integration.
3. Install Lookout from the HACS store.
4. Restart Home Assistant.

### Manual install

1. Copy the custom_components/lookout folder into your Home
   Assistant config's custom_components folder.
2. Restart Home Assistant.

## Setting up Lookout

Go to Settings, then Devices and Services, then Add Integration, and
search for Lookout.

1. Provider and model: enter your LLM Vision provider ID and model
   name, and choose a scan interval from 1 to 30 minutes.
2. Add cameras: pick a camera and give it a name, one at a time. Keep
   adding as many as you have, or finish after one.
3. Dashboard preview: Lookout shows a ready to paste Lovelace card
   matching the entities it just created.

To add, rename, or remove cameras later, or to change the provider,
model, or scan interval: Settings, then Devices and Services, then
Lookout, then Configure.

## On providers

Lookout depends on the llmvision integration rather than calling a
provider's API directly. This is not a Gemini specific dependency.
llmvision itself supports multiple providers, including local vision
models through Ollama, OpenAI, Anthropic, and others. Gemini is simply
what this project's own testing has used so far, because it has a
free tier. Switching providers, including to a fully local model, only
requires configuring it in llmvision and updating the model field in
Lookout's options. No code changes are needed.

## Entities

| Entity | Notes |
|---|---|
| sensor.lookout_sky_condition | Clear, Mostly Clear, Partly Cloudy, Mostly Cloudy, Overcast, Foggy, Rainy, or Night. Fog and rain take priority over the cloud based label. |
| sensor.lookout_effective_sky_obstruction | The higher of average cloud cover and average fog density. Use this for Adaptive Cover, not average cloud cover alone. |
| sensor.lookout_average_cloud_cover | Average cloud cover across all cameras |
| sensor.lookout_average_fog_density | Average fog and haze density across all cameras |
| sensor.lookout_average_rain_intensity | Average rain intensity across all cameras |
| sensor.lookout_camera_cloud_cover | Per camera cloud cover |
| sensor.lookout_camera_fog_density | Per camera fog and haze density |
| sensor.lookout_camera_rain_intensity | Per camera rain intensity |
| sensor.lookout_camera_confidence | Per camera confidence, diagnostic |
| binary_sensor.lookout_camera_sun_visible | True only if the solar disc is directly visible |
| binary_sensor.lookout_camera_fog_detected | Shows as Wet or Dry, moisture device class |
| binary_sensor.lookout_camera_rain_detected | Shows as Wet or Dry, moisture device class |
| sensor.lookout_last_update | Timestamp of the last successful LLM call, diagnostic |
| number.lookout_scan_interval | Adjustable 1 to 30 minute polling interval |
| button.lookout_run_now | Forces an immediate analysis, bypassing the daylight gate |

Camera specific entities use the name you gave each camera during
setup, for example sensor.lookout_front_cloud_cover.

## Using Effective Sky Obstruction with Adaptive Cover

If you use a cloud cover based sun protection automation, such as an
Adaptive Cover blueprint with a cloud cover sensor input expecting a
0 to 100 percent value, point it at
sensor.lookout_effective_sky_obstruction rather than
sensor.lookout_average_cloud_cover. The latter only reflects cloud
cover and would stay at 0 percent during ground fog under a clear sky.
The former accounts for both.

If your cameras face different directions and disagree meaningfully,
for example front camera in full sun while the back camera sees fog, a
single blended global sensor may not be precise enough for a cover on
a specific side of the house. Per camera obstruction sensors are a
reasonable future addition if that turns out to matter in practice.

## Roadmap

Sky: improved sky classification, cloud density as distinct from
simple percent cover, sunrise and sunset visibility.

Weather: smoke detection and storm detection. Fog and rain are already
implemented.

Camera health: spider web detection, dirty lens detection, condensation
detection, camera obstruction detection. This is deliberately not
combined with the sky analysis prompt, since it likely needs its own
prompt and schema so it does not dilute the accuracy of either.

Platform: historical observations and trends. Home Assistant's built
in long term statistics already accumulate automatically for every
sensor here, so basic history needs no extra code; dedicated trend
entities are a later step. A button to regenerate the dashboard card
on demand, after adding more cameras, is a reasonable next addition.

The goal remains a reliable observation system built on what outdoor
cameras can actually see, focused on observation rather than
automation itself.

## Changelog

0.4.0

Added fog and haze detection, and rain detection, per camera and
averaged. Added the Effective Sky Obstruction sensor for automations
like Adaptive Cover. Sky Condition is now fog and rain aware. The
prompt now explicitly distinguishes lens contamination from actual
scene rain. Confidence sensors and Last Update moved to a Diagnostic
category on the device page. Added translations/en.json, which fixes
config flow fields rendering as raw field names on some Home Assistant
frontend versions.

0.3.0

Renamed from AI Sky Observer to Lookout. Rewrote the options flow to
mirror the setup flow's add camera loop instead of a raw YAML editor.
Added the scan interval slider, the Run Now button, and the Last
Update sensor. Confirmed working end to end on a live Home Assistant
instance, including a multi day test through storm conditions.

0.2.0

Rewritten from a YAML package into a proper HACS custom integration
with a real config flow. Cameras are a user named, arbitrary length
list instead of hardcoded camera_1 and camera_2. Added the auto
generated dashboard card.

0.1.x

Original YAML package version: helpers, script, automation, and
template sensors, hardcoded to two cameras.

## License

MIT. See LICENSE.
