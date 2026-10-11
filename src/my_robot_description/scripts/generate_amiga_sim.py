#!/usr/bin/env python3

from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


PACKAGE = Path(__file__).resolve().parents[1]

SOURCE = PACKAGE / "urdf/amiga_sim.urdf.xacro"

OUTPUT = PACKAGE / "urdf/amiga_sim_fixed.sdf"

WHEELS = [
    "front_left_wheel_link",
    "front_right_wheel_link",
    "rear_left_wheel_link",
    "rear_right_wheel_link",
]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        urdf = Path(tmp) / "amiga.urdf"

        subprocess.run(
            ["xacro", str(SOURCE), "-o", str(urdf)],
            check=True,
        )

        result = subprocess.run(
            ["gz", "sdf", "-p", str(urdf)],
            check=True,
            capture_output=True,
            text=True,
        )

        root = ET.fromstring(result.stdout)

        for wheel in WHEELS:
            link = root.find(f".//link[@name='{wheel}']")

            if link is None:
                raise RuntimeError(f"Missing wheel: {wheel}")

            collision = link.find("collision")

            if collision is None:
                raise RuntimeError(f"Missing collision: {wheel}")

            surface = collision.find("surface")
            if surface is None:
                surface = ET.SubElement(collision, "surface")

            friction = surface.find("friction")
            if friction is None:
                friction = ET.SubElement(surface, "friction")

            ode = friction.find("ode")
            if ode is None:
                ode = ET.SubElement(friction, "ode")

            parameters = {
                "mu": "1",
                "mu2": "1",
                "slip1": "0.035",
                "slip2": "0",
                "fdir1": "0 0 1",
            }

            for tag, value in parameters.items():
                element = ode.find(tag)
                if element is None:
                    element = ET.SubElement(ode, tag)
                element.text = value

        ET.indent(root, space="  ")

        ET.ElementTree(root).write(
            OUTPUT,
            encoding="unicode",
            xml_declaration=True,
        )

    print("Generated:", OUTPUT)


if __name__ == "__main__":
    main()
