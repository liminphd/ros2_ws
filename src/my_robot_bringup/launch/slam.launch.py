import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    bringup_share = get_package_share_directory('my_robot_bringup')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')

    slam_config = os.path.join(
        bringup_share,
        'config',
        'slam_toolbox.yaml'
    )

    official_slam_launch = os.path.join(
        slam_toolbox_share,
        'launch',
        'online_async_launch.py'
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(official_slam_launch),
        launch_arguments={
            'slam_params_file': slam_config,
            'use_sim_time': 'false',
            'autostart': 'true',
            'use_lifecycle_manager': 'false',
        }.items()
    )

    return LaunchDescription([
        slam
    ])
