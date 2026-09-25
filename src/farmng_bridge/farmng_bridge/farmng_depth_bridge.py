#!/usr/bin/env python3

import asyncio
import json
import struct
import threading
import time

import cv2
import numpy as np
import websockets

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge


class FarmngDepthBridge(Node):

    def __init__(self):
        super().__init__('farmng_depth_bridge')

        # ------------------------------------------------------------
        # Parameters
        # Defaults preserve the already-tested FRONT OAK configuration.
        # The same executable can be launched again with different
        # parameters for rear / future cameras.
        # ------------------------------------------------------------

        self.declare_parameter(
            'uri',
            'ws://10.95.76.1:8765'
        )

        self.declare_parameter(
            'topic',
            '/camera/front/depth/image_raw'
        )

        self.declare_parameter(
            'camera_info_topic',
            '/camera/front/depth/camera_info'
        )

        self.declare_parameter(
            'frame_id',
            'front_camera_depth_optical_frame'
        )

        # Front OAK rectified depth intrinsics at 640x400.
        # These defaults preserve the previously validated OAK0 setup.
        self.declare_parameter('fx', 283.016220095)
        self.declare_parameter('fy', 283.016220095)
        self.declare_parameter('cx', 321.574234010)
        self.declare_parameter('cy', 204.766273500)

        self.uri = self.get_parameter('uri').value
        self.topic = self.get_parameter('topic').value
        self.camera_info_topic = (
            self.get_parameter('camera_info_topic').value
        )
        self.frame_id = self.get_parameter('frame_id').value

        self.fx = float(self.get_parameter('fx').value)
        self.fy = float(self.get_parameter('fy').value)
        self.cx = float(self.get_parameter('cx').value)
        self.cy = float(self.get_parameter('cy').value)

        # ------------------------------------------------------------
        # ROS publishers
        # ------------------------------------------------------------

        self.publisher = self.create_publisher(
            Image,
            self.topic,
            10
        )

        self.camera_info_publisher = self.create_publisher(
            CameraInfo,
            self.camera_info_topic,
            10
        )

        self.bridge = CvBridge()

        self.frame_count = 0
        self.t0 = time.monotonic()

        self.get_logger().info(
            f'Connecting to {self.uri}'
        )

        self.get_logger().info(
            f'Publishing image: {self.topic}'
        )

        self.get_logger().info(
            f'Publishing camera info: {self.camera_info_topic}'
        )

        self.get_logger().info(
            f'Frame: {self.frame_id}'
        )

        self.get_logger().info(
            'Intrinsics: '
            f'fx={self.fx:.6f}, '
            f'fy={self.fy:.6f}, '
            f'cx={self.cx:.6f}, '
            f'cy={self.cy:.6f}'
        )

        # WebSocket receive loop runs separately from ROS spin.
        self.thread = threading.Thread(
            target=self.run_async,
            daemon=True
        )
        self.thread.start()

    def run_async(self):
        asyncio.run(self.receive_loop())

    async def receive_loop(self):

        while rclpy.ok():

            try:

                async with websockets.connect(
                    self.uri,
                    max_size=None,
                    compression=None
                ) as ws:

                    self.get_logger().info(
                        'Depth WebSocket connected'
                    )

                    while rclpy.ok():

                        packet = await ws.recv()

                        if not isinstance(packet, bytes):
                            continue

                        if len(packet) < 4:
                            continue

                        header_len = struct.unpack(
                            '!I',
                            packet[:4]
                        )[0]

                        metadata = json.loads(
                            packet[
                                4:4 + header_len
                            ].decode('utf-8')
                        )

                        png = packet[
                            4 + header_len:
                        ]

                        depth = cv2.imdecode(
                            np.frombuffer(
                                png,
                                dtype=np.uint8
                            ),
                            cv2.IMREAD_UNCHANGED
                        )

                        if depth is None:
                            continue

                        if depth.dtype != np.uint16:
                            continue

                        # ------------------------------------------------
                        # Depth Image
                        # ------------------------------------------------

                        msg = self.bridge.cv2_to_imgmsg(
                            depth,
                            encoding='16UC1'
                        )

                        timestamp_ns = int(
                            metadata.get(
                                'timestamp_ns',
                                time.time_ns()
                            )
                        )

                        msg.header.stamp.sec = (
                            timestamp_ns // 1_000_000_000
                        )

                        msg.header.stamp.nanosec = (
                            timestamp_ns % 1_000_000_000
                        )

                        # Normally supplied by Brain server.
                        # Parameter is the fallback.
                        msg.header.frame_id = metadata.get(
                            'frame_id',
                            self.frame_id
                        )

                        # ------------------------------------------------
                        # CameraInfo
                        #
                        # Depth output is rectified, therefore:
                        # D = 0
                        # R = identity
                        # K/P describe the rectified depth image.
                        # ------------------------------------------------

                        camera_info = CameraInfo()

                        camera_info.header = msg.header

                        camera_info.width = depth.shape[1]
                        camera_info.height = depth.shape[0]

                        camera_info.distortion_model = 'plumb_bob'

                        camera_info.d = [
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0
                        ]

                        camera_info.k = [
                            self.fx, 0.0, self.cx,
                            0.0, self.fy, self.cy,
                            0.0, 0.0, 1.0
                        ]

                        camera_info.r = [
                            1.0, 0.0, 0.0,
                            0.0, 1.0, 0.0,
                            0.0, 0.0, 1.0
                        ]

                        camera_info.p = [
                            self.fx, 0.0, self.cx, 0.0,
                            0.0, self.fy, self.cy, 0.0,
                            0.0, 0.0, 1.0, 0.0
                        ]

                        self.publisher.publish(msg)

                        self.camera_info_publisher.publish(
                            camera_info
                        )

                        # ------------------------------------------------
                        # Statistics
                        # ------------------------------------------------

                        self.frame_count += 1

                        now = time.monotonic()

                        if now - self.t0 >= 5.0:

                            fps = (
                                self.frame_count
                                / (now - self.t0)
                            )

                            self.get_logger().info(
                                'depth %.1f Hz, '
                                '%dx%d, %s'
                                % (
                                    fps,
                                    depth.shape[1],
                                    depth.shape[0],
                                    depth.dtype
                                )
                            )

                            self.frame_count = 0
                            self.t0 = now

            except Exception as exc:

                # During normal shutdown the ROS context may already
                # be invalid, so avoid unnecessary logging then.
                if rclpy.ok():
                    self.get_logger().warning(
                        f'Depth connection error: {exc}'
                    )

                    await asyncio.sleep(2.0)


def main(args=None):

    rclpy.init(args=args)

    node = FarmngDepthBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()