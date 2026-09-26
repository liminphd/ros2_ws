#!/usr/bin/env python3

import argparse
import json
import socket
import struct
import subprocess


MOTOR_IDS = {
    "18A": "motor_a_rpm",
    "18B": "motor_b_rpm",
    "18C": "motor_c_rpm",
    "18D": "motor_d_rpm",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read AMIGA motor RPM CAN feedback and forward it over UDP."
    )
    parser.add_argument(
        "--udp-ip",
        default="10.95.76.100",
        help="Destination ROS 2 computer IP (default: 10.95.76.100)",
    )
    parser.add_argument(
        "--udp-port",
        type=int,
        default=5006,
        help="Destination UDP port (default: 5006)",
    )
    parser.add_argument(
        "--can-interface",
        default="can0",
        help="CAN interface to read (default: can0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    can_filter = (
        f"{args.can_interface},"
        "18A:7FF,18B:7FF,18C:7FF,18D:7FF"
    )

    proc = subprocess.Popen(
        ["candump", "-L", can_filter],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    latest = {}

    print(
        f"READ-ONLY {args.can_interface} -> "
        f"UDP {args.udp_ip}:{args.udp_port}"
    )
    print("Waiting for 18A/18B/18C/18D...")

    try:
        for line in proc.stdout:
            try:
                frame = line.strip().split()[-1]
                can_id, hexdata = frame.split("#")
                can_id = can_id.upper()

                if can_id not in MOTOR_IDS:
                    continue

                data = bytes.fromhex(hexdata)
                if len(data) < 6:
                    continue

                rpm = struct.unpack("<h", data[4:6])[0]
                latest[MOTOR_IDS[can_id]] = rpm

                if len(latest) == 4:
                    payload = json.dumps(latest).encode("utf-8")
                    sock.sendto(
                        payload,
                        (args.udp_ip, args.udp_port),
                    )

            except Exception as exc:
                print("PARSE_ERROR:", repr(exc))

    except KeyboardInterrupt:
        pass

    finally:
        proc.terminate()
        sock.close()
        print("Stopped.")


if __name__ == "__main__":
    main()
