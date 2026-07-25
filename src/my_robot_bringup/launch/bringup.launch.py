import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    bringup_dir = get_package_share_directory("my_robot_bringup")

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

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "description.launch.py")
        )
    )

    sensors_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "sensors.launch.py")
        ),
        launch_arguments={
            "use_lidar": use_lidar,
            "use_camera": use_camera,
        }.items()
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "localization.launch.py")
        )
    )

    visualization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "visualization.launch.py")
        )
    )

    return LaunchDescription([
        declare_use_lidar,
        declare_use_camera,
        description_launch,
        sensors_launch,
        localization_launch,
        visualization_launch,
    ])