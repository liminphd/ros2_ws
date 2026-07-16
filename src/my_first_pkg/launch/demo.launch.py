import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory('my_first_pkg'),
        'config',
        'robot_params.yaml',
    )
    return LaunchDescription([
        Node(
            package='my_first_pkg',
            executable='publisher',
            name='robot_publisher',
            output='screen',
        ),

        Node(
            package='my_first_pkg',
            executable='subscriber',
            name='robot_subscriber',
            output='screen',
        ),

        Node(
            package='my_first_pkg',
            executable='move_robot_action_server',
            name='action_server',
            output='screen',
        ),

        Node(
            package='my_first_pkg',
            executable='parameter_demo',
            name='parameter_demo',
            parameters=[config_file],
            output='screen',
        ),
    ])