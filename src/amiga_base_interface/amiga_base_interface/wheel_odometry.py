import math

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from std_msgs.msg import Int32MultiArray


class WheelOdometry(Node):

    def __init__(self):
        super().__init__('amiga_wheel_odometry')

        self.declare_parameter('wheel_radius', 0.20626480624709637)
        self.declare_parameter('gear_ratio', 30.0)
        self.declare_parameter('track_width', 1.229)

        self.wheel_radius = float(
            self.get_parameter('wheel_radius').value
        )
        self.gear_ratio = float(
            self.get_parameter('gear_ratio').value
        )
        self.track_width = float(
            self.get_parameter('track_width').value
        )

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.last_time = None

        self.publisher_ = self.create_publisher(
            Odometry,
            '/wheel/odometry',
            10
        )

        self.subscription = self.create_subscription(
            Int32MultiArray,
            '/amiga/motor_rpm',
            self.motor_callback,
            10
        )

        self.get_logger().info(
            'AMIGA wheel odometry started: '
            f'radius={self.wheel_radius:.6f} m, '
            f'gear_ratio={self.gear_ratio:.3f}, '
            f'track_width={self.track_width:.3f} m'
        )

    def motor_callback(self, msg):
        if len(msg.data) != 4:
            self.get_logger().warning(
                'Expected 4 motor RPM values'
            )
            return

        a, b, c, d = msg.data

        k = (
            2.0 * math.pi * self.wheel_radius
            / (60.0 * self.gear_ratio)
        )

        # AMIGA motor orientation:
        # A = right rear
        # B = left rear (sign inverted)
        # C = left front (sign inverted)
        # D = right front
        rr = a * k
        rl = -b * k
        fl = -c * k
        fr = d * k

        left = 0.5 * (rl + fl)
        right = 0.5 * (rr + fr)

        linear = 0.5 * (left + right)
        angular = (right - left) / self.track_width

        now = self.get_clock().now()

        if self.last_time is None:
            self.last_time = now
            return

        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        if dt <= 0.0 or dt > 0.5:
            return

        self.x += linear * math.cos(self.yaw) * dt
        self.y += linear * math.sin(self.yaw) * dt
        self.yaw += angular * dt

        msg_out = Odometry()

        msg_out.header.stamp = now.to_msg()
        msg_out.header.frame_id = 'odom'
        msg_out.child_frame_id = 'base_link'

        msg_out.pose.pose.position.x = self.x
        msg_out.pose.pose.position.y = self.y
        msg_out.pose.pose.position.z = 0.0

        half_yaw = 0.5 * self.yaw

        msg_out.pose.pose.orientation.z = math.sin(half_yaw)
        msg_out.pose.pose.orientation.w = math.cos(half_yaw)

        msg_out.twist.twist.linear.x = linear
        msg_out.twist.twist.angular.z = angular

        # Conservative covariance for skid-steer wheel odometry.
        # Values are intentionally non-zero because wheel slip is expected.
        msg_out.pose.covariance[0] = 0.10
        msg_out.pose.covariance[7] = 0.10
        msg_out.pose.covariance[35] = 0.20

        msg_out.twist.covariance[0] = 0.04
        msg_out.twist.covariance[7] = 0.10
        msg_out.twist.covariance[35] = 0.08

        self.publisher_.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)

    node = WheelOdometry()

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
