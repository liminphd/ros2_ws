import time

import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import MoveRobot


class MoveRobotActionServer(Node):

	def __init__(self):
		super().__init__('move_robot_action_server')

		self._callback_group = ReentrantCallbackGroup()

		self._action_server = ActionServer(
			self,
			MoveRobot,
			'move_robot',
			execute_callback=self.execute_callback,
			cancel_callback=self.cancel_callback,
			callback_group=self._callback_group,
		)

	def cancel_callback(self, goal_handle):
		self.get_logger().info('Received cancel request')
		return CancelResponse.ACCEPT

	def execute_callback(self, goal_handle):
		target_distance = goal_handle.request.distance
		feedback_msg = MoveRobot.Feedback()

		for current_distance in range(1, target_distance + 1):
			if goal_handle.is_cancel_requested:
				self.get_logger().info('Goal canceled')

				goal_handle.canceled()

				result = MoveRobot.Result()
				result.success = False
				return result

			feedback_msg.current_distance = current_distance
			goal_handle.publish_feedback(feedback_msg)

			self.get_logger().info(
				f'Current distance: {current_distance}'
			)

			time.sleep(1.0)

		goal_handle.succeed()

		result = MoveRobot.Result()
		result.success = True
		return result


def main(args=None):
	rclpy.init(args=args)

	node = MoveRobotActionServer()

	executor = MultiThreadedExecutor(num_threads=2)
	executor.add_node(node)

	try:
		executor.spin()
	except KeyboardInterrupt:
		pass
	finally:
		executor.shutdown()
		node.destroy_node()
		rclpy.shutdown()


if __name__ == '__main__':
	main()