from launch import LaunchDescription
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    bringup_share = get_package_share_directory("my_robot_bringup")

    ekf_config_file = os.path.join(
        bringup_share,
        "config",
        "ekf.yaml"
    )

    navsat_config_file = os.path.join(
        bringup_share,
        "config",
        "navsat.yaml"
    )

    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[ekf_config_file]
    )

    navsat_node = Node(
        package="robot_localization",
        executable="navsat_transform_node",
        name="navsat_transform_node",
        output="screen",
        parameters=[navsat_config_file],
        remappings=[
            ("imu", "/imu/data"),
            ("gps/fix", "/imu/nav_sat_fix"),
            ("odometry/filtered", "/odometry/global"),
            ("odometry/gps", "/odometry/gps"),
            ("gps/filtered", "/gps/filtered"),
        ]
    )

    return LaunchDescription([
        ekf_node,
        navsat_node
    ])
