# Autonomous Agricultural Robot Framework

A platform-independent and modular ROS2 framework for autonomous agricultural robots.

This project is developed using **ROS2 Jazzy** on **Ubuntu 24.04** at **Technion – Israel Institute of Technology**. The objective is to build a reusable software framework for autonomous agricultural robots with multi-sensor integration, localization, mapping and navigation capabilities.

---

# Current Status

## Completed

- ✅ ROS2 Jazzy development environment
- ✅ Robot Description (URDF/Xacro)
- ✅ Modular Bringup architecture
- ✅ CSPC COIN-D6 LiDAR integration
- ✅ Orbbec Gemini335 stereo camera integration
- ✅ TF tree verification
- ✅ robot_localization EKF framework
- ✅ RViz visualization

## In Progress

- 🔄 Dual-sensor validation (LiDAR + Camera)
- 🔄 IMU integration

## Planned

- Dual Antenna GPS integration
- Multi-sensor fusion
- SLAM Toolbox
- Navigation2
- Autonomous navigation
- Platform-independent deployment

---

# Project Milestones

| Stage | Status |
|--------|--------|
| ROS2 Development Environment | ✅ |
| Robot Description | ✅ |
| Modular Bringup | ✅ |
| Sensor Integration | ✅ |
| Sensor Fusion | 🔄 |
| Mapping (SLAM) | ⏳ |
| Navigation2 | ⏳ |
| Autonomous Navigation | ⏳ |

---

# Software Architecture

Current framework:

```text
                    bringup.launch.py
                            │
      ┌─────────────┬──────────────┬──────────────┐
      │             │              │              │
description      sensors      localization   visualization
      │             │              │              │
 Robot Model   LiDAR / Camera      EKF          RViz
```

Target framework:

```text
                  Autonomous Agricultural Robot Framework
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
 Robot Description          Sensor Layer            Robot Bringup
        │                         │                         │
        │          ┌──────────────┼──────────────┐          │
        │          │              │              │          │
     LiDAR     Stereo Camera      IMU      Dual GPS         │
        │          │              │              │          │
        └──────────┴──────────────┴──────────────┘
                               │
                 robot_localization (Sensor Fusion)
                               │
                    SLAM / Localization
                               │
                         Navigation2
                               │
                        Motion Control
                               │
                Autonomous Agricultural Applications
```

---

# Repository Structure

```text
ros2_ws
│
├── docs
│   └── architecture
│
├── src
│   ├── cspc_lidar_sdk_ros2
│   ├── my_robot_description
│   ├── my_robot_bringup
│   ├── my_robot_interfaces
│   ├── my_first_pkg
│   └── robot_sensors
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
| my_robot_bringup | Modular bringup and launch system |
| robot_sensors | Sensor configuration and sensor launch management |
| cspc_lidar_sdk_ros2 | CSPC COIN-D6 LiDAR ROS2 driver |
| my_robot_interfaces | Custom ROS2 interfaces |
| my_first_pkg | ROS2 learning and testing examples |

---

# Hardware Platform

## Current Sensors

- CSPC COIN-D6 LiDAR
- Orbbec Gemini335 Stereo Camera

## Planned Sensors

- IMU
- Dual Antenna GPS

## Target Robot Platforms

- Custom ROS2 Robot
- farm-ng AMIGA
- AgileX Scout

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

Launch the complete robot system:

```bash
ros2 launch my_robot_bringup bringup.launch.py
```

Launch with optional sensors:

```bash
ros2 launch my_robot_bringup bringup.launch.py \
    use_lidar:=true \
    use_camera:=true
```

---

# Documentation

Project documentation is located in:

```text
docs/architecture/
```

Including:

- System Overview
- Package Design
- Sensor Architecture

---

# Future Roadmap

- IMU integration
- Dual GPS integration
- EKF sensor fusion
- SLAM Toolbox
- Navigation2
- Platform-independent deployment
- Autonomous agricultural applications

---

# Author

**Min Li**

Faculty of Civil and Environmental Engineering

Technion – Israel Institute of Technology

Supervisor: **Prof. Raphael Linker**

---

# License

This project is intended for research and educational purposes.