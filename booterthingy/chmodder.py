import os


def chmod(path: str, mode: str) -> None:
    """Set file permissions.

    Args:
        path: Path to the file or directory.
        mode: Permission string as octal digits, e.g. "755", "644".

    Raises:
        ValueError: If the mode string is invalid.
        OSError: If chmod fails.
    """
    if not mode.isdigit():
        raise ValueError(f"Invalid mode: {mode}")
    os.chmod(path, int(mode, 8))
