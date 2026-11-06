#
#	OrangeFox Recovery Project
#	OnePlus Nord N100 (billie2)
#
FDEVICE="billie2"

fox_get_target_device() {
  if echo "$BASH_SOURCE" | grep -q "/$FDEVICE/"; then
      FOX_BUILD_DEVICE="$FDEVICE";
  elif set | grep BASH_ARGV | grep -w \"$FDEVICE\"; then
      FOX_BUILD_DEVICE="$FDEVICE";
  elif echo "${BASH_SOURCE[0]}" | grep -q "/$FDEVICE/"; then
      FOX_BUILD_DEVICE="$FDEVICE";
  elif echo "$0" | grep -q "$FDEVICE"; then
      FOX_BUILD_DEVICE="$FDEVICE";
  fi
}

if [ -z "$1" -a -z "$FOX_BUILD_DEVICE" ]; then
   fox_get_target_device
fi

if [ "$1" = "$FDEVICE" -o "$FOX_BUILD_DEVICE" = "$FDEVICE" ]; then

	export LC_ALL="C"
	export TARGET_ARCH="arm64"
	export ALLOW_MISSING_DEPENDENCIES=true

	export FOX_BUILD_TYPE="Stable"
	export FOX_VANILLA_BUILD=1
	export OF_DISABLE_MIUI_SPECIFIC_FEATURES=1
	export FOX_AB_DEVICE=1

	export TARGET_DEVICE_ALT="OnePlusN100,BE2013"
	export FOX_TARGET_DEVICES="billie2,$TARGET_DEVICE_ALT"

	# Partition mapper
	export FOX_RECOVERY_SYSTEM_PARTITION="/dev/block/mapper/system"
	export FOX_RECOVERY_VENDOR_PARTITION="/dev/block/mapper/vendor"

	# Storage theme paths
	export FOX_SETTINGS_ROOT_DIRECTORY=/persist/recovery
	export FOX_MISCELLANEOUS_ROOT_DIRECTORY=/sdcard

	# Tools & features
	export FOX_USE_TAR_BINARY=1
	export FOX_USE_SED_BINARY=1
	export FOX_USE_LZ4_BINARY=1
	export FOX_USE_ZSTD_BINARY=1
	export FOX_USE_DATE_BINARY=1
	export FOX_USE_GREP_BINARY=1
	export FOX_USE_BUSYBOX_BINARY=1
	export FOX_USE_XZ_UTILS=1
	export FOX_USE_UPDATED_MAGISKBOOT=1
	export FOX_MOVE_MAGISK_INSTALLER_TO_RAMDISK=1
	export FOX_DELETE_AROMAFM=1

fi
