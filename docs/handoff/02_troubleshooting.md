# AMIGA Troubleshooting Guide

## Purpose

This document records known integration issues, diagnostic checks, and recovery boundaries for the ROS 2 framework on the farm-ng AMIGA platform.

Use read-only diagnostics first. Do not change native AMIGA services, CAN configuration, sensor power, device ownership, or control-chain components merely to make an error disappear.

## Troubleshooting Principles

1. Identify whether the failure is in hardware, network transport, ROS 2 publication, TF, localization, perception, or the control chain before changing configuration.
2. Prefer passive inspection of processes, topics, TF, services, logs, and network state before restarting components.
3. Do not restart or reconfigure the native CAN interface as a generic troubleshooting step.
4. Do not open or reconfigure the SBG serial device while another SBG driver instance may own it.
5. Do not allow the native Furrow Assist stack and the custom ROS 2 OAK servers to own the Ethernet OAK cameras simultaneously.
6. Do not treat a successful static startup as proof that physical navigation, obstacle avoidance, joystick override, or emergency recovery has been validated.

## Known Issue 1: OAK Camera Ownership Conflict

The Ethernet OAK cameras cannot be used simultaneously by the native farm-ng Furrow Assist pipeline and the custom ROS 2 OAK camera servers.

Symptoms can include failure to open an OAK device, missing camera streams, or a custom camera server failing while the native Furrow Assist service is active.

### Read-Only Diagnosis

First determine whether the native Furrow Assist service is active on the AMIGA Brain and whether custom OAK servers are already running.

On the AMIGA Brain, inspect the Furrow Assist service without changing its state:

    systemctl status farmng-furrow_assist_25_0.service --no-pager

Inspect relevant processes:

    ps aux | grep -Ei "furrow|depthai|oak|camera" | grep -v grep

On the ROS 2 computer, inspect whether the expected camera topics are present:

    ros2 topic list | grep -E "^/camera/(front|rear)/"

If Furrow Assist is active and the custom OAK pipeline cannot open the cameras, treat device ownership as the first suspected cause. Do not repeatedly restart both pipelines.

### Ownership Boundary

Use only one OAK ownership mode at a time:

- Native mode: farm-ng Furrow Assist owns the OAK cameras.
- ROS 2 mode: the custom OAK servers own the cameras and publish data for the ROS 2 perception pipeline.

Changing between these modes is an intentional operational action, not a generic troubleshooting step. Confirm the required mode before stopping or starting any service.

## Known Issue 2: DepthAI Overlay / Underlay Build Warning

During a workspace build, colcon may report that `depthai_ros_driver_v3` exists both in the workspace install tree and in the ROS 2 Jazzy underlay.

The observed build completed successfully despite this warning. Therefore, do not interpret the warning alone as a build failure.

### Diagnosis

Check whether the build actually completed and inspect the package locations:

    ros2 pkg prefix depthai_ros_driver_v3

    find ~/ros2_ws/install /opt/ros/jazzy -maxdepth 2 -type d -name "depthai_ros_driver_v3" 2>/dev/null

If colcon reports a successful build and the existing camera pipeline is functioning, do not modify the DepthAI installation merely to remove the warning.

The warning matters because overriding a package from an underlay can cause include-order, API, or ABI compatibility problems if the overlay and underlay versions differ.

Do not use `--allow-overriding depthai_ros_driver_v3` as an automatic fix. First determine which package version the project is intended to use and verify compatibility.

## Known Issue 3: AMIGA Base Feedback / CAN Data Path

The ROS 2 base-feedback path is intended to receive AMIGA motor RPM data passively and convert it into wheel odometry. It must not be confused with the robot command path.

### Expected ROS 2 Topics

The main feedback topics are:

    /amiga/motor_rpm
    /wheel/odometry

Use read-only ROS 2 inspection to check whether they exist and contain data:

    ros2 topic info /amiga/motor_rpm
    ros2 topic info /wheel/odometry
    ros2 topic hz /amiga/motor_rpm
    ros2 topic hz /wheel/odometry

When the robot is stationary, zero motor RPM and zero wheel velocity are valid observations and do not by themselves indicate a fault.

### AMIGA Brain Checks

If motor RPM data is missing, inspect the native CAN interface and passive forwarding process before changing anything:

    systemctl status farmng-can-interface.service --no-pager

    ps aux | grep -Ei "can_motor_sender|candump" | grep -v grep

The native CAN interface is part of the AMIGA platform. Do not stop, restart, change bitrate, or reconfigure it as a generic ROS 2 troubleshooting action.

Do not use CAN transmit commands to diagnose a missing feedback topic. Feedback diagnosis should remain read-only until the hardware and control state are explicitly cleared for motion testing.

### Wheel Odometry Interpretation

Wheel odometry is derived from the received motor RPM values using the configured wheel radius, gear ratio, motor sign convention, and track width.

The current RPM-to-wheel mapping and yaw sign must be confirmed during controlled dynamic validation. Static zero-speed data cannot prove the dynamic sign convention or skid-steer yaw accuracy.

## Known Issue 4: TF, Localization, and SBG Ownership

Localization failures can originate from missing TF, missing sensor topics, duplicate sensor drivers, or incorrect frame ownership. Check these separately before changing EKF parameters.

### Read-Only ROS 2 Checks

Inspect the relevant nodes and topics:

    ros2 node list | sort

    ros2 topic list | grep -E "sbg|imu|odometry|tf"

Check the local filtered odometry:

    ros2 topic hz /odometry/filtered

    ros2 topic echo /odometry/filtered --once

Check the SBG IMU stream:

    ros2 topic hz /sbg/imu_data

    ros2 topic echo /sbg/imu_data --once

### TF Checks

For the local localization chain, verify that the required transforms are available before blaming the EKF:

    ros2 run tf2_ros tf2_echo odom base_link

For SLAM or map-based workflows, also inspect the map-to-odom relationship when the corresponding localization component is running:

    ros2 run tf2_ros tf2_echo map odom

Missing or conflicting transforms should be diagnosed at their publisher before adding another TF publisher.

### Duplicate SBG Driver Check

More than one SBG driver instance can create serial-device ownership problems, duplicate ROS 2 nodes, or conflicting frame behavior.

If multiple SBG-related nodes or processes appear, identify how each instance was started before stopping, restarting, or launching another driver.

Do not open or reconfigure the SBG serial port as a generic recovery action. Preserve the existing working sensor configuration until the ownership problem is understood.

The local EKF and the GNSS/global localization workflow are separate validation stages. A working local `/odometry/filtered` stream does not by itself prove that outdoor GNSS/global localization is correct.

## Known Issue 5: SLAM, Saved Map, and Perception

Mapping and navigation depend on several upstream data paths. Diagnose sensor input, TF, and map publication separately instead of treating every Nav2 symptom as a navigation failure.

### SLAM Input Checks

When SLAM is already running, inspect the laser input and map output:

    ros2 topic hz /scan_multi

    ros2 topic hz /map

Also verify the required TF relationship:

    ros2 run tf2_ros tf2_echo map odom

If `/scan_multi` is missing, diagnose the LiDAR and scan-processing path before changing SLAM parameters.

If scan data is present but the map-to-odom transform is missing, identify whether SLAM is running and publishing the expected transform before adding another TF publisher.

### Saved Map Checks

When the saved-map workflow is already running, inspect map publication with:

    ros2 topic info /map

    ros2 topic echo /map --once

The saved-map loader has been statically validated. Successful `/map` publication does not prove localization accuracy while the robot is moving.

### Perception Checks

Inspect the expected perception topics before changing Nav2 costmap parameters:

    ros2 topic hz /scan_multi

    ros2 topic list | grep -E "^/camera/(front|rear)/"

If OAK topics are missing, check camera ownership first. If LiDAR-derived data are missing, diagnose the LiDAR and scan-processing path independently.

Static obstacle-layer inputs and TF prerequisites have been validated, but dynamic obstacle stop/avoidance behavior still requires controlled physical testing.

## Stop Conditions and Escalation

Stop software troubleshooting and confirm the hardware or operational state before proceeding if any of the following occurs:

- a fuse, emergency-stop, power, motor-controller, or other hardware safety issue is unresolved
- the expected AMIGA native service state is unknown
- CAN errors appear together with unexpected hardware behavior
- more than one process may own the same camera or serial device
- TF or sensor data become inconsistent after starting a duplicate driver
- a proposed diagnostic step would transmit a motion command or modify the control chain

Do not bypass a hardware restriction with software configuration changes.

After a hardware or control issue is resolved, resume validation from the relevant earlier phase rather than jumping directly to autonomous navigation.

For physical motion testing, follow `docs/validation/01_dynamic_validation_plan.md` and `docs/validation/02_motion_experiment_protocol.md`.

## Related Handoff Documents

- Operator guide: `docs/handoff/01_operator_guide.md`
- Dynamic validation plan: `docs/validation/01_dynamic_validation_plan.md`
- Motion experiment protocol: `docs/validation/02_motion_experiment_protocol.md`
- Main repository guide: `README.md`
