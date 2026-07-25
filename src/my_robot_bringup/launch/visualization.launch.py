import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    rviz_config = os.path.join(
        get_package_share_directory("my_robot_description"),
        "rviz",
        "robot.rviz"
    )

    clean_ld_library_path = ":".join(
        path
        for path in os.environ.get("LD_LIBRARY_PATH", "").split(":")
        if path and not path.startswith("/snap/")
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        additional_env={
            "LD_LIBRARY_PATH": clean_ld_library_path
        },
        output="screen"
    )

    return LaunchDescription([
        rviz_node
    ])