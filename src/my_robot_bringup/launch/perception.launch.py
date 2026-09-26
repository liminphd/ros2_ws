from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    # ---------------------------------------------------------
    # Front OAK (Farm-ng oak0)
    # MXID: 14442C1071C4CDD200
    # Brain depth server: ws://10.95.76.1:8765
    # DepthAI depth alignment: RECTIFIED_RIGHT (CAM_C)
    # ---------------------------------------------------------
    front_depth_bridge = Node(
        package="farmng_bridge",
        executable="farmng_depth_bridge",
        name="farmng_front_depth_bridge",
        output="screen",
        parameters=[{
            "uri": "ws://10.95.76.1:8765",
            "topic": "/camera/front/depth/image_raw",
            "camera_info_topic": "/camera/front/depth/camera_info",
            "frame_id": "front_camera_depth_optical_frame",
            "fx": 282.52703857421875,
            "fy": 282.4111022949219,
            "cx": 322.3250732421875,
            "cy": 202.55392456054688,
        }],
    )

    # ---------------------------------------------------------
    # Rear OAK (Farm-ng oak1)
    # MXID: 14442C10A1B3E6D200
    # Brain depth server: ws://10.95.76.1:8766
    # DepthAI depth alignment: RECTIFIED_RIGHT (CAM_C)
    # ---------------------------------------------------------
    rear_depth_bridge = Node(
        package="farmng_bridge",
        executable="farmng_depth_bridge",
        name="farmng_rear_depth_bridge",
        output="screen",
        parameters=[{
            "uri": "ws://10.95.76.1:8766",
            "topic": "/camera/rear/depth/image_raw",
            "camera_info_topic": "/camera/rear/depth/camera_info",
            "frame_id": "rear_camera_depth_optical_frame",
            "fx": 289.75628662109375,
            "fy": 289.7078552246094,
            "cx": 317.12738037109375,
            "cy": 199.55506896972656,
        }],
    )

    # ---------------------------------------------------------
    # Depth image -> PointCloud2
    # ---------------------------------------------------------
    front_depth_to_points = Node(
        package="depth_image_proc",
        executable="point_cloud_xyz_node",
        name="front_depth_to_points",
        output="screen",
        remappings=[
            ("image_rect", "/camera/front/depth/image_raw"),
            ("camera_info", "/camera/front/depth/camera_info"),
            ("points", "/camera/front/depth/points"),
        ],
    )

    rear_depth_to_points = Node(
        package="depth_image_proc",
        executable="point_cloud_xyz_node",
        name="rear_depth_to_points",
        output="screen",
        remappings=[
            ("image_rect", "/camera/rear/depth/image_raw"),
            ("camera_info", "/camera/rear/depth/camera_info"),
            ("points", "/camera/rear/depth/points"),
        ],
    )

    # ---------------------------------------------------------
    # Front obstacle ROI
    # ---------------------------------------------------------
    front_oak_crop = Node(
        package="pcl_ros",
        executable="filter_crop_box_node",
        name="front_oak_crop",
        output="screen",
        remappings=[
            ("input", "/camera/front/depth/points"),
            ("output", "/camera/front/obstacles"),
        ],
        parameters=[{
            "input_frame": "base_link",
            "output_frame": "base_link",
            "min_x": 0.70,
            "max_x": 3.0,
            "min_y": -1.5,
            "max_y": 1.5,
            "min_z": -0.67,
            "max_z": 2.0,
        }],
    )

    # ---------------------------------------------------------
    # Rear obstacle ROI
    # ---------------------------------------------------------
    rear_oak_crop = Node(
        package="pcl_ros",
        executable="filter_crop_box_node",
        name="rear_oak_crop",
        output="screen",
        remappings=[
            ("input", "/camera/rear/depth/points"),
            ("output", "/camera/rear/obstacles"),
        ],
        parameters=[{
            "input_frame": "base_link",
            "output_frame": "base_link",
            "min_x": -3.0,
            "max_x": -0.70,
            "min_y": -1.5,
            "max_y": 1.5,
            "min_z": -0.67,
            "max_z": 2.0,
        }],
    )

    return LaunchDescription([
        front_depth_bridge,
        rear_depth_bridge,
        front_depth_to_points,
        rear_depth_to_points,
        front_oak_crop,
        rear_oak_crop,
    ])
