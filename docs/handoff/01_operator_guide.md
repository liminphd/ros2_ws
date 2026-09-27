# AMIGA Operator Guide

## Purpose

This document provides the operational entry point for the ROS 2 autonomous
agricultural robot framework on the farm-ng AMIGA platform.

It separates statically validated startup and inspection procedures from
procedures that still require physical robot motion for final validation.

## Safety and Validation Status

The static ROS 2 sensor, TF, local localization, perception, SLAM input, and
saved-map loading workflows have been validated.

The following procedures are not yet considered dynamically validated:

- complete Nav2 command path
- joystick/manual override
- emergency-stop and recovery
- driven SLAM
- saved-map localization while driving
- outdoor GNSS/global localization
- autonomous map-based navigation
- dynamic obstacle stop/avoidance
- AMIGA trajectory recording and reload

Do not mark these items as validated until physical testing has been completed.

## Workspace Setup

Open a terminal and source ROS 2 and the workspace:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

If the workspace has changed, rebuild it before operation:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Recommended Static Startup

The recommended handoff entry point is:

```bash
ros2 launch my_robot_bringup demo.launch.py
```

`demo.launch.py` starts six independently selectable components:

- robot description and TF
- sensors
- read-only AMIGA base feedback
- local EKF localization
- OAK perception
- RViz

All six switches default to `true`.

Navigation is intentionally separate from the static startup.

## Localization Modes

### Local Localization

Start the local EKF with:

```bash
ros2 launch my_robot_bringup local_localization.launch.py
```

This mode uses `config/ekf.yaml` and publishes the primary filtered odometry on:

```text
/odometry/filtered
```

### GNSS / Global Localization

The global localization launch entry point is:

```bash
ros2 launch my_robot_bringup localization.launch.py
```

This starts the local EKF, global EKF, and `navsat_transform_node`.

The global localization workflow still requires final outdoor dynamic validation.

## SLAM Mode

Start SLAM with:

```bash
ros2 launch my_robot_bringup slam.launch.py
```

This starts `slam_toolbox` in online asynchronous mode using `config/slam_toolbox.yaml`.

The SLAM input and TF prerequisites have been statically validated. Driven mapping and real-map saving still require physical motion validation.

## Saved Map Mode

Load an existing saved map with:

```bash
ros2 launch my_robot_bringup map.launch.py map:=/absolute/path/to/map.yaml
```

This starts `nav2_map_server` and its lifecycle manager.

The saved-map loader and `/map` publication have been statically validated. Localization while driving on a saved map still requires dynamic validation.

## Research Data Recording

For localization and skid-steer motion experiments, record the core research topics with:

    cd ~/ros2_ws
    src/my_robot_bringup/scripts/record_research_core.sh

After each experiment, validate the recorded bag before analysis:

    python3 tools/analysis/validate_research_bag.py /path/to/research_core_bag

The validator checks that the required motor RPM, wheel odometry, SBG IMU, and filtered odometry topics contain data and reports their time coverage.

After validation, export the raw per-topic data to CSV with:

    python3 tools/analysis/export_research_core.py /path/to/research_core_bag

Keep the original MCAP bag unchanged. Store exported CSV files, plots, synchronized datasets, and analysis results separately.

The detailed motion experiment procedure is defined in `docs/validation/02_motion_experiment_protocol.md`.

## Navigation

Navigation is intentionally not part of the default static demo startup.

The repository provides the separate launch entry point:

    ros2 launch my_robot_bringup navigation.launch.py

The Nav2 configuration and static prerequisites have been inspected and statically tested where possible.

The complete command path, physical robot response, joystick/manual override, emergency-stop recovery, and dynamic obstacle behavior still require controlled physical validation.

Do not treat autonomous navigation as fully validated until the dynamic validation plan has been completed.

## Validation Documents

- Dynamic validation plan: `docs/validation/01_dynamic_validation_plan.md`
- Motion experiment protocol: `docs/validation/02_motion_experiment_protocol.md`

## Related Documentation

- Main repository guide: `README.md`
- System overview: `docs/architecture/01_system_overview.md`
- Package design: `docs/architecture/02_package_design.md`
- Sensor architecture: `docs/architecture/03_sensor_architecture.md`

Operator troubleshooting and second-platform migration procedures are maintained as separate handoff documents.
