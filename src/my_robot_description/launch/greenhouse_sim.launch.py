import os
import subprocess
from pathlib import Path

from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessStart
from launch_ros.actions import Node


PACKAGE = Path(__file__).resolve().parents[1]

WORLD = PACKAGE / "worlds/greenhouse_realistic.sdf"
GENERATOR = PACKAGE / "scripts/generate_amiga_sim.py"
MODEL = PACKAGE / "urdf/amiga_sim_fixed.sdf"


def generate_model(context, *args, **kwargs):
    result = subprocess.run(
        ["pgrep", "-f", "^gz sim server$"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        raise RuntimeError(
            "Gazebo Server is already running. "
            "Close the existing simulation before launching another."
        )

    subprocess.run(
        ["python3", str(GENERATOR)],
        check=True
    )
    return []


def generate_launch_description():
    from launch.actions import OpaqueFunction

    clean_env = os.environ.copy()

    for key in [
        "GTK_PATH",
        "GTK_EXE_PREFIX",
        "GIO_MODULE_DIR",
        "GSETTINGS_SCHEMA_DIR",
        "GTK_IM_MODULE_FILE",
        "LOCPATH",
    ]:
        clean_env.pop(key, None)

    clean_env["GZ_PARTITION"] = "greenhouse_fixed_test"

    gazebo = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r",
            str(WORLD)
        ],
        output="screen",
        env=clean_env
    )

    spawn = ExecuteProcess(
        cmd=[
            "python3",
            str(PACKAGE / "scripts/spawn_amiga.py"),
        ],
        output="screen",
        additional_env={
            "GZ_PARTITION": "greenhouse_fixed_test"
        }
    )


    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="amiga_gz_bridge",
        arguments=[
            "/model/amiga/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/model/amiga/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/world/greenhouse_realistic/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        remappings=[
            ("/model/amiga/cmd_vel", "/cmd_vel"),
            ("/model/amiga/odometry", "/odom"),
            ("/world/greenhouse_realistic/clock", "/clock"),
        ],
        additional_env={
            "GZ_PARTITION": "greenhouse_fixed_test"
        },
        output="screen",
    )


    urdf_result = subprocess.run(
        [
            "xacro",
            str(PACKAGE / "urdf/amiga_sim.urdf.xacro"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="amiga_robot_state_publisher",
        parameters=[
            {
                "robot_description": urdf_result.stdout,
                "frame_prefix": "amiga/",
                "use_sim_time": True,
            }
        ],
        output="screen",
    )

    odom_tf = ExecuteProcess(
        cmd=[
            "python3",
            str(PACKAGE / "scripts/odom_tf_broadcaster.py"),
        ],
        output="screen",
    )

    return LaunchDescription([
        OpaqueFunction(function=generate_model),
        gazebo,
        bridge,
        spawn,
        robot_state_publisher,
        odom_tf,
    ])
