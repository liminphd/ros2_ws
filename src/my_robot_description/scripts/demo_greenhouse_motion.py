#!/usr/bin/env python3
import argparse
import csv
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image
import yaml

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose, FollowPath
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus

BASE = Path.home() / "ros2_ws/src/my_robot_description"
OUT = Path.home() / "ros2_ws/logs/full_coverage"
OUT.mkdir(parents=True, exist_ok=True)

CFG = yaml.safe_load(
    (BASE / "maps/greenhouse_working_map.yaml").read_text()
)
IMG = np.asarray(
    Image.open(BASE / "maps" / CFG["image"]).convert("L")
)
H, W = IMG.shape
RES = float(CFG["resolution"])
OX, OY, _ = CFG["origin"]

# 1.41 x 0.80 m body plus 0.20 m margin
U, V = np.meshgrid(
    np.linspace(-0.905, 0.905, 47),
    np.linspace(-0.60, 0.60, 31)
)
U, V = U.ravel(), V.ravel()

START = (141.0, 3.0)
DEST = (141.8, 7.75)
DEST_YAW = math.pi

def free(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    wx = x + c * U - s * V
    wy = y + s * U + c * V

    ix = np.rint((wx - OX) / RES).astype(int)
    iy = H - 1 - np.rint((wy - OY) / RES).astype(int)

    if np.any((ix < 0) | (ix >= W) |
              (iy < 0) | (iy >= H)):
        return False

    return bool(np.all(IMG[iy, ix] >= 250))

def pose(node, x, y, yaw):
    msg = PoseStamped()
    msg.header.frame_id = "map"
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.pose.position.x = float(x)
    msg.pose.position.y = float(y)
    msg.pose.orientation.z = math.sin(yaw / 2)
    msg.pose.orientation.w = math.cos(yaw / 2)
    return msg

def wait_future(node, future, seconds):
    rclpy.spin_until_future_complete(
        node, future, timeout_sec=seconds
    )
    if not future.done():
        raise RuntimeError("Action response timeout")
    result = future.result()
    if result is None:
        raise RuntimeError("Action response unavailable")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    rclpy.init()
    node = Node("greenhouse_motion_demo")
    planner = ActionClient(
        node, ComputePathToPose, "/compute_path_to_pose"
    )
    follower = ActionClient(
        node, FollowPath, "/follow_path"
    )

    handle = None

    try:
        if not planner.wait_for_server(timeout_sec=15):
            raise RuntimeError("Planner unavailable")

        print("===== GREENHOUSE MOTION DEMO =====")
        print("Start:", START)
        print("Goal:", DEST)

        # Read current Gazebo ground-truth pose before planning.
        current_msgs = []
        sub = node.create_subscription(
            PoseStamped,
            "/gazebo/amiga/ground_truth",
            lambda msg: current_msgs.append(msg),
            10
        )

        deadline = time.monotonic() + 8
        while not current_msgs and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)

        if not current_msgs:
            raise RuntimeError("Ground Truth unavailable")

        current_pose = current_msgs[-1].pose
        sx = current_pose.position.x
        sy = current_pose.position.y
        q = current_pose.orientation
        syaw = math.atan2(
            2.0 * (q.w*q.z + q.x*q.y),
            1.0 - 2.0 * (q.y*q.y + q.z*q.z)
        )
        print(f"Live start: ({sx:.3f}, {sy:.3f}), yaw={math.degrees(syaw):.1f} deg")

        goal = ComputePathToPose.Goal()
        goal.start = pose(node, sx, sy, syaw)
        goal.goal = pose(node, *DEST, DEST_YAW)
        goal.planner_id = "GridBased"
        goal.use_start = True

        handle_plan = wait_future(
            node, planner.send_goal_async(goal), 20
        )

        if not handle_plan.accepted:
            raise RuntimeError("Planner rejected goal")

        result = wait_future(
            node, handle_plan.get_result_async(), 45
        )

        if result.status != GoalStatus.STATUS_SUCCEEDED:
            raise RuntimeError(
                f"Planning failed: {result.status}"
            )

        path = result.result.path
        xy = [
            (p.pose.position.x, p.pose.position.y)
            for p in path.poses
        ]

        if len(xy) < 2:
            raise RuntimeError("Empty path")

        length = sum(
            math.dist(a, b)
            for a, b in zip(xy[:-1], xy[1:])
        )

        print("Path points:", len(xy))
        print("Length:", round(length, 2), "m")

        # Audit straight path and heading transitions.
        issues = []
        previous_heading = None

        for i, (a, b) in enumerate(zip(xy[:-1], xy[1:])):
            dx, dy = b[0]-a[0], b[1]-a[1]
            distance = math.hypot(dx, dy)

            if distance < 1e-7:
                continue

            heading = math.atan2(dy, dx)

            if previous_heading is not None:
                delta = math.atan2(
                    math.sin(heading-previous_heading),
                    math.cos(heading-previous_heading)
                )
                n = max(
                    1,
                    math.ceil(abs(delta)/math.radians(3))
                )
                for j in range(n+1):
                    yaw = previous_heading + delta*j/n
                    if not free(a[0], a[1], yaw):
                        issues.append(("TURN", i, *a))
                        break

            n = max(1, math.ceil(distance / 0.025))
            for j in range(n+1):
                t = j/n
                x = a[0] + t*dx
                y = a[1] + t*dy

                if not free(x, y, heading):
                    issues.append(("MOVE", i, x, y))
                    break

            previous_heading = heading

        # Check terminal rotation to required heading.
        if previous_heading is not None:
            delta = math.atan2(
                math.sin(DEST_YAW-previous_heading),
                math.cos(DEST_YAW-previous_heading)
            )
            n = max(
                1, math.ceil(abs(delta)/math.radians(3))
            )
            for j in range(n+1):
                yaw = previous_heading + delta*j/n
                if not free(*xy[-1], yaw):
                    issues.append(("FINAL TURN", len(xy)-1, *xy[-1]))
                    break

        csv_path = OUT / "demo_access_planned_path.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])
            writer.writerows(xy)

        print("Footprint issues:", len(issues))
        for item in issues[:10]:
            print("BLOCK:", item)
        print("Planned path saved:", csv_path)

        if issues:
            print("NOT SAFE TO EXECUTE")
            return

        print("STATIC FOOTPRINT CHECK PASSED")

        if not args.execute:
            print("CHECK ONLY: robot has not moved.")
            print("Run with --execute for the Gazebo demo.")
            return

        # This demo assumes the robot is still at the spawn pose.
        # Verify before sending the action.
        from geometry_msgs.msg import PoseStamped as GT
        gt_pose = []

        sub = node.create_subscription(
            GT, "/gazebo/amiga/ground_truth",
            lambda msg: gt_pose.append(msg),
            10
        )

        deadline = time.monotonic() + 5
        while not gt_pose and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)

        if not gt_pose:
            raise RuntimeError("No ground truth pose")

        current = gt_pose[-1].pose.position
        err = math.hypot(
            current.x-sx,
            current.y-sy
        )
        print("Robot starting-position error:", round(err,3))

        if err > 0.30:
            raise RuntimeError(
                "Robot has moved from the checked start; replan"
            )

        if not follower.wait_for_server(timeout_sec=15):
            raise RuntimeError("FollowPath unavailable")

        follow_goal = FollowPath.Goal()
        follow_goal.path = path
        follow_goal.controller_id = "FollowPath"

        handle = wait_future(
            node, follower.send_goal_async(follow_goal), 15
        )

        if not handle.accepted:
            raise RuntimeError("FollowPath rejected")

        print("ROBOT MOVING - Gazebo demonstration started")
        print("Press Ctrl+C to cancel.")

        result_future = handle.get_result_async()
        deadline = time.monotonic() + 240

        while rclpy.ok() and not result_future.done():
            rclpy.spin_once(node, timeout_sec=0.2)

            if time.monotonic() > deadline:
                handle.cancel_goal_async()
                raise RuntimeError("Demo timeout; cancel requested")

        outcome = result_future.result()

        if outcome.status == GoalStatus.STATUS_SUCCEEDED:
            print("DEMO RESULT: SUCCEEDED")
        else:
            print("DEMO RESULT:", outcome.status)
            print(
                "Controller error:",
                getattr(outcome.result, "error_code", "unknown")
            )

    except KeyboardInterrupt:
        print("Operator requested STOP")
        if handle is not None:
            handle.cancel_goal_async()
            rclpy.spin_once(node, timeout_sec=1.0)

    except Exception as exc:
        print("ERROR:", exc)

    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()
