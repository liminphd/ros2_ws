#!/usr/bin/env python3

import math
import socket
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class FarmngCmdVelBridge(Node):
    """
    ROS 2 /cmd_vel -> Farm-ng Brain TCP Nexus relay.

    Data path:

        ROS 2 /cmd_vel
              |
              v
        farmng_cmd_vel_bridge.py
              |
              | TCP
              v
        10.95.76.1:15432
              |
              v
        ~/nexus_relay.py
              |
              v
        Farm-ng Nexus Teleop

    Relay protocol:

        Motion:
            v_axis,h_axis\\n

        Stop:
            STOP\\n

    Validated mapping:

        ROS linear.x
            -> v_axis = 2.0 * linear.x

        ROS angular.z
            -> h_axis = -angular.z

    Important:

        The Brain relay performs TeleopActivate before each command.

        STOP causes the Brain relay to issue an explicit
        TeleopDeactivate through the official Nexus API.
    """

    def __init__(self):
        super().__init__('farmng_cmd_vel_bridge')

        # ------------------------------------------------------------
        # Parameters
        # ------------------------------------------------------------

        self.declare_parameter(
            'relay_host',
            '10.95.76.1'
        )

        self.declare_parameter(
            'relay_port',
            15432
        )

        self.declare_parameter(
            'cmd_vel_topic',
            '/cmd_vel'
        )

        # Start conservatively.
        #
        # linear.x = 0.30 m/s
        # -> v_axis = 0.60
        #
        # 0.60 has already been tested directly through the relay.
        self.declare_parameter(
            'max_linear_mps',
            0.30
        )

        # ROS angular velocity limit.
        self.declare_parameter(
            'max_angular_rps',
            0.60
        )

        # Final Farm-ng axis safety limits.
        self.declare_parameter(
            'max_v_axis',
            0.60
        )

        self.declare_parameter(
            'max_h_axis',
            0.60
        )

        # If /cmd_vel disappears, stop the vehicle.
        self.declare_parameter(
            'cmd_timeout_sec',
            0.50
        )

        # Same rate as the smooth direct Python test.
        self.declare_parameter(
            'send_rate_hz',
            20.0
        )

        # TCP connection timeout.
        self.declare_parameter(
            'connect_timeout_sec',
            2.0
        )

        # Small deadband to avoid noise creating motion sessions.
        self.declare_parameter(
            'linear_deadband',
            0.001
        )

        self.declare_parameter(
            'angular_deadband',
            0.001
        )

        # ------------------------------------------------------------
        # Read parameters
        # ------------------------------------------------------------

        self.relay_host = (
            self.get_parameter('relay_host')
            .get_parameter_value()
            .string_value
        )

        self.relay_port = (
            self.get_parameter('relay_port')
            .get_parameter_value()
            .integer_value
        )

        self.cmd_vel_topic = (
            self.get_parameter('cmd_vel_topic')
            .get_parameter_value()
            .string_value
        )

        self.max_linear = (
            self.get_parameter('max_linear_mps')
            .get_parameter_value()
            .double_value
        )

        self.max_angular = (
            self.get_parameter('max_angular_rps')
            .get_parameter_value()
            .double_value
        )

        self.max_v_axis = (
            self.get_parameter('max_v_axis')
            .get_parameter_value()
            .double_value
        )

        self.max_h_axis = (
            self.get_parameter('max_h_axis')
            .get_parameter_value()
            .double_value
        )

        self.cmd_timeout = (
            self.get_parameter('cmd_timeout_sec')
            .get_parameter_value()
            .double_value
        )

        self.send_rate = (
            self.get_parameter('send_rate_hz')
            .get_parameter_value()
            .double_value
        )

        self.connect_timeout = (
            self.get_parameter('connect_timeout_sec')
            .get_parameter_value()
            .double_value
        )

        self.linear_deadband = (
            self.get_parameter('linear_deadband')
            .get_parameter_value()
            .double_value
        )

        self.angular_deadband = (
            self.get_parameter('angular_deadband')
            .get_parameter_value()
            .double_value
        )

        # ------------------------------------------------------------
        # Shared command state
        # ------------------------------------------------------------

        self._lock = threading.Lock()

        self._linear = 0.0
        self._angular = 0.0

        self._last_cmd_time = 0.0

        self._shutdown_requested = False

        # TCP socket owned by worker thread.
        self._sock = None

        # True only after at least one motion command has been sent.
        self._motion_active = False

        # ------------------------------------------------------------
        # ROS subscription
        # ------------------------------------------------------------

        self.subscription = self.create_subscription(
            Twist,
            self.cmd_vel_topic,
            self.cmd_vel_callback,
            10
        )

        # ------------------------------------------------------------
        # TCP worker
        # ------------------------------------------------------------

        self._worker_thread = threading.Thread(
            target=self._worker_main,
            daemon=True
        )

        self._worker_thread.start()

        # ------------------------------------------------------------
        # Startup information
        # ------------------------------------------------------------

        self.get_logger().info(
            'Farm-ng TCP cmd_vel bridge started'
        )

        self.get_logger().info(
            f'  topic       : {self.cmd_vel_topic}'
        )

        self.get_logger().info(
            f'  relay       : {self.relay_host}:{self.relay_port}'
        )

        self.get_logger().info(
            f'  linear max  : +/-{self.max_linear:.3f} m/s'
        )

        self.get_logger().info(
            f'  angular max : +/-{self.max_angular:.3f} rad/s'
        )

        self.get_logger().info(
            f'  v_axis max  : +/-{self.max_v_axis:.2f}'
        )

        self.get_logger().info(
            f'  h_axis max  : +/-{self.max_h_axis:.2f}'
        )

        self.get_logger().info(
            f'  send rate   : {self.send_rate:.1f} Hz'
        )

        self.get_logger().info(
            f'  timeout     : {self.cmd_timeout:.2f} s'
        )

        self.get_logger().info(
            '  STOP        : explicit Nexus TeleopDeactivate'
        )

    # ================================================================
    # Utility
    # ================================================================

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    # ================================================================
    # ROS callback
    # ================================================================

    def cmd_vel_callback(self, msg: Twist):
        linear = float(msg.linear.x)
        angular = float(msg.angular.z)

        if (
            not math.isfinite(linear)
            or not math.isfinite(angular)
        ):
            self.get_logger().warning(
                'Ignoring non-finite /cmd_vel'
            )
            return

        linear = self._clamp(
            linear,
            -self.max_linear,
            self.max_linear
        )

        angular = self._clamp(
            angular,
            -self.max_angular,
            self.max_angular
        )

        if abs(linear) < self.linear_deadband:
            linear = 0.0

        if abs(angular) < self.angular_deadband:
            angular = 0.0

        with self._lock:
            self._linear = linear
            self._angular = angular
            self._last_cmd_time = time.monotonic()

    # ================================================================
    # Command state
    # ================================================================

    def _get_command(self):
        now = time.monotonic()

        with self._lock:
            linear = self._linear
            angular = self._angular
            last_cmd_time = self._last_cmd_time

        if last_cmd_time == 0.0:
            return 0.0, 0.0, False

        if (now - last_cmd_time) > self.cmd_timeout:
            return 0.0, 0.0, False

        return linear, angular, True

    # ================================================================
    # ROS -> Farm-ng mapping
    # ================================================================

    def linear_to_v_axis(self, linear_mps):
        """
        Experimentally validated:

            ROS linear.x = +0.10 m/s
                ->
            Farm-ng v_axis = +0.20

        Therefore:

            v_axis = 2.0 * linear.x
        """

        axis = 2.0 * linear_mps

        return self._clamp(
            axis,
            -self.max_v_axis,
            self.max_v_axis
        )

    def angular_to_h_axis(self, angular_rps):
        """
        ROS convention:

            angular.z > 0
                -> left turn

        Farm-ng validated convention:

            h_axis < 0
                -> left turn

            h_axis > 0
                -> right turn

        Therefore:

            h_axis = -angular.z
        """

        axis = -angular_rps

        return self._clamp(
            axis,
            -self.max_h_axis,
            self.max_h_axis
        )

    # ================================================================
    # TCP
    # ================================================================

    def _connect(self):
        if self._sock is not None:
            return True

        try:
            self.get_logger().info(
                f'Connecting to Brain relay '
                f'{self.relay_host}:{self.relay_port}'
            )

            sock = socket.create_connection(
                (
                    self.relay_host,
                    self.relay_port
                ),
                timeout=self.connect_timeout
            )

            # We only use sendall().
            # Remove the short connection timeout after connection.
            sock.settimeout(None)

            self._sock = sock

            self.get_logger().info(
                'Brain relay connected'
            )

            return True

        except Exception as exc:
            self._sock = None

            self.get_logger().error(
                f'Brain relay connection failed: {exc}'
            )

            return False

    def _close_socket(self):
        sock = self._sock

        self._sock = None

        if sock is None:
            return

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        try:
            sock.close()
        except Exception:
            pass

    def _send_line(self, text):
        if self._sock is None:
            raise RuntimeError(
                'TCP relay socket is not connected'
            )

        payload = (
            text.rstrip('\n') + '\n'
        ).encode('ascii')

        self._sock.sendall(payload)

    def _send_motion(self, v_axis, h_axis):
        command = (
            f'{v_axis:.3f},{h_axis:.3f}'
        )

        self._send_line(command)

    def _send_stop(self, reason):
        """
        Relay interprets STOP as:

            TeleopDeactivateRequest()

        through the official Farm-ng Nexus API.
        """

        if self._sock is None:
            self._motion_active = False
            return

        try:
            self._send_line('STOP')

            self.get_logger().info(
                f'STOP sent [{reason}]'
            )

        except Exception as exc:
            self.get_logger().warning(
                f'STOP send failed [{reason}]: {exc}'
            )

        finally:
            self._motion_active = False

    # ================================================================
    # Worker
    # ================================================================

    def _worker_main(self):
        period = (
            1.0 / self.send_rate
            if self.send_rate > 0.0
            else 0.05
        )

        next_tick = time.monotonic()

        while (
            not self._shutdown_requested
            and rclpy.ok()
        ):
            linear, angular, fresh = self._get_command()

            moving = (
                fresh
                and (
                    abs(linear) >= self.linear_deadband
                    or
                    abs(angular) >= self.angular_deadband
                )
            )

            # --------------------------------------------------------
            # Motion
            # --------------------------------------------------------

            if moving:
                if not self._connect():
                    time.sleep(0.5)
                    next_tick = time.monotonic()
                    continue

                v_axis = self.linear_to_v_axis(
                    linear
                )

                h_axis = self.angular_to_h_axis(
                    angular
                )

                try:
                    self._send_motion(
                        v_axis,
                        h_axis
                    )

                    self._motion_active = True

                except Exception as exc:
                    self.get_logger().error(
                        f'Motion send failed: {exc}'
                    )

                    # Socket is no longer trustworthy.
                    self._close_socket()

                    self._motion_active = False

                    time.sleep(0.25)

            # --------------------------------------------------------
            # Stop / timeout / zero command
            # --------------------------------------------------------

            else:
                if self._motion_active:
                    reason = (
                        'zero-command'
                        if fresh
                        else 'cmd-timeout'
                    )

                    self._send_stop(
                        reason
                    )

                    # End this Teleop TCP session cleanly.
                    self._close_socket()

                elif self._sock is not None:
                    # No motion is active.
                    # Do not keep an unnecessary idle TCP connection.
                    self._close_socket()

            # --------------------------------------------------------
            # Monotonic 20 Hz scheduling
            # --------------------------------------------------------

            next_tick += period

            sleep_time = (
                next_tick - time.monotonic()
            )

            if sleep_time > 0.0:
                time.sleep(sleep_time)

            else:
                # If delayed badly, reset instead of trying to catch up.
                next_tick = time.monotonic()

        # ============================================================
        # Shutdown safety
        # ============================================================

        if self._motion_active:
            self._send_stop(
                'bridge-shutdown'
            )

        self._close_socket()

    # ================================================================
    # Shutdown
    # ================================================================

    def stop(self):
        self.get_logger().info(
            'Stopping Farm-ng TCP cmd_vel bridge'
        )

        self._shutdown_requested = True

        with self._lock:
            self._linear = 0.0
            self._angular = 0.0
            self._last_cmd_time = 0.0


def main(args=None):
    rclpy.init(args=args)

    node = FarmngCmdVelBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.stop()

        if (
            node._worker_thread is not None
            and node._worker_thread.is_alive()
        ):
            node._worker_thread.join(
                timeout=2.0
            )

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()