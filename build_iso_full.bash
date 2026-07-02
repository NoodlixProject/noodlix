#! /bin/bash

cp -a system-initramfs/* installer_iso/boot/initramfs/installer/efidata/initramfs/

./pack_any_initramfs.bash installer_iso/boot/initramfs/installer/efidata/initramfs/ installer_iso/boot/initramfs/installer/efidata/initramfs.img

./build.sh installer_iso noodlix.iso