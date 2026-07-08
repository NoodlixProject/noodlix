# Noodlix — Technical Overview

Noodlix is an experimental x86_64 Linux distribution where every userspace
component is written in pure Python and compiled to fully static native
binaries via [transpilatron](https://github.com/NoodlixProject/transpilatron)
— an AI-powered Python-to-C transpiler. No GNU userland. No systemd. No bash.
No CPython runtime.

---

## Core Philosophy

- **Python at every level** — the PID 1 init, the installer, every OS component
  starts as Python. It never runs as Python.
- **Transpilatron compiles it away** — the Python source is the spec.
  Transpilatron generates optimized C from it, producing a static binary with
  zero runtime dependencies.
- **Every binary is standalone** — no shared libraries, no ld.so, no dynamic
  linking on the target. What you wrote as Python ships as a single .text blob.
- **The package manager *is* transpilatron** — `transpilatron package recipe.toml`
  compiles a Python source into a static binary and drops it into the build
  tree. No binary packages, no dynamic linking, no runtime deps.

---

## Architecture

```
                          ┌──────────────────────────────────────┐
                          │         Dev Machine (x86_64)         │
                          │  ┌──────────┐  ┌────────────────┐   │
                          │  │ Python   │  │ Transpilatron  │   │
                          │  │ 3.13/3.14│  │ (Python→C AI)  │   │
                          │  └──────────┘  └────────────────┘   │
                          │        │               │            │
                          │        ▼               ▼            │
                          │  ┌────────────────────────────────┐ │
                          │  │         build.sh / build_iso   │ │
                          │  │  packs initramfs → xorriso →   │ │
                          │  │  Limine bios-install → ISO     │ │
                          │  └────────────────────────────────┘ │
                          └──────────────────────────────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────────────────┐
                          │         Installer ISO (55MB)         │
                          │  ┌────────────────────────────────┐ │
                          │  │ Limine bootloader               │ │
                          │  │ Linux 6.1.177 kernel            │ │
                          │  │ initramfs.gz:                   │ │
                          │  │   ├── init (static, PID 1)      │ │
                          │  │   ├── /installer/main.py        │ │
                          │  │   ├── /installer/efidata/       │ │
                          │  │   │   └── EFI data payload      │ │
                          │  │   └── /installer/rootdata/      │ │
                          │  │       └── rootfs payload        │ │
                          │  └────────────────────────────────┘ │
                          └──────────────────────────────────────┘
                                       │
                              (install to disk)
                                       │
                                       ▼
                          ┌──────────────────────────────────────┐
                          │         Installed System             │
                          │  ┌────────────────────────────────┐ │
                          │  │ EFI partition:                 │ │
                          │  │   Limine + kernel + nested     │ │
                          │  │   initramfs (from efidata/)    │ │
                          │  │                                │ │
                          │  │ Root partition:                │ │
                          │  │   All transpiled noodles       │ │
                          │  │   (from rootdata/)             │ │
                          │  └────────────────────────────────┘ │
                          └──────────────────────────────────────┘
```

---

## Components

### booterthingy/ — PID 1 Init

The first process started by the kernel. Written in Python 3.13, compiled to a
static binary via transpilatron.

Current responsibilities:
- Mounts proc, sysfs, devtmpfs
- (Hands off — no root filesystem handling yet)

Future: mount root filesystem, switch_root to the system initramfs.

### installer/ — Interactive Installer

Runs in the initramfs. Written in Python 3.14 (zero runtime deps).

Flow:
1. Mounts proc, sys, dev, tmpfs
2. User selects target disk → fdisk for partitioning
3. Formats EFI partition (vfat) and root partition (ext4)
4. Copies `efidata/` → EFI partition
5. Copies `rootdata/` → root partition
6. Unmounts, reboots

### Kernel — Linux 6.1.177

Custom build with:
- x86_64 architecture
- Custom `.config` at `kernel/noodlix-working.config`
- Custom io_uring modifications
- Boots with `init=/init console=tty0 vga=792 loglevel=8`

The full kernel source is **not** tracked in git — only the config file is.
Download and build via `environment_setup.py`.

### Limine Bootloader

Prebuilt EFI and BIOS binaries in `limine-binary/`. Two `limine.conf` files:

| Location | Title | Purpose |
|----------|-------|---------|
| `installer_iso/boot/limine/limine.conf` | "Noodlix Installer" | Booting the installer ISO |
| `efidata/boot/limine/limine.conf` | "Noodlix" | Booting the installed system |

---

## Boot Flows

### 1. Installer ISO (the special ISO)

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

### 2. Installed System (booting from disk)

```
UEFI/BIOS → Limine (on EFI partition) → Kernel → initramfs.gz → booterthingy
                                                                       ↓
                                                               mounts proc/sys/dev
                                                                       ↓
                                                               (future: mount rootfs,
                                                                switch_root)
```

---

## The Package System
Packages are just a idea. THEY ARE NOT IMPLEMENTED YET.
### How packages work

There are no binary packages, no package repositories, no runtime dependencies.

A "noodle" (package) is a recipe and Python source:

```
noodle-hello-world/
├── source/main.py       # Python code
└── noodle.toml          # metadata, deps, flags
```

Building:

```bash
makenoodle noodle-hello-world/recipe.toml # nonexistint. will work on it.
```

This produces a static binary. The user places it in the rootfs
(`system-rootfs/`) or initramfs directly. The build script includes it in the
ISO.

### Transpilatron

AI-powered Python-to-C transpiler. Owned by the same org
(`NoodlixProject/transpilatron`). Key properties:

- Input: Python 3.x source
- Output: optimized C99, compiled to a static ELF binary
- No CPython runtime on target
- Every binary is standalone (no libpython, no dynamic loader)
- Self-hosting potential: transpilatron can transpile itself

---

## Build System

### Files

| Script | Purpose |
|--------|---------|
| `build.sh` | Packs initramfs, runs xorriso, installs Limine → `noodlix.iso` |
| `build_iso_full.bash` | Copies system-rootfs/ + system-initramfs/, packs, builds ISO |
| `pack_any_initramfs.bash` | Generic cpio+gzip initramfs packer |
| `testinvm.sh` | QEMU launcher (ISO boot or disk boot) |
| `environment_setup.py` | Installs deps, uv, transpilatron, kernel source, builds kernel |

### Build workflow

```bash
# 1. Set up environment (deps, kernel, transpilatron)
python3 environment_setup.py

# 2. Populate system-rootfs/ with transpiled noodles
#    (manual — place static binaries in system-rootfs/)

# 3. Build the ISO
./build_iso_full.bash

# 4. Test in QEMU
./testinvm.sh
# Option 1 = Boot installer ISO
# Option 2 = Boot from disk (after install)
```

### Reproducibility

Every build starts from `installer_iso/` which is tracked in git. The
`environment_setup.py` downloads the same kernel version (6.1.177) and applies
the same config. The initramfs is rebuilt from the same `init` binary. The ISO
output is deterministic with xorriso.

---

## Project Structure

```
noodlix_core/
├── Build scripts
│   ├── build.sh                  # ISO builder
│   ├── build_iso_full.bash       # Full workflow
│   ├── pack_any_initramfs.bash   # Initramfs packer
│   ├── testinvm.sh               # QEMU launcher
│   └── environment_setup.py      # Dev environment setup
│
├── Core components
│   ├── booterthingy/             # PID 1 init (Python → transpiled)
│   ├── installer/                # Interactive installer (Python)
│   └── kernel/noodlix-working.config  # Kernel config
│
├── Staging (tracked in git)
│   └── installer_iso/            # ISO build directory (19 files, 55MB)
│       ├── boot/kernel.img       # Kernel binary
│       ├── boot/limine/          # Bootloader + config
│       ├── boot/initramfs.gz     # Compressed initramfs
│       ├── boot/initramfs/       # Initramfs contents
│       │   ├── init              # PID 1 (transpiled binary)
│       │   ├── bin/fdisk etc.    # Static utilities
│       │   └── installer/        # Installer + payloads
│       └── EFI/BOOT/BOOTX64.EFI  # EFI executable
│
├── Source payloads (untracked)
│   ├── system-initramfs/         # Copied into efidata/initramfs/
│   └── system-rootfs/            # Copied into rootdata/
│
├── Upstream source trees (untracked, excluded via .gitignore)
│   ├── kernel/                   # Full Linux 6.1.177 source
│   ├── util-linux-2.40/
│   ├── e2fsprogs-1.47.3/
│   └── iw-6.17/
│
├── Config
│   ├── .gitignore
│   └── AGENTS.md
│
├── Tools
│   ├── limine-binary/            # Limine bootloader
│   └── *.EFI, *.sys, *.bin
│
└── Outputs (untracked)
    ├── noodlix.iso               # Built ISO
    └── noodlix_disk.img          # QEMU test disk
```

---

## Current Status

| Feature | Status |
|---------|--------|
| Installer ISO boots in QEMU | ✅ |
| Disk partitioning (fdisk) interactive | ✅ |
| Format vfat + ext4 | ✅ |
| Copy efidata/ → EFI partition | ✅ |
| Copy rootdata/ → root partition | ✅ |
| Reboot into installed system | ✅ boots to Limine |
| Root filesystem (mount, switch_root) | ❌ — not yet built |
| System initramfs | ❌ — placeholder |
| Kernel download + build script | ✅ |
| Nested initramfs for installed system | ❌ — placeholder |
| Display server | ❌ — planned |
| Package manager (transpilatron-based) | ❌ — planned |
| Self-hosting transpilatron | ❌ — planned |
| Formatting/linting | ❌ — follow existing patterns |

---

## Repository

- **GitHub**: https://github.com/NoodlixProject/noodlix
- **Remote**: `origin https://github.com/NoodlixProject/noodlix.git`
- **Transpilatron**: https://github.com/NoodlixProject/transpilatron
- **Branch**: `main`

### Git conventions

- Build artifacts and upstream source trees are `.gitignore`'d
- `installer_iso/` is tracked (19 files, 55MB)
- Kernel source is not tracked — only `kernel/noodlix-working.config`
- `.env` (OpenRouter API key) is gitignored

### Key commits

- Root commit: clean initial commit with 36 project files (8993 lines)
- Subsequent commits tracked `installer_iso/`, fixed `.gitignore`, added build
  automation

---

## Known Gotchas

1. **Working directory sensitivity**: Build scripts `cd` and use relative paths.
   Always run from the project root.

2. **Duplicated modules**: `mounter.py` and `power.py` are duplicated between
   `installer/` and `booterthingy/`. Changes must be mirrored.

3. **`system-initramfs/` and `system-rootfs/` are empty** — placeholder
   directories for future payloads.

4. **`init` is a transpiled binary** — edit `booterthingy/main.py`, recompile
   with `transpilatron --minimal main.py`.

5. **`noodlix_vars.fd`** auto-created by `testinvm.sh` from OVMF vars.
   Requires OVMF UEFI firmware installed on the host.

6. **Python 3.14 requirement** for the installer — pre-release/development
   version.

7. **Kernel config is `noodlix-working.config`** — not `.config`. Must be
   copied/renamed for `make` to pick it up (done automatically by
   `environment_setup.py`).

8. **No automated testing** — no CI/CD, no linters, no formatters.

9. **QEMU needs `-display sdl` without `gl=on`** — `gl=on` clobbers the UEFI
   framebuffer on some hosts.
