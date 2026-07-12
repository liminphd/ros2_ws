import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from my_robot_interfaces.action import MoveRobot


class MoveRobotActionClient(Node):

    def __init__(self):
        super().__init__('move_robot_action_client')

        self._action_client = ActionClient(
            self,
            MoveRobot,
            'move_robot'
        )

        self._goal_handle = None
        self._cancel_timer = None

    def send_goal(self, distance):
        goal_msg = MoveRobot.Goal()
        goal_msg.distance = distance

        self._action_client.wait_for_server()

        self.get_logger().info(f'Sending goal: {distance}')

        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

        send_goal_future.add_done_callback(
            self.goal_response_callback
        )

    def goal_response_callback(self, future):
        self._goal_handle = future.result()

        if not self._goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted')

        result_future = self._goal_handle.get_result_async()
        result_future.add_done_callback(
            self.result_callback
        )

        self._cancel_timer = self.create_timer(
            3.0,
            self.cancel_goal
        )

    def feedback_callback(self, feedback_msg):
        current_distance = feedback_msg.feedback.current_distance

        self.get_logger().info(
            f'Feedback: current distance = {current_distance}'
        )

    def cancel_goal(self):
        if self._cancel_timer is not None:
            self._cancel_timer.cancel()

        if self._goal_handle is None:
            return

        self.get_logger().info('Sending cancel request')

        cancel_future = self._goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(
            self.cancel_done_callback
        )

    def cancel_done_callback(self, future):
        cancel_response = future.result()

        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info('Cancel request accepted')
        else:
            self.get_logger().info('Cancel request rejected')

    def result_callback(self, future):
        result = future.result().result

        self.get_logger().info(
            f'Result success: {result.success}'
        )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = MoveRobotActionClient()
    node.send_goal(100)

    rclpy.spin(node)

    node.destroy_node()


if __name__ == '__main__':
    main()