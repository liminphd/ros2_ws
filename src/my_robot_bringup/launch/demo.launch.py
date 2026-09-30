import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    AndSubstitution,
    LaunchConfiguration,
    NotSubstitution,
)
from launch_ros.actions import Node


def include_launch(package_name, launch_file, condition):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(package_name),
                "launch",
                launch_file,
            )
        ),
        condition=IfCondition(condition),
    )


def generate_launch_description():
    use_description = LaunchConfiguration("use_description")
    use_sensors = LaunchConfiguration("use_sensors")
    use_base_feedback = LaunchConfiguration("use_base_feedback")
    use_localization = LaunchConfiguration("use_localization")
    use_perception = LaunchConfiguration("use_perception")
    use_rviz = LaunchConfiguration("use_rviz")
    use_slam = LaunchConfiguration("use_slam")
    use_saved_map_localization = LaunchConfiguration(
        "use_saved_map_localization"
    )
    map_yaml = LaunchConfiguration("map")
    use_navigation = LaunchConfiguration("use_navigation")
    use_base_control = LaunchConfiguration("use_base_control")

    saved_map_condition = AndSubstitution(
        use_saved_map_localization,
        NotSubstitution(use_slam),
    )

    saved_map_localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("my_robot_bringup"),
                "launch",
                "saved_map_localization.launch.py",
            )
        ),
        condition=IfCondition(saved_map_condition),
        launch_arguments={"map": map_yaml}.items(),
    )

    navigation_launch = include_launch(
        "my_robot_bringup",
        "navigation.launch.py",
        use_navigation,
    )

    navigation_tf_gate = Node(
        package="my_robot_bringup",
        executable="wait_for_navigation_tf",
        name="wait_for_navigation_tf",
        output="screen",
        condition=IfCondition(use_navigation),
    )

    def start_navigation_if_tf_ready(event, context):
        if event.returncode == 0:
            return [navigation_launch]

        print(
            "[demo.launch] Navigation TF gate exited without readiness; "
            "Nav2 will NOT start."
        )
        return []

    navigation_after_tf = RegisterEventHandler(
        OnProcessExit(
            target_action=navigation_tf_gate,
            on_exit=start_navigation_if_tf_ready,
        ),
        condition=IfCondition(use_navigation),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_description",
            default_value="true",
            description="Start robot_state_publisher and static robot TF.",
        ),
        DeclareLaunchArgument(
            "use_sensors",
            default_value="true",
            description="Start the ROS 2 sensor stack.",
        ),
        DeclareLaunchArgument(
            "use_base_feedback",
            default_value="true",
            description="Start read-only AMIGA motor RPM receiver and wheel odometry.",
        ),
        DeclareLaunchArgument(
            "use_localization",
            default_value="true",
            description="Start the local EKF.",
        ),
        DeclareLaunchArgument(
            "use_perception",
            default_value="true",
            description="Start front/rear OAK depth perception.",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start RViz.",
        ),
        DeclareLaunchArgument(
            "use_slam",
            default_value="false",
            description="Start SLAM Toolbox for online mapping and map-to-odom TF.",
        ),
        DeclareLaunchArgument(
            "use_saved_map_localization",
            default_value="false",
            description=(
                "Start map_server and AMCL for saved-map localization. "
                "Ignored while use_slam is true."
            ),
        ),
        DeclareLaunchArgument(
            "map",
            default_value="",
            description="Full path to the saved map YAML file.",
        ),
        DeclareLaunchArgument(
            "use_navigation",
            default_value="false",
            description="Start Nav2 planning, control, velocity smoothing, and collision monitoring.",
        ),
        DeclareLaunchArgument(
            "use_base_control",
            default_value="false",
            description="Enable the AMIGA actuator command bridge. Requires the Brain Nexus relay.",
        ),

        include_launch(
            "my_robot_bringup",
            "description.launch.py",
            use_description,
        ),
        include_launch(
            "my_robot_bringup",
            "sensors.launch.py",
            use_sensors,
        ),
        include_launch(
            "amiga_base_interface",
            "base_interface.launch.py",
            use_base_feedback,
        ),
        include_launch(
            "my_robot_bringup",
            "local_localization.launch.py",
            use_localization,
        ),
        include_launch(
            "my_robot_bringup",
            "perception.launch.py",
            use_perception,
        ),
        include_launch(
            "my_robot_bringup",
            "visualization.launch.py",
            use_rviz,
        ),
        include_launch(
            "my_robot_bringup",
            "slam.launch.py",
            use_slam,
        ),
        saved_map_localization_launch,
        navigation_tf_gate,
        navigation_after_tf,
        Node(
            package="farmng_bridge",
            executable="farmng_cmd_vel_bridge",
            name="farmng_cmd_vel_bridge",
            output="screen",
            condition=IfCondition(use_base_control),
            parameters=[{
                "cmd_vel_topic": "/cmd_vel",
                "relay_host": "10.95.76.1",
                "relay_port": 15432,
            }],
        ),
    ])
