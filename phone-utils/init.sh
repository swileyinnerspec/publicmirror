#!/bin/sh
#This generates an init.sh for starting a full PMOS rootfs directly from the initramfs
#This is not intended as a replacement for the mkinitfs package 
[ -e /etc/postmarketos-mkinitfs/hooks/10-verbose-initfs.sh ] && set -x

. /etc/deviceinfo
. ./init_functions.sh

export PATH=/usr/bin:/bin:/usr/sbin:/sbin
/bin/busybox --install -s
/bin/busybox-extras --install -s

# Mount everything, set up logging, modules, mdev
mount_proc_sys_dev
setup_log
setup_firmware_path
# shellcheck disable=SC2154,SC2086
[ -d /lib/modules ] && modprobe -a ${deviceinfo_modules_initfs} ext4 usb_f_rndis

setup_mdev
setup_framebuffer

# Hooks
for hook in /etc/postmarketos-mkinitfs/hooks/*.sh; do
	[ -e "$hook" ] || continue
	sh "$hook"
done

# Always run dhcp daemon/usb networking for now (later this should only
# be enabled, when having the debug-shell hook installed for debugging,
# or get activated after the initramfs is done with an OpenRC service).
setup_usb_network
start_udhcpd

mount_boot_partition /boot
show_splash_loading
extract_initramfs_extra @INITRAMFS_EXTRA@

# Mount boot partition into sysroot, so OpenRC doesn't need to do it (#664)
umount /boot
mount_boot_partition /sysroot/boot "rw"

init="/sbin/init"
setup_bootchart2

# Switch root
killall telnetd mdev msm-fb-refresher 2>/dev/null
umount /proc
umount /sys
umount /dev/pts
umount /dev

# shellcheck disable=SC2093
exec "$init"

echo "ERROR: switch_root failed!"
echo "Looping forever. Install and use the debug-shell hook to debug this."
echo "For more information, see <https://postmarketos.org/debug-shell>"
loop_forever
