import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node


def generate_launch_description():
    robot_description_path = os.path.join(
        get_package_share_directory('my_robot_description'),
        'urdf',
        'robot.urdf.xacro'
    )

    robot_description = {
        'robot_description': Command([
            'xacro ',
            robot_description_path
        ])
    }

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    return LaunchDescription([
        joint_state_publisher_node,
        robot_state_publisher_node
    ])