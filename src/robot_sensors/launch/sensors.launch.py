from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    package_share = get_package_share_directory("robot_sensors")

    def include_launch(filename):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    package_share,
                    "launch",
                    filename,
                )
            )
        )

    # ---------------------------------------------------------
    # Velodyne LiDAR
    # ---------------------------------------------------------
    velodyne_launch = include_launch(
        "velodyne.launch.py"
    )

    # ---------------------------------------------------------
    # SBG INS / IMU
    # ---------------------------------------------------------
    sbg_launch = include_launch(
        "sbg.launch.py"
    )

    # ---------------------------------------------------------
    # IMU covariance / gyro bias correction
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Farm-ng camera bridge
    #
    # OAK cameras are owned by the Farm-ng Brain / Furrow Assist.
    # Do NOT launch the old direct DepthAI OAK nodes here.
    #
    # oak/0/mono -> /camera/front/image_raw
    # oak/1/mono -> /camera/rear/image_raw
    # ---------------------------------------------------------
    farmng_camera_bridge = Node(
        package="farmng_bridge",
        executable="farmng_camera_bridge",
        name="farmng_camera_bridge",
        output="screen",
    )

    return LaunchDescription([
        velodyne_launch,
        sbg_launch,
        imu_covariance_node,
        farmng_camera_bridge,
    ])
