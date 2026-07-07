import os


def chmod(path: str, mode: str) -> None:
    """Set file permissions.

    Args:
        path: Path to the file or directory.
        mode: Permission string as octal digits, e.g. "755", "644".

    Permission digits (each 0-7):
        Digit | Binary | Permissions
        ------|--------|------------
        0     | 000    | ---
        1     | 001    | --x
        2     | 010    | -w-
        3     | 011    | -wx
        4     | 100    | r--
        5     | 101    | r-x
        6     | 110    | rw-
        7     | 111    | rwx

        A 4th digit sets special bits:
        Digit | Bit
        ------|----
        0     | none
        1     | sticky
        2     | setgid
        3     | sticky + setgid
        4     | setuid
        5     | setuid + sticky
        6     | setuid + setgid
        7     | setuid + setgid + sticky

        Examples: "644" = rw-r--r--, "4755" = rwsr-xr-x

    Raises:
        ValueError: If the mode string is invalid.
        OSError: If chmod fails.
    """
    if not mode.isdigit():
        raise ValueError(f"Invalid mode: {mode}")
    os.chmod(path, int(mode, 8))
