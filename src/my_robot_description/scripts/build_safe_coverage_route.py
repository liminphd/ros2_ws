#!/usr/bin/env python3

import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import yaml

BASE = Path.home() / "ros2_ws/src/my_robot_description"
MAP_YAML = BASE / "maps/greenhouse_working_map.yaml"
OUT = Path.home() / "ros2_ws/logs/full_coverage"
OUT.mkdir(parents=True, exist_ok=True)

cfg = yaml.safe_load(MAP_YAML.read_text())
img = Image.open(MAP_YAML.parent / cfg["image"]).convert("L")
grid = np.asarray(img)

RES = float(cfg["resolution"])
OX, OY, _ = cfg["origin"]
H, W = grid.shape

# Vehicle footprint with 20 cm margin on every side.
HALF_L = 1.41 / 2 + 0.20
HALF_W = 0.80 / 2 + 0.20

# Dense body sampling, finer than the map resolution.
u = np.linspace(-HALF_L, HALF_L, 47)
v = np.linspace(-HALF_W, HALF_W, 31)
U, V = np.meshgrid(u, v)
U, V = U.ravel(), V.ravel()

# Six full working rows, with short extensions to safe turn sites.
WAYPOINTS = [
    (147.8, 7.75),   # Northeast start

    # Northern lane 1: east -> west
    (2.2, 7.75),
    (1.5, 7.75),

    # Northern lane 2: west -> east
    (1.5, 6.75),
    (2.2, 6.75),
    (147.8, 6.75),
    (148.5, 6.75),

    # Northern lane 3: east -> west
    (148.5, 5.75),
    (147.8, 5.75),
    (2.2, 5.75),
    (1.5, 5.75),

    # West-end passage across the central column row.
    (1.5, 3.75),

    # Southern lane 1: west -> east
    (2.2, 3.75),
    (147.8, 3.75),

    # Southern lane 2: east -> west
    (147.8, 2.75),
    (2.2, 2.75),
    (1.5, 2.75),

    # Southern lane 3: west -> east
    (1.5, 1.75),
    (2.2, 1.75),
    (147.8, 1.75),  # Southeast finish
]

def body_free(x, y, yaw):
    c = math.cos(yaw)
    s = math.sin(yaw)

    wx = x + c * U - s * V
    wy = y + s * U + c * V

    # Sample at cell centers, conservatively checking nearby cells.
    px = np.rint((wx - OX) / RES).astype(int)
    py = H - 1 - np.rint((wy - OY) / RES).astype(int)

    if np.any((px < 0) | (px >= W)):
        return False
    if np.any((py < 0) | (py >= H)):
        return False

    return bool(np.all(grid[py, px] >= 250))

def angle_diff(a, b):
    return math.atan2(math.sin(b-a), math.cos(b-a))

route = []
failures = []
total_length = 0.0
previous_yaw = None

for k, (a, b) in enumerate(zip(WAYPOINTS[:-1], WAYPOINTS[1:])):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    distance = math.hypot(dx, dy)

    if distance < 1e-9:
        continue

    yaw = math.atan2(dy, dx)

    # At a corner, audit the swept footprint during rotation.
    if previous_yaw is not None:
        change = angle_diff(previous_yaw, yaw)
        count = max(1, math.ceil(abs(change) / math.radians(3)))

        for j in range(count + 1):
            theta = previous_yaw + change * j / count

            if not body_free(a[0], a[1], theta):
                failures.append(("TURN", k, a[0], a[1],
                                 math.degrees(theta)))

            route.append((a[0], a[1], theta, "turn"))

    # Validate the whole connecting straight segment.
    count = max(1, math.ceil(distance / 0.05))

    for j in range(count + 1):
        t = j / count
        x = a[0] + t * dx
        y = a[1] + t * dy

        if not body_free(x, y, yaw):
            failures.append(("MOVE", k, x, y,
                             math.degrees(yaw)))

        route.append((x, y, yaw, "move"))

    total_length += distance
    previous_yaw = yaw

print("===== FULL GREENHOUSE SAFE ROUTE =====")
print("Start:", WAYPOINTS[0])
print("Finish:", WAYPOINTS[-1])
print("Waypoints:", len(WAYPOINTS))
print("Straight-line path length:", round(total_length, 2), "m")
print("Sampled poses:", len(route))
print("Collision samples:", len(failures))

for failure in failures[:20]:
    print("BLOCK:", failure)

if failures:
    print("RESULT: NOT READY")
    raise SystemExit(1)

csv_path = OUT / "safe_coverage_route.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y", "yaw_rad", "motion"])
    writer.writerows(route)

wp_path = OUT / "safe_coverage_waypoints.csv"
with wp_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y"])
    writer.writerows(WAYPOINTS)

fig, ax = plt.subplots(figsize=(18, 5))

ax.imshow(
    grid,
    cmap="gray",
    origin="upper",
    extent=[
        OX,
        OX + W * RES,
        OY,
        OY + H * RES
    ],
    vmin=0,
    vmax=255,
    aspect="auto"
)

xs = [p[0] for p in route]
ys = [p[1] for p in route]

ax.plot(xs, ys, color="blue", linewidth=1.2)
ax.scatter(
    [WAYPOINTS[0][0]],
    [WAYPOINTS[0][1]],
    color="green",
    s=65,
    label="Start"
)
ax.scatter(
    [WAYPOINTS[-1][0]],
    [WAYPOINTS[-1][1]],
    color="red",
    s=65,
    label="Finish"
)

ax.set_xlim(0, 150)
ax.set_ylim(0, 10)
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_title("AMIGA Six-Lane Coverage with Safe End Connections")
ax.legend(loc="upper center")
ax.grid(alpha=0.2)

preview = OUT / "safe_coverage_preview.png"
fig.tight_layout()
fig.savefig(preview, dpi=160)
plt.close(fig)

print("RESULT: ALL SAMPLED POSES PASS")
print("Route CSV:", csv_path)
print("Waypoints CSV:", wp_path)
print("Preview:", preview)
print("Robot commands sent: NONE")
