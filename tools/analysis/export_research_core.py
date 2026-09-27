#!/usr/bin/env python3

import argparse
import csv
import math
from collections import Counter
from pathlib import Path

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


CORE_TOPICS = {
    "/amiga/motor_rpm",
    "/wheel/odometry",
    "/sbg/imu_data",
    "/odometry/filtered",
}

# Must match wheel_odometry.py.
WHEEL_RADIUS_M = 0.206
GEAR_RATIO = 30.0
TRACK_WIDTH_M = 1.229


def stamp_to_ns(stamp):
    """Convert a ROS builtin_interfaces/Time message to nanoseconds."""
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def motor_rpm_to_motion(data):
    """Convert AMIGA A/B/C/D motor RPM values to wheel-side motion."""
    if len(data) != 4:
        raise ValueError(f"Expected 4 motor RPM values, got {len(data)}")

    a, b, c, d = data

    k = 2.0 * math.pi * WHEEL_RADIUS_M / (60.0 * GEAR_RATIO)

    # AMIGA motor orientation:
    # A = right rear
    # B = left rear (sign inverted)
    # C = left front (sign inverted)
    # D = right front
    rr = a * k
    rl = -b * k
    fl = -c * k
    fr = d * k

    left_mps = 0.5 * (rl + fl)
    right_mps = 0.5 * (rr + fr)

    linear_mps = 0.5 * (left_mps + right_mps)
    angular_rad_s = (right_mps - left_mps) / TRACK_WIDTH_M

    return {
        "motor_a_rpm": a,
        "motor_b_rpm": b,
        "motor_c_rpm": c,
        "motor_d_rpm": d,
        "left_mps": left_mps,
        "right_mps": right_mps,
        "linear_mps_recalc": linear_mps,
        "angular_rad_s_recalc": angular_rad_s,
    }


def write_csv(path, rows):
    """Write extracted rows without modifying or resampling timestamps."""
    if not rows:
        print(f"WARNING: no rows for {path.name}")
        return

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect an AMIGA research_core MCAP bag."
    )
    parser.add_argument(
        "bag",
        type=Path,
        help="Path to a rosbag2 research_core directory",
    )
    args = parser.parse_args()

    bag = args.bag.expanduser().resolve()

    if not bag.is_dir():
        raise SystemExit(f"ERROR: bag directory not found: {bag}")

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(
            uri=str(bag),
            storage_id="mcap",
        ),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        ),
    )

    topic_types = {
        info.name: info.type
        for info in reader.get_all_topics_and_types()
    }

    missing = sorted(CORE_TOPICS - set(topic_types))
    if missing:
        raise SystemExit(
            "ERROR: required topics missing from bag metadata:\n  "
            + "\n  ".join(missing)
        )

    counts = Counter()
    first_values = {}

    rows = {
        "/amiga/motor_rpm": [],
        "/wheel/odometry": [],
        "/sbg/imu_data": [],
        "/odometry/filtered": [],
    }

    while reader.has_next():
        topic, raw, bag_time_ns = reader.read_next()

        if topic not in CORE_TOPICS:
            continue

        msg_type = get_message(topic_types[topic])
        msg = deserialize_message(raw, msg_type)

        counts[topic] += 1

        if topic == "/amiga/motor_rpm":
            motion = motor_rpm_to_motion(list(msg.data))
            rows[topic].append({
                "bag_time_ns": bag_time_ns,
                **motion,
            })

        elif topic == "/wheel/odometry":
            rows[topic].append({
                "bag_time_ns": bag_time_ns,
                "header_time_ns": stamp_to_ns(msg.header.stamp),
                "linear_x": msg.twist.twist.linear.x,
                "angular_z": msg.twist.twist.angular.z,
            })

        elif topic == "/sbg/imu_data":
            rows[topic].append({
                "bag_time_ns": bag_time_ns,
                "header_time_ns": stamp_to_ns(msg.header.stamp),
                "gyro_x": msg.gyro.x,
                "gyro_y": msg.gyro.y,
                "gyro_z": msg.gyro.z,
            })

        elif topic == "/odometry/filtered":
            rows[topic].append({
                "bag_time_ns": bag_time_ns,
                "header_time_ns": stamp_to_ns(msg.header.stamp),
                "linear_x": msg.twist.twist.linear.x,
                "angular_z": msg.twist.twist.angular.z,
            })

        if topic not in first_values:
            if topic == "/amiga/motor_rpm":
                value = list(msg.data)

            elif topic == "/wheel/odometry":
                value = {
                    "linear_x": msg.twist.twist.linear.x,
                    "angular_z": msg.twist.twist.angular.z,
                }

            elif topic == "/sbg/imu_data":
                value = {
                    "frame_id": msg.header.frame_id,
                    "gyro_z": msg.gyro.z,
                }

            else:
                value = {
                    "linear_x": msg.twist.twist.linear.x,
                    "angular_z": msg.twist.twist.angular.z,
                }

            first_values[topic] = (bag_time_ns, value)

    output_dir = bag.parent / f"{bag.name}_csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_outputs = {
        "/amiga/motor_rpm": output_dir / "motor_rpm.csv",
        "/wheel/odometry": output_dir / "wheel_odometry.csv",
        "/sbg/imu_data": output_dir / "sbg_imu.csv",
        "/odometry/filtered": output_dir / "filtered_odometry.csv",
    }

    for topic, path in csv_outputs.items():
        write_csv(path, rows[topic])

    print(f"Bag: {bag}")
    print(f"CSV output: {output_dir}")
    print()
    print("===== CORE TOPIC COUNTS =====")

    for topic in sorted(CORE_TOPICS):
        print(f"{topic:25s} {counts[topic]}")

    print()
    print("===== EXTRACTED ROW COUNTS =====")
    for topic in sorted(CORE_TOPICS):
        print(f"{topic:25s} {len(rows[topic])}")

    print()
    print("===== FIRST EXTRACTED ROW =====")
    for topic in sorted(CORE_TOPICS):
        if rows[topic]:
            print(f"{topic}: {rows[topic][0]}")

    print()
    print("===== FIRST VALUES =====")

    for topic in sorted(CORE_TOPICS):
        if topic not in first_values:
            print(f"{topic}: NO MESSAGES")
            continue

        timestamp, value = first_values[topic]
        print(f"{topic}")
        print(f"  bag_time_ns: {timestamp}")
        print(f"  value: {value}")


if __name__ == "__main__":
    main()
