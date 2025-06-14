import os
import sys
import subprocess

def find_5gb_drives():
    drives = []
    output = subprocess.check_output(['lsblk', '-b', '-o', 'NAME,SIZE']).decode('utf-8').strip().split('\n')[1:]

    for line in output:
        parts = line.split()
        name = parts[0]
        size = int(parts[1])
        # make sure we're not hitting the larger boot disk, drive names change
        if 4.9e9 <= size <= 5.5e9:
            drives.append(f'/dev/{name}')
        if len(drives) >= 4:
            break
    print(drives)
    return drives

def create_raid(drives, level):
    if len(drives) < 4:
        print("Not enough drives for RAID setup.")
        return None

    raid_device = '/dev/md0'
    level_str = str(level)
    if level == 10 or level == 5:
        level_str = '10' if level == 10 else '5'

    print(f"Creating RAID{level_str} array with devices: {drives}...")

    create_cmd = [
        'sudo', 'mdadm', '--create', raid_device,
        f'--level={level_str}',
        f'--raid-devices={len(drives)}'
    ] + drives + [
        '--assume-clean',
        '--force'
    ]

    print(f"Executing command: {' '.join(create_cmd)}") # Print for debugging/logging
    try:
        process = subprocess.run(
            create_cmd,
            input=b'yes\n',
            check=True,
        )
        print("STDOUT:", process.stdout)
        print("STDERR:", process.stderr)
        print(f"RAID{level_str} array '{raid_device}' created successfully.")
        return raid_device
    except subprocess.CalledProcessError as e:
        print(f"Error creating RAID{level_str} array '{raid_device}':")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return None
    except FileNotFoundError:
        print("Error: mdadm command not found. Make sure mdadm is installed.")
        return None

    return raid_device

def run_fio(raid_device):
    print("Running fio test...")
    fio_cmd = [
        'sudo', 'fio', '--name=raid-test', '--rw=readwrite', '--bs=4k',
        '--runtime=10', '--verify=md5', '--numjobs=4', '--time_based',
        '--group_reporting', '--filename=' + raid_device
    ]
    print(fio_cmd)
    subprocess.run(fio_cmd, check=True)

def clean_up(raid_device, drives):
    print("Cleaning up...")
    subprocess.run(['sudo', 'mdadm', '--stop', raid_device], check=True)
    subprocess.run(['sudo', 'mdadm', '--zero-superblock'] + drives, check=True)

def main():
    try:
        drives = find_5gb_drives()
        if drives is None:
            sys.exit(1)
        raid_levels = [0, 1, 10, 5]

        for level in raid_levels:
            raid_device = create_raid(drives, level)
            if raid_device:
                run_fio(raid_device)
                clean_up(raid_device, drives)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
