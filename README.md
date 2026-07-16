# ROS2 Workspace

This repository contains my ROS2 learning projects developed with ROS2 Jazzy.

## Packages

### my_first_pkg

Basic ROS2 examples including:

- Publisher
- Subscriber
- Service
- Action Server
- Action Client

### my_robot_interfaces

Custom ROS2 interfaces:

- Action: MoveRobot.action

## Environment

- Ubuntu 24.04
- ROS2 Jazzy
- Python 3.12

## Build

```bash
colcon build --symlink-install
```

## Source

```bash
source install/setup.bash
```

## Run Action Server

```bash
ros2 run my_first_pkg move_robot_action_server
```

## Run Action Client

```bash
ros2 run my_first_pkg move_robot_action_client
```