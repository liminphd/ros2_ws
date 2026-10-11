#!/usr/bin/env python3

import math
import os

os.environ.setdefault("GZ_PARTITION", "greenhouse_fixed_test")

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from gz.transport13 import Node as GzNode
from gz.msgs10.marker_pb2 import Marker
from gz.msgs10.empty_pb2 import Empty


TRACK_HALF_SPACING = 0.29
TRACK_WIDTH = 0.12
GROUND_Z = 0.035

POINT_STEP = 0.06
SEGMENTS_PER_MARKER = 60


def add_triangle(marker, a, b, c):
    for x, y in (a, b, c):
        p = marker.point.add()
        p.x = x
        p.y = y
        p.z = GROUND_Z


class TireTracks(Node):
    def __init__(self):
        super().__init__("amiga_tire_tracks")

        self.gz = GzNode()
        self.last = {"left": None, "right": None}
        self.chunks = {"left": [], "right": []}
        self.ids = {"left": 0, "right": 0}
        self.dirty = set()

        self.create_subscription(
            PoseStamped,
            "/gazebo/amiga/ground_truth",
            self.on_pose,
            10
        )

        self.create_timer(0.5, self.flush)

        self.get_logger().info(
            "Gazebo tire track visualizer started"
        )

    def wheel_center(self, x, y, yaw, offset):
        return (
            x - math.sin(yaw) * offset,
            y + math.cos(yaw) * offset
        )

    def on_pose(self, msg):
        q = msg.pose.orientation
        yaw = math.atan2(
            2 * (q.w * q.z + q.x * q.y),
            1 - 2 * (q.y * q.y + q.z * q.z)
        )

        x = msg.pose.position.x
        y = msg.pose.position.y

        for side, offset in (
            ("left", TRACK_HALF_SPACING),
            ("right", -TRACK_HALF_SPACING)
        ):
            current = self.wheel_center(x, y, yaw, offset)
            previous = self.last[side]

            if previous is None:
                self.last[side] = current
                continue

            distance = math.dist(current, previous)

            if distance < POINT_STEP:
                continue

            # Avoid drawing a misleading line across a pose jump.
            if distance > 0.6:
                self.last[side] = current
                continue

            dx = current[0] - previous[0]
            dy = current[1] - previous[1]

            nx = -dy / distance * TRACK_WIDTH / 2
            ny = dx / distance * TRACK_WIDTH / 2

            a = (previous[0] + nx, previous[1] + ny)
            b = (previous[0] - nx, previous[1] - ny)
            c = (current[0] + nx, current[1] + ny)
            d = (current[0] - nx, current[1] - ny)

            if len(self.chunks[side]) >= SEGMENTS_PER_MARKER:
                self.flush_side(side)
                self.ids[side] += 1
                self.chunks[side] = []

            self.chunks[side].append((a, b, c, d))
            self.last[side] = current
            self.dirty.add(side)

    def make_marker(self, side):
        marker = Marker()
        marker.ns = "amiga_tire_" + side
        marker.id = self.ids[side]
        marker.action = Marker.ADD_MODIFY
        marker.type = Marker.TRIANGLE_LIST

        marker.pose.orientation.w = 1.0
        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0

        for field in (
            marker.material.ambient,
            marker.material.diffuse
        ):
            field.r = 0.22
            field.g = 0.13
            field.b = 0.07
            field.a = 1.0

        for a, b, c, d in self.chunks[side]:
            add_triangle(marker, a, b, c)
            add_triangle(marker, b, d, c)

        return marker

    def flush_side(self, side):
        if not self.chunks[side]:
            return

        marker = self.make_marker(side)

        try:
            result, _ = self.gz.request(
                "/marker",
                marker,
                Marker,
                Empty,
                1000
            )

            if not result:
                self.get_logger().warning(
                    f"Marker request failed: {side}"
                )

        except Exception as exc:
            self.get_logger().error(str(exc))

    def flush(self):
        for side in tuple(self.dirty):
            self.flush_side(side)

        self.dirty.clear()


def main():
    rclpy.init()
    node = TireTracks()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.flush()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
