import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_sensors')

    driver_config = os.path.join(
        package_share,
        'config',
        'velodyne',
        'driver.yaml',
    )

    transform_config = os.path.join(
        package_share,
        'config',
        'velodyne',
        'transform.yaml',
    )

    calibration_file = os.path.join(
        package_share,
        'config',
        'velodyne',
        'VLP16db.yaml',
    )

    velodyne_driver_node = Node(
        package='velodyne_driver',
        executable='velodyne_driver_node',
        name='velodyne_driver_node',
        output='screen',
        parameters=[driver_config],
    )

    velodyne_transform_node = Node(
        package='velodyne_pointcloud',
        executable='velodyne_transform_node',
        name='velodyne_transform_node',
        output='screen',
        parameters=[
            transform_config,
            {
                'calibration': calibration_file,
            },
        ],
    )

    velodyne_laserscan_node = Node(
        package='velodyne_laserscan',
        executable='velodyne_laserscan_node',
        name='velodyne_laserscan_node',
        output='screen',
    )

    scan_multi_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        remappings=[
            ('cloud_in', '/velodyne_points'),
            ('scan', '/scan_multi_raw'),
        ],
        parameters=[{
            'target_frame': 'base_link',
            'transform_tolerance': 0.05,
            'min_height': -0.50,
            'max_height': 0.30,
            'angle_min': -1.827875,
            'angle_max': 1.827875,
            'angle_increment': 0.007,
            'scan_time': 0.1,
            'range_min': 0.9,
            'range_max': 20.0,
            'use_inf': True,
            'inf_epsilon': 1.0,
        }],
    )


    scan_self_mask_node = Node(
        package='robot_sensors',
        executable='scan_self_mask',
        name='scan_self_mask',
        output='screen',
    )

    return LaunchDescription([
        velodyne_driver_node,
        velodyne_transform_node,
        velodyne_laserscan_node,
        scan_multi_node,
        scan_self_mask_node,
    ])