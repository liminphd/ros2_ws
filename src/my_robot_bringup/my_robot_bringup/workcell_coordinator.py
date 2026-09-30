import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

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

        self.stationary_sub = self.create_subscription(
            Bool,
            '/workcell/base_stationary',
            self.stationary_callback,
            10,
        )

        self.waiting_for_base = False
        self.work_authorized = False
        self.active_workcell_id = ''

        self.get_logger().info('Workcell coordinator started')

    def status_callback(self, msg):
        self.get_logger().info(
            f'Workcell={msg.workcell_id} state={msg.state} '
            f'message={msg.message}'
        )

        if msg.state == WorkcellStatus.STOP_REQUESTED:
            self.waiting_for_base = True
            self.active_workcell_id = msg.workcell_id

            command = WorkcellCommand()
            command.command = WorkcellCommand.STOPPING
            command.workcell_id = msg.workcell_id
            command.message = 'Stop request accepted; waiting for base stationary confirmation'
            self.command_pub.publish(command)

            self.get_logger().info(
                f'STOPPING sent to workcell={msg.workcell_id}'
            )

        elif (
            msg.state == WorkcellStatus.COMPLETED
            and self.work_authorized
            and msg.workcell_id == self.active_workcell_id
        ):
            command = WorkcellCommand()
            command.command = WorkcellCommand.RESUME_ALLOWED
            command.workcell_id = msg.workcell_id
            command.message = 'Work completed; mission resume permitted'
            self.command_pub.publish(command)

            self.get_logger().info(
                f'RESUME_ALLOWED sent to workcell={msg.workcell_id}'
            )

            self.work_authorized = False
            self.waiting_for_base = False
            self.active_workcell_id = ''


    def stationary_callback(self, msg):
        self.get_logger().info(
            f'Base stationary={msg.data}'
        )

        if msg.data and self.waiting_for_base:
            command = WorkcellCommand()
            command.command = WorkcellCommand.BASE_READY
            command.workcell_id = self.active_workcell_id
            command.message = 'Base stationary confirmed; work permitted'
            self.command_pub.publish(command)

            self.get_logger().info(
                f'BASE_READY sent to workcell={self.active_workcell_id}'
            )

            self.waiting_for_base = False
            self.work_authorized = True


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
