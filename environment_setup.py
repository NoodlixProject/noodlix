from platform import system
from subprocess import run
from os import environ, chdir, cpu_count
from shutil import copy2
from pathlib import Path


def get_linux_distro():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=")[1].strip().strip('"')
    except FileNotFoundError:
        pass
    return "Unknown"


if system() == "Linux":
    distro = get_linux_distro()
    print(f"Linux distribution: {distro}")
elif system() == "Windows":
    print(
        "ERROR: Windows is not supported. This tool requires a Debian or Ubuntu-based Linux distribution."
    )
    exit(1)
elif system() == "Darwin":
    print(
        "ERROR: macOS is not supported. This tool requires a Debian or Ubuntu-based Linux distribution. And I hate macs."
    )
    exit(1)
else:
    print(
        f"ERROR: Unrecognized operating system ({system()}). This tool requires a Debian or Ubuntu-based Linux distribution. Heeeeeeey. Are you running this on Noodlix itself? Clever."
    )
    exit(1)

if (
    "debian" not in distro.lower()
    and "ubuntu" not in distro.lower()
    and environ.get("ND_SETUP_APT_OVERRIDE") != "1"
):
    print(f"ERROR: '{distro}' is not a supported distribution.")
    print("This tool requires a Debian or Ubuntu-based Linux distribution.")
    print(
        "If you are sure that your distrobution has apt, please set the ND_SETUP_APT_OVERRIDE=1 environment variable."
    )
    exit(1)

print("Environment check passed. Let's cook noodles.")
run(["sudo", "apt", "update"])
run(["sudo", "apt", "upgrade", "-y"])
run(["sudo", "apt", "update"])
run(
    [
        "sudo",
        "apt",
        "install",
        "-y",
        "xorriso",
        "git",
        "make",
        "build-essential",
        "cpio",
        "wget",
        "flex",
        "bison",
        "libssl-dev",
    ]
)
run("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True)
chdir("booterthingy")
run(["uv", "sync"])
chdir("..")
run("uv tool install transpilatron", shell=True)

# Download and extract Linux 6.1.175 kernel source if not already present
print("\nChecking for Linux 6.1.175 kernel source...")
kernel_source_dir = Path("kernel/linux-6.1.175")
if not kernel_source_dir.exists():
    print("Linux 6.1.175 source not found. Downloading...")
    kernel_tar = Path("kernel/linux-6.1.175.tar.xz")
    
    # Download the kernel source
    run(
        ["wget", "-O", str(kernel_tar),
         "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.1.175.tar.xz"]
    )
    
    if kernel_tar.exists():
        print(f"Extracting {kernel_tar.name}...")
        run(["tar", "xf", str(kernel_tar), "-C", "kernel"])
        print("Kernel source extracted successfully.")
    else:
        print("ERROR: Failed to download kernel source.")
        exit(1)
else:
    print("Linux 6.1.175 source already present.")

# Copy the config file to the kernel source directory
config_src = Path("kernel/noodlix-working.config")
config_dst = Path("kernel/linux-6.1.175/.config")
if config_src.exists():
    copy2(config_src, config_dst)
    print(f"Copied {config_src} to {config_dst}")
else:
    print(f"ERROR: Config file not found at {config_src}")
    exit(1)

yn = input("Type y to compile kernel or n to skip kernel compilation (default n): ")
if yn.lower() == "y":
    print("Building kernel (this may take a while)...")
    chdir("kernel/linux-6.1.175")
    run(["make", "-j" + str(cpu_count() or 1)])
    print("Kernel build complete!")
    chdir("arch/x86_64/boot")
    run(["cp", "bzImage", "../../../../../installer_iso/boot/kernel.img"])
    run(["cp", "bzImage", "../../../../../installer_iso/boot/initramfs/installer/efidata/boot/kernel.img"])
    chdir("../../../../..")
    print("Copied bzImage to installer_iso/boot/kernel.img and efidata/boot/kernel.img.")
else:
    print("Skipped kernel compilation.")

print("All done! You can now run ./build_iso_full.bash to build the ISO.")
