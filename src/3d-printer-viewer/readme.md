# 3D printer viewer

A visualization of an Ender 3 v2 3D-printer using Threejs. It can be accessed in your webbrowser on [http://localhost:8000](http://localhost:8000).
The Docker image is also on docker hub: https://hub.docker.com/r/joostm8/3d-printer-viewer

The ender3v2.glb was exported from the STEP file from https://grabcad.com/library/creality-ender-3-v2-4
Export was done with FreeCAD.

# Compose
Example docker compose:
   
    services:
      3d-printer-viewer:
        image: joostm8/3d-printer-viewer
        restart: unless-stopped
        ports:
         - 8000:8000


# Websocket "API"
The javascript code running on the loaded webpage tries to set up websocket connection to a websocket server on `ws://localhost:9090`.

You should use this address to host your websocket server.

To control the printer, there are three "types" of commands the client (the webpage) accepts:

## Mesh
A mesh command can be used to reset the currently drawn mesh. Send a JSON payload on the websocket with the following content:

    {"type":"mesh", "reset":[True|False]}

## PositionUpdate
A position update command can be used to update the position. Send a JSON payload on the websocket with the following content:

    {"type":"positionUpdate", "x":[x],"y":[y],"z":[z],"e":[True|False]}

`x`,`y` and `z` must be specified in meters. `e` is a boolean indicating if the printer made an extrusion between the previous position and the updated position.

## Extrusion
An extrusion command can be used to update the visualization of the extrusion. You shouldn't have to use this, the default values are fine.

To update the values, send a JSON payload on the websocket with the following content:

    {"type":"extrusion","extruding":[True|False], "extrusionWidth":[width], "extrusionDepth":[depth]}

Where `width` and `depth` should be in meters.

## Performance/under the hood

For rendering the printed mesh, every 60 points are added to the mesh. Assuming updates at 60 Hz, that means the mesh gets updated every second. Responsiveness seems okay from what I've tested, and this means the print visualization can scale to layers with much more points.

TODO: websocket connection restoring?

## test script

`ws_text_server.py` is a little script that allows you to test the visualization, is has the printer print a cylinder.