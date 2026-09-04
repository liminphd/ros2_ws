import math
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from sensor_msgs.msg import Imu
from tf2_ros import Buffer, TransformListener


def yaw_from_q(q):
    return math.atan2(
        2.0 * (q.w*q.z + q.x*q.y),
        1.0 - 2.0 * (q.y*q.y + q.z*q.z)
    )


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class N(Node):
    def __init__(self):
        super().__init__('yaw_turn_test')

        self.buf = Buffer()
        self.listener = TransformListener(self.buf, self)

        self.create_subscription(
            Imu,
            '/imu/data_cov',
            self.imu_cb,
            50
        )

        self.recording = False
        self.last_stamp = None
        self.gyro_integral = 0.0
        self.samples = 0

    def imu_cb(self, msg):
        if not self.recording:
            return

        stamp = (
            msg.header.stamp.sec +
            msg.header.stamp.nanosec * 1e-9
        )

        if self.last_stamp is not None:
            dt = stamp - self.last_stamp

            if 0.0 < dt < 0.2:
                self.gyro_integral += (
                    msg.angular_velocity.z * dt
                )

        self.last_stamp = stamp
        self.samples += 1

    def get_yaw(self, target, source='base_link'):
        deadline = time.time() + 10.0

        while time.time() < deadline:
            try:
                tf = self.buf.lookup_transform(
                    target,
                    source,
                    rclpy.time.Time(),
                    timeout=Duration(seconds=0.2)
                )

                return yaw_from_q(tf.transform.rotation)

            except Exception:
                time.sleep(0.05)

        raise RuntimeError(
            f'Cannot get TF {target} <- {source}'
        )


rclpy.init()
node = N()

spin_thread = threading.Thread(
    target=rclpy.spin,
    args=(node,)
)
spin_thread.start()

try:
    print('\nRobot stationary.')
    input('Press ENTER to START... ')

    odom_start = node.get_yaw('odom')
    map_start = node.get_yaw('map')

    node.gyro_integral = 0.0
    node.samples = 0
    node.last_stamp = None
    node.recording = True

    print('\nNow rotate robot LEFT or RIGHT.')
    print('Rotate slowly.')
    input('After stopping, press ENTER to END... ')

    node.recording = False

    odom_end = node.get_yaw('odom')
    map_end = node.get_yaw('map')

    ekf_dyaw = math.degrees(
        wrap(odom_end - odom_start)
    )
    slam_dyaw = math.degrees(
        wrap(map_end - map_start)
    )
    gyro_deg = math.degrees(
        node.gyro_integral
    )

    print('\n===== YAW TEST =====')
    print(f'IMU samples     = {node.samples}')
    print(f'Gyro integrated = {gyro_deg:+.3f} deg')
    print(f'EKF d_yaw       = {ekf_dyaw:+.3f} deg')
    print(f'SLAM d_yaw      = {slam_dyaw:+.3f} deg')
    print(f'EKF - gyro      = {ekf_dyaw-gyro_deg:+.3f} deg')
    print(f'SLAM - gyro     = {slam_dyaw-gyro_deg:+.3f} deg')

finally:
    node.recording = False

    if rclpy.ok():
        rclpy.shutdown()

    spin_thread.join(timeout=2.0)
    node.destroy_node()
