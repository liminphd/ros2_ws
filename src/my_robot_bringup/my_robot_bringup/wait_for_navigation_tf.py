#!/usr/bin/env python3

import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener


class NavigationTfWaiter(Node):
    """Exit successfully only after the TF chain required by Nav2 is ready."""

    def __init__(self):
        super().__init__("wait_for_navigation_tf")

        self.declare_parameter("check_period", 0.2)
        self.declare_parameter("stable_duration", 1.0)
        self.declare_parameter("log_period", 5.0)

        self.check_period = float(
            self.get_parameter("check_period").value
        )
        self.stable_duration = float(
            self.get_parameter("stable_duration").value
        )
        self.log_period = float(
            self.get_parameter("log_period").value
        )

        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)

    def wait(self):
        self.get_logger().info(
            "Waiting for Nav2 TF prerequisites: "
            "map -> odom and odom -> base_link"
        )

        ready_since = None
        last_log = 0.0

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=self.check_period)

            now = time.monotonic()

            map_to_odom = self.buffer.can_transform(
                "map",
                "odom",
                rclpy.time.Time(),
                timeout=Duration(seconds=0.0),
            )

            odom_to_base = self.buffer.can_transform(
                "odom",
                "base_link",
                rclpy.time.Time(),
                timeout=Duration(seconds=0.0),
            )

            if map_to_odom and odom_to_base:
                if ready_since is None:
                    ready_since = now
                    self.get_logger().info(
                        "Required TF chain detected; checking stability."
                    )

                if now - ready_since >= self.stable_duration:
                    self.get_logger().info(
                        "Nav2 TF prerequisites are ready."
                    )
                    return
            else:
                ready_since = None

                if now - last_log >= self.log_period:
                    self.get_logger().info(
                        "Still waiting: "
                        f"map->odom={map_to_odom}, "
                        f"odom->base_link={odom_to_base}"
                    )
                    last_log = now


def main(args=None):
    rclpy.init(args=args)
    node = NavigationTfWaiter()
    success = False

    try:
        node.wait()
        success = True
    except KeyboardInterrupt:
        node.get_logger().info(
            "TF readiness wait interrupted; Nav2 must not start."
        )
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
