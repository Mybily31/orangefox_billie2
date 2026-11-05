#
# OrangeFox Recovery configuration for the OnePlus Nord N100 (billie2)
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

OF_MAINTAINER := bily31

# Display (720x1600, waterdrop notch)
OF_SCREEN_H := 1600
OF_STATUS_H := 72
OF_HIDE_NOTCH := 1
OF_STATUS_INDENT_LEFT := 30
OF_STATUS_INDENT_RIGHT := 30
OF_CLOCK_POS := 0
OF_USE_GREEN_LED := 0
OF_USE_LEGACY_BATTERY_SERVICES := 1

# A/B device with a dedicated recovery partition (not virtual A/B)
OF_AB_DEVICE_WITH_RECOVERY_PARTITION := 1

# Dynamic partitions: super is 10 GiB, two 5 GiB slot groups
OF_DYNAMIC_FULL_SIZE := 10737418240

# Force the prebuilt kernel from prebuilt/Image.gz
OF_FORCE_PREBUILT_KERNEL := 1

# The stock vendor image ships keymaster 4.0
OF_DEFAULT_KEYMASTER_VERSION := 4.0

# Partition tools and backup defaults
OF_ENABLE_ALL_PARTITION_TOOLS := 1
OF_QUICK_BACKUP_LIST := /boot;/recovery;/data;/metadata;/dtbo;
OF_SKIP_MULTIUSER_FOLDERS_BACKUP := 1
OF_WIPE_METADATA_AFTER_DATAFORMAT := 1
OF_UNBIND_SDCARD_F2FS := 1

# Logging
OF_LOOP_DEVICE_ERRORS_TO_LOG := 1
