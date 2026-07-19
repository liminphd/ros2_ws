import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_share = get_package_share_directory('cspc_lidar')

    params_file = os.path.join(
        package_share,
        'params',
        'cspc_lidar.yaml'
    )

    rviz_config = os.path.join(
        package_share,
        'rviz',
        'rviz.rviz'
    )

    lidar_node = Node(
        package='cspc_lidar',
        executable='cspc_lidar',
        name='cspc_lidar',
        output='screen',
        parameters=[params_file]
    )

    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_static_tf',
        arguments=[
            '--x', '0',
            '--y', '0',
            '--z', '0',
            '--roll', '0',
            '--pitch', '0',
            '--yaw', '0',
            '--frame-id', 'base_link',
            '--child-frame-id', 'laser_link'
        ],
        output='screen'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=[
            '-d',
            rviz_config
        ],
        output='screen'
    )

    return LaunchDescription([
        lidar_node,
        static_tf_node,
        rviz_node
    ])