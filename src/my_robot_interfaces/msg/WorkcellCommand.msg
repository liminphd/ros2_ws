# Command/permission from the mobile-base framework to an external workcell.

uint8 HOLD=0
uint8 STOPPING=1
uint8 BASE_READY=2
uint8 RESUME_ALLOWED=3
uint8 ABORT=4

uint8 command

# Destination workcell. Use "all" when applicable.
string workcell_id

# Human-readable information for logging/debugging.
string message
