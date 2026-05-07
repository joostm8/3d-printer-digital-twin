# Domain: Beer Brewing Digital Twin

Read this file when a user asks to set up a digital twin for a brewing setup.

## Step 1 — Identify the use case

Ask (in plain language):
- "Are you monitoring an active **fermentation vessel** (temperature, gravity, CO2)?"
- "Or are you tracking a **full brew day** — mash temp, boil, fermentation in sequence?"
- "Or do you want a **recipe simulation** — predict final gravity and ABV before you brew?"

Use case mapping:
- Fermentation monitoring → use_case: general
- Full brew day → use_case: brew-day  (note: not yet scaffolded, see contributing guide)
- Recipe simulation → use_case: recipe-simulation  (note: not yet scaffolded)

If unsure → default to **general**.

## Step 2 — Identify the sensor/hardware interface

Ask: "How do your sensors connect?"
- **Tilt Hydrometer or similar Bluetooth sensor** (common for home brewers)
- **Wired sensors via a Raspberry Pi or Arduino** (DIY setups)
- **I don't have sensors yet / want to simulate**

Hardware mapping:
- Tilt → ingredient: tilt-bridge (MQTT bridge for Tilt BLE data) — not yet scaffolded
- Wired → ingredient: telegraf with serial/GPIO input — not yet scaffolded
- Simulation → ingredient: sensor-simulator — not yet scaffolded

## Step 3 — Broker and observability

Same as other domains:
- Broker: mosquitto (default) or zenoh
- Observability stack: TimescaleDB + Grafana (shared core ingredient)

## Step 4 — Output

This domain's recipes are not yet scaffolded. Tell the user:

> "The beer brewing domain is on the roadmap. The shared observability core (Grafana, TimescaleDB, InfluxDB) is already available as an ingredient in `cookbooks/3d-printer/*/ingredients/core.yaml`.
> To scaffold this domain, copy that ingredient into a new `cookbooks/beer-brewing/` folder and add a sensor bridge service specific to your hardware."

Point contributors to `cookbooks/registry.yaml` to register new domains.
