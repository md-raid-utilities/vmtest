#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause

echo "Configure Kernel..."
printf '\r\n' | make localmodconfig V1 -j$(nproc)
cp .config config.pre

echo "Enable all RAID modules..."
gawk '
{
    if ($0 ~ /^(# )?CONFIG_MD_RAID[01456](=[ymn]| is not set)?$/) {
        next;
    }
    print $0;
}
END {
    print "CONFIG_MD_RAID0=y";
    print "CONFIG_MD_RAID1=y";
    print "CONFIG_MD_RAID10=y";
    print "CONFIG_MD_RAID456=y";
}' .config > .config.tmp

cp .config.tmp .config

echo "Done updating .config!"
