import json
import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


class UdpMotorReceiver(Node):

    def __init__(self):
        super().__init__('amiga_udp_motor_receiver')

        self.declare_parameter('udp_port', 5006)
        port = self.get_parameter('udp_port').value

        self.publisher_ = self.create_publisher(
            Int32MultiArray,
            '/amiga/motor_rpm',
            10
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.setblocking(False)

        self.timer = self.create_timer(0.01, self.receive_data)

        self.get_logger().info(
            f'Listening for AMIGA motor RPM on UDP port {port}'
        )

    def receive_data(self):
        try:
            data, _ = self.sock.recvfrom(4096)
        except BlockingIOError:
            return

        try:
            payload = json.loads(data.decode('utf-8'))

            motor_a = int(payload['motor_a_rpm'])
            motor_b = int(payload['motor_b_rpm'])
            motor_c = int(payload['motor_c_rpm'])
            motor_d = int(payload['motor_d_rpm'])

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.get_logger().warning(f'Invalid UDP packet: {e}')
            return

        msg = Int32MultiArray()
        msg.data = [motor_a, motor_b, motor_c, motor_d]

        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = UdpMotorReceiver()

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
