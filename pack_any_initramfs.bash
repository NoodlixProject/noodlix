#!/bin/bash
set -e

INITRAMFS_DIR="${1}"
INITRAMFS_OUT="${2}"

if [ -z "$INITRAMFS_DIR" ] || [ -z "$INITRAMFS_OUT" ]; then
    echo "Usage: $0 <initramfs_dir> <output.gz>"
    exit 1
fi

echo "==> Packing initramfs from $INITRAMFS_DIR to $INITRAMFS_OUT..."
cd "$INITRAMFS_DIR"
find . | cpio -o -H newc | gzip > "$OLDPWD/$INITRAMFS_OUT"
cd "$OLDPWD"
echo "==> Done!"
