#!/usr/bin/env python3

from copy import deepcopy
from json import dumps
from enum import Enum
import os


class Arch(Enum):
    """
    CPU architecture supported by CI.
    """

    AARCH64 = "aarch64"
    S390X = "s390x"
    X86_64 = "x86_64"


def set_output(name, value):
    """Write an output variable to the GitHub output file."""
    with open(os.getenv("GITHUB_OUTPUT"), "a", encoding="utf-8") as file:
        file.write(f"{name}={value}\n")


def generate_test_config(test):
    """Create the configuration for the provided test."""
    experimental = test.endswith("_parallel")
    config = {
        "test": test,
        "continue_on_error": experimental,
        # While in experimental mode, parallel jobs may get stuck
        # anywhere, including in user space where the kernel won't detect
        # a problem and panic. We add a second layer of (smaller) timeouts
        # here such that if we get stuck in a parallel run, we hit this
        # timeout and fail without affecting the overall job success (as
        # would be the case if we hit the job-wide timeout). For
        # non-experimental jobs, 360 is the default which will be
        # superseded by the overall workflow timeout (but we need to
        # specify something).
        "timeout_minutes": 30 if experimental else 360,
    }
    return config


def get_tests(config):
    tests = [
        "test_progs",
        "test_progs_parallel",
        "test_progs_no_alu32",
        "test_progs_no_alu32_parallel",
        "test_maps",
        "test_verifier",
    ]
    if config.get("parallel_tests", True):
        return tests
    return [test for test in tests if not test.endswith("parallel")]


matrix = [
    {
        "kernel": "LATEST",
        "runs_on": [],
        "arch": Arch.X86_64.value,
        "toolchain": "gcc",
        "llvm-version": "16",
        "run_veristat": True,
    },
    {
        "kernel": "LATEST",
        "runs_on": [],
        "arch": Arch.X86_64.value,
        "toolchain": "llvm",
        "llvm-version": "16",
    },
    {
        "kernel": "LATEST",
        "runs_on": [],
        "arch": Arch.AARCH64.value,
        "toolchain": "gcc",
        "llvm-version": "16",
    },
    # {
    #     "kernel": "LATEST",
    #     "runs_on": [],
    #     "arch": Arch.AARCH64.value,
    #     "toolchain": "llvm",
    #     "llvm-version": "16",
    # },
    {
        "kernel": "LATEST",
        "runs_on": [],
        "arch": Arch.S390X.value,
        "toolchain": "gcc",
        "llvm-version": "16",
        "parallel_tests": False,
    },
]
self_hosted_repos = [
    "kernel-patches/bpf",
    "kernel-patches/vmtest",
]

for idx in range(len(matrix) - 1, -1, -1):
    if matrix[idx]["toolchain"] == "gcc":
        matrix[idx]["toolchain_full"] = "gcc"
    else:
        matrix[idx]["toolchain_full"] = "llvm-" + matrix[idx]["llvm-version"]

    # Set run_veristat to false by default.
    matrix[idx]["run_veristat"] = matrix[idx].get("run_veristat", False)
    # Feel in the tests
    matrix[idx]["tests"] = {"include": [
            generate_test_config(test)
            for test in get_tests(matrix[idx])
        ]
    }

# Only a few repository within "kernel-patches" use self-hosted runners.
if (
    os.environ["GITHUB_REPOSITORY_OWNER"] != "kernel-patches"
    or os.environ["GITHUB_REPOSITORY"] not in self_hosted_repos
):
    # Outside of those repositories, we only run on x86_64 GH hosted runners (ubuntu-20.04)
    # We need to run on ubuntu 20.04 because our rootfs is based on debian buster and we
    # otherwise get library versioning issue such as
    # `./test_verifier: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found (required by ./test_verifier)`
    for idx in range(len(matrix) - 1, -1, -1):
        if matrix[idx]["arch"] != Arch.X86_64.value:
            del matrix[idx]
        else:
            matrix[idx]["runs_on"] = ["ubuntu-20.04"]
else:
    # Otherwise, run on (self-hosted, arch) runners
    for idx in range(len(matrix) - 1, -1, -1):
        matrix[idx]["runs_on"].extend(["self-hosted", matrix[idx]["arch"]])

build_matrix = {"include": matrix}

set_output("build_matrix", dumps(build_matrix))