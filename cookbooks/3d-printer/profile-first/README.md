# Profile-first cookbook

This cookbook keeps one compose entrypoint and uses profiles as flavor switches.

## Why use this
- One place to manage service wiring.
- Easy to add new flavor combinations.
- Useful when experimenting with variants.

## Flavors
- octoprint-marlin
- octoprint-klipper
- mainsail-klipper

## Broker profile
- mosquitto
- zenoh

## Start examples
- OctoPrint Marlin + Mosquitto:
  - docker compose -f cookbooks/profile-first/docker-compose.yaml --profile octoprint-marlin --profile mosquitto up -d
- Mainsail Klipper + Zenoh:
  - docker compose -f cookbooks/profile-first/docker-compose.yaml --profile mainsail-klipper --profile zenoh up -d

## Notes
- Choose exactly one flavor profile.
- Choose exactly one broker profile.
- Core observability services are always enabled.