#!/usr/bin/env python3

import asyncio
import threading

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Float64, Int32

import websockets
from nexus.nexus_pb2 import Feedback


WS_URI = "ws://10.95.76.1:8008/stream_data_json_ws/filter/state"


class FarmngBridge(Node):

    def __init__(self):
        super().__init__("farmng_bridge")

        # ---------------------------------------------------------
        # ROS2 publishers
        # ---------------------------------------------------------
        self.odom_pub = self.create_publisher(
            Odometry,
            "/farmng/odom",
            10,
        )

        self.navsat_pub = self.create_publisher(
            NavSatFix,
            "/farmng/navsat",
            10,
        )

        self.heading_pub = self.create_publisher(
            Float64,
            "/farmng/heading",
            10,
        )

        # GNSS / RTK quality publishers
        self.carr_soln_pub = self.create_publisher(
            Int32,
            "/farmng/gps/carr_soln_kind",
            10,
        )

        self.correction_kind_pub = self.create_publisher(
            Int32,
            "/farmng/gps/correction_kind",
            10,
        )

        self.h_acc_pub = self.create_publisher(
            Float64,
            "/farmng/gps/horizontal_accuracy",
            10,
        )

        self.v_acc_pub = self.create_publisher(
            Float64,
            "/farmng/gps/vertical_accuracy",
            10,
        )

        # Cache latest GNSS accuracy because not every Feedback message
        # necessarily contains Capabilities.
        self.gps_h_acc = None
        self.gps_v_acc = None

        self.get_logger().info("Farm-ng bridge started")

        # Run websocket client in background thread
        self.thread = threading.Thread(
            target=self.websocket_thread,
            daemon=True,
        )
        self.thread.start()

    def websocket_thread(self):
        asyncio.run(self.websocket_loop())

    async def websocket_loop(self):
        while rclpy.ok():
            try:
                async with websockets.connect(
                    WS_URI,
                    max_size=None,
                ) as ws:

                    self.get_logger().info(
                        "Connected to Farm-ng filter/state"
                    )

                    while rclpy.ok():
                        try:
                            msg = await asyncio.wait_for(
                                ws.recv(),
                                timeout=3.0,
                            )

                        except asyncio.TimeoutError:
                            self.get_logger().warning(
                                "No Farm-ng data for 3 s; reconnecting..."
                            )
                            break

                        if not isinstance(msg, bytes):
                            continue

                        fb = Feedback()
                        fb.ParseFromString(msg)

                        if not fb.HasField("amiga_state"):
                            continue

                        self.publish_state(fb.amiga_state)

            except Exception as e:
                self.get_logger().warning(
                    f"WebSocket error: {e}; reconnecting..."
                )

            if rclpy.ok():
                await asyncio.sleep(1.0)

    def publish_state(self, state):

        now = self.get_clock().now().to_msg()

        # ---------------------------------------------------------
        # Farm-ng capabilities -> GNSS / RTK quality
        # ---------------------------------------------------------
        if state.HasField("capabilities"):
            c = state.capabilities

            # Carrier solution:
            # 0 = no carrier solution
            # 1 = float
            # 2 = fixed
            carr = Int32()
            carr.data = int(c.carr_soln_kind)
            self.carr_soln_pub.publish(carr)

            correction = Int32()
            correction.data = int(c.gps_correction_kind)
            self.correction_kind_pub.publish(correction)

            if c.HasField("gps_horizontal_accuracy"):
                self.gps_h_acc = c.gps_horizontal_accuracy

                h_msg = Float64()
                h_msg.data = float(self.gps_h_acc)
                self.h_acc_pub.publish(h_msg)

            if c.HasField("gps_vertical_accuracy"):
                self.gps_v_acc = c.gps_vertical_accuracy

                v_msg = Float64()
                v_msg.data = float(self.gps_v_acc)
                self.v_acc_pub.publish(v_msg)

        # ---------------------------------------------------------
        # Farm-ng motion estimation -> /farmng/odom
        # ---------------------------------------------------------
        if state.HasField("motion_estimation"):
            m = state.motion_estimation

            odom = Odometry()

            odom.header.stamp = now
            odom.header.frame_id = "farmng_odom"
            odom.child_frame_id = "base_link"

            # Publish only velocity information for now.
            # Position/orientation are intentionally left unset because
            # Farm-ng frame conventions have not yet been fully validated.
            odom.twist.twist.linear.x = m.linear_velocity
            odom.twist.twist.angular.z = m.angular_velocity

            self.odom_pub.publish(odom)

        # ---------------------------------------------------------
        # Farm-ng global pose
        # ---------------------------------------------------------
        if state.HasField("global_pose"):
            g = state.global_pose

            # Heading
            heading = Float64()
            heading.data = g.heading
            self.heading_pub.publish(heading)

            # GNSS position
            if g.HasField("position"):
                fix = NavSatFix()

                fix.header.stamp = now
                fix.header.frame_id = "farmng_gnss"

                fix.status.status = NavSatStatus.STATUS_FIX
                fix.status.service = NavSatStatus.SERVICE_GPS

                fix.latitude = g.position.latitude
                fix.longitude = g.position.longitude
                fix.altitude = g.position.altitude

                # Use cached Farm-ng GNSS accuracy if available.
                if (
                    self.gps_h_acc is not None
                    and self.gps_v_acc is not None
                    and self.gps_h_acc > 0.0
                    and self.gps_v_acc > 0.0
                ):
                    h = self.gps_h_acc
                    v = self.gps_v_acc

                    # Variance = standard deviation^2
                    fix.position_covariance[0] = h * h
                    fix.position_covariance[4] = h * h
                    fix.position_covariance[8] = v * v

                    fix.position_covariance_type = (
                        NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
                    )

                else:
                    fix.position_covariance_type = (
                        NavSatFix.COVARIANCE_TYPE_UNKNOWN
                    )

                self.navsat_pub.publish(fix)


def main():

    rclpy.init()

    node = FarmngBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
