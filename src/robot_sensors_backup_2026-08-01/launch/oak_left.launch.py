import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    robot_sensors_share = get_package_share_directory('robot_sensors')
    depthai_share = get_package_share_directory('depthai_ros_driver_v3')

    params_file = os.path.join(
        robot_sensors_share,
        'config',
        'oak',
        'left_camera.yaml',
    )

    oak0_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                depthai_share,
                'launch',
                'driver.launch.py',
            )
        ),
        launch_arguments={
            'name': 'oak0',
            'namespace': '',
            'parent_frame': 'base_link',
            'params_file': params_file,
            'use_rviz': 'false',
            'publish_tf_from_calibration': 'true',
            'pointcloud.enable': 'false',
        }.items(),
    )

    return LaunchDescription([
        oak0_launch,
    ])