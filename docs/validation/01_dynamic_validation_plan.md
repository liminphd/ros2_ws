# AMIGA Dynamic Validation Plan

## Purpose

This document defines the validation sequence to be followed after the
AMIGA motion-control hardware is confirmed safe and operational.

Dynamic tests must not begin until the hardware fault/fuse issue has been
resolved and normal manual control has been confirmed.

The purpose is to validate the system progressively from basic motion safety
to autonomous navigation, rather than enabling the complete autonomous stack
at once.

## Phase 0 — Preconditions

- [ ] fuse/hardware issue resolved
- [ ] robot powers up normally
- [ ] emergency stop available and verified
- [ ] test area is clear
- [ ] operator is ready for immediate manual intervention
- [ ] ROS 2 sensor and feedback topics are healthy
- [ ] research MCAP recorder is ready

## Phase 1 — Basic Motion and Safety

- [ ] verify native/manual forward motion
- [ ] verify native/manual reverse motion
- [ ] verify left/right turning
- [ ] verify commanded direction matches robot motion
- [ ] verify robot stops when command input stops
- [ ] verify emergency-stop behavior
- [ ] verify recovery after emergency stop
- [ ] verify joystick/manual override

## Phase 2 — Motion Feedback and Localization

During low-speed controlled motion:

- [ ] verify `/amiga/motor_rpm`
- [ ] verify `/wheel/odometry`
- [ ] verify SBG IMU/INS data
- [ ] verify `/odometry/filtered`
- [ ] verify `odom -> base_link`
- [ ] record a research MCAP dataset
- [ ] compare wheel-derived and INS yaw rate

## Phase 3 — Mapping and Saved Map

- [ ] perform low-speed driven SLAM
- [ ] verify `/scan_multi` during motion
- [ ] verify map quality in RViz
- [ ] save the generated map
- [ ] restart using the saved map
- [ ] verify saved-map loading
- [ ] verify localization against the saved map

## Phase 4 — Navigation

- [ ] validate a short A-to-B navigation goal
- [ ] verify planned path
- [ ] verify local and global costmaps
- [ ] verify velocity command chain
- [ ] validate turning behavior
- [ ] validate multi-goal or longer-path navigation

## Phase 5 — Obstacle Handling

- [ ] verify static obstacle detection
- [ ] verify obstacle marking and clearing
- [ ] verify autonomous obstacle avoidance
- [ ] verify Collision Monitor slowdown/stop behavior
- [ ] verify operator/manual takeover

## Phase 6 — AMIGA Trajectory Workflow

- [ ] record a native AMIGA trajectory
- [ ] save the trajectory
- [ ] reload the saved trajectory
- [ ] validate trajectory reuse outdoors

## Phase 7 — End-to-End Demonstration

From a clean startup:

- [ ] start the documented sensor and ROS 2 stack
- [ ] establish localization
- [ ] load or create a map
- [ ] execute autonomous navigation
- [ ] demonstrate obstacle handling
- [ ] demonstrate operator override
- [ ] record experiment data
- [ ] shut down cleanly

## Validation Rule

A task should be marked complete only after it has been physically or
experimentally verified. Static configuration checks must not be reported
as successful dynamic validation.
