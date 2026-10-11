#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path

WORLD = "greenhouse_realistic"
MODEL = Path(__file__).resolve().parents[1] / "urdf/amiga_sim_fixed.sdf"
PARTITION = "greenhouse_fixed_test"


def run(cmd, timeout=10):
    env = os.environ.copy()
    env["GZ_PARTITION"] = PARTITION
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def model_exists():
    result = run(["gz", "model", "--list"], timeout=10)
    return (
        result.returncode == 0
        and any(
            line.strip() == "- amiga"
            for line in result.stdout.splitlines()
        )
    )


def main():
    if not MODEL.is_file():
        sys.exit(f"ERROR: Model file missing: {MODEL}")

    print("Waiting for Gazebo world...", flush=True)

    deadline = time.monotonic() + 60

    while time.monotonic() < deadline:
        result = run(["gz", "service", "-l"])
        if f"/world/{WORLD}/create" in result.stdout.splitlines():
            break
        time.sleep(1)
    else:
        sys.exit("ERROR: Gazebo create service not available")

    if model_exists():
        print("AMIGA already exists; skipping spawn.", flush=True)
        return

    request = (
        f'sdf_filename: "{MODEL}", '
        'name: "amiga", '
        'pose: {position: {x: 141, y: 3.0, z: 0.715}, '
        'orientation: {z: 1, w: 0}}'
    )

    print("Spawning AMIGA...", flush=True)

    result = run(
        [
            "gz", "service",
            "-s", f"/world/{WORLD}/create",
            "--reqtype", "gz.msgs.EntityFactory",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "30000",
            "--req", request,
        ],
        timeout=40,
    )

    if result.returncode != 0 or "data: true" not in result.stdout:
        sys.exit(
            "ERROR: AMIGA spawn failed\n"
            + result.stdout + result.stderr
        )

    deadline = time.monotonic() + 15

    while time.monotonic() < deadline:
        if model_exists():
            print("SUCCESS: AMIGA entity verified.", flush=True)
            return
        time.sleep(1)

    sys.exit("ERROR: Spawn acknowledged but AMIGA not found")


if __name__ == "__main__":
    main()
