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

# syscall() — generic syscall wrapper for pivot_root
libc.syscall.argtypes = [
    ctypes.c_long,  # syscall number
    ctypes.c_char_p,  # arg1 (new_root)
    ctypes.c_char_p,  # arg2 (put_old)
]
libc.syscall.restype = ctypes.c_long

# umount2()
libc.umount2.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
]
libc.umount2.restype = ctypes.c_int

MS_MOVE = 8192

# pivot_root syscall number on x86_64
SYS_pivot_root = 155

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


def pivot_root(new_root: str, put_old: str):
    ret = libc.syscall(
        SYS_pivot_root,
        new_root.encode(),
        put_old.encode(),
    )
    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def switch_root(newroot: str, init: str):
    # Create mount point for old root inside new root
    put_old = os.path.join(newroot, ".old_root")
    os.makedirs(put_old, exist_ok=True)

    # Swap mounts: newroot becomes /, old root goes to put_old
    pivot_root(newroot, put_old)

    os.chdir("/")

    # Unmount the old initramfs root — lazy is fine, it frees the RAM
    umount("/.old_root", MNT_DETACH)

    os.execv(init, [init])
