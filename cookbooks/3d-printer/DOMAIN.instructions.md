# Domain: 3D Printer Digital Twin

Read this file when a user asks to set up a digital twin for a 3D printer.

## Step 1 — Identify the use case

Ask (in plain language):
- "Are you mainly interested in **monitoring your printer** (temperatures, print progress, alerts)?"
- "Or do you want to **simulate thermal behaviour** — e.g. predict how the nozzle or bed heats up?"
- "Or do you want to **track quality of the printed object** layer by layer?"

Use case mapping:
- Monitoring → use_case: general
- Thermal simulation → use_case: temperature-simulation  (note: compose extensions needed, see below)
- Object quality → use_case: object-tracking  (note: compose extensions needed, see below)

If unsure, default to **general**.

## Step 2 — Identify the printer setup

Ask (use these exact friendly options):
1. "Which web interface do you use to control your printer?"
   - **OctoPrint** (the classic orange interface — common on Ender 3, Prusa, and most stock printers)
   - **Mainsail** (the modern Klipper interface — usually installed intentionally)
   - "I'm not sure / I don't have one yet"

2. If OctoPrint: "Is your printer running its **original firmware** (the default that came with it), or did you install **Klipper**?"
   - If unsure → default to original/stock firmware.

3. If the user mentions a printer model name (e.g. "Ender 3", "Prusa MK4", "CR-10"):
   - Treat common consumer printers as stock Marlin unless Klipper is explicitly mentioned.
   - Confirm: "Is your Ender 3 running the firmware it came with, or have you flashed Klipper?"

Flavor mapping:
- OctoPrint + stock firmware → octoprint-marlin
- OctoPrint + Klipper → octoprint-klipper
- Mainsail (always Klipper) → mainsail-klipper

## Step 3 — Identify the broker

Ask: "Which MQTT broker would you like to use?"
- **Mosquitto** *(recommended — widely used, simple setup)*
- **Zenoh bridge** *(alternative for edge/cloud scenarios)*

If unsure → default to **mosquitto**.

## Step 4 — Identify the cookbook style

Ask: "Do you prefer..."
- **A single compose file with profile switches** — good if you want to experiment with variants
- **One ready-to-run compose file per combination** — simpler, no profiles to remember

If unsure → default to **recipe-per-flavor**.

## Step 5 — Output the run command

For recipe-per-flavor:
```
docker compose -f cookbooks/3d-printer/recipe-per-flavor/compose.<flavor>.<broker>.yaml up -d
```

For profile-first:
```
docker compose -f cookbooks/3d-printer/profile-first/docker-compose.yaml --profile <flavor> --profile <broker> up -d
```

## Notes on extended use cases

For **temperature-simulation** and **object-tracking** use cases, the general monitoring recipe is a starting point. Extend it by adding a simulation sidecar via `include:` in a new compose file under `cookbooks/combined/`. Point the user to `cookbooks/combined/` for cross-domain or extended recipes.
