# System Overview

## Project Objective

This project aims to develop a modular and platform-independent ROS2 framework for autonomous agricultural robots.

The framework integrates multiple sensors, localization, mapping, and autonomous navigation into a reusable software architecture.

---

# Overall Architecture

```
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
                     Localization / SLAM
                               │
                          Navigation2
                               │
                        Motion Controller
                               │
                  Agricultural Robot Applications
```

---

# Current Progress

Completed

- Robot Description
- Robot Bringup
- LiDAR Integration
- Gemini335 Stereo Camera
- RViz Visualization

In Progress

- Framework Architecture
- Documentation

Planned

- IMU
- Dual GPS
- robot_localization
- SLAM
- Navigation2

---

# Design Principles

- Modular
- Platform Independent
- Reusable
- Easy to Extend
- ROS2 Native

---

# Future Robot Platforms

- Custom Robot
- Farm-ng AMIGA
- AgileX Scout