import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def include_launch(package_name, launch_file, condition):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(package_name),
                "launch",
                launch_file,
            )
        ),
        condition=IfCondition(condition),
    )


def generate_launch_description():
    use_description = LaunchConfiguration("use_description")
    use_sensors = LaunchConfiguration("use_sensors")
    use_base_feedback = LaunchConfiguration("use_base_feedback")
    use_localization = LaunchConfiguration("use_localization")
    use_perception = LaunchConfiguration("use_perception")
    use_rviz = LaunchConfiguration("use_rviz")

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_description",
            default_value="true",
            description="Start robot_state_publisher and static robot TF.",
        ),
        DeclareLaunchArgument(
            "use_sensors",
            default_value="true",
            description="Start the ROS 2 sensor stack.",
        ),
        DeclareLaunchArgument(
            "use_base_feedback",
            default_value="true",
            description="Start read-only AMIGA motor RPM receiver and wheel odometry.",
        ),
        DeclareLaunchArgument(
            "use_localization",
            default_value="true",
            description="Start the local EKF.",
        ),
        DeclareLaunchArgument(
            "use_perception",
            default_value="true",
            description="Start front/rear OAK depth perception.",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start RViz.",
        ),

        include_launch(
            "my_robot_bringup",
            "description.launch.py",
            use_description,
        ),
        include_launch(
            "my_robot_bringup",
            "sensors.launch.py",
            use_sensors,
        ),
        include_launch(
            "amiga_base_interface",
            "base_interface.launch.py",
            use_base_feedback,
        ),
        include_launch(
            "my_robot_bringup",
            "local_localization.launch.py",
            use_localization,
        ),
        include_launch(
            "my_robot_bringup",
            "perception.launch.py",
            use_perception,
        ),
        include_launch(
            "my_robot_bringup",
            "visualization.launch.py",
            use_rviz,
        ),
    ])
