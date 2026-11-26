#!/bin/bash
# What takes the space inside a class-VM .ova: biggest folders and installed packages, read-only.
#   sudo ova-size-report.sh <pmity-lab.ova> <work dir>
# Used after "Build the VM" in vm-release.yml, and once on the published 2026-11-23 release to compare (LGS-3: the
# .ova grew from 3.44 to 3.83 GB and outgrew the 10 download pieces).
set -euo pipefail
OVA=$1; T=$2
mkdir -p "$T/m"
tar -xf "$OVA" -C "$T" --wildcards '*.vmdk'
qemu-img convert -O raw "$T"/*.vmdk "$T/disk.raw"; rm -f "$T"/*.vmdk
L=$(losetup -f --show -P -r "$T/disk.raw")
P=$(lsblk -lnbo NAME,SIZE,TYPE "$L" | awk '$3=="part"{print $2, $1}' | sort -n | tail -1 | cut -d' ' -f2)
[ -n "$P" ] || { lsblk "$L"; echo "no partition found"; exit 1; }
mount -o ro,noload "/dev/$P" "$T/m"
echo "== used on the disk"; df -B1M --output=used,size "$T/m" | tail -1
echo "== folders over 40 MB (3 levels)"
du -xm -d3 --threshold=40M "$T/m" 2>/dev/null | sort -n | sed "s#$T/m#  #" | tail -45
echo "== biggest installed packages (MB)"
dpkg-query --admindir="$T/m/var/lib/dpkg" -W -f '${Installed-Size}\t${Package} ${Version}\n' | sort -n | tail -30 | awk -F'\t' '{printf "  %6.0f  %s\n", $1/1024, $2}'
echo "== package count: $(dpkg-query --admindir="$T/m/var/lib/dpkg" -W | wc -l); kernels: $(ls "$T/m/boot" | grep -c '^vmlinuz-')"
ls "$T/m/boot" | grep vmlinuz
umount "$T/m"; losetup -d "$L"; rm -f "$T/disk.raw"
