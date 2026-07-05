#! /bin/bash
set -e

mkdir -p installer_iso/boot/initramfs/installer/efidata/initramfs/
cp -a system-initramfs/* installer_iso/boot/initramfs/installer/efidata/initramfs/ 2>/dev/null || true

mkdir -p installer_iso/boot/initramfs/installer/rootdata/
cp -a system-rootfs/* installer_iso/boot/initramfs/installer/rootdata/ 2>/dev/null || true

./pack_any_initramfs.bash installer_iso/boot/initramfs/installer/efidata/initramfs/ installer_iso/boot/initramfs/installer/efidata/initramfs.img

./build.sh installer_iso noodlix.iso