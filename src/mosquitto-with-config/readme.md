# Mosquitto image with config

This is a mosquitto image with a default config baked into it that allows anonymous connections.
Simply there to save some time while testing such that you don't need to specify the config file.

# info

Eclipse Mosquitto MQTT server with baked in configuration that allows anonymous users.

Example docker compose:
    
    services:
      mosquitto:
        image: joostm8/mosquitto-anonymous-allowed
        container_name: mosquitto
        restart: unless-stopped
        ports:
          - "1883:1883"
        volumes:
          - mosquitto-data:/mosquitto/data
          - mosquitto-log:/mosquitto/log
    
    volumes:
      mosquitto-data:
      mosquitto-log:

Refer to main Eclipse Mosquitto repository for all information. https://hub.docker.com/_/eclipse-mosquitto/