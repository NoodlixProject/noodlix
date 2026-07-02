import ctypes
import os

libc = ctypes.CDLL(None, use_errno=True)

# x86_64 syscall number
SYS_reboot = 169

LINUX_REBOOT_MAGIC1 = 0xFEE1DEAD
LINUX_REBOOT_MAGIC2 = 672274793

LINUX_REBOOT_CMD_RESTART = 0x1234567
LINUX_REBOOT_CMD_HALT = 0xCDEF0123
LINUX_REBOOT_CMD_POWER_OFF = 0x4321FEDC


def _reboot(cmd):
    ret = libc.syscall(
        SYS_reboot,
        LINUX_REBOOT_MAGIC1,
        LINUX_REBOOT_MAGIC2,
        cmd,
        0,
    )

    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def reboot():
    _reboot(LINUX_REBOOT_CMD_RESTART)


def halt():
    _reboot(LINUX_REBOOT_CMD_HALT)


def poweroff():
    _reboot(LINUX_REBOOT_CMD_POWER_OFF)
