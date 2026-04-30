#!/usr/bin/env python3
"""
Moonraker/Klipper MQTT -> WebSocket bridge.

Dependencies:
    pip install paho-mqtt websockets

Run:
    python klipper_mqtt_to_ws_server.py

Environment variables:
    MQTT_BROKER              (default: broker)
    MQTT_PORT                (default: 1883)
    WS_HOST                  (default: 0.0.0.0)
    WS_PORT                  (default: 9090)
    MOONRAKER_INSTANCE_NAME  (default: hostname)

WebSocket output interface is compatible with the existing OctoPrint bridge:
    {"type":"mesh","reset":true}
    {"type":"positionUpdate","x":<m>,"y":<m>,"z":<m>,"e":<bool>}
"""

import asyncio
import json
import logging
import os
import socket
from typing import Any, Dict, Optional, Set

import paho.mqtt.client as mqtt
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

MQTT_BROKER = "broker" # don't forget to change to broker for the dockerized version.
MQTT_PORT = 1883
WS_HOST = "0.0.0.0"
WS_PORT = 9090
#INSTANCE_NAME = os.getenv("MOONRAKER_INSTANCE_NAME", socket.gethostname())
INSTANCE_NAME = 'moonraker-virtual-printer'

STATUS_TOPIC = f"{INSTANCE_NAME}/klipper/status"
SPLIT_STATUS_TOPIC = f"{INSTANCE_NAME}/klipper/state/#"
SPLIT_STATUS_TOPIC_PREFIX = f"{INSTANCE_NAME}/klipper/state/"
API_RESPONSE_TOPIC = f"{INSTANCE_NAME}/moonraker/api/response"

# Bridge state
bridge_state = "idle"  # idle | printing | paused
current_print_name: Optional[str] = None
last_position_m = {"x": 0.0, "y": 0.0, "z": 0.0}
last_e_mm: Optional[float] = None

mqtt_event_queue: Optional[asyncio.Queue] = None
connected_websockets: Set[Any] = set()


def _mm_to_m(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value) / 1000.0
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def broadcast_json(obj: Dict[str, Any]) -> None:
    if not connected_websockets:
        return
    text = json.dumps(obj)
    stale = []
    for ws in list(connected_websockets):
        try:
            await ws.send(text)
        except Exception:
            stale.append(ws)
    for ws in stale:
        connected_websockets.discard(ws)


def on_connect(client, userdata, flags, rc, properties=None):
    del client, flags, properties
    if rc != 0:
        logging.error("Failed to connect to MQTT broker: rc=%s", rc)
        return

    logging.info("Connected to MQTT broker at %s:%s", MQTT_BROKER, MQTT_PORT)
    topics = [STATUS_TOPIC, SPLIT_STATUS_TOPIC, API_RESPONSE_TOPIC]
    for topic in topics:
        userdata["client"].subscribe(topic)
        logging.info("Subscribed to MQTT topic: %s", topic)


def on_message(client, userdata, msg):
    del client
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
        loop.call_soon_threadsafe(queue.put_nowait, (msg.topic, payload))
    except Exception:
        logging.exception("Failed to enqueue MQTT message")


async def ws_handler(websocket):
    connected_websockets.add(websocket)
    logging.info("WebSocket client connected. Total clients: %d", len(connected_websockets))
    try:
        async for _ in websocket:
            pass
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_websockets.discard(websocket)
        logging.info("WebSocket client disconnected. Total clients: %d", len(connected_websockets))


async def _set_idle(reason: str) -> None:
    global bridge_state, current_print_name, last_e_mm
    bridge_state = "idle"
    current_print_name = None
    last_e_mm = None
    logging.info("State -> idle (%s)", reason)


async def _handle_print_stats(print_stats: Dict[str, Any]) -> None:
    global bridge_state, current_print_name, last_e_mm

    new_state = str(print_stats.get("state", "")).lower()
    filename = print_stats.get("filename")

    if filename:
        current_print_name = str(filename)

    if new_state == "printing":
        if bridge_state != "printing":
            if bridge_state == "paused":
                bridge_state = "printing"
                logging.info("State -> printing (resumed)")
            else:
                bridge_state = "printing"
                last_e_mm = None
                await broadcast_json({"type": "mesh", "reset": True})
                logging.info("State -> printing (started, file=%s)", current_print_name)
        return

    if new_state == "paused":
        bridge_state = "paused"
        await broadcast_json(
            {
                "type": "positionUpdate",
                "x": last_position_m["x"],
                "y": last_position_m["y"],
                "z": last_position_m["z"],
                "e": False,
            }
        )
        logging.info("State -> paused")
        return

    if new_state in {"complete", "error", "standby", "cancelled"}:
        await _set_idle(new_state)


async def _handle_motion_report(motion_report: Dict[str, Any]) -> None:
    global last_e_mm

    # Klipper usually reports [x, y, z, e] in millimeters as live_position.
    live_position = motion_report.get("live_position")
    if not isinstance(live_position, (list, tuple)) or len(live_position) < 3:
        return

    x = _mm_to_m(live_position[0])
    y = _mm_to_m(live_position[1])
    z = _mm_to_m(live_position[2])
    e_mm = live_position[3] if len(live_position) > 3 else 0.0

    if x is None or y is None or z is None:
        return

    last_position_m["x"] = x
    last_position_m["y"] = y
    last_position_m["z"] = z

    current_e_mm = _safe_float(e_mm, default=0.0)
    if last_e_mm is None:
        e_bool = False
    else:
        # Extrusion is active only when the E axis increases (ignores retracts/travel).
        e_bool = (current_e_mm - last_e_mm) > 1e-6
    last_e_mm = current_e_mm

    await broadcast_json({"type": "positionUpdate", "x": x, "y": y, "z": z, "e": e_bool})


async def _handle_status_update(status_data: Dict[str, Any]) -> None:
    # `status_data` may be the direct status object or wrapped in {"status": ...}.
    status = status_data.get("status") if isinstance(status_data.get("status"), dict) else status_data

    if not isinstance(status, dict):
        return

    motion_report = status.get("motion_report")
    if isinstance(motion_report, dict):
        await _handle_motion_report(motion_report)

    print_stats = status.get("print_stats")
    if isinstance(print_stats, dict):
        await _handle_print_stats(print_stats)


async def _handle_api_notification(payload: Dict[str, Any]) -> None:
    method = payload.get("method")
    params = payload.get("params") or []

    if method == "notify_status_update" and isinstance(params, list) and params:
        first = params[0]
        if isinstance(first, dict):
            await _handle_status_update(first)
        return

    if method in {"notify_klippy_shutdown", "notify_klippy_disconnected"}:
        await _set_idle(method)


def _split_status_topic_to_status_update(topic: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not topic.startswith(SPLIT_STATUS_TOPIC_PREFIX):
        return None

    subtopic = topic[len(SPLIT_STATUS_TOPIC_PREFIX) :]
    parts = subtopic.split("/")
    if len(parts) < 2:
        return None

    object_name = parts[0]
    state_name = "/".join(parts[1:])

    # For split status Moonraker publishes payloads as {"eventtime": ..., "value": ...}.
    if not isinstance(payload, dict) or "value" not in payload:
        return None

    return {object_name: {state_name: payload.get("value")}}


async def handle_mqtt_event(topic: str, payload_text: str) -> None:
    try:
        payload = json.loads(payload_text) if payload_text else {}
    except Exception:
        logging.exception("Invalid JSON payload on topic %s", topic)
        return

    if topic == STATUS_TOPIC and isinstance(payload, dict):
        await _handle_status_update(payload)
        return

    split_status_update = _split_status_topic_to_status_update(topic, payload)
    if split_status_update is not None:
        await _handle_status_update(split_status_update)
        return

    if topic == API_RESPONSE_TOPIC and isinstance(payload, dict):
        # Moonraker publishes JSON-RPC responses and notifications to this topic.
        # Notifications can be identified by their `method` field.
        if "method" in payload:
            await _handle_api_notification(payload)


async def mqtt_consumer_loop(queue: asyncio.Queue) -> None:
    while True:
        topic, payload_text = await queue.get()
        try:
            await handle_mqtt_event(topic, payload_text)
        except Exception:
            logging.exception("Error handling MQTT event %s", topic)


async def main() -> None:
    global mqtt_event_queue
    mqtt_event_queue = asyncio.Queue()

    client_userdata = {}
    client = mqtt.Client(userdata=client_userdata)
    client_userdata["client"] = client
    client_userdata["loop"] = asyncio.get_running_loop()
    client_userdata["queue"] = mqtt_event_queue

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    ws_server = await websockets.serve(ws_handler, WS_HOST, WS_PORT)
    logging.info("WebSocket server listening on ws://%s:%d", WS_HOST, WS_PORT)

    consumer_task = asyncio.create_task(mqtt_consumer_loop(mqtt_event_queue))

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
