# Autonomous Agricultural Robot Framework

A modular ROS 2 framework for autonomous agricultural robots, developed
and tested on the Farm-ng AMIGA skid-steer platform.

The current system integrates LiDAR, dual OAK depth cameras, SBG
GNSS/INS/IMU, wheel odometry, sensor fusion, obstacle perception, SLAM,
and Nav2.

The framework separates sensor and localization bringup from
motion-capable navigation so that the system can be inspected and
validated before robot motion is enabled.

## Current Platform

Primary robot:

- Farm-ng AMIGA skid-steer agricultural robot
- ROS 2 Jazzy
- Ubuntu 24.04 on the ROS 2 computer
- Farm-ng Brain connected over Ethernet
- Velodyne VLP-16 LiDAR
- Front OAK-D-W PoE depth camera
- Rear OAK-D-W PoE depth camera
- SBG GNSS/INS/IMU
- Four-motor RPM feedback from the AMIGA CAN network

The repository is also being structured for transfer to additional
agricultural robot platforms.

## System Architecture

The current runtime architecture is:

    Farm-ng AMIGA Brain
        |
        +-- Front OAK depth server :8765
        |
        +-- Rear OAK depth server  :8766
        |
        +-- Read-only CAN RPM feedback
        |
        v
    ROS 2 computer
        |
        +-- robot description / TF
        |
        +-- VLP-16 + SBG sensor drivers
        |
        +-- AMIGA motor RPM receiver
        |       |
        |       +--> wheel odometry
        |
        +-- local EKF
        |
        +-- OAK depth bridges
        |       |
        |       +--> PointCloud2
        |       +--> front/rear obstacle clouds
        |
        +-- SLAM or GNSS/global localization
        |
        +-- Nav2 navigation

The main static system entry point is:

    ros2 launch my_robot_bringup bringup.launch.py

It starts:

- robot description and TF
- VLP-16 and SBG sensors
- IMU covariance processing
- passive AMIGA motor RPM reception
- wheel odometry
- local EKF localization
- front and rear OAK depth perception

It does **not** start Nav2 navigation.

## Safety and Operating Modes

The system deliberately separates feedback/perception startup from
motion-capable navigation.

### Static Bringup

`bringup.launch.py` contains sensor, feedback, localization, and
perception components. The AMIGA base interface used by this launch
receives motor feedback and publishes wheel odometry; it does not send
robot motion commands.

This mode should be used first when checking:

- sensor connectivity
- TF
- wheel RPM feedback
- wheel odometry
- IMU data
- EKF output
- depth point clouds
- obstacle clouds

### Navigation

`navigation.launch.py` is a separate motion-capable launch file.

It starts Nav2 components including the controller server, behavior
server, velocity smoother, collision monitor, planner, BT navigator,
and waypoint follower.

Do not treat navigation startup as equivalent to static bringup.
Before motion tests, verify the robot control path, emergency-stop
procedure, obstacle handling, and manual/joystick override.

### Brain-side CAN Feedback

The current Brain-side RPM bridge is read-only with respect to CAN. It
uses `candump` to observe motor feedback and forwards decoded RPM values
to the ROS 2 computer over UDP.

The raw CAN RPM decoder is project-side code rather than an official
Farm-ng high-level MotorState decoder. Motor sign conventions must be
revalidated if the implementation is later replaced by the official
Farm-ng MotorState interface.

## Build and Environment

Tested ROS 2 computer environment:

- Ubuntu 24.04
- ROS 2 Jazzy

Build the workspace from the repository root:

    cd ~/ros2_ws
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash

The workspace must be sourced in every new terminal before launching
repository packages.

## Network and Brain-side Services

The Farm-ng Brain provides the OAK depth streams and motor RPM feedback
used by the ROS 2 computer.

Tested Brain-side deployment directory:

    /mnt/amiga_tools/

Repository copies of these scripts are stored in:

    tools/amiga_brain/

The Brain-side tools are:

- `front_depth_server.py`
- `rear_depth_server.py`
- `can_motor_sender_candump.py`

The tested depth endpoints are:

    Front OAK: ws://10.95.76.1:8765
    Rear OAK:  ws://10.95.76.1:8766

Motor RPM feedback is forwarded to the ROS 2 computer over UDP port
5006.

See `tools/amiga_brain/README.md` for the Brain environment, hardware
mapping, deployment notes, and CAN decoder limitations.

## Startup Sequence

Use the following order when bringing up the static system.

### 1. Verify Brain-side services

Before starting ROS 2 perception, confirm that the front and rear depth
servers and the passive motor RPM feedback process are running on the
Farm-ng Brain.

Do not overwrite or restart active Brain-side scripts during a robot
session unless the shutdown and restart are intentional.

### 2. Build and source the ROS 2 workspace

    cd ~/ros2_ws
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash

### 3. Start the static ROS 2 system

    ros2 launch my_robot_bringup bringup.launch.py

This starts the current sensor, feedback, local localization, and
perception stack without starting Nav2 navigation.

### 4. Verify the core data paths

Check that the expected topics exist:

    ros2 topic list

Important topics include:

    /scan_multi
    /velodyne_points
    /imu/data
    /imu/data_cov
    /amiga/motor_rpm
    /wheel/odometry
    /odometry/filtered
    /camera/front/depth/image_raw
    /camera/front/depth/camera_info
    /camera/front/depth/points
    /camera/front/obstacles
    /camera/rear/depth/image_raw
    /camera/rear/depth/camera_info
    /camera/rear/depth/points
    /camera/rear/obstacles

Check representative publication rates with:

    ros2 topic hz /scan_multi
    ros2 topic hz /imu/data
    ros2 topic hz /amiga/motor_rpm
    ros2 topic hz /wheel/odometry
    ros2 topic hz /odometry/filtered
    ros2 topic hz /camera/front/obstacles
    ros2 topic hz /camera/rear/obstacles

When the robot is stationary, zero or near-zero motor RPM and wheel
odometry are expected.

### 5. Verify TF

The static bringup should provide the transforms required to relate
the sensors and obstacle clouds to `base_link`, while the local EKF
provides the local `odom` to `base_link` relationship.

Inspect TF before proceeding to navigation or SLAM.

For example:

    ros2 run tf2_ros tf2_echo base_link front_camera_depth_optical_frame
    ros2 run tf2_ros tf2_echo base_link rear_camera_depth_optical_frame

### 6. Verify obstacle perception

The front and rear OAK pipelines are:

    depth image
        -> depth_image_proc
        -> PointCloud2
        -> CropBox in base_link
        -> obstacle cloud

The current obstacle topics are:

    /camera/front/obstacles
    /camera/rear/obstacles

The Nav2 local costmap is configured to consume these two obstacle
clouds together with `/scan_multi`.

The current OAK obstacle clouds are used for local-costmap marking.
They are not currently configured as collision-monitor safety sources.


## Localization and Mapping Modes

The repository currently provides separate launch files for local
localization, GNSS/global localization, and SLAM.

### Local Localization

    ros2 launch my_robot_bringup local_localization.launch.py

This starts the local `robot_localization` EKF using `ekf.yaml`.

The normal static `bringup.launch.py` already includes this local
localization launch, so it does not normally need to be started
separately.

### GNSS / Global Localization

    ros2 launch my_robot_bringup localization.launch.py

This launch contains:

- local EKF
- global EKF
- `navsat_transform_node`

It uses:

- `ekf.yaml`
- `ekf_global.yaml`
- `navsat.yaml`

This mode is intended for outdoor GNSS-based operation. GNSS/global
localization should be validated outdoors with valid GNSS/INS data
before it is used as part of an autonomous navigation test.

### SLAM

    ros2 launch my_robot_bringup slam.launch.py

This starts `slam_toolbox` using:

    config/slam_toolbox.yaml

SLAM and GNSS/global localization represent different operating modes.
Select the mode appropriate to the environment and experiment rather
than starting every localization component simultaneously.

## Navigation

Navigation is intentionally started separately:

    ros2 launch my_robot_bringup navigation.launch.py

This launch is motion-capable and includes:

- Nav2 controller server
- smoother server
- planner server
- behavior server
- BT navigator
- waypoint follower
- velocity smoother
- collision monitor
- Nav2 lifecycle manager

The default Nav2 configuration is:

    src/my_robot_bringup/config/nav2.yaml

The local costmap currently combines:

- `/scan_multi`
- `/camera/front/obstacles`
- `/camera/rear/obstacles`

The collision monitor currently uses the LiDAR path rather than the OAK
obstacle clouds.

Navigation should only be started after static sensor, TF, localization,
costmap, robot-control, and emergency/manual override checks have been
completed.

## Repository Structure

    ros2_ws/
    |
    +-- src/
    |   |
    |   +-- my_robot_bringup/
    |   |   +-- launch/
    |   |   +-- config/
    |   |
    |   +-- robot_sensors/
    |   |   +-- launch/
    |   |   +-- config/
    |   |
    |   +-- amiga_base_interface/
    |   |
    |   +-- farmng_bridge/
    |   |
    |   +-- my_robot_description/
    |   |
    |   +-- ...
    |
    +-- tools/
    |   +-- amiga_brain/
    |
    +-- docs/
        +-- architecture/

Key responsibilities:

- `my_robot_bringup`: system-level launch and localization/navigation
  configuration
- `robot_sensors`: VLP-16, SBG, and sensor preprocessing
- `amiga_base_interface`: passive AMIGA motor feedback reception and
  wheel odometry
- `farmng_bridge`: Farm-ng Brain to ROS 2 data bridges
- `my_robot_description`: robot model and sensor TF
- `tools/amiga_brain`: Brain-side OAK depth and CAN-feedback utilities
- `docs/architecture`: architecture notes

## Current Validation Status

The following static integration paths have been exercised on the
current AMIGA platform:

- VLP-16 point cloud and `/scan_multi`
- SBG IMU data
- IMU covariance processing
- passive four-motor RPM feedback
- wheel odometry
- local EKF output
- front OAK depth stream
- rear OAK depth stream
- front/rear depth-to-point-cloud conversion
- front/rear obstacle ROI filtering
- LiDAR obstacle input to the Nav2 local costmap
- front OAK obstacle input to the Nav2 local costmap
- rear OAK obstacle input to the Nav2 local costmap
- combined LiDAR + front OAK + rear OAK local-costmap marking

Static obstacle integration does not by itself validate dynamic obstacle
avoidance or the complete robot safety chain.

## Remaining Handoff Work

Before treating the repository as a complete autonomous-robot handoff,
the following items still require final validation and/or documentation:

- controlled motion test of the complete Nav2 command path
- dynamic obstacle stop/avoidance behavior
- joystick/manual override behavior
- emergency-stop and recovery procedure
- trajectory and experiment-log saving workflow
- outdoor GNSS/global localization validation
- parameterized demonstration procedure
- migration procedure for the second robot platform
- final operator troubleshooting guide

These items should be documented as they are verified rather than
being described as completed in advance.

## Architecture Documentation

Additional architecture notes are available under:

    docs/architecture/

Current documents include:

- `01_system_overview.md`
- `02_package_design.md`
- `03_sensor_architecture.md`

## Development Principle

The framework is intended to keep hardware-specific interfaces,
perception, localization, and navigation sufficiently separated that
the higher-level ROS 2 stack can be reused on another agricultural
robot with limited changes to hardware drivers, parameters, and robot
description.
