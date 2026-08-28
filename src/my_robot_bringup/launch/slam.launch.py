import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    bringup_share = get_package_share_directory(
        "my_robot_bringup"
    )

    slam_config = os.path.join(
        bringup_share,
        "config",
        "slam_toolbox.yaml",
    )

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_config],
    )

    return LaunchDescription([
        slam_node,
    ])
