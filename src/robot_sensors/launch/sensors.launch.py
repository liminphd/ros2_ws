from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    package_share = get_package_share_directory("robot_sensors")

    def include_launch(filename):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(package_share, "launch", filename)
            )
        )

    velodyne_launch = include_launch("velodyne.launch.py")
    sbg_launch = include_launch("sbg.launch.py")

    oak_front_launch = TimerAction(
        period=2.0,
        actions=[
            include_launch("oak_front.launch.py")
        ],
    )

    oak_rear_launch = TimerAction(
        period=15.0,
        actions=[
            include_launch("oak_rear.launch.py")
        ],
    )

    imu_covariance_node = Node(
        package="robot_sensors",
        executable="imu_covariance_node",
        name="imu_covariance_node",
        output="screen",
        parameters=[{
            "input_topic": "/imu/data",
            "output_topic": "/imu/data_cov",
            "gyro_z_variance": 1.0e-6,
        }],
    )

    return LaunchDescription([
        velodyne_launch,
        sbg_launch,
        imu_covariance_node,
        oak_front_launch,
        oak_rear_launch,
    ])
