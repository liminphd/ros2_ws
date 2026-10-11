#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import Path as RosPath
from geometry_msgs.msg import PoseStamped

CSV = Path.home() / "ros2_ws/logs/full_coverage/safe_coverage_route.csv"

class CoverageViewer(Node):
    def __init__(self):
        super().__init__("safe_coverage_rviz_viewer")

        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.publisher = self.create_publisher(
            RosPath, "/greenhouse/full_coverage_path", qos
        )

        self.path = RosPath()
        self.path.header.frame_id = "map"

        with CSV.open() as f:
            rows = csv.DictReader(f)
            for row in rows:
                yaw = float(row["yaw_rad"])

                p = PoseStamped()
                p.header.frame_id = "map"
                p.pose.position.x = float(row["x"])
                p.pose.position.y = float(row["y"])
                p.pose.orientation.z = math.sin(yaw / 2)
                p.pose.orientation.w = math.cos(yaw / 2)

                self.path.poses.append(p)

        self.timer = self.create_timer(2.0, self.publish_path)
        self.publish_path()

        self.get_logger().info(
            f"Coverage path loaded: {len(self.path.poses)} poses"
        )

    def publish_path(self):
        stamp = self.get_clock().now().to_msg()
        self.path.header.stamp = stamp
        for p in self.path.poses:
            p.header.stamp = stamp
        self.publisher.publish(self.path)

def main():
    rclpy.init()
    node = CoverageViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()
