import os
import sys
from shutil import copytree

from mounter import MNT_DETACH, mount, umount
from power import reboot


def _divider():
    print("=======================================================")


print("NOODLIX INSTALLER")
_divider()

print("Hello from the Noodlix installer!")
_divider()

print("Please wait, we are setting up the environment...")


if mount("proc", "/proc", "proc") != 0:
    print("FATAL: proc mount failed")
    sys.exit(1)

if mount("sysfs", "/sys", "sysfs") != 0:
    print("FATAL: sysfs mount failed")
    sys.exit(1)

if mount("devtmpfs", "/dev", "devtmpfs") != 0:
    print("FATAL: devtmpfs mount failed")
    sys.exit(1)

if mount("tmpfs", "/tmp", "tmpfs") != 0:
    print("FATAL: tmpfs mount failed")
    sys.exit(1)


print("Environment setup complete!")
_divider()


print("Begin DISK SETUP...")
print("Listing available disks:")

with open("/proc/partitions", "r") as f:
    print(f.read())

disk = input("Please enter disk name (/dev/... or sda): ").strip()

if not disk.startswith("/dev/"):
    disk = "/dev/" + disk

if not os.path.exists(disk):
    print("FATAL: disk not found:", disk)
    sys.exit(1)

print("Please refer to the installation guide on how to use fdisk to set up the correct partition layout")
pid = os.fork()
if pid == 0:
    os.execv("/bin/fdisk", ["/bin/fdisk", disk])
else:
    os.waitpid(pid, 0)

print("Disk setup complete!")
_divider()

print("Partition list now:")
with open("/proc/partitions", "r") as f:
    print(f.read())

_divider()


print("Preparing EFI partition...")
_divider()

efi_partition = input("Please enter EFI partition (/dev/... or name): ").strip()

if not efi_partition.startswith("/dev/"):
    efi_partition = "/dev/" + efi_partition

if not os.path.exists(efi_partition):
    print("FATAL: EFI partition not found:", efi_partition)
    sys.exit(1)

os.makedirs("/mnt/efi", exist_ok=True)
print("Formatting EFI Partition...")
pid = os.fork()
if pid == 0:
    os.execv("/bin/mkfs.vfat", ["/bin/mkfs.vfat", "-F", "32", efi_partition])
    sys.exit(1)
else:
    _, status = os.waitpid(pid, 0)
    if status != 0:
        print("FATAL: Formatting failed with code", status)
        sys.exit(1)
print("EFI partition formatted successfully!")
print("Mounting EFI partition...")
if mount(efi_partition, "/mnt/efi", "vfat") != 0:
    print("FATAL: Failed to mount EFI partition")
    sys.exit(1)

print("EFI partition mounted successfully!")
_divider()


print("Preparing root partition...")
_divider()

root_partition = input("Please enter root partition (/dev/... or name): ").strip()

if not root_partition.startswith("/dev/"):
    root_partition = "/dev/" + root_partition

if not os.path.exists(root_partition):
    print("FATAL: root partition not found:", root_partition)
    sys.exit(1)
destroy_confirm = input(
    "WARNING: This will erase all data on the root partition! Type 'yes' to continue: "
).strip()
if destroy_confirm.lower() != "yes":
    print("Aborting root partition setup.")
    sys.exit(1)
print("Creating ext4 filesystem on root partition...")
pid = os.fork()
if pid == 0:
    os.execv("/bin/mkfs.ext4", ["/bin/mkfs.ext4", root_partition])
else:
    os.waitpid(pid, 0)

print("Root partition prepared successfully!")
_divider()
print("Mount the root partition to /mnt/root...")
os.makedirs("/mnt/root", exist_ok=True)
if mount(root_partition, "/mnt/root", "ext4") != 0:
    print("FATAL: Failed to mount root partition")
    sys.exit(1)
print("Root partition mounted successfully!")
_divider()
print("Let's noodle!")
_divider()
print("Copy the EFI partition...")
copytree("/installer/efidata", "/mnt/efi", dirs_exist_ok=True)
print("EFI partition setup complete!")
print("Unmounting EFI partition...")
umount("/mnt/efi", MNT_DETACH)
print("EFI partition unmounted successfully!")
_divider()
print("Copying root partition...")
copytree("/installer/rootdata", "/mnt/root", dirs_exist_ok=True)
print("Root partition setup complete!")
_divider()
print("Unmounting root partition...")
umount("/mnt/root", MNT_DETACH)
print("Root partition unmounted successfully!")
_divider()
print("Installation complete!")
_divider()
input("Please remove the installation media, then press Enter...")
reboot()
