import os
import mounter

if os.getpid() != 1:
    print("This script must be run as init (PID 1)")
    exit(1)

print("Mounting proc, sysfs, and devtmpfs...")
try:
    mounter.mount("proc", "/proc", "proc")
    mounter.mount("sysfs", "/sys", "sysfs")
    mounter.mount("devtmpfs", "/dev", "devtmpfs")
except Exception as e:
    print(f"Failed to mount: {e}")
    print("System cannot continue, halting...")
    exit(1)

print("Mounting complete, continuing...")
