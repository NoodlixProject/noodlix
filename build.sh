#!/bin/bash
set -e

ISO_DIR="${1:-iso}"
INITRAMFS_DIR="$ISO_DIR/boot/initramfs"
INITRAMFS_OUT="$ISO_DIR/boot/initramfs.gz"

ISO_OUT="${2:-noodlix.iso}"

echo "==> Packing initramfs..."
cd "$INITRAMFS_DIR"
find . | cpio -o -H newc | gzip > "../../../$INITRAMFS_OUT"
cd ../../..

echo "==> Building ISO..."
xorriso -as mkisofs \
    -b boot/limine/limine-bios-cd.bin \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    --efi-boot boot/limine/limine-uefi-cd.bin \
    -efi-boot-part \
    --efi-boot-image \
    --protective-msdos-label \
    -o "$ISO_OUT" \
    "$ISO_DIR"

echo "==> Installing Limine BIOS bootloader..."
./limine bios-install "$ISO_OUT"

echo "==> Done! $ISO_OUT ready."