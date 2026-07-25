# System Overview

## Project Objective

This project aims to develop a modular, platform-independent, and reusable ROS2 framework for autonomous agricultural robots.

The framework is designed to integrate multiple sensors, localization, mapping, perception, and autonomous navigation into a unified software architecture. It emphasizes modularity, scalability, and maintainability so that different robot platforms can reuse the same software stack with minimal modifications.

The project is developed during a research internship at the Technion – Israel Institute of Technology.

---

# System Architecture

```
                 Autonomous Agricultural Robot Framework
                                │
        ┌───────────────────────┴────────────────────────┐
        │                                                │
 Robot Description                               Robot Bringup
        │                                                │
        └───────────────────────┬────────────────────────┘
                                │
                           Sensor Layer
     ┌──────────────┬──────────────┬──────────────┬──────────────┐
     │              │              │              │
   LiDAR      Stereo Camera       IMU        Dual GPS
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                                │
                  robot_localization (EKF)
                                │
                         Localization
                                │
                         SLAM Toolbox
                                │
                          Navigation2
                                │
                      Motion Controller
                                │
                Agricultural Robot Applications
```

---

# Software Architecture

```
ros2_ws
│
├── my_robot_description
│       Robot model (URDF/Xacro)
│
├── my_robot_bringup
│       Launch system
│       Configuration files
│
├── cspc_lidar_sdk_ros2
│       LiDAR driver
│
├── my_robot_interfaces
│       Custom ROS2 interfaces
│
└── Future Packages
        robot_localization
        slam_toolbox
        nav2
        perception
```

---

# Package Responsibilities

## my_robot_description

Responsible for

- Robot URDF/Xacro
- Robot kinematic model
- TF tree
- Robot visualization

---

## my_robot_bringup

Responsible for

- System launch
- Sensor startup
- Localization startup
- Navigation startup
- Configuration management

Launch files

- bringup.launch.py
- description.launch.py
- sensors.launch.py
- localization.launch.py
- navigation.launch.py (planned)

Configuration files

- ekf.yaml
- nav2_params.yaml (planned)
- sensor_params.yaml (planned)

---

## cspc_lidar_sdk_ros2

Responsible for

- CSPC LiDAR communication
- LaserScan publishing
- PointCloud publishing

This package is maintained as a third-party driver and should not be modified unless necessary.

---

## my_robot_interfaces

Responsible for

- Custom ROS2 messages
- Services
- Actions

---

# Sensor Architecture

Current sensors

- CSPC COIN-D6 LiDAR
- Gemini335 Stereo Camera

Planned sensors

- IMU
- Dual-antenna GPS
- Wheel Odometry

All sensors are managed through the Sensor Layer, allowing hardware replacement without affecting upper software layers.

---

# Localization Architecture

Localization is implemented using **robot_localization**.

Current status

- EKF framework created
- Configuration file established
- Launch architecture completed

Planned sensor fusion

- IMU
- GPS
- Wheel Odometry

Output

- /odometry/filtered
- TF (map → odom → base_link)

---

# Navigation Architecture

Navigation will be implemented using Navigation2.

Main components

- Global Planner
- Local Planner
- Controller Server
- Behavior Tree
- Costmaps
- Recovery Behaviors

---

# Current Progress

## Completed

- ROS2 Jazzy workspace
- Robot Description
- Bringup package
- LiDAR integration
- Gemini335 integration
- RViz visualization
- Launch architecture
- EKF framework
- Project documentation

---

## In Progress

- Framework architecture
- Sensor abstraction
- Localization framework

---

## Planned

- IMU integration
- Dual GPS integration
- robot_localization configuration
- SLAM Toolbox
- Navigation2
- Autonomous navigation
- Agricultural task planning

---

# Design Principles

The framework follows the following design principles.

- Modular
- Platform-independent
- Reusable
- Scalable
- Easy to extend
- ROS2 native
- Hardware abstraction
- Configuration driven

---

# Supported Robot Platforms

Current

- Custom Agricultural Robot

Planned

- Farm-ng AMIGA
- AgileX Scout
- Other ROS2-compatible mobile robots

---

# Development Roadmap

## Phase 1 — Robot Foundation

- ROS2 workspace
- Robot Description
- Bringup
- LiDAR integration
- Camera integration

Status

Completed

---

## Phase 2 — Localization

- IMU
- GPS
- Wheel Odometry
- robot_localization

Status

In Progress

---

## Phase 3 — Mapping

- SLAM Toolbox
- Occupancy Grid Mapping

Status

Planned

---

## Phase 4 — Autonomous Navigation

- Navigation2
- Path Planning
- Obstacle Avoidance
- Mission Execution

Status

Planned

---

# Repository Structure

```
ros2_ws/
│
├── docs/
│   ├── architecture/
│   ├── reports/
│   └── images/
│
├── src/
│   ├── my_robot_description/
│   ├── my_robot_bringup/
│   ├── my_robot_interfaces/
│   └── cspc_lidar_sdk_ros2/
│
├── install/
├── build/
└── log/
```

---

# Future Work

Future work will focus on

- Multi-sensor fusion
- Autonomous localization
- SLAM
- Navigation2 integration
- Agricultural task execution
- Multi-platform deployment
- Performance optimization