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

    return LaunchDescription([
        velodyne_driver_node,
        velodyne_transform_node,
        velodyne_laserscan_node,
    ])