#!/usr/bin/env python3

import csv
import math
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as RosPath


class TrajectoryRecorder(Node):
    def __init__(self):
        super().__init__('amiga_trajectory_recorder')

        output_dir = Path.home() / 'ros2_ws/logs/trajectories'
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = datetime.now().strftime('amiga_%Y%m%d_%H%M%S.csv')
        self.filepath = output_dir / filename

        self.file = open(self.filepath, 'w', newline='', buffering=1)
        self.writer = csv.writer(self.file)
        self.writer.writerow(['sim_time', 'x', 'y', 'z', 'yaw_rad'])

        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.pub = self.create_publisher(
            RosPath, '/amiga/actual_path', qos
        )

        self.sub = self.create_subscription(
            PoseStamped,
            '/gazebo/amiga/ground_truth',
            self.callback,
            10
        )

        self.path = RosPath()
        self.path.header.frame_id = 'map'

        self.last_xy = None
        self.timer = self.create_timer(1.0, self.publish_path)

        self.get_logger().info(
            f'Trajectory recording to: {self.filepath}'
        )

    def callback(self, msg):
        x = msg.pose.position.x
        y = msg.pose.position.y

        # Store a point when the robot has moved at least 2 cm.
        if self.last_xy is not None:
            if math.hypot(
                x - self.last_xy[0],
                y - self.last_xy[1]
            ) < 0.02:
                return

        self.last_xy = (x, y)

        q = msg.pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

        stamp = msg.header.stamp
        sim_time = stamp.sec + stamp.nanosec * 1e-9

        self.writer.writerow([
            f'{sim_time:.3f}',
            f'{x:.5f}',
            f'{y:.5f}',
            f'{msg.pose.position.z:.5f}',
            f'{yaw:.6f}'
        ])

        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose

        self.path.poses.append(pose)

    def publish_path(self):
        if not self.path.poses:
            return

        self.path.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.path)

    def destroy_node(self):
        self.file.close()
        super().destroy_node()


def main():
    rclpy.init()
    node = TrajectoryRecorder()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
