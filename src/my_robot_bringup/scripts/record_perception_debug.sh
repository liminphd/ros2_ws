#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
source "$HOME/ros2_ws/install/setup.bash"

set -u

DATA_ROOT="${AMIGA_BAG_ROOT:-$HOME/ros2_ws/bag_data}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT="${DATA_ROOT}/${STAMP}_perception_debug"

mkdir -p "$DATA_ROOT"

echo "Recording AMIGA perception debug data"
echo "Output: $OUTPUT"
echo "Current profile: LiDAR + local costmap + TF"
echo "Stop safely with Ctrl+C"

ros2 bag record \
  -s mcap \
  -o "$OUTPUT" \
  --topics \
  /scan_multi \
  /local_costmap/costmap \
  /tf \
  /tf_static
