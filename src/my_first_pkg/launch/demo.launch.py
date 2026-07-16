from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'publisher_name',
            default_value='robot_publisher'
        ),

        DeclareLaunchArgument(
            'subscriber_name',
            default_value='robot_subscriber'
        ),

        Node(
            package='my_first_pkg',
            executable='publisher',
            name=LaunchConfiguration('publisher_name')
        ),

        Node(
            package='my_first_pkg',
            executable='subscriber',
            name=LaunchConfiguration('subscriber_name')
        ),

        Node(
            package='my_first_pkg',
            executable='move_robot_action_server',
            name='action_server'
        ),
    ])