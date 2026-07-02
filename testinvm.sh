#!/bin/bash

# 1. Ask the user what they want to boot
echo "========================================"
echo "          NOODLIX BOOT SELECT           "
echo "========================================"
echo "1) Boot Installer (ISO + Hard Disk attached)"
echo "2) Boot Hard Disk Only (Production Run)"
read -p "Select boot target [1-2]: " boot_choice

# 2. Check if disk image exists, create it if missing
if [ ! -f noodlix_disk.img ]; then
    echo "Creating missing disk image..."
    qemu-img create -f raw noodlix_disk.img 20G
fi

# 3. Create a local copy of the VARS file if it doesn't exist yet
if [ ! -f noodlix_vars.fd ]; then
    echo "Creating local copy of UEFI VARS..."
    cp /usr/share/OVMF/OVMF_VARS_4M.fd noodlix_vars.fd
    chmod 644 noodlix_vars.fd
fi

echo "========================================"
echo "           VM IS RUNNING                "
echo "========================================"

# 4. Handle QEMU launching based on selection
if [ "$boot_choice" == "1" ]; then
    # Boot Installer ISO
    qemu-system-x86_64 \
        -enable-kvm \
        -cpu host \
        -m 2G \
        -smp 2 \
        -drive file=/usr/share/OVMF/OVMF_CODE_4M.fd,if=pflash,format=raw,readonly=on \
        -drive file=noodlix_vars.fd,if=pflash,format=raw \
        -drive file=noodlix.iso,media=cdrom,format=raw \
        -drive file=noodlix_disk.img,if=virtio,format=raw \
        -vga virtio \
        -display sdl
else
    # Boot directly from hard drive only
    qemu-system-x86_64 \
        -enable-kvm \
        -cpu host \
        -m 2G \
        -smp 2 \
        -drive file=/usr/share/OVMF/OVMF_CODE_4M.fd,if=pflash,format=raw,readonly=on \
        -drive file=noodlix_vars.fd,if=pflash,format=raw \
        -drive file=noodlix_disk.img,if=virtio,format=raw \
        -vga virtio \
        -display sdl
fi