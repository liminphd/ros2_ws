from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='amiga_base_interface',
            executable='udp_motor_receiver',
            name='amiga_udp_motor_receiver',
            output='screen',
        ),

        Node(
            package='amiga_base_interface',
            executable='wheel_odometry',
            name='amiga_wheel_odometry',
            output='screen',
        ),
    ])
