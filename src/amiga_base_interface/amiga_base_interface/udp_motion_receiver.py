import json
import socket

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped


class UdpMotionReceiver(Node):

    def __init__(self):
        super().__init__('amiga_udp_motion_receiver')

        self.declare_parameter('udp_port', 5005)
        port = self.get_parameter('udp_port').value

        self.publisher_ = self.create_publisher(
            TwistStamped,
            '/amiga/motion_estimation',
            10
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.setblocking(False)

        self.timer = self.create_timer(0.01, self.receive_data)

        self.get_logger().info(
            f'Listening for AMIGA motion estimation on UDP port {port}'
        )

    def receive_data(self):
        try:
            data, addr = self.sock.recvfrom(4096)
        except BlockingIOError:
            return

        try:
            payload = json.loads(data.decode('utf-8'))

            linear = float(payload['linear_velocity'])
            angular = float(payload['angular_velocity'])

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.get_logger().warning(f'Invalid UDP packet: {e}')
            return

        msg = TwistStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        msg.twist.linear.x = linear
        msg.twist.angular.z = angular

        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = UdpMotionReceiver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
