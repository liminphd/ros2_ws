#!/usr/bin/env python3

import math
import os
import threading
import time

import rclpy
from rclpy.node import Node as RosNode
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster

from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V


def yaw_from_quaternion(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    )


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class GazeboGroundTruthLocalizer(RosNode):

    def __init__(self):
        super().__init__('amiga_ground_truth_localizer')

        

        self.lock = threading.Lock()
        self.ground_truth = None
        self.odom = None
        self.last_ground_truth = None
        self.last_odom = None
        self.last_log = 0.0

        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/gazebo/amiga/ground_truth',
            10
        )

        self.tf_pub = TransformBroadcaster(self)

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.on_odom,
            10
        )

        self.gz_node = GzNode()

        topic = (
            '/world/greenhouse_realistic/'
            'dynamic_pose/info'
        )

        result = self.gz_node.subscribe(
            Pose_V,
            topic,
            self.on_gazebo_pose
        )

        if result is False:
            raise RuntimeError('Gazebo subscription failed')

        self.timer = self.create_timer(
            0.05,
            self.publish_localization
        )

        self.get_logger().info(
            'Ground truth localizer started'
        )

    def on_gazebo_pose(self, msg):
        for pose in msg.pose:
            if pose.name != 'amiga':
                continue

            data = (
                pose.position.x,
                pose.position.y,
                pose.position.z,
                pose.orientation.x,
                pose.orientation.y,
                pose.orientation.z,
                pose.orientation.w,
            )

            with self.lock:
                self.ground_truth = data
                self.last_ground_truth = time.monotonic()

            break

    def on_odom(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation

        data = (
            p.x,
            p.y,
            p.z,
            yaw_from_quaternion(q)
        )

        with self.lock:
            self.odom = data
            self.last_odom = time.monotonic()

    def publish_localization(self):
        with self.lock:
            gt = self.ground_truth
            odom = self.odom
            gt_time = self.last_ground_truth
            odom_time = self.last_odom

        if gt is None or odom is None:
            return

        now = time.monotonic()

        # Do not publish TF using stale positions.
        if now - gt_time > 1.0 or now - odom_time > 1.0:
            return

        gx, gy, gz, qx, qy, qz, qw = gt
        ox, oy, oz, oyaw = odom

        class Q:
            pass

        q = Q()
        q.x, q.y, q.z, q.w = qx, qy, qz, qw

        gyaw = yaw_from_quaternion(q)

        # T_map_odom = T_map_base * inverse(T_odom_base)
        myaw = normalize_angle(gyaw - oyaw)

        c = math.cos(myaw)
        s = math.sin(myaw)

        mx = gx - (c * ox - s * oy)
        my = gy - (s * ox + c * oy)
        mz = gz - oz

        stamp = self.get_clock().now().to_msg()

        # Independent Gazebo ground truth topic.
        truth = PoseStamped()
        truth.header.stamp = stamp
        truth.header.frame_id = 'map'

        truth.pose.position.x = gx
        truth.pose.position.y = gy
        truth.pose.position.z = gz

        truth.pose.orientation.x = qx
        truth.pose.orientation.y = qy
        truth.pose.orientation.z = qz
        truth.pose.orientation.w = qw

        self.pose_pub.publish(truth)

        # Publish ONLY map -> amiga/odom.
        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = 'map'
        tf.child_frame_id = 'amiga/odom'

        tf.transform.translation.x = mx
        tf.transform.translation.y = my
        tf.transform.translation.z = mz

        tf.transform.rotation.x = 0.0
        tf.transform.rotation.y = 0.0
        tf.transform.rotation.z = math.sin(myaw / 2.0)
        tf.transform.rotation.w = math.cos(myaw / 2.0)

        self.tf_pub.sendTransform(tf)

        if now - self.last_log > 5.0:
            self.get_logger().info(
                f'GT=({gx:.3f}, {gy:.3f}, '
                f'{math.degrees(gyaw):.1f}deg) '
                f'map->odom=({mx:.3f}, {my:.3f}, '
                f'{math.degrees(myaw):.1f}deg)'
            )
            self.last_log = now


def main():
    rclpy.init()
    node = None

    try:
        node = GazeboGroundTruthLocalizer()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
