#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
#

echo "Copy base .config"
cp /boot/config-`uname -r`* .config

echo "Make localmodconfig"
yes '' | make localmodconfig -j20
cp .config config.pre

echo "Turn on CONFIG_MD_RAID0"
gawk '{gsub(/# CONFIG_MD_RAID0 is not set/, "CONFIG_MD_RAID0=y")} 1' .config > .config.tmp
cp .config.tmp .config

echo "Turn on CONFIG_MD_RAID1"
gawk '{gsub(/# CONFIG_MD_RAID1 is not set/, "CONFIG_MD_RAID1=y")} 1' .config  > .config.tmp
cp .config.tmp .config

echo "Turn on CONFIG_MD_RAID10"
gawk '{gsub(/# CONFIG_MD_RAID10 is not set/, "CONFIG_MD_RAID10=y")} 1' .config > .config.tmp
cp .config.tmp .config

echo "Turn on CONFIG_MD_RAID456"
gawk '{gsub(/# CONFIG_MD_RAID456 is not set/, "CONFIG_MD_RAID456=y")} 1' .config > .config.tmp
cp .config.tmp .config

echo "Done updating .config!"
