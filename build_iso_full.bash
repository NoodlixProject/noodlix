#! /bin/bash
set -e

# Copy system initramfs into efidata and pack it for the installed system
mkdir -p installer_iso/boot/initramfs/installer/efidata/boot/initramfs/
cp -a system-initramfs/* installer_iso/boot/initramfs/installer/efidata/boot/initramfs/ 2>/dev/null || true
./pack_any_initramfs.bash installer_iso/boot/initramfs/installer/efidata/boot/initramfs/ installer_iso/boot/initramfs/installer/efidata/boot/initramfs.gz

# Copy rootfs into rootdata/
mkdir -p installer_iso/boot/initramfs/installer/rootdata/
cp -a system-rootfs/* installer_iso/boot/initramfs/installer/rootdata/ 2>/dev/null || true

# Build the outer initramfs and ISO
./build.sh installer_iso noodlix.iso