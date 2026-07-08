# Noodlix Core — Agent Guide

A custom Linux distribution (x86_64) built from scratch. Produces a bootable ISO with an interactive installer that partitions disks, creates filesystems, and copies pre-baked root/EFI data.

---

## Project Structure

```
noodlix_core/
├── build.sh                     # ISO builder: pack initramfs → xorriso → Limine install
├── build_iso_full.bash          # Full workflow: copy system-initramfs, pack, build ISO
├── pack_any_initramfs.bash      # Generic cpio+gzip initramfs packer (idempotent utility)
├── testinvm.sh                  # QEMU launcher: interactive menu (installer ISO or disk boot)
│
├── kernel/                      # Linux 6.1.177 source, x86_64, custom io_uring modifications
│   └── noodlix-working.config   # Kernel .config (138KB)
│
├── booterthingy/                # Python 3.13 — minimal PID 1 init (compiled to binary via transpilatron)
│   ├── main.py                  # Mounts proc/sys/devtmpfs, then stops
│   ├── mounter.py               # ctypes mount/umount/switch_root wrapper
│   ├── power.py                 # ctypes syscall reboot/halt/poweroff wrapper
│   ├── pyproject.toml           # minimal, no deps
│   └── uv.lock
│
├── installer/                   # Python 3.14 — interactive installer (runs in initramfs)
│   ├── main.py                  # Partition, format (vfat/ext4), copy efidata/rootdata, reboot
│   ├── mounter.py               # Same as booterthingy/mounter.py (duplicated)
│   ├── power.py                 # Same as booterthingy/power.py (duplicated)
│   └── pyproject.toml           # zero runtime deps
│
├── installer_iso/               # Staging directory for the built ISO
│   ├── boot/
│   │   ├── kernel.img           # Linux kernel binary
│   │   ├── initramfs.gz         # Compressed initramfs (packed from boot/initramfs/)
│   │   ├── initramfs/
│   │   │   ├── init             # Compiled binary — the PID 1
│   │   │   ├── installer/
│   │   │   │   ├── efidata/     # EFI partition payload (Limine + kernel + nested initramfs)
│   │   │   │   └── rootdata/    # Root filesystem payload (mounted at /mnt/root)
│   │   │   └── {dev,proc,sys,tmp,mnt}/
│   │   └── limine/              # Limine bootloader files + limine.conf
│   └── EFI/BOOT/BOOTX64.EFI
│
├── limine-binary/               # Limine bootloader source + prebuilt binaries
│   ├── Makefile                 # Builds `limine` tool from limine.c (C99)
│   └── *.EFI, *.bin, *.sys      # Bootloader binaries
│
├── system-initramfs/            # EMPTY — placeholder for future "system" initramfs template
├── util-linux-2.40/             # Upstream source (fdisk, etc.)
├── e2fsprogs-1.47.3/            # Upstream source (mkfs.ext4)
├── iw-6.17/                     # Upstream iw (wireless) source
│
├── noodlix.iso                  # Built ISO output
├── noodlix_disk.img             # QEMU disk image (20G raw, auto-created by testinvm.sh)
├── noodlix_vars.fd              # UEFI VARS copy (auto-created by testinvm.sh)
├── mkfs.vfat.static             # Static mkfs.vfat binary
├── .env                         # Contains OPENROUTER_API_KEY
└── AGENTS.md                    # ← This file
```

---

## Essential Commands

### Build the ISO
```bash
# Quick build (from existing installer_iso/ staging)
./build.sh installer_iso noodlix.iso

# Full build (copy system-initramfs → pack → build)
./build_iso_full.bash
```
Note: `build_iso_full.bash` copies from `system-initramfs/` (currently empty). Its `cp` command will silently fail/no-op because the glob expands to nothing — the script has no `set -e` so it continues. Pack and build still run.

### Test in QEMU
```bash
./testinvm.sh       # Interactive: 1=boot ISO, 2=boot from disk
```
Requires `qemu-system-x86_64`, `OVMF` UEFI firmware (`/usr/share/OVMF/OVMF_CODE_4M.fd` + `OVMF_VARS_4M.fd`), and SDL. Creates `noodlix_disk.img` (20G) and `noodlix_vars.fd` if missing.

### Pack an initramfs (utility)
```bash
./pack_any_initramfs.bash <source_dir> <output.gz>
```

### Bootloader
```bash
cd limine-binary && make
# Produces `limine` tool binary (needed for `build.sh`'s bios-install step)
```

### Kernel
```bash
cd kernel && make -j$(nproc)
```
Uses existing `.config` (aliased from `noodlix-working.config`). For a fresh kernel, run `make x86_64_defconfig` first. Requires standard kernel build toolchain (gcc, make, flex, bison, etc.).

### Python components
```bash
# booterthingy — compile to binary with transpilatron (creates `init`)
cd booterthingy && transpilatron --minimal main.py -o init

# installer — requires Python 3.14 (pre-release), no deps
cd installer && python main.py
```

---

## Architecture & Control Flow

### Boot chain
1. **UEFI/BIOS** → **Limine bootloader** (reads `boot/limine/limine.conf`)
2. **Kernel** boots with `init=/init console=tty0 vga=792 loglevel=8`
3. Kernel loads **initramfs.gz** as the initial rootfs
4. **`/init`** (compiled booterthingy binary, PID 1) runs:
   - Mounts proc, sysfs, devtmpfs
   - Currently stops after mounting (minimal — more to be added)
5. During install: **`/installer/main.py`** runs interactively:
   - Mounts proc/sys/dev/tmpfs
   - User picks disk → `fdisk` for partitioning
   - Formats EFI partition (vfat) and root partition (ext4)
   - Copies `efidata/` → EFI partition, `rootdata/` → root partition
   - Unmounts, reboots

### Initramfs layout (inside `installer_iso/boot/initramfs/`)
```
/
├── init              # Booterthingy compiled binary (PID 1)
├── installer/        # Python installer scripts
│   ├── main.py
│   ├── mounter.py
│   ├── power.py
│   ├── efidata/      # → gets copied to EFI partition
│   │   ├── EFI/BOOT/BOOTX64.EFI
│   │   └── boot/
│   │       ├── kernel.img
│   │       ├── initramfs/        # Empty (nested initramfs placeholder)
│   │       └── limine/limine.conf
│   └── rootdata/     # → gets copied to root partition (currently empty)
├── proc/, sys/, dev/, tmp/, mnt/
```

### Two limine.conf files
- **`installer_iso/boot/limine/limine.conf`** — used when booting the installer ISO (title: "Noodlix Installer")
- **`installer_iso/.../efidata/boot/limine/limine.conf`** — gets copied to installed system's EFI partition (title: "Noodlix")

---

## Code Patterns & Conventions

### Python
- **No third-party dependencies** — standard library only
- **ctypes for system calls** — mount/umount/reboot all go through `ctypes.CDLL(None, use_errno=True)` calling libc directly
- **`os.fork()` + `os.execv()`** — used to run external tools (`fdisk`, `mkfs.vfat`, `mkfs.ext4`) rather than `subprocess`
- **Error handling**: check return codes manually, `sys.exit(1)` on failure
- **No type annotations** used consistently (some functions typed, some not)
- **Two Python versions in use**: installer needs 3.14, booterthingy needs 3.13

### Shell scripts
- `set -e` used in build scripts (fails fast)
- Build scripts assume **working directory is project root** — they `cd` into subdirectories and back out relative to that
- `testinvm.sh` uses interactive `read` for menu selection

### Kernel
- Linux 6.1.177, arch `x86_64` (with `x86_64_defconfig`)
- Custom config at `kernel/noodlix-working.config`
- Custom modifications in `kernel/io_uring/` (compare against upstream 6.1.177)

---

## Known Gotchas

1. **Working directory sensitivity**: Build scripts (`build.sh`, `pack_any_initramfs.bash`) `cd` into directories and use `OLDPWD`/relative paths. Always run from the project root.

2. **Duplicated modules**: `mounter.py` and `power.py` are duplicated verbatim between `installer/` and `booterthingy/`. A change to one must be manually mirrored to the other.

3. **`system-initramfs/` is empty** — `build_iso_full.bash` copies everything from it, but it's a placeholder with no content yet. The copy step silently succeeds with nothing.

4. **Git repo on GitHub** — tracked at `origin https://github.com/JTSJohnny/noodlix.git`. The repo excludes upstream source trees (`kernel/`, `util-linux-2.40/`, etc.) and large build artifacts via `.gitignore`. Only the kernel config (`kernel/noodlix-working.config`) is tracked from the kernel source. Force-pushed a clean root commit to remove large files from history — don't push large files again.

5. **Static binaries** — `mkfs.vfat.static` lives at the project root. The initramfs needs its own copy at runtime.

6. **`init` binary is compiled** — `installer_iso/boot/initramfs/init` is a transpilatron-compiled binary, not a script. Edit `booterthingy/main.py` and recompile with `transpilatron --minimal main.py -o init`.

7. **`noodlix_vars.fd`** is auto-created by `testinvm.sh` from the system's `/usr/share/OVMF/OVMF_VARS_4M.fd`. If the system doesn't have OVMF installed, QEMU boot fails.

8. **Python 3.14 requirement** for the installer is unusually new (not yet released as stable). The `.python-version` files reflect pre-release/development versions.

9. **OpenRouter API key** in `.env` (`sk-or-v1-...`) — sensitive; avoid leaking or committing.

10. **Kernel config is separate** — the config file is named `noodlix-working.config` (not `.config`), so it won't be picked up by `make` without manually copying/renaming.

11. **No formatter/linter configured** — no ruff, black, mypy, or similar tooling. Follow existing patterns.

12. **`noodlix_disk.img`** is a 20G raw disk image — takes significant space. Auto-created by `testinvm.sh` if missing.

13. **Both limine.conf files have identical `cmdline`** — if you change kernel parameters, update both.
