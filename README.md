# Noodlix Core

A custom x86_64 Linux distribution where every userspace component is written
in Python and compiled to a fully static native binary via
[transpilatron](https://github.com/NoodlixProject/transpilatron) — an
AI-powered Python-to-C transpiler. No CPython runtime on the target.

Produces a bootable ISO with an interactive installer that partitions disks,
formats vfat/ext4, and copies system data onto the target.

## Quick Start

```bash
# Set up your build environment
python3 environment_setup.py

# Build the ISO
./build_iso_full.bash

# Test in QEMU
./testinvm.sh
```

Select **1 (Boot ISO)** to launch the installer, then **2 (Boot from disk)**
to test the installed system.

## Project Structure

| Path | Purpose |
|------|---------|
| `booterthingy/` | Python 3.13 — two-stage init for the installed system. `initramfs-stage.py` mounts rootfs and switch_root's to it; `rootfs-stage.py` is a placeholder for the next boot phase. |
| `installer/` | Python 3.14 — interactive installer. Transpiled to a static binary and placed as `/init` in the initramfs. Partitions disks, formats vfat/ext4, copies system data, reboots. |
| `limine-binary/` | Limine bootloader (EFI + BIOS binaries) plus Makefile. |
| `kernel/noodlix-working.config` | Custom Linux 6.1.175 kernel config. |
| `installer_iso/` | Staging directory for the ISO. Tracks prebuilt kernel, initramfs, and EFI payload. |
| `system-initramfs/` | Placeholder — copied into the nested initramfs for the installed system. |
| `system-rootfs/` | Placeholder — copied into rootdata/ for the root filesystem. |
| `build.sh` | Packs initramfs, runs xorriso, installs Limine → `noodlix.iso`. |
| `build_iso_full.bash` | Full workflow — copies `system-rootfs/` and `system-initramfs/`, packs initramfs, builds ISO. |
| `pack_any_initramfs.bash` | Generic cpio+gzip initramfs packer. |
| `testinvm.sh` | QEMU launcher — interactive menu for ISO boot or disk boot. |
| `environment_setup.py` | Installs apt deps, uv, transpilatron, downloads kernel source, builds kernel, copies bzImage. |

## Architecture

### Boot flow 1: Installer ISO

The special ISO that partitions and installs Noodlix to disk.

```
UEFI/BIOS → Limine → Kernel → initramfs.gz → /init (transpiled installer, static binary)
                                                   ↓
                                           mounts proc/sys/dev/tmpfs
                                                   ↓
                                           user picks disk, runs fdisk
                                                   ↓
                                           formats EFI (vfat) + root (ext4)
                                                   ↓
                                           rewrites efidata/limine.conf → adds drive= parameter
                                                   ↓
                                           copies efidata/ → EFI partition
                                           copies rootdata/ → root partition
                                                   ↓
                                           unmounts, reboots
```

### Boot flow 2: Installed system

After installation, booting from the target disk. The kernel receives
`drive=/dev/sdXN` from the limine.conf written by the installer.

```
UEFI/BIOS → Limine (on EFI partition) → Kernel → initramfs.gz → /init
                                                                      ↓
                                           mounts proc/sys/dev
                                                                      ↓
                                           reads drive= from /proc/cmdline
                                                                      ↓
                                           mounts root partition → /mnt/drive
                                                                      ↓
                                           calls switch_root("/mnt/drive", "/noodlix/init")
                                                                      ↓
                                           (rootfs-stage: next boot phase, not yet implemented)
```

### The two-stage init

The booterthingy provides two Python files that each get transpiled to static
binaries for different boot phases:

1. **`initramfs-stage.py`** — runs inside the initial initramfs. Mounts proc/sys/dev,
   reads the `drive=` kernel parameter, mounts the real root partition, and
   calls `switch_root` to hand off to the system on disk.
2. **`rootfs-stage.py`** — placeholder. Will run as PID 1 after switch_root
   once the root filesystem has a real init.

## Build Dependencies

- **QEMU** (`qemu-system-x86_64`) with UEFI firmware (`OVMF`)
- **xorriso**, **gzip**, **cpio**
- **Python 3.13** (for booterthingy) and **Python 3.14** (for installer)
- **transpilatron** — install via `uv tool install transpilatron`
- Linux kernel build toolchain (gcc, make, flex, bison, libssl-dev)
- **SDL** library for QEMU display

## Repository Notes

- Only `kernel/noodlix-working.config` is tracked from the kernel source.
- Upstream source trees (`util-linux-2.40/`, `e2fsprogs-1.47.3/`, `iw-6.17/`)
  are excluded via `.gitignore`.
- `installer_iso/` is tracked (prebuilt staging).
- `.env` (OpenRouter API key) is gitignored — do not commit.
- `system-initramfs/` and `system-rootfs/` are placeholders — empty on disk
  but get copied when they have content.

## License

AGPL-3.0 © 2026 **Johnny Konczal** <johnnytechsys@outlook.com>

This software is primarily licensed under the GNU Affero General Public
License v3 (AGPL-3.0). The author reserves the right to offer commercial
licensing for proprietary use cases — contact the author for inquiries.
