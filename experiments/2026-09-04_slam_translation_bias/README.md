# SLAM Translation Bias Experiments
Date: 2026-09-04
Platform: Farm-ng AMIGA
ROS 2: Jazzy

## Current baseline

SLAM input:
- scan_topic: /scan_multi
- pointcloud_to_laserscan target_frame: base_link
- height range: -0.50 to +0.30 m
- range_max: 20.0 m

slam_toolbox:
- minimum_time_interval: 0.1
- minimum_travel_distance: 0.1
- minimum_travel_heading: 0.5
- correlation_search_space_dimension: 0.1
- distance_variance_penalty: 0.5
- max_laser_range: 20.0

Wheel odometry:
- effective rolling radius: 0.206 m

## Main observations

1. Wheel odometry / EKF forward distance is accurate.
2. SBG gyro and EKF yaw agree very closely.
3. Single-ring /scan produced large SLAM yaw errors.
4. /scan_multi significantly improved SLAM yaw estimation.
5. SLAM translation still shows motion-dependent bias.
6. Physical lateral deviation remains only a few centimeters,
   while SLAM can introduce tens of centimeters of translation correction.
7. Forward and reverse motion can produce opposite-sign lateral SLAM corrections.

## Important experiments

### Single-ring /scan yaw test
Gyro integrated: +6.364 deg
EKF d_yaw: +6.355 deg
SLAM d_yaw: +17.152 deg
SLAM - gyro: +10.789 deg

### /scan_multi yaw test - left turn
Gyro: +12.003 deg
EKF: +12.046 deg
SLAM: +12.160 deg
SLAM - gyro: +0.158 deg

### /scan_multi yaw test - right turn
Gyro: -17.623 deg
EKF: -17.684 deg
SLAM: -17.684 deg
SLAM - gyro: -0.061 deg

### 5 m forward test
EKF:
- forward: +4.987 m
- lateral: +0.047 m
- yaw: +1.172 deg

SLAM:
- forward: +4.971 m
- lateral: -0.250 m
- yaw: +1.574 deg

SLAM - EKF lateral: -0.297 m

Physical lateral was only a few centimeters.

### 5 m reverse test
EKF:
- forward: -5.174 m
- lateral: +0.030 m
- yaw: -0.678 deg

SLAM:
- forward: -5.000 m
- lateral: +0.350 m
- yaw: -0.078 deg

SLAM - EKF lateral: +0.320 m

Physical position remained close to the reference line,
approximately 2-3 cm lateral offset.

### map->odom logger, correlation_search_space_dimension = 0.1
Fresh start:
x = 0
y = 0
yaw = 0 deg

After approximately 5 m:
x ≈ +0.305 m
y ≈ -0.161 m
yaw ≈ +0.800 deg

Total translation correction ≈ 0.345 m.

## Current conclusion

The main remaining SLAM issue is not yaw.

The dominant problem is motion-dependent translation correction from scan matching.

Physical trajectory remains close to the reference line, while slam_toolbox introduces translation corrections on the order of tens of centimeters.

This should be treated as a localization reliability issue rather than a wheel odometry or IMU failure.
