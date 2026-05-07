# Recipe-per-flavor cookbook

This cookbook provides profile-free final compose files. Each file is one complete recipe.

## Why use this
- Maximum readability for end users.
- No profile flags in final command.
- Easy to hand over and run as-is.

## Available recipes
- compose.octoprint-marlin.mosquitto.yaml
- compose.octoprint-marlin.zenoh.yaml
- compose.octoprint-klipper.mosquitto.yaml
- compose.octoprint-klipper.zenoh.yaml
- compose.mainsail-klipper.mosquitto.yaml
- compose.mainsail-klipper.zenoh.yaml

## Start examples
- docker compose -f cookbooks/recipe-per-flavor/compose.octoprint-marlin.mosquitto.yaml up -d
- docker compose -f cookbooks/recipe-per-flavor/compose.mainsail-klipper.zenoh.yaml up -d

## Notes
- Each recipe includes the same core observability services.
- Choose one recipe file and run it directly.
