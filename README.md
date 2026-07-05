# Noodlix Core

A custom x86_64 Linux distribution built from scratch — featuring a custom Linux 6.1.175 kernel, Python-based PID 1 init, an interactive installer, and a Limine bootloader stack. Produces a bootable ISO that partitions disks, creates filesystems, and copies the system onto target hardware.

## Quick Start

```bash
# Set up your build environment
python3 environment_setup.py

# Build the ISO
./build.sh installer_iso noodlix.iso

# Test in QEMU
./testinvm.sh
```

Select **1 (Boot ISO)** from the QEMU menu, run the installer, then select **2 (Boot from disk)** to test the installed system.

## Project Structure

| Path | Purpose |
|------|---------|
| `booterthingy/` | Python 3.13 — PID 1 init (compiled to binary via transpilatron). Mounts proc/sys/devtmpfs. |
| `installer/` | Python 3.14 — interactive installer. Partitions disks, formats vfat/ext4, copies system data. |
| `limine-binary/` | Limine bootloader (EFI + BIOS binaries) plus `Makefile` to build the `limine` tool. |
| `kernel/noodlix-working.config` | Custom Linux 6.1.175 kernel config (full kernel source not tracked — download separately). |
| `build.sh` | Packs initramfs, runs xorriso, installs Limine to produce `noodlix.iso`. |
| `build_iso_full.bash` | Full workflow — copies system-initramfs, packs, builds ISO. |
| `pack_any_initramfs.bash` | Generic cpio+gzip initramfs packer. |
| `testinvm.sh` | QEMU launcher with interactive menu (ISO boot or disk boot). |
| `environment_setup.py` | Installs system dependencies, uv, transpilatron, and copies kernel config. |

## Build Dependencies

- **QEMU** (`qemu-system-x86_64`) with UEFI firmware (`OVMF`)
- **xorriso**, **gzip**, **cpio**
- **Python 3.13** (for booterthingy) and **Python 3.14** (for installer)
- **transpilatron** — Python-to-C transpiler (install via `uv tool install transpilatron`)
- Linux kernel build toolchain (gcc, make, flex, bison, etc.) if rebuilding the kernel
- **SDL** library for QEMU display (`-display sdl` without `gl=on`)

## Boot Flows

The booterthingy (PID 1) and the installer are separate components. The installer runs from a special ISO — it is **not** present in the installed system.

### Flow 1: Installer ISO

The special ISO that partitions and installs Noodlix to disk.

```
UEFI/BIOS → Limine → Kernel → initramfs.gz → booterthingy (PID 1)
                                                   ↓
                                           mounts proc/sys/dev
                                                   ↓
                                           launches /installer/main.py
                                                   ↓
                                           fdisk → mkfs.vfat → mkfs.ext4
                                                   ↓
                                           copies efidata/ → EFI partition
                                           copies rootdata/ → root partition
                                                   ↓
                                           unmounts, reboots
```

### Flow 2: Installed System

After installation, booting from the target disk.

```
UEFI/BIOS → Limine (on EFI partition) → Kernel → initramfs.gz → booterthingy (PID 1)
                                                                       ↓
                                                               mounts proc/sys/dev
                                                                       ↓
                                                               (future: mount rootfs,
                                                                switch_root to system)
```

## Repository Notes

- **Only the kernel config** (`kernel/noodlix-working.config`) is tracked — full kernel source must be downloaded separately (Linux 6.1.175).
- Upstream source trees (`util-linux-2.40/`, `e2fsprogs-1.47.3/`, `iw-6.17/`) are excluded via `.gitignore`.
- Build artifacts (`noodlix.iso`, `noodlix_disk.img`, `installer_iso/`, etc.) are gitignored.
- The `.env` file (OpenRouter API key) is gitignored — do not commit.

## License

AGPL-3.0 © 2026 **Johnny Konczal** <johnnytechsys@outlook.com>

This software is primarily licensed under the GNU Affero General Public
License v3 (AGPL-3.0). The author reserves the right to offer commercial
licensing for proprietary use cases — contact the author for inquiries.
