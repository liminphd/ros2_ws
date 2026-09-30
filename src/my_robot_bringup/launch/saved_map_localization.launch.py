from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    bringup_share = get_package_share_directory("my_robot_bringup")

    map_yaml = LaunchConfiguration("map")
    use_sim_time = LaunchConfiguration("use_sim_time")

    amcl_config = os.path.join(
        bringup_share,
        "config",
        "amcl.yaml",
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{
            "yaml_filename": map_yaml,
            "topic_name": "map",
            "frame_id": "map",
            "use_sim_time": use_sim_time,
        }],
    )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[
            amcl_config,
            {"use_sim_time": use_sim_time},
        ],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_saved_map_localization",
        output="screen",
        parameters=[{
            "autostart": True,
            "node_names": ["map_server", "amcl"],
            "use_sim_time": use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "map",
            default_value="",
            description="Full path to the saved map YAML file",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock",
        ),
        map_server,
        amcl,
        lifecycle_manager,
    ])
