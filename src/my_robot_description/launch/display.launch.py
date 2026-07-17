import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share = get_package_share_directory(
        'my_robot_description'
    )

    xacro_file = os.path.join(
        package_share,
        'urdf',
        'robot.urdf.xacro',
    )

    rviz_config_file = os.path.join(
        package_share,
        'rviz',
        'robot_camera.rviz',
    )

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            xacro_file,
        ]),
        value_type=str,
    )

    orbbec_share = get_package_share_directory(
        'orbbec_camera'
    )

    camera_launch_file = os.path.join(
        orbbec_share,
        'launch',
        'gemini_330_series.launch.py',
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            camera_launch_file
        ),
        launch_arguments={
            'enable_accel': 'true',
            'enable_gyro': 'true',
            'enable_sync_output_accel_gyro': 'true',
        }.items(),
    )

    return LaunchDescription([
        camera_launch,

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'robot_description': robot_description}
            ],
            output='screen',
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=[
                '-d',
                rviz_config_file,
            ],
            output='screen',
        ),
    ])