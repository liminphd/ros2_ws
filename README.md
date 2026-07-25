# Autonomous Agricultural Robot Framework

A modular ROS2-based software framework for autonomous agricultural robots.

This project is developed using **ROS2 Jazzy** on **Ubuntu 24.04**. The objective is to build a platform-independent and modular software architecture for autonomous agricultural robots with multi-sensor integration, localization, mapping and navigation capabilities.

---

# Project Goals

The main objectives of this project are:

- Build a modular ROS2 software framework
- Develop a platform-independent robot architecture
- Integrate multiple sensors
- Support autonomous navigation
- Provide a reusable framework for agricultural robotics research

---

# Hardware Platform

## Current Sensors

- COIN-D6 LiDAR
- Gemini335 Stereo Camera

## Planned Sensors

- Dual Antenna GPS
- IMU

## Robot Platforms

Current

- Custom ROS2 robot platform

Future

- AMIGA Farm-ng
- AgileX Scout

---

# Repository Structure

```text
ros2_ws
│
├── docs
│   ├── architecture
│   ├── images
│   └── reports
│
├── src
│   ├── cspc_lidar_sdk_ros2
│   ├── my_robot_description
│   ├── my_robot_bringup
│   ├── my_robot_interfaces
│   └── my_first_pkg
│
├── build
├── install
└── log
```

### Package Description

| Package | Description |
|----------|-------------|
| my_robot_description | Robot URDF/Xacro model |
| my_robot_bringup | Robot startup and launch system |
| cspc_lidar_sdk_ros2 | COIN-D6 LiDAR ROS2 driver |
| my_robot_interfaces | Custom ROS2 interfaces |
| my_first_pkg | ROS2 communication examples for learning and testing |

---

# Current Progress

## Completed

- Ubuntu 24.04 development environment
- ROS2 Jazzy installation
- VS Code development environment
- Git & GitHub configuration
- ROS2 Publisher / Subscriber
- ROS2 Service
- ROS2 Action
- ROS2 Parameters
- ROS2 Launch
- Robot URDF/Xacro model
- Robot Bringup system
- COIN-D6 LiDAR integration
- Gemini335 Stereo Camera integration
- Robot TF configuration
- RViz visualization

## In Progress

- Framework refactoring
- Project documentation
- Software architecture design

## Planned

- IMU integration
- Dual Antenna GPS integration
- Robot localization
- Sensor fusion
- SLAM
- Navigation2
- Autonomous navigation
- Agricultural robot applications

---

# Software Architecture

Current framework:

```text
Robot Description
        │
Robot Bringup
        │
LiDAR Driver
        │
Stereo Camera
        │
RViz
```

Target framework:

```text
                    Autonomous Agricultural Robot Framework
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
 Robot Description           Sensor Layer              Robot Bringup
        │                          │                          │
        │          ┌───────────────┼────────────────┐         │
        │          │               │                │         │
     LiDAR      Stereo Camera     IMU         Dual GPS        │
        │          │               │                │         │
        └──────────┴───────────────┴────────────────┘
                               │
                      Sensor Fusion (robot_localization)
                               │
                         SLAM / Localization
                               │
                           Navigation2
                               │
                          Motion Control
                               │
                       Agricultural Applications
```

---

# Development Environment

| Item | Version |
|------|---------|
| Operating System | Ubuntu 24.04 |
| ROS | ROS2 Jazzy |
| Language | Python 3.12 / C++ |
| IDE | Visual Studio Code |

---

# Build

```bash
colcon build --symlink-install
```

---

# Source

```bash
source install/setup.bash
```

---

# Launch

```bash
ros2 launch my_robot_bringup bringup.launch.py
```

---

# Future Work

The future development will focus on:

- Modular sensor management
- GPS integration
- IMU integration
- Multi-sensor fusion
- Robot localization
- SLAM
- Navigation2
- Platform-independent robot framework
- Autonomous agricultural robot applications

---

# Author

**Min Li**

Faculty of Civil and Environmental Engineering

Technion – Israel Institute of Technology

Supervisor: **Prof. Raphael Linker**