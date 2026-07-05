import os
import mounter
import re

print("Hello from booterthingy!")
print("WELCOME TO NOODLIX")
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
print("Detecting drive...")
cmdline = open("/proc/cmdline").read()
print(f"Kernel commands: {cmdline}")
drive = re.search(r"drive=(\S+)", cmdline)
if drive is None:
    print("ERROR, your installation is corrupted.")
    print("System cannot continue, halting...")
    exit(1)
else:
    drive = drive.group(1)
print("Drive path: ", drive)
print("Mounting...")

try:
    os.makedirs("/mnt/drive", exist_ok=True)
    mounter.mount(drive, "/mnt/drive", "ext4")

except Exception as e:
    print(f"Failed to mount: {e}")
    print("System cannot continue, halting...")
    exit(1)

print("Handing off to the drive...")

try:
    # Path is relative to new root — /mnt/drive becomes /
    mounter.switch_root("/mnt/drive", "/noodlix/init")

except Exception as e:
    print(f"Failed to pivot root: {e}")
    print("System cannot continue, halting...")
    exit(1)
