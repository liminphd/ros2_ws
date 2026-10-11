#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus

BASE = Path.home() / "ros2_ws/src/my_robot_description"
CSV = Path.home() / "ros2_ws/logs/full_coverage/safe_coverage_waypoints.csv"

# Maximum permitted centerline deviation from each prescribed
# straight segment. This is a route-fidelity threshold, not
# a substitute for footprint collision checking.
MAX_DEVIATION = 0.35
ENDPOINT_TOL = 0.30

def heading(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])

def pose(node, x, y, yaw):
    p = PoseStamped()
    p.header.frame_id = "map"
    p.header.stamp = node.get_clock().now().to_msg()
    p.pose.position.x = float(x)
    p.pose.position.y = float(y)
    p.pose.orientation.z = math.sin(yaw / 2)
    p.pose.orientation.w = math.cos(yaw / 2)
    return p

def deviation(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    if d2 == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0., min(1., ((p[0]-ax)*dx + (p[1]-ay)*dy)/d2))
    return math.hypot(p[0]-(ax+t*dx), p[1]-(ay+t*dy))

def run():
    with CSV.open() as f:
        waypoints = [
            (float(r["x"]), float(r["y"]))
            for r in csv.DictReader(f)
        ]

    rclpy.init()
    node = Node("full_coverage_nav2_preflight")
    client = ActionClient(node, ComputePathToPose,
                          "/compute_path_to_pose")

    if not client.wait_for_server(timeout_sec=15):
        print("ERROR: /compute_path_to_pose unavailable")
        node.destroy_node()
        rclpy.shutdown()
        return

    print("===== NAV2 FULL ROUTE PREFLIGHT =====")
    print("Waypoint count:", len(waypoints))
    print("Segments:", len(waypoints)-1)
    print("No movement commands will be sent.")
    print()

    passed = 0
    failed = 0

    for i, (a, b) in enumerate(zip(waypoints[:-1], waypoints[1:])):
        yaw = heading(a, b)

        goal = ComputePathToPose.Goal()
        goal.start = pose(node, *a, yaw)
        goal.goal = pose(node, *b, yaw)
        goal.use_start = True
        goal.planner_id = "GridBased"

        future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, future,
                                         timeout_sec=30)

        if not future.done():
            print(f"SEG {i:02d}: FAIL - goal timeout")
            failed += 1
            continue

        handle = future.result()
        if handle is None or not handle.accepted:
            print(f"SEG {i:02d}: FAIL - goal rejected")
            failed += 1
            continue

        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(
            node, result_future, timeout_sec=45
        )

        if not result_future.done():
            print(f"SEG {i:02d}: FAIL - result timeout")
            failed += 1
            continue

        outcome = result_future.result()

        if outcome is None or outcome.status != GoalStatus.STATUS_SUCCEEDED:
            code = getattr(outcome.result, "error_code", "unknown") \
                if outcome is not None else "unknown"
            print(f"SEG {i:02d}: FAIL - Nav2 error={code}")
            failed += 1
            continue

        path = outcome.result.path.poses

        if len(path) < 2:
            print(f"SEG {i:02d}: FAIL - empty path")
            failed += 1
            continue

        xy = [(p.pose.position.x, p.pose.position.y) for p in path]
        max_dev = max(deviation(p, a, b) for p in xy)

        start_err = math.dist(xy[0], a)
        finish_err = math.dist(xy[-1], b)
        length = sum(math.dist(p, q) for p, q in zip(xy[:-1], xy[1:]))

        ok = (max_dev <= MAX_DEVIATION and
              start_err <= ENDPOINT_TOL and
              finish_err <= ENDPOINT_TOL)

        status = "PASS" if ok else "REVIEW"

        print(
            f"SEG {i:02d}: {status} "
            f"({a[0]:.2f},{a[1]:.2f}) -> "
            f"({b[0]:.2f},{b[1]:.2f}) "
            f"length={length:.2f}m "
            f"max_dev={max_dev:.2f}m "
            f"start_err={start_err:.2f}m "
            f"end_err={finish_err:.2f}m"
        )

        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print("===== PREFLIGHT SUMMARY =====")
    print("PASS:", passed)
    print("FAIL/REVIEW:", failed)

    if failed == 0:
        print("All segments passed the route-fidelity check.")
        print("Footprint and controller execution checks still required.")
    else:
        print("Do not execute the full mission yet.")
        print("Review failed segments before continuing.")

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    run()
