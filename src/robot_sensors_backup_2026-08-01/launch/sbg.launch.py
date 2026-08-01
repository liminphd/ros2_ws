import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_sensors')

    sbg_config = os.path.join(
        package_share,
        'config',
        'sbg',
        'sbg_device.yaml',
    )

    sbg_device_node = Node(
        package='sbg_driver',
        executable='sbg_device',
        name='sbg_device',
        output='screen',
        parameters=[sbg_config],
    )

    return LaunchDescription([
        sbg_device_node,
    ])
