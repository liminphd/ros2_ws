# AMIGA Motion Experiment Protocol

## Purpose

This protocol defines repeatable motion experiments for characterising
wheel-odometry error on the AMIGA skid-steer platform.

The main quantity of interest is:

`e_omega = omega_wheel - omega_INS`

The experiments study how wheel-derived yaw-rate error varies with:

- left/right motor RPM difference
- vehicle yaw rate
- forward velocity
- turning direction
- motion pattern
- surface/terrain condition

Dynamic experiments must not begin until the hardware/fuse issue has been
resolved and Phase 0 and Phase 1 of `01_dynamic_validation_plan.md` have
been completed.

## Baseline Experiment Matrix

| ID | Motion | Level | Main Purpose |
|---|---|---|---|
| E01 | Stationary | baseline | Sensor/noise baseline |
| E02 | Straight | low | Low-speed straight baseline |
| E03 | Straight | medium | Speed effect during straight motion |
| E04 | Left turn | low | Low-speed left skid-steer error |
| E05 | Right turn | low | Low-speed right skid-steer error |
| E06 | Left turn | medium | Turning-rate/speed effect |
| E07 | Right turn | medium | Turning-rate/speed effect |
| E08 | S-curve | low | Direction-change/transient behaviour |
| E09 | Mixed path | variable | Combined representative motion |

Exact low and medium test speeds must be selected only after basic motion
and safety validation.

## Data Recording

Use `src/my_robot_bringup/scripts/record_research_core.sh` as the primary
recorder for motion experiments.

The recorder includes:

- `/amiga/motor_rpm`
- `/wheel/odometry`
- `/imu/data_cov`
- `/odometry/filtered`
- `/sbg/imu_data`
- `/sbg/ekf_euler`
- `/sbg/ekf_nav`
- `/sbg/gps_hdt`
- `/sbg/gps_pos`
- `/sbg/gps_vel`
- `/tf`
- `/tf_static`

Do not begin a formal run unless the required topics are present and updating.

## Standard Run Procedure

For every experiment:

1. Position the robot at the test start point.
2. Confirm the test area is clear.
3. Confirm emergency-stop/manual intervention is available.
4. Start `record_research_core.sh`.
5. Keep the robot stationary for approximately 10 seconds.
6. Execute the planned motion.
7. Stop the robot completely.
8. Keep the robot stationary for approximately 10 seconds.
9. Stop the MCAP recording with `Ctrl+C`.
10. Record the experiment metadata immediately.

Raw MCAP data should remain unchanged after recording.

## Required Metadata

Record the following for every run:

- experiment ID
- date and time
- MCAP directory name
- robot/platform
- operator
- test location
- surface/terrain condition
- motion type
- commanded speed or control setting
- approximate test duration
- GNSS/RTK status if available
- unusual wheel slip
- obstacle or operator intervention
- sensor or system abnormalities
- additional notes

## Primary Analysis Variables

The initial analysis should extract or derive:

- left motor RPM
- right motor RPM
- `|RPM_L - RPM_R|`
- wheel-derived forward velocity
- wheel-derived yaw rate
- INS yaw rate
- filtered odometry forward velocity
- filtered odometry yaw rate
- `e_omega = omega_wheel - omega_INS`
- time

Preserve original timestamps and raw measurements before filtering,
interpolation, synchronization, or resampling.

## Initial Analysis Questions

1. How large is wheel-derived yaw-rate error during straight motion?
2. How does the error change during left and right turns?
3. Does error magnitude increase with `|RPM_L - RPM_R|`?
4. Does error magnitude increase with vehicle yaw rate?
5. Does forward speed affect the error?
6. Is the relationship symmetric between left and right turns?
7. How large are transient errors when steering direction changes?
8. Does the relationship change with surface or terrain?

## Data Integrity Rule

Raw MCAP recordings are the primary experimental record and should remain
unchanged.

Derived CSV files, plots, filtered signals, and analysis results should be
generated separately from the raw recordings.

A run should not be treated as valid research data until its topic coverage,
timestamps, and experiment metadata have been checked.
