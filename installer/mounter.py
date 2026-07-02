import ctypes
import os

libc = ctypes.CDLL(None, use_errno=True)

# mount()
libc.mount.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_ulong,
    ctypes.c_void_p,
]
libc.mount.restype = ctypes.c_int

# umount2()
libc.umount2.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
]
libc.umount2.restype = ctypes.c_int

MS_MOVE = 8192

MNT_FORCE = 1
MNT_DETACH = 2
MNT_EXPIRE = 4
UMOUNT_NOFOLLOW = 8


def mount(
    source: str, target: str, fstype: str, flags: int = 0, data: str | None = None
):
    ret = libc.mount(
        source.encode() if source else None,
        target.encode(),
        fstype.encode() if fstype else None,
        ctypes.c_ulong(flags),
        data.encode() if data else None,
    )

    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def umount(target: str, flags: int = 0):
    ret = libc.umount2(
        target.encode(),
        flags,
    )

    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def switch_root(newroot: str, init: str):
    os.chdir(newroot)

    # Move the mounted new root onto /
    if libc.mount(b".", b"/", None, ctypes.c_ulong(MS_MOVE), None) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))

    os.chdir("/")
    os.chroot(".")

    # Optional: unmount old initramfs mounts
    for path in ("/proc", "/sys", "/dev"):
        try:
            umount(path, MNT_DETACH)
        except OSError:
            pass

    os.execv(init, [init])
