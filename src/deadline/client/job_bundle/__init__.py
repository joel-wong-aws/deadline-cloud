# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

__all__ = [
    "adaptors",
    "create_job_history_bundle_dir",
    "read_job_bundle_parameters",
    "apply_job_parameters",
    "deadline_yaml_dump",
]

import datetime
import glob
import os
import sys

from ..config import get_setting
from ._yaml import deadline_yaml_dump
from .parameters import apply_job_parameters, read_job_bundle_parameters


def create_job_history_bundle_dir(submitter_name: str, job_name: str) -> str:
    """
    Creates a new directory in the configured directory
    settings.job_history_dir, in which to place a new
    job bundle for submission.

    The directory will look like
      <job_history_dir>/YYYY-mm/YYYY-mm-ddTHH-##-<submitter_name>-<job_name>
    """
    job_history_dir = str(get_setting("settings.job_history_dir"))
    job_history_dir = os.path.expanduser(job_history_dir)

    # Clean the submitter_name's characters
    submitter_name_cleaned = "".join(
        char for char in submitter_name if char.isalnum() or char in " -_"
    )

    timestamp = datetime.datetime.now()
    month_tag = timestamp.strftime("%Y-%m")
    date_tag = timestamp.strftime("%Y-%m-%d")

    month_dir = os.path.join(job_history_dir, month_tag)
    if not os.path.isdir(month_dir):
        os.makedirs(month_dir)

    # Index the files so they sort in order of submission
    number = 1
    existing_dirs = sorted(glob.glob(os.path.join(month_dir, f"{date_tag}-*")))
    if existing_dirs:
        latest_dir = existing_dirs[-1]
        number = int(os.path.basename(latest_dir)[len(date_tag) + 1 :].split("-", 1)[0]) + 1

    job_dir_prefix = f"{date_tag}-{number:02}-{submitter_name_cleaned}-"

    max_job_name_prefix = 128  # max job name from OpenJD spec

    # max path length - manifest file name
    # 256 - len("\manifests\d2b2c3102af5a862db950a2e30255429_input")
    # = 207
    if sys.platform in ["win32", "cygwin"]:
        max_job_name_prefix = min(
            207 - len(os.path.abspath(os.path.join(month_dir, job_dir_prefix))), max_job_name_prefix
        )
        if max_job_name_prefix < 1:
            raise RuntimeError(
                "Job history directory is too long. Please update your 'settings.job_history_dir' to a shorter path."
            )

    # Clean the job_name's characters and truncate for the filename
    job_name_cleaned = "".join(char for char in job_name if char.isalnum() or char in " -_")
    job_name_cleaned = job_name_cleaned[:max_job_name_prefix]

    result = os.path.join(month_dir, f"{job_dir_prefix}{job_name_cleaned}")
    os.makedirs(result)
    return result
