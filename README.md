# 3d-printer-digital-twin

Repository containing a 3d printer digital twin (shadow) setup to be used at the 2nd Next-gen DT Engineering workshop

the main components are shown below.

<img src="images/component-diagram-overview.png" alt="Component diagram overview" />

## Testing

Have been tested and working: octoprint, mosquitto, grafana (with little configuration of dashboard)

TODO

- try replacing eclipse mosquitto with zenoh mqtt bridge and see if that works out of the box.
- try the klipper virtual printer with moonraker/mainsail. Also checkout the mqtt config of moonraker.
- try the klipper virtual printer with octoprint

## configurability:

Note: not yet implemented, part of todo

The docker compose file uses profiles to make services configurable:

* virtual printer: swap between octoprint's virtual printer and a klipper virtual printer with option `--profile octoprint-marlin` or `--profile octoprint-klipper`
* klipper API server (only for when using simulated klipper printer): swap between octoprint with virtual klipper printer and Moonraker/Mainsail with option `--profile octoprint-klipper` or `--profile mainsail-klipper`

For example

        docker compose --profile mosquitto --profile octoprint-marlin up -d

## Notes on the octoprint config

The octoprint instance comes preconfigured, but for reference this section contains some notes on the config.

## notes about root user:

https://forums.docker.com/t/bind-mount-with-current-users-ownership/147176/3

Unless directories used for bind mounts already exist, docker creates them with the root user. Some containers need you to specify user: "0" to be able to write to the directories. The clean approach would be to chmod the directories after creation, but just running as root user is faster.

## Notes on the Zenoh MQTT broker:

Doesn't support QoS 2 - doesn't break our demo luckily
Doesn't support Last Will & Status -> in Octoprint, must disable this (two checkmarks in MQTT config), otherwise client will keep disconnecting.
