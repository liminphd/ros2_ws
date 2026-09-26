import asyncio
import json
import struct
import time

import cv2
import depthai as dai
import websockets

MXID = "14442C10A1B3E6D200"
HOST = "0.0.0.0"
PORT = 8766

OUT_W = 640
OUT_H = 400
FPS = 30


def make_pipeline():
    pipeline = dai.Pipeline()

    left = pipeline.create(dai.node.MonoCamera)
    right = pipeline.create(dai.node.MonoCamera)
    stereo = pipeline.create(dai.node.StereoDepth)
    xout = pipeline.create(dai.node.XLinkOut)

    left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    right.setBoardSocket(dai.CameraBoardSocket.CAM_C)

    left.setResolution(
        dai.MonoCameraProperties.SensorResolution.THE_800_P
    )
    right.setResolution(
        dai.MonoCameraProperties.SensorResolution.THE_800_P
    )

    left.setFps(FPS)
    right.setFps(FPS)

    stereo.setDefaultProfilePreset(
        dai.node.StereoDepth.PresetMode.HIGH_DENSITY
    )
    stereo.setLeftRightCheck(True)

    left.out.link(stereo.left)
    right.out.link(stereo.right)

    xout.setStreamName("depth")
    stereo.depth.link(xout.input)

    return pipeline


def find_rear():
    devices = dai.Device.getAllAvailableDevices()

    for info in devices:
        if info.getMxId() == MXID:
            return info

    raise RuntimeError("Rear OAK not found: " + MXID)


async def main():
    info = find_rear()
    pipeline = make_pipeline()

    print("Opening REAR OAK:", info.getMxId(), info.name)

    with dai.Device(pipeline, info) as device:
        q = device.getOutputQueue(
            "depth",
            maxSize=2,
            blocking=False
        )

        clients = set()
        frame_count = 0
        byte_count = 0
        t_stats = time.monotonic()

        async def handler(ws):
            clients.add(ws)
            print("Client connected:", ws.remote_address)

            try:
                await ws.wait_closed()
            finally:
                clients.discard(ws)
                print("Client disconnected")

        async with websockets.serve(
            handler,
            HOST,
            PORT,
            max_size=None,
            compression=None
        ):
            print(f"Depth server: ws://{HOST}:{PORT}")
            print(f"Output: {OUT_W}x{OUT_H} uint16 PNG")

            while True:
                msg = q.tryGet()

                if msg is None:
                    await asyncio.sleep(0.001)
                    continue

                depth = msg.getFrame()

                depth_small = cv2.resize(
                    depth,
                    (OUT_W, OUT_H),
                    interpolation=cv2.INTER_NEAREST
                )

                ok, encoded = cv2.imencode(
                    ".png",
                    depth_small,
                    [cv2.IMWRITE_PNG_COMPRESSION, 1]
                )

                if not ok:
                    continue

                metadata = {
                    "timestamp_ns": time.time_ns(),
                    "width": OUT_W,
                    "height": OUT_H,
                    "encoding": "16UC1",
                    "unit": "mm",
                    "format": "png",
                    "frame_id": "rear_camera_depth_optical_frame",
                }

                header = json.dumps(
                    metadata,
                    separators=(",", ":")
                ).encode("utf-8")

                packet = (
                    struct.pack("!I", len(header))
                    + header
                    + encoded.tobytes()
                )

                frame_count += 1
                byte_count += len(packet)

                dead = []

                for ws in list(clients):
                    try:
                        await ws.send(packet)
                    except Exception:
                        dead.append(ws)

                for ws in dead:
                    clients.discard(ws)

                now = time.monotonic()

                if now - t_stats >= 5.0:
                    dt = now - t_stats
                    print(
                        "frames=%.1f Hz clients=%d output=%.2f Mbps"
                        % (
                            frame_count / dt,
                            len(clients),
                            byte_count * 8.0 / dt / 1e6,
                        )
                    )

                    frame_count = 0
                    byte_count = 0
                    t_stats = now


if __name__ == "__main__":
    asyncio.run(main())
