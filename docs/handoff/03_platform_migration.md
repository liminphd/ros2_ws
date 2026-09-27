# Platform Migration Guide

## Purpose

This document describes how to migrate the modular ROS 2 framework from the farm-ng AMIGA platform to another mobile robot without assuming that AMIGA-specific hardware parameters or interfaces are transferable.

The migration goal is to reuse the platform-independent ROS 2 architecture while isolating and replacing platform-specific hardware, geometry, sensor, and control interfaces.

## Migration Principle

Separate the system into three categories:

1. reusable framework components
2. platform-specific components that must be replaced or reconfigured
3. behaviors and assumptions that must be revalidated on the target robot

Do not copy AMIGA hardware parameters to a new platform merely because the ROS 2 graph or launch files start successfully.

## Reusable Framework Components

The following architecture can normally be retained as the starting point for a new platform:

- modular bringup and launch-file structure
- robot description and TF organization pattern
- sensor abstraction and ROS 2 topic organization
- robot_localization-based state-estimation architecture
- SLAM and saved-map workflow structure
- Nav2 configuration structure
- perception pipeline structure
- MCAP research-data recording workflow
- bag validation and offline analysis tools
- validation and handoff methodology

Reuse of the architecture does not mean reuse of every parameter. Hardware-dependent values must be reviewed before target-platform operation.

## Platform-Specific Components

The following components must be reviewed for every target robot. They define the hardware adaptation layer and must not be assumed to be platform-independent.

### 1. Robot Geometry and Description

Review and replace as required:

- URDF/Xacro dimensions and links
- `base_link` and `base_footprint` geometry
- wheel locations and wheel radius
- sensor mounting positions and orientations
- collision and footprint geometry
- static TF relationships

The AMIGA wheel-odometry implementation currently uses the following reference values:

- wheel radius: `0.206 m`
- gear ratio: `30`
- track width: `1.229 m`

These are AMIGA-specific reference values, not framework defaults. Measure or obtain the corresponding parameters for the target platform.

### 2. Base Feedback and Wheel Odometry

The target platform must provide a defined source of base-motion feedback, such as motor RPM, wheel encoder velocity, or native odometry.

On the current AMIGA integration, four received motor values are converted using a platform-specific motor ordering and sign convention before left/right wheel velocity and yaw rate are calculated.

Do not transfer the AMIGA motor ordering or sign convention to another robot without verification.

For the target platform, verify:

- number and ordering of drive motors or wheel encoders
- sign of each wheel during forward and reverse motion
- conversion from raw feedback to wheel linear velocity
- left/right aggregation method
- linear-velocity sign and scale
- angular-velocity sign and scale
- effective track-width behavior during turning or slip

Static zero-speed data cannot validate these relationships. They require controlled low-speed dynamic testing after the target platform is cleared for motion.

### 3. Sensors and Perception

Each sensor must be treated as a platform-specific device even when the downstream ROS 2 topic interface is retained.

For every sensor on the target platform, verify:

- device model and driver
- physical connection and network or serial interface
- ROS 2 topic names and message types
- frame IDs
- mounting position and orientation
- update rate and timestamp behavior
- calibration and covariance information
- launch parameters and device-specific identifiers

### OAK Cameras

The current AMIGA perception pipeline contains platform-specific OAK configuration. Review and replace the following when migrating:

- front and rear camera server URI or network address
- device identity or MXID when used by the camera server
- depth image and camera-info topic names
- optical frame IDs
- camera intrinsics
- camera extrinsics in the robot description
- point-cloud crop-box or ROI limits

Do not assume that AMIGA camera intrinsics, extrinsics, or crop regions are valid for a camera mounted on the target robot.

If the target platform uses different cameras, preserve the downstream ROS 2 interface where practical rather than forcing the new hardware to reproduce AMIGA-specific device configuration.

### LiDAR

The current AMIGA system uses a VLP16-based LiDAR pipeline. A target platform may retain the same downstream scan interface while using a different LiDAR or driver.

Verify the LiDAR driver, frame ID, mounting transform, point-cloud processing, scan generation, range behavior, and the source of `/scan_multi`.

Do not treat the presence of `/scan_multi` alone as proof that the LiDAR geometry or obstacle locations are correct.

### GNSS / INS / IMU

The current localization architecture uses SBG-derived inertial and GNSS data. A target robot may use the same sensor, a different GNSS/INS unit, or separate GNSS and IMU devices.

Verify coordinate convention, frame ID, orientation convention, covariance, update rate, antenna geometry, lever arms, and ROS 2 topic mapping before enabling the data in state estimation.

Do not copy AMIGA sensor extrinsics or GNSS/INS mounting assumptions to another platform.

### 4. Localization Configuration

The localization architecture can be reused, but the fusion configuration must be reviewed for the target platform.

Before reusing an EKF configuration, verify:

- available odometry sources
- IMU orientation and angular-velocity conventions
- wheel-odometry sign, scale, and covariance
- sensor update rates and timestamps
- frame IDs and TF ownership
- which state variables each sensor should contribute
- covariance values and failure behavior
- GNSS/INS availability and global-localization requirements

Do not copy AMIGA EKF covariance or sensor-selection assumptions merely because the target robot publishes topics with similar names.

Validate local odometry first. Add global GNSS-based localization only after the local TF and state-estimation chain is stable.

### 5. Control Interface and Nav2

Control portability must be treated separately from localization and perception portability.

A target robot may use a different command transport, motor controller, native autonomy stack, watchdog, velocity interface, or command-ownership mechanism.

Before connecting Nav2 output to the target base, determine and document:

- the target base command interface
- command message type and units
- linear and angular sign conventions
- command timeout or watchdog behavior
- zero-command behavior
- velocity and acceleration limits
- command ownership and arbitration
- manual or joystick override behavior
- emergency-stop and recovery procedure

Do not assume that a `/cmd_vel` topic means that two robot platforms have equivalent control behavior.

The Nav2 configuration may be reused as a starting structure, but footprint, kinematic limits, controller parameters, velocity smoothing, collision-monitor parameters, and costmap settings must be reviewed for the target robot.

Physical Nav2 testing must occur only after the target platform has independently passed its low-speed manual-control and safety checks.

## Recommended Migration Sequence

Use the following order when bringing the framework onto a new robot. Do not begin with autonomous navigation.

### Phase 1: Static Platform Definition

1. create or update the robot description
2. define `base_link`, `base_footprint`, wheel geometry, and sensor frames
3. verify the static TF tree
4. configure sensor drivers and topic interfaces
5. verify sensor topics, frame IDs, rates, and timestamps without commanding motion

### Phase 2: Passive Base Feedback

1. connect the target platform feedback interface
2. verify raw wheel, encoder, RPM, or native odometry data
3. confirm that stationary feedback is stable
4. record a stationary baseline bag
5. validate the recorded data before proceeding

### Phase 3: Controlled Dynamic Validation

After the target platform is explicitly cleared for motion:

1. verify wheel or encoder signs at very low speed
2. verify forward and reverse linear velocity
3. verify left and right angular-velocity signs
4. compare wheel-derived motion with the independent IMU or GNSS/INS reference
5. characterize platform-specific slip or kinematic error

Do not tune the localization filter to hide an incorrect wheel sign, scale, geometry, or TF relationship.

### Phase 4: Localization and Perception

1. validate local state estimation
2. validate sensor extrinsics against observed geometry
3. validate LiDAR and camera obstacle locations
4. validate SLAM or saved-map localization as required
5. add and validate global GNSS-based localization when required

### Phase 5: Control and Autonomous Navigation

Only after the target base control and safety behavior are understood:

1. validate the base command interface independently
2. validate command timeout, zero command, limits, and manual override
3. connect the navigation command chain
4. validate low-speed path following
5. validate obstacle stop or avoidance behavior
6. validate emergency-stop and recovery behavior

## Migration Acceptance Criteria

The framework should be considered migrated only when the target platform has evidence for the required functions rather than merely a successful build or launch.

At minimum, record whether the following have passed, failed, or remain untested:

- robot description and TF
- sensor publication and timing
- passive base feedback
- wheel or native odometry signs and scale
- local localization
- global localization when required
- perception geometry
- data recording and offline validation
- manual control and safety behavior
- Nav2 path following when required
- obstacle handling when required
- manual override and emergency recovery when required

Keep untested functions explicitly marked as untested. Do not infer target-platform validation from AMIGA results.
