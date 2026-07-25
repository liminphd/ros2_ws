import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    use_lidar = LaunchConfiguration("use_lidar")
    use_camera = LaunchConfiguration("use_camera")

    declare_use_lidar = DeclareLaunchArgument(
        "use_lidar",
        default_value="true",
        description="Start the CSPC LiDAR driver"
    )

    declare_use_camera = DeclareLaunchArgument(
        "use_camera",
        default_value="true",
        description="Start the Orbbec Gemini 335 camera driver"
    )

    lidar_node = Node(
        package="cspc_lidar",
        executable="cspc_lidar",
        name="cspc_lidar",
        output="screen",
        condition=IfCondition(use_lidar)
    )

    lidar_static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="lidar_static_tf",
        arguments=[
            "--x", "0",
            "--y", "0",
            "--z", "0",
            "--roll", "0",
            "--pitch", "0",
            "--yaw", "0",
            "--frame-id", "base_link",
            "--child-frame-id", "laser_link"
        ],
        output="screen",
        condition=IfCondition(use_lidar)
    )

    orbbec_launch_file = os.path.join(
        get_package_share_directory("orbbec_camera"),
        "launch",
        "gemini_330_series.launch.py"
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(orbbec_launch_file),
        condition=IfCondition(use_camera)
    )

    return LaunchDescription([
        declare_use_lidar,
        declare_use_camera,
        lidar_node,
        lidar_static_tf_node,
        camera_launch
    ])