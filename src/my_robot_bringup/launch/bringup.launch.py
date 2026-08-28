import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def include_launch(package_name, launch_file):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(package_name),
                "launch",
                launch_file,
            )
        )
    )


def generate_launch_description():

    description = include_launch(
        "my_robot_bringup",
        "description.launch.py",
    )

    sensors = include_launch(
        "my_robot_bringup",
        "sensors.launch.py",
    )

    base_interface = include_launch(
        "amiga_base_interface",
        "base_interface.launch.py",
    )

    local_localization = include_launch(
        "my_robot_bringup",
        "local_localization.launch.py",
    )

    return LaunchDescription([
        description,
        sensors,
        base_interface,
        local_localization,
    ])
