import rclpy
from rclpy.node import Node

from my_robot_interfaces.msg import WorkcellCommand
from my_robot_interfaces.msg import WorkcellStatus


class WorkcellCoordinator(Node):
    def __init__(self):
        super().__init__('workcell_coordinator')

        self.command_pub = self.create_publisher(
            WorkcellCommand,
            '/workcell/command',
            10,
        )

        self.status_sub = self.create_subscription(
            WorkcellStatus,
            '/workcell/status',
            self.status_callback,
            10,
        )

        self.get_logger().info('Workcell coordinator started')

    def status_callback(self, msg):
        self.get_logger().info(
            f'Workcell={msg.workcell_id} state={msg.state} '
            f'message={msg.message}'
        )

        if msg.state == WorkcellStatus.STOP_REQUESTED:
            command = WorkcellCommand()
            command.command = WorkcellCommand.STOPPING
            command.workcell_id = msg.workcell_id
            command.message = 'Stop request accepted; waiting for base stationary confirmation'
            self.command_pub.publish(command)

            self.get_logger().info(
                f'STOPPING sent to workcell={msg.workcell_id}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = WorkcellCoordinator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
