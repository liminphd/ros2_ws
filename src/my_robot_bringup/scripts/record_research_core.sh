#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
source "$HOME/ros2_ws/install/setup.bash"

set -u

DATA_ROOT="${AMIGA_BAG_ROOT:-$HOME/ros2_ws/bag_data}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT="${DATA_ROOT}/${STAMP}_research_core"

mkdir -p "$DATA_ROOT"

echo "Recording AMIGA research core data"
echo "Output: $OUTPUT"
echo "Stop safely with Ctrl+C"

ros2 bag record \
  -s mcap \
  -o "$OUTPUT" \
  --topics \
  /amiga/motor_rpm \
  /wheel/odometry \
  /imu/data_cov \
  /odometry/filtered \
  /sbg/imu_data \
  /sbg/ekf_euler \
  /sbg/ekf_nav \
  /sbg/gps_hdt \
  /sbg/gps_pos \
  /sbg/gps_vel \
  /tf \
  /tf_static
