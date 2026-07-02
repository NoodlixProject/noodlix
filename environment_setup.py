from platform import system
from subprocess import run
from os import environ, chdir
from shutil import copy2


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
    ]
)
run("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True)
chdir("booterthingy")
run(["uv", "sync"])
chdir("..")
run("uv tool install transpilatron", shell=True)
copy2("kernel/noodlix-working.config", "kernel/.config")
yn = input("Type y to compile kernel or n to use default kernel (default n): ")
if yn.lower() == "y":
    run(["make", "-C", "kernel"])
else:
    print("All done!")

print("Complete")
