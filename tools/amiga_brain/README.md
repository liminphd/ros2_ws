# Farm-ng AMIGA Brain-side Tools

These scripts run on the Farm-ng AMIGA Brain and provide sensor and
motor-feedback data required by the ROS 2 computer.

They are separate from the ROS 2 packages under `src/`.

## Tested Brain Environment

- Host: `quamash-queue`
- System Python: Python 3.8.10
- Farm-ng Python: `/farm_ng_image/venv/bin/python`
- OpenCV: 4.7.0
- DepthAI: 2.22.0.0
- websockets: 11.0.3
- `candump`: `/usr/bin/candump`

## Hardware Mapping

| Device | MXID | Service |
| --- | --- | --- |
| Front OAK-D-W PoE | `14442C1071C4CDD200` | WebSocket 8765 |
| Rear OAK-D-W PoE | `14442C10A1B3E6D200` | WebSocket 8766 |

Both depth pipelines use:

- CAM_B as the left mono camera
- CAM_C as the right mono camera
- 800P mono input
- 30 FPS
- StereoDepth `HIGH_DENSITY`
- left-right consistency check
- 640 x 400 output
- `16UC1` depth in millimetres
- PNG transport over WebSocket

## 1. Front Depth Server

Run on the Brain:

    /farm_ng_image/venv/bin/python \
      /mnt/amiga_tools/front_depth_server.py

Provides:

    ws://<brain-ip>:8765
    frame_id: front_camera_depth_optical_frame

## 2. Rear Depth Server

Run on the Brain:

    /farm_ng_image/venv/bin/python \
      /mnt/amiga_tools/rear_depth_server.py

Provides:

    ws://<brain-ip>:8766
    frame_id: rear_camera_depth_optical_frame

## 3. Motor RPM Feedback

`can_motor_sender_candump.py` is a read-only CAN feedback bridge.

It reads CAN IDs `0x18A`, `0x18B`, `0x18C`, and `0x18D` using
`candump`, then forwards decoded RPM values as JSON over UDP.

Default configuration:

    CAN interface: can0
    ROS 2 computer: 10.95.76.100
    UDP port: 5006

Run on the Brain:

    python3 /mnt/amiga_tools/can_motor_sender_candump.py

The repository version also supports:

    python3 can_motor_sender_candump.py \
      --udp-ip 10.95.76.100 \
      --udp-port 5006 \
      --can-interface can0

## CAN Safety

This script uses `candump` only. It does not send CAN frames and does
not provide robot motion commands.

Do not replace `candump` with `cansend` or another CAN-writing mechanism
without a separate control-system safety review.

## RPM Decoder Limitation

The current implementation decodes each motor RPM as a signed
little-endian 16-bit value from CAN payload bytes 4-5:

    rpm = int16_le(data[4:6])

This mapping has been validated against the current AMIGA feedback
stream, but it is a project-side raw CAN decoding method rather than
an official Farm-ng high-level MotorState decoder.

If this bridge is later replaced with the official Farm-ng MotorState
interface, verify motor sign conventions before using the data in
wheel odometry.

## Brain to ROS 2 Data Flow

    Front OAK
        |
        +-- front_depth_server.py :8765
        |       |
        |       +--> farmng_depth_bridge
        |               |
        |               +--> front depth image
        |               +--> point cloud
        |               +--> front obstacle cloud
        |
    Rear OAK
        |
        +-- rear_depth_server.py :8766
                |
                +--> farmng_depth_bridge
                        |
                        +--> rear depth image
                        +--> point cloud
                        +--> rear obstacle cloud

    AMIGA CAN (read only)
        |
        +-- candump
                |
                +--> can_motor_sender_candump.py
                        |
                        +--> UDP :5006
                                |
                                +--> udp_motor_receiver
                                        |
                                        +--> /amiga/motor_rpm
                                                |
                                                +--> wheel_odometry
                                                        |
                                                        +--> /wheel/odometry

## Deployment

Repository copies:

    tools/amiga_brain/

Tested Brain deployment location:

    /mnt/amiga_tools/

Copy scripts to the Brain only when the existing processes are stopped
deliberately. Do not overwrite scripts that are currently running as
part of an active robot session.

## Scope

These tools provide sensor and motor-feedback data only.

They are not the robot motion-control interface. Navigation, joystick
override, autonomous commands, and other motion-control functions must
be handled and validated separately.
