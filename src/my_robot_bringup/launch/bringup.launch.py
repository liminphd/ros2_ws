from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    lidar_node = Node(
        package='cspc_lidar',
        executable='cspc_lidar',
        name='cspc_lidar',
        output='screen'
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
        output='screen'
    )

    return LaunchDescription([
        lidar_node,
        static_tf_node,
        rviz_node
    ])