# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Tests the job bundle folders created for the user's history of jobs.
"""

import os
import sys
import tempfile
import pytest

from freezegun import freeze_time

from deadline.client import config, job_bundle


def test_create_job_bundle_dir(fresh_deadline_config):
    # Use a temporary directory for the job history
    with tempfile.TemporaryDirectory() as tmpdir:
        config.set_setting("settings.job_history_dir", tmpdir)
        EXPECTED_DIRS = [
            "2023-01-15-01-cli_job-Test CLI Job Name",
            "2023-01-15-02-maya-Maya  Job with  Characters",
            "2023-01-15-03-cli_job-",
            "2023-04-15-01-maya-my_scene_filemb",
        ]
        EXPECTED_FULL_PATHS = [os.path.join(tmpdir, reldir[:7], reldir) for reldir in EXPECTED_DIRS]

        # Create a bunch of job bundle directories in order, and check that the expected dir is
        # there in each case.
        with freeze_time("2023-01-15T03:05"):
            assert (
                job_bundle.create_job_history_bundle_dir("cli_job", "Test CLI Job Name")
                == EXPECTED_FULL_PATHS[0]
            )
        assert os.path.isdir(EXPECTED_FULL_PATHS[0])
        with freeze_time("2023-01-15T12:12"):
            assert (
                job_bundle.create_job_history_bundle_dir("maya", "Maya : Job with %~\\/ Characters")
                == EXPECTED_FULL_PATHS[1]
            )
        assert os.path.isdir(EXPECTED_FULL_PATHS[1])
        with freeze_time("2023-01-15T07:10"):
            assert job_bundle.create_job_history_bundle_dir("cli_job", "") == EXPECTED_FULL_PATHS[2]
        assert os.path.isdir(EXPECTED_FULL_PATHS[2])
        with freeze_time("2023-04-15T19:59"):
            assert (
                job_bundle.create_job_history_bundle_dir("maya", "my_scene_file.mb")
                == EXPECTED_FULL_PATHS[3]
            )
        assert os.path.isdir(EXPECTED_FULL_PATHS[3])

        # Confirm the full set of expected directories
        assert sorted(os.listdir(tmpdir)) == ["2023-01", "2023-04"]
        assert sorted(os.listdir(os.path.join(tmpdir, "2023-01"))) == EXPECTED_DIRS[:3]
        assert sorted(os.listdir(os.path.join(tmpdir, "2023-04"))) == EXPECTED_DIRS[3:]


def test_job_history_dir_truncation(fresh_deadline_config):
    # Use a temporary directory for the job history
    with tempfile.TemporaryDirectory() as tmpdir, freeze_time("2024-12-27T12:34:56"):
        tmpdir_path_length = len(os.path.abspath(tmpdir))
        long_tmpdir = os.path.join(
            tmpdir,
            "dir" + "1" * (140 - tmpdir_path_length),
        )
        config.set_setting("settings.job_history_dir", long_tmpdir)

        job_name_127_chars = "job1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234"
        output_path = job_bundle.create_job_history_bundle_dir(
            "MySubmitter",
            job_name_127_chars,
        )

        if sys.platform in ["win32", "cygwin"]:
            assert len(os.path.abspath(output_path)) == 207
            assert str(os.path.abspath(output_path)).startswith(
                str(
                    os.path.abspath(
                        os.path.join(
                            long_tmpdir, "2024-12", "2024-12-27-01-MySubmitter-job1234567890"
                        )
                    )
                )
            )
            assert (
                len(
                    os.path.abspath(
                        os.path.join(
                            output_path, "manifests", "d2b2c3102af5a862db950a2e30255429_input"
                        )
                    )
                )
                == 256
            )
        else:
            assert output_path == os.path.join(
                long_tmpdir, "2024-12", f"2024-12-27-01-MySubmitter-{job_name_127_chars}"
            )
            assert len(output_path) > 256
        assert os.path.isdir(output_path)


def test_job_history_dir_truncation_from_job_name_with_129_chars(fresh_deadline_config):
    # Use a temporary directory for the job history
    if sys.platform in ["win32", "cygwin"]:
        # Windows has a long tmp dir path so it will truncate anyway - we only want to test job name truncation
        tmp_parent_dir = "C:\\ProgramData"
    else:
        tmp_parent_dir = None
    with tempfile.TemporaryDirectory(dir=tmp_parent_dir) as tmpdir, freeze_time(
        "2024-08-26T18:42:05"
    ):
        config.set_setting("settings.job_history_dir", tmpdir)

        job_name_129_chars = "test12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345"
        output_path = job_bundle.create_job_history_bundle_dir(
            "SubmitterFour",
            job_name_129_chars,
        )
        assert output_path == os.path.join(
            tmpdir,
            "2024-08",
            "2024-08-26-01-SubmitterFour-test1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234",
        )
        assert os.path.isdir(output_path)


def test_job_history_dir_exceeds_256_characters(fresh_deadline_config):
    # Use a temporary directory for the job history
    with tempfile.TemporaryDirectory() as tmpdir, freeze_time("2023-11-12T13:14:15"):
        tmpdir_path_length = len(os.path.abspath(tmpdir))
        long_tmpdir = os.path.join(
            tmpdir,
            "dir" + "1" * (256 - tmpdir_path_length),
        )
        config.set_setting("settings.job_history_dir", long_tmpdir)

        job_name_1_char = "a"

        if sys.platform in ["win32", "cygwin"]:
            with pytest.raises(RuntimeError, match="Job history directory is too long"):
                job_bundle.create_job_history_bundle_dir(
                    "SubmitterFive",
                    job_name_1_char,
                )
        else:
            output_path = job_bundle.create_job_history_bundle_dir(
                "SubmitterFive",
                job_name_1_char,
            )
            assert output_path == os.path.join(
                long_tmpdir,
                "2023-11",
                "2023-11-12-01-SubmitterFive-a",
            )
            assert os.path.isdir(output_path)


@pytest.mark.parametrize(
    "submitter_name, job_name, freeze_date, expected_output_path",
    [
        pytest.param(
            "SubmitterOne",
            "JobOne",
            "2023-09-25",
            os.path.join("2023-09", "2023-09-25-01-SubmitterOne-JobOne"),
            id="NoInvalidCharacters",
        ),
        pytest.param(
            "Submitter...Two",
            "Job@#$%^?Two",
            "2023-09-25",
            os.path.join("2023-09", "2023-09-25-01-SubmitterTwo-JobTwo"),
            id="InvalidCharactersInNames",
        ),
        pytest.param(
            "\\..\\..\\..\\SubmitterThree",
            "./../../Job/Three",
            "2023-09-25",
            os.path.join("2023-09", "2023-09-25-01-SubmitterThree-JobThree"),
            id="PathsInNames",
        ),
    ],
)
def test_create_job_bundle_dir_sanitization(
    submitter_name: str,
    job_name: str,
    freeze_date: str,
    expected_output_path: str,
    fresh_deadline_config,
):
    # Use a temporary directory for the job history
    with tempfile.TemporaryDirectory() as tmpdir, freeze_time(freeze_date):
        config.set_setting("settings.job_history_dir", tmpdir)
        assert job_bundle.create_job_history_bundle_dir(submitter_name, job_name) == os.path.join(
            tmpdir, expected_output_path
        )
        assert os.path.isdir(os.path.join(tmpdir, expected_output_path))
