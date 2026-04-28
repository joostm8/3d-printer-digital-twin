#!/usr/bin/env python3
"""
MQTT -> WebSocket data bridge for OctoPrint events.

Dependencies:
    pip install paho-mqtt websockets

Run:
    python mqtt_websocket_data_bridge.py

Listens MQTT on mqtt://localhost:1883
Hosts WebSocket on ws://localhost:8080

Behavior: see user's specification.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

MQTT_BROKER = "broker"
MQTT_PORT = 1883
WS_HOST = "0.0.0.0"
WS_PORT = 9090

TOPICS = [
    "octoPrint/event/PrintStarted",
    "octoPrint/event/PrintFailed",
    "octoPrint/event/PrintDone",
    "octoPrint/event/PrintCancelled",
    "octoPrint/event/PrintPaused",
    "octoPrint/event/PrintResumed",
    "octoPrint/event/PositionUpdate",
]

# Global state
state = "idle"  # idle | printing | paused
current_print_name: Optional[str] = None
previous_e: Optional[float] = None

# asyncio queue used to pass MQTT events from paho thread into asyncio loop
mqtt_event_queue: Optional[asyncio.Queue] = None

# set of connected websocket clients
connected_websockets = set()


# ---------------- MQTT callbacks ----------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        for topic in TOPICS:
            client.subscribe(topic)
            logging.info("Subscribed to %s", topic)
    else:
        logging.error("Failed to connect to MQTT broker: rc=%s", rc)


def on_message(client, userdata, msg):
    payload = None
    try:
        payload = msg.payload.decode("utf-8")
    except Exception:
        logging.exception("Failed decoding payload for topic %s", msg.topic)
        return

    loop = userdata.get("loop")
    queue = userdata.get("queue")
    if loop is None or queue is None:
        logging.error("Missing loop/queue in MQTT userdata")
        return

    try:
        # pass tuple of topic and raw payload string
        loop.call_soon_threadsafe(queue.put_nowait, (msg.topic, payload))
    except Exception:
        logging.exception("Failed to enqueue MQTT message")


# ---------------- Websocket helpers ----------------
async def broadcast_json(obj: Dict[str, Any]):
    if not connected_websockets:
        return
    text = json.dumps(obj)
    to_remove = []
    for ws in list(connected_websockets):
        try:
            await ws.send(text)
        except Exception:
            logging.warning("Removing closed websocket client")
            to_remove.append(ws)
    for ws in to_remove:
        connected_websockets.discard(ws)


async def ws_handler(websocket):
    # register
    connected_websockets.add(websocket)
    logging.info("Websocket client connected. Total clients: %d", len(connected_websockets))
    try:
        # keep connection open; we do not expect incoming messages but handle if any
        async for _ in websocket:
            # ignore incoming messages
            pass
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_websockets.discard(websocket)
        logging.info("Websocket client disconnected. Total clients: %d", len(connected_websockets))


# ---------------- Message handling ----------------
async def handle_mqtt_event(topic: str, payload_text: str):
    global state, current_print_name, previous_e
    try:
        payload = json.loads(payload_text) if payload_text else {}
    except Exception:
        logging.exception("Invalid JSON payload on topic %s: %s", topic, payload_text)
        payload = {}

    logging.info("MQTT event %s -> %s", topic, payload)

    if topic == "octoPrint/event/PrintStarted":
        # store name, set printing, send mesh reset
        name = payload.get("name")
        current_print_name = name
        state = "printing"
        previous_e = None
        await broadcast_json({"type": "mesh", "reset": True})
        logging.info("State -> printing (name=%s)", name)
        return

    if topic == "octoPrint/event/PositionUpdate":
        # if state != "printing":
        #     # ignore position updates when not printing
        #     return
        # expected fields: x,y,z,e
        # javascript visualization code expects in meters
        x = payload.get("x")/1000
        y = payload.get("y")/1000
        z = payload.get("z")/1000
        e = payload.get("e")/1000
        try:
            # convert numeric-like strings to float if needed
            e_val = 0 if e is None else float(e)
        except Exception:
            e_val = 0
        # determine forwarded e boolean
        e_bool = False if e_val < 0 else True
        msg = {"type": "positionUpdate", "x": x, "y": y, "z": z, "e": e_bool}
        await broadcast_json(msg)
        return

    if topic == "octoPrint/event/PrintFailed":
        # go to idle
        state = "idle"
        current_print_name = None
        previous_e = None
        logging.info("State -> idle (print failed)")
        return

    if topic == "octoPrint/event/PrintDone":
        state = "idle"
        current_print_name = None
        previous_e = None
        logging.info("State -> idle (print done)")
        return

    if topic == "octoPrint/event/PrintPaused":
        # payload contains position object
        pos = payload.get("position") or {}
        px = pos.get("x")/1000
        py = pos.get("y")/1000
        pz = pos.get("z")/1000
        state = "paused"
        # set e True in this message
        msg = {"type": "positionUpdate", "x": px, "y": py, "z": pz, "e": True}
        await broadcast_json(msg)
        logging.info("State -> paused")
        return

    if topic == "octoPrint/event/PrintResumed" or topic == "octoPrint/event/PrintResumed":
        # resume printing
        if state == "paused":
            state = "printing"
            logging.info("State -> printing (resumed)")
        return

    if topic == "octoPrint/event/PrintCancelled":
        pos = payload.get("position") or {}
        px = pos.get("x")/1000
        py = pos.get("y")/1000
        pz = pos.get("z")/1000
        # send position with e True and go idle
        msg = {"type": "positionUpdate", "x": px, "y": py, "z": pz, "e": True}
        await broadcast_json(msg)
        state = "idle"
        current_print_name = None
        previous_e = None
        logging.info("State -> idle (cancelled)")
        return


# ---------------- Main asyncio loop ----------------
async def mqtt_consumer_loop(queue: asyncio.Queue):
    while True:
        topic, payload_text = await queue.get()
        try:
            await handle_mqtt_event(topic, payload_text)
        except Exception:
            logging.exception("Error handling MQTT event %s", topic)


async def main():
    global mqtt_event_queue
    mqtt_event_queue = asyncio.Queue()

    # start MQTT client in background thread
    client = mqtt.Client(userdata={})
    # provide asyncio loop and queue in userdata so callback can access
    client._userdata = {"loop": asyncio.get_running_loop(), "queue": mqtt_event_queue}
    client.user_data_set(client._userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    # start websocket server
    ws_server = await websockets.serve(ws_handler, WS_HOST, WS_PORT)
    logging.info("Websocket server listening on ws://%s:%d", WS_HOST, WS_PORT)

    # run mqtt consumer task
    consumer_task = asyncio.create_task(mqtt_consumer_loop(mqtt_event_queue))

    # run forever
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        consumer_task.cancel()
        client.loop_stop()
        ws_server.close()
        await ws_server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down")
