# Autonomous Agricultural Robot Framework

A modular, platform-independent ROS2 framework for autonomous agricultural robots.

This project is being developed at the **Technion – Israel Institute of Technology** using **ROS2 Jazzy (Ubuntu 24.04)**.

The objective is to build a reusable perception and navigation framework capable of integrating multiple sensors, performing localization and mapping, and supporting autonomous agricultural applications.

---

# Project Overview

Current software architecture integrates multiple sensing modules into a unified ROS2 framework.

Current hardware platform:

- CSPC COIN-D6 LiDAR
- Dual Luxonis OAK-D-W PoE Cameras
- SBG Ellipse IMU
- Dual-Antenna GNSS (under integration)

Current software stack:

- ROS2 Jazzy
- robot_localization
- RViz2
- Modular Launch System

Future software stack:

- SLAM Toolbox
- Navigation2
- Autonomous Navigation
- Jetson-based Manipulator Integration

---

# Current Status

## Completed

- ✅ ROS2 Jazzy development environment
- ✅ Modular workspace architecture
- ✅ Robot Description (URDF/Xacro)
- ✅ Modular Bringup framework
- ✅ CSPC COIN-D6 LiDAR integration
- ✅ SBG Ellipse IMU integration
- ✅ Dual OAK-D-W PoE camera integration
- ✅ Dual-camera ROS2 launch framework
- ✅ TF tree verification
- ✅ RViz visualization

## In Progress

- 🔄 Dual Antenna GNSS integration
- 🔄 Unified sensor launch
- 🔄 robot_localization configuration

## Planned

- Sensor fusion
- SLAM Toolbox
- Navigation2
- Autonomous navigation
- Jetson integration
- Manipulator integration
- Platform-independent deployment

---

# Project Milestones

| Stage | Status |
|--------|--------|
| ROS2 Development Environment | ✅ |
| Robot Description | ✅ |
| LiDAR Integration | ✅ |
| IMU Integration | ✅ |
| Dual Camera Integration | ✅ |
| GNSS Integration | 🔄 |
| Sensor Fusion (EKF) | 🔄 |
| SLAM | ⏳ |
| Navigation2 | ⏳ |
| Autonomous Navigation | ⏳ |

---

# Software Architecture

Current architecture

```text
                     bringup.launch.py
                              │
      ┌──────────────┬──────────────┬──────────────┐
      │              │              │              │
 description      sensors     localization   visualization
      │              │              │              │
 Robot Model   LiDAR / OAK / SBG    EKF          RViz
```

Target architecture

```text
                 Autonomous Agricultural Robot Framework
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
 Robot Description           Sensor Layer             Robot Bringup
        │                          │                          │
        │          ┌───────────────┼────────────────┐         │
        │          │               │                │         │
     LiDAR     Dual OAK Cameras    IMU        Dual GNSS       │
        │          │               │                │         │
        └──────────┴───────────────┴────────────────┘
                               │
                 robot_localization (Sensor Fusion)
                               │
                     Mapping / Localization
                               │
                         Navigation2
                               │
                       Motion Controller
                               │
             Autonomous Agricultural Applications
```

---

# Repository Structure

```text
ros2_ws
│
├── docs
│
├── src
│   ├── cspc_lidar_sdk_ros2
│   ├── my_robot_bringup
│   ├── my_robot_description
│   ├── my_robot_interfaces
│   ├── robot_sensors
│   │
│   ├── config
│   │   ├── velodyne
│   │   ├── sbg
│   │   └── oak
│   │
│   └── launch
│       ├── velodyne.launch.py
│       ├── sbg.launch.py
│       ├── oak_left.launch.py
│       ├── oak_right.launch.py
│       ├── oak_cameras.launch.py
│       └── sensors.launch.py
│
├── build
├── install
└── log
```

---

# Package Overview

| Package | Description |
|----------|-------------|
| my_robot_description | Robot URDF/Xacro model |
| my_robot_bringup | Robot bringup and launch system |
| robot_sensors | Sensor configuration and launch management |
| cspc_lidar_sdk_ros2 | CSPC LiDAR ROS2 driver |
| my_robot_interfaces | Custom ROS2 interfaces |
| my_first_pkg | ROS2 experiments and testing |

---

# Hardware Platform

## Current Sensors

- CSPC COIN-D6 LiDAR
- Dual Luxonis OAK-D-W PoE Cameras
- SBG Ellipse IMU

## Under Integration

- Dual Antenna GNSS

## Future Hardware

- NVIDIA Jetson
- Robotic Manipulator
- Autonomous Agricultural Robot Platform

---

# Development Environment

| Item | Version |
|------|---------|
| Operating System | Ubuntu 24.04 |
| ROS | ROS2 Jazzy |
| Programming Language | Python 3.12 / C++ |
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

Launch LiDAR

```bash
ros2 launch robot_sensors velodyne.launch.py
```

Launch IMU

```bash
ros2 launch robot_sensors sbg.launch.py
```

Launch Dual OAK Cameras

```bash
ros2 launch robot_sensors oak_cameras.launch.py
```

Launch Complete Robot

```bash
ros2 launch my_robot_bringup bringup.launch.py
```

---

# Documentation

Project documentation is located in

```text
docs/
```

Documentation includes

- System Architecture
- Sensor Architecture
- Launch Architecture
- Robot Description
- Package Design

---

# Future Roadmap

- Complete GNSS integration
- robot_localization EKF configuration
- Multi-sensor synchronization
- SLAM Toolbox
- Navigation2
- Jetson deployment
- Manipulator integration
- Autonomous agricultural navigation

---

# Author

**Min Li**

Faculty of Civil and Environmental Engineering

Technion – Israel Institute of Technology

Supervisor: **Prof. Raphael Linker**

---

# License

This repository is intended for research and educational purposes.
