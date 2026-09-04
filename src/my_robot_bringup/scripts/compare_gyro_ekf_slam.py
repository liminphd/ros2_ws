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


def relative_motion(start, end):
    dx = end['x'] - start['x']
    dy = end['y'] - start['y']
    y0 = start['yaw']

    forward = math.cos(y0)*dx + math.sin(y0)*dy
    lateral = -math.sin(y0)*dx + math.cos(y0)*dy
    dyaw = wrap(end['yaw'] - start['yaw'])

    return forward, lateral, math.degrees(dyaw)


class Recorder(Node):
    def __init__(self):
        super().__init__('gyro_ekf_slam_compare')

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
        self.imu_samples = 0

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
        self.imu_samples += 1

    def pose(self, target, source):
        deadline = time.time() + 10.0

        while time.time() < deadline:
            try:
                tf = self.buf.lookup_transform(
                    target,
                    source,
                    rclpy.time.Time(),
                    timeout=Duration(seconds=0.2)
                )

                t = tf.transform.translation
                q = tf.transform.rotation

                return {
                    'x': t.x,
                    'y': t.y,
                    'yaw': yaw_from_q(q)
                }

            except Exception:
                time.sleep(0.05)

        raise RuntimeError(
            f'Cannot get TF {target} <- {source}'
        )


rclpy.init()
node = Recorder()

thread = threading.Thread(
    target=rclpy.spin,
    args=(node,),
    daemon=True
)
thread.start()

try:
    print('\nRobot must be stationary and aligned.')
    input('Press ENTER to START... ')

    start_odom = node.pose('odom', 'base_link')
    start_map  = node.pose('map', 'base_link')

    node.gyro_integral = 0.0
    node.imu_samples = 0
    node.last_stamp = None
    node.recording = True

    print('\nRECORDING...')
    print('Drive forward about 5 m.')
    input('Stop robot, then immediately press ENTER to END... ')

    node.recording = False

    end_odom = node.pose('odom', 'base_link')
    end_map  = node.pose('map', 'base_link')

    ef, el, ey = relative_motion(start_odom, end_odom)
    sf, sl, sy = relative_motion(start_map, end_map)

    gyro_deg = math.degrees(node.gyro_integral)

    print('\n===== GYRO =====')
    print(f'IMU samples       = {node.imu_samples}')
    print(f'Gyro integrated   = {gyro_deg:+.3f} deg')

    print('\n===== EKF / ODOM =====')
    print(f'forward           = {ef:+.3f} m')
    print(f'lateral           = {el:+.3f} m  (+ = left)')
    print(f'd_yaw             = {ey:+.3f} deg')

    print('\n===== SLAM / MAP =====')
    print(f'forward           = {sf:+.3f} m')
    print(f'lateral           = {sl:+.3f} m  (+ = left)')
    print(f'd_yaw             = {sy:+.3f} deg')

    print('\n===== DIFFERENCES =====')
    print(f'EKF yaw - gyro    = {ey-gyro_deg:+.3f} deg')
    print(f'SLAM yaw - gyro   = {sy-gyro_deg:+.3f} deg')
    print(f'SLAM - EKF lateral= {sl-el:+.3f} m')

finally:
    node.destroy_node()
    rclpy.shutdown()
