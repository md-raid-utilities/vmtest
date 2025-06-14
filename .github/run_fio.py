import os
import sys
import subprocess

def find_5gb_drives():
    drives = []
    try:
        output = subprocess.check_output(
            ['lsblk', '-b', '-o', 'NAME,SIZE'],
            text=True
        ).strip().split('\n')[1:]

        for line in output:
            parts = line.split()
            if len(parts) != 2:
                continue
            name, size_str = parts
            size = int(size_str)
            # Check if size is small enough to not be the boot drive
            if 4.9e9 <= size <= 5.5e9:
                drives.append(f'/dev/{name}')
                if len(drives) >= 4:
                    break
    except subprocess.CalledProcessError as e:
        print(f"Error executing lsblk: {e}")
    return drives

def create_raid(drives, level):
    if len(drives) < 4:
        print("Not enough drives for RAID setup.")
        return None

    raid_device = '/dev/md0'
    level_str = str(level)
    if level in [5, 10]:
        level_str = str(level)

    print(f"Creating RAID{level_str} array with devices: {drives}...")

    create_cmd = [
        'sudo', 'mdadm', '--create', raid_device,
        f'--level={level_str}',
        f'--raid-devices={len(drives)}'
    ] + drives + [
        '--assume-clean',
        '--force'
    ]

    print(f"Executing command: {' '.join(create_cmd)}")
    try:
        result = subprocess.run(
            create_cmd,
            input='yes\n',
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("RAID created successfully.")
        return raid_device
    except subprocess.CalledProcessError as e:
        print(f"Error creating RAID{level_str}: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return None
    except FileNotFoundError:
        print("Error: mdadm command not found. Please install mdadm.")
        return None

def run_fio(raid_device):
    fio_cmd = [
        'sudo', 'fio', '--name=raid-test', '--rw=readwrite', '--bs=4k',
        '--runtime=10', '--verify=md5', '--numjobs=4', '--time_based',
        '--group_reporting', '--offset_increment=1G', '--filename=' + raid_device
    ]
    print("Running fio test with command:", ' '.join(fio_cmd))
    try:
        subprocess.run(fio_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"fio test failed: {e}")

def clean_up(raid_device, drives):
    print("Cleaning up RAID array and drives...")
    try:
        subprocess.run(['sudo', 'mdadm', '--stop', raid_device], check=True)
        subprocess.run(['sudo', 'mdadm', '--zero-superblock'] + drives, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during cleanup: {e}")

def main():
    drives = find_5gb_drives()
    if not drives:
        print("No suitable drives found.")
        sys.exit(1)

    raid_levels = [0, 1, 10, 5]
    for level in raid_levels:
        raid_device = create_raid(drives, level)
        if raid_device:
            run_fio(raid_device)
            clean_up(raid_device, drives)
        else:
            print(f"Skipping RAID level {level} due to creation failure.")

if __name__ == "__main__":
    main()
