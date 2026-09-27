#!/usr/bin/env python3

import argparse
from collections import Counter
from pathlib import Path

import rosbag2_py


REQUIRED_TOPICS = {
    "/amiga/motor_rpm",
    "/wheel/odometry",
    "/sbg/imu_data",
    "/odometry/filtered",
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate core topic coverage in an AMIGA research bag."
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

    counts = Counter()
    first_time_ns = {}
    last_time_ns = {}

    while reader.has_next():
        topic, _, bag_time_ns = reader.read_next()

        if topic in REQUIRED_TOPICS:
            counts[topic] += 1

            if topic not in first_time_ns:
                first_time_ns[topic] = bag_time_ns

            last_time_ns[topic] = bag_time_ns

    print(f"Bag: {bag}")
    print()
    print("===== REQUIRED TOPIC COVERAGE =====")

    passed = True

    for topic in sorted(REQUIRED_TOPICS):
        count = counts[topic]

        if topic not in topic_types:
            status = "MISSING"
            passed = False
        elif count == 0:
            status = "ZERO MESSAGES"
            passed = False
        else:
            status = "PASS"

        print(f"{topic:25s} count={count:6d}  {status}")

    print()
    print("===== TOPIC TIME COVERAGE =====")

    for topic in sorted(REQUIRED_TOPICS):
        if counts[topic] == 0:
            print(f"{topic:25s} no messages")
            continue

        duration_s = (
            last_time_ns[topic] - first_time_ns[topic]
        ) / 1e9

        print(
            f"{topic:25s}"
            f" duration={duration_s:8.3f} s"
            f" first={first_time_ns[topic]}"
            f" last={last_time_ns[topic]}"
        )

    print()
    print("===== RESULT =====")

    if passed:
        print("PASS: all required research topics contain messages.")
    else:
        print("FAIL: bag is incomplete for core motion research.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
