import asyncio
import websockets
import json
import math

async def send_cylinder(websocket):
    await asyncio.sleep(3)  # wait before extrusion begins
    # --- move to start position ---
    start_pos = {"x": 0.125, "y": 0.075, "z": 0.0}
    duration = 2.0
    steps = 120  # 60 Hz * 2 seconds
    for i in range(steps + 1):
        t = i / steps
        x = t * start_pos["x"]
        y = t * start_pos["y"]
        z = t * start_pos["z"]
        await websocket.send(json.dumps({"type": "position", "x": x, "y": y, "z": z}))
        await asyncio.sleep(duration / steps)

    # await asyncio.sleep(0.1)  # wait before extrusion begins

    # --- start extrusion ---
    start_extrusion = {
        "type": "extrusion",
        "extruding": True,
        "extrusionWidth": 0.0045,
        "extrusionDepth": 0.01
    }
    await websocket.send(json.dumps(start_extrusion))
    await asyncio.sleep(0.2)

    # --- generate cylindrical extrusion path ---
    diameter = 0.1
    radius = diameter / 2
    center_x = 0.075
    center_y = 0.075
    z_step = 0.003
    circle_steps = 120
    theta = 0.0
    z = 0.0

    while z <= 0.125:
        x = center_x + radius * math.cos(theta)
        y = center_y + radius * math.sin(theta)
        pos_packet = {"type": "position", "x": x, "y": y, "z": z}
        await websocket.send(json.dumps(pos_packet))
        await asyncio.sleep(1 / 60)
        theta += 2 * math.pi / circle_steps
        if theta >= 2 * math.pi:
            theta -= 2 * math.pi
            z += z_step

    # --- stop extrusion ---
    stop_extrusion = {"type": "extrusion", "extruding": False}
    await websocket.send(json.dumps(stop_extrusion))

async def main():
    async with websockets.serve(send_cylinder, "0.0.0.0", 9090):
        print("WebSocket server running at ws://0.0.0.0:9090")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
