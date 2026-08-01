from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    robot_sensors_share = get_package_share_directory('robot_sensors')

    oak0_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                robot_sensors_share,
                'launch',
                'oak_left.launch.py',
            )
        )
    )

    oak1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                robot_sensors_share,
                'launch',
                'oak_right.launch.py',
            )
        )
    )

    return LaunchDescription([
        oak0_launch,
        oak1_launch,
    ])