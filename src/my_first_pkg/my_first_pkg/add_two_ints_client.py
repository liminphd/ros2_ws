import sys

import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class AddTwoIntsClient(Node):

    def __init__(self):
        super().__init__('add_two_ints_client')

        self.client = self.create_client(
            AddTwoInts,
            'add_two_ints'
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for service...')

        self.request = AddTwoInts.Request()

    def send_request(self, a, b):
        self.request.a = a
        self.request.b = b
        self.future = self.client.call_async(self.request)
        return self.future
def main(args=None):
    rclpy.init(args=args)

    client_node = AddTwoIntsClient()

    future = client_node.send_request(
        int(sys.argv[1]),
        int(sys.argv[2])
    )

    rclpy.spin_until_future_complete(client_node, future)

    response = future.result()

    client_node.get_logger().info(
        f'Result: {response.sum}'
    )

    client_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()   