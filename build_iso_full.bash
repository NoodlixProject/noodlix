#! /bin/bash

cp -a system-initramfs/* installer_iso/boot/initramfs/installer/efidata/initramfs/
cp -a system-rootfs/* installer_iso/boot/initramfs/installer/rootdata/

./pack_any_initramfs.bash installer_iso/boot/initramfs/installer/efidata/initramfs/ installer_iso/boot/initramfs/installer/efidata/initramfs.img

./build.sh installer_iso noodlix.iso