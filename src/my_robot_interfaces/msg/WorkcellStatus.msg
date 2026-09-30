# Generic interface between the mobile-base framework and an external
# agricultural workcell (e.g. one arm, multiple arms, sprayer, sampler).
#
# The workcell owns:
# - target detection
# - target localization
# - manipulator planning/control
# - end-effector control
#
# The mobile-base framework owns:
# - navigation
# - stopping the base
# - confirming the base is stationary
# - resuming the mission

uint8 IDLE=0
uint8 TARGET_DETECTED=1
uint8 STOP_REQUESTED=2
uint8 WAITING_FOR_BASE=3
uint8 WORKING=4
uint8 COMPLETED=5
uint8 FAILED=6
uint8 SAFE_HOLD=7

uint8 state

# Unique workcell identifier, e.g. "arm_1", "dual_arm", "harvester".
string workcell_id

# Human-readable information for logging/debugging.
string message
