import rclpy
from rclpy.node import Node


class ParameterDemo(Node):

    def __init__(self):
        super().__init__('parameter_demo')

        self.declare_parameter('robot_name', 'ROS2_Robot')

        robot_name = self.get_parameter(
            'robot_name'
        ).value

        self.get_logger().info(
            f'Robot Name: {robot_name}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = ParameterDemo()

    rclpy.spin_once(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()