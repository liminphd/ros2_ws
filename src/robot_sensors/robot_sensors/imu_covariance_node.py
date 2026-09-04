#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuCovarianceNode(Node):

    def __init__(self):
        super().__init__('imu_covariance_node')

        self.declare_parameter('input_topic', '/imu/data')
        self.declare_parameter('output_topic', '/imu/data_cov')
        self.declare_parameter('gyro_z_variance', 1.0e-6)
        self.declare_parameter('gyro_bias_calibration_duration', 10.0)

        input_topic = self.get_parameter(
            'input_topic'
        ).get_parameter_value().string_value

        output_topic = self.get_parameter(
            'output_topic'
        ).get_parameter_value().string_value

        self.gyro_z_variance = self.get_parameter(
            'gyro_z_variance'
        ).get_parameter_value().double_value

        self.calibration_duration = self.get_parameter(
            'gyro_bias_calibration_duration'
        ).get_parameter_value().double_value

        self.publisher = self.create_publisher(
            Imu,
            output_topic,
            10,
        )

        self.subscription = self.create_subscription(
            Imu,
            input_topic,
            self.imu_callback,
            10,
        )

        self.calibration_start_time = None
        self.bias_samples = []
        self.gyro_z_bias = 0.0
        self.bias_calibrated = False

        self.get_logger().info(
            f'IMU covariance wrapper: '
            f'{input_topic} -> {output_topic}, '
            f'gyro_z_variance={self.gyro_z_variance:.3e}'
        )

        self.get_logger().info(
            f'Gyro Z bias calibration enabled for '
            f'{self.calibration_duration:.1f} s. '
            f'Keep robot stationary during startup.'
        )

    def imu_callback(self, msg):

        if self.calibration_start_time is None:
            self.calibration_start_time = time.monotonic()

        if not self.bias_calibrated:
            self.bias_samples.append(
                msg.angular_velocity.z
            )

            elapsed = (
                time.monotonic()
                - self.calibration_start_time
            )

            if elapsed >= self.calibration_duration:
                if self.bias_samples:
                    self.gyro_z_bias = (
                        sum(self.bias_samples)
                        / len(self.bias_samples)
                    )

                    self.bias_calibrated = True

                    self.get_logger().info(
                        f'Gyro Z bias calibrated: '
                        f'{self.gyro_z_bias:.9e} rad/s '
                        f'from {len(self.bias_samples)} samples'
                    )

        out = Imu()

        out.header = msg.header

        out.orientation = msg.orientation
        out.orientation_covariance = list(
            msg.orientation_covariance
        )

        out.angular_velocity = msg.angular_velocity

        if self.bias_calibrated:
            out.angular_velocity.z = (
                msg.angular_velocity.z
                - self.gyro_z_bias
            )

        out.angular_velocity_covariance = list(
            msg.angular_velocity_covariance
        )

        out.linear_acceleration = msg.linear_acceleration
        out.linear_acceleration_covariance = list(
            msg.linear_acceleration_covariance
        )

        # Fixed baseline covariance for SBG gyro z.
        # Static measurement on 2026-08-27:
        # variance ~= 1.21e-7 (rad/s)^2.
        # Use a conservative fixed baseline of 1.0e-6.
        out.angular_velocity_covariance[8] = (
            self.gyro_z_variance
        )

        self.publisher.publish(out)


def main(args=None):
    rclpy.init(args=args)

    node = ImuCovarianceNode()

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
