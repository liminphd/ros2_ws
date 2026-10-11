#!/usr/bin/env python3

import math
from pathlib import Path
from PIL import Image
import yaml

base = Path.home() / "ros2_ws/src/my_robot_description"
cfg = yaml.safe_load(
    (base / "maps/greenhouse_working_map.yaml").read_text()
)
img = Image.open(
    base / "maps" / cfg["image"]
).convert("L")

res = float(cfg["resolution"])
ox, oy, _ = cfg["origin"]

L = 1.41 / 2 + 0.20
W = 0.80 / 2 + 0.20

script = base / "scripts/greenhouse_full_coverage_plan.py"

import importlib.util
spec = importlib.util.spec_from_file_location("coverage", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

waypoints = mod.WAYPOINTS

def collision(x, y, yaw):
    c = math.cos(yaw)
    s = math.sin(yaw)

    # Conservative coverage of robot body in local coordinates.
    for i in range(-10, 11):
        u = L * i / 10
        for j in range(-8, 9):
            v = W * j / 8

            wx = x + c*u - s*v
            wy = y + s*u + c*v

            px = round((wx-ox)/res)
            py = img.height-1-round((wy-oy)/res)

            if not (0 <= px < img.width and
                    0 <= py < img.height):
                return True

            if img.getpixel((px, py)) < 250:
                return True

    return False

failures = []

def test(x, y, yaw, label):
    if collision(x, y, yaw):
        failures.append(
            (label, round(x, 3), round(y, 3),
             round(math.degrees(yaw), 1))
        )

last_heading = None

for k, (a, b) in enumerate(zip(waypoints[:-1], waypoints[1:])):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    heading = math.atan2(dy, dx)

    # Validate a conservative in-place rotation at each corner.
    if last_heading is not None:
        change = math.atan2(
            math.sin(heading-last_heading),
            math.cos(heading-last_heading)
        )
        n = max(1, math.ceil(abs(change)/math.radians(5)))
        for j in range(n+1):
            yaw = last_heading + change*j/n
            test(a[0], a[1], yaw, f"turn {k}")

    distance = math.hypot(dx, dy)
    n = max(1, math.ceil(distance/0.1))

    for j in range(n+1):
        t = j/n
        x = a[0] + t*dx
        y = a[1] + t*dy
        test(x, y, heading, f"segment {k}")

    last_heading = heading

print("===== FULL COVERAGE FOOTPRINT AUDIT =====")
print("Segments:", len(waypoints)-1)
print("Failures:", len(failures))

for f in failures[:25]:
    print("BLOCK:", f)

if failures:
    print("RESULT: NOT READY FOR EXECUTION")
else:
    print("RESULT: ALL SAMPLED POSES PASS")
