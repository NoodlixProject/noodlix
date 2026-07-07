import ctypes
import os
import stat

libc = ctypes.CDLL(None, use_errno=True)

# chmod()
libc.chmod.argtypes = [ctypes.c_char_p, ctypes.c_uint]
libc.chmod.restype = ctypes.c_int


def chmod(path: str, mode: str) -> None:
    """Set file permissions.

    Args:
        path: Path to the file or directory.
        mode: Permission string — numeric ("755", "644") or symbolic ("u+x", "a-w").

    Raises:
        ValueError: If the mode string is invalid.
        OSError: If chmod fails.
    """
    # Convert mode string to integer
    if mode.isdigit():
        # Numeric mode — parse as octal
        mode_int = int(mode, 8)
    elif "+" in mode or "-" in mode or "=" in mode:
        # Symbolic mode — resolve current mode and apply changes
        st = os.stat(path)
        current = stat.S_IMODE(st.st_mode)
        mode_int = _parse_symbolic(mode, current)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    ret = libc.chmod(path.encode(), mode_int)
    if ret != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))


def _parse_symbolic(sym_mode: str, current: int) -> int:
    """Parse a symbolic mode string (e.g. "u+x", "a-w", "go+r") and apply to current mode."""
    WHO_MAP = {"u": stat.S_IRWXU, "g": stat.S_IRWXG, "o": stat.S_IRWXO, "a": 0o777}
    PERM_MAP = {
        "r": stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
        "w": stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH,
        "x": stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
    }

    # Split on comma for multiple clauses
    clauses = sym_mode.split(",")
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue

        # Parse who
        if clause[0] in WHO_MAP:
            who_str = clause[0]
            who = WHO_MAP[who_str]
            rest = clause[1:]
        else:
            who = 0o777  # default "a"
            rest = clause

        # Parse operation and permissions
        if "+" in rest:
            parts = rest.split("+")
            op = "+"
        elif "-" in rest:
            parts = rest.split("-")
            op = "-"
        elif "=" in rest:
            parts = rest.split("=")
            op = "="
        else:
            raise ValueError(f"Invalid symbolic mode: {clause}")

        perm_part = parts[1] if len(parts) > 1 else ""

        # Build permission bits
        perm_bits = 0
        for p in perm_part:
            if p in PERM_MAP:
                perm_bits |= PERM_MAP[p]

        # Apply to the relevant who bits
        if op == "+":
            current |= perm_bits & who
        elif op == "-":
            current &= ~(perm_bits & who)
        elif op == "=":
            # Clear who bits, then set
            current &= ~who
            current |= perm_bits & who

    return current