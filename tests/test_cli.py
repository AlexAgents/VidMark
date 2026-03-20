# VidMark
# Copyright (C) 2026 qexela
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
CLI test runner for local development.

Note: In CI you typically run `pytest -q` directly.
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_MODULES = {
    "1": ("Attacks", "tests.test_attacks"),
    "2": ("ECC", "tests.test_ecc"),
    "3": ("Embedder", "tests.test_embedder"),
    "4": ("Embedder_more", "tests.test_embedder_more"),
    "5": ("Extractor", "tests.test_extractor"),
    "6": ("Metrics", "tests.test_metrics"),
    "7": ("Payload", "tests.test_payload"),
    "8": ("Scrambler", "tests.test_scrambler"),
    "9": ("Video_utils_ffmpeg_cmd", "tests.test_video_utils_ffmpeg_cmd"),
    "10": ("Keyfile", "tests.test_keyfile.py"),
    "a": ("ALL tests", None),
}


def run_test(module_name):
    """Run a single test module using pytest."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if module_name is None:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=root
        )
    else:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "--tb=short",
             "-k", module_name.replace("tests.", "")],
            cwd=root
        )
    return result.returncode


def main():
    while True:
        print("\n" + "=" * 50)
        print(" VidMark - Test Runner")
        print("=" * 50)
        for key, (name, _) in TEST_MODULES.items():
            print(f" [{key}] {name}")
        print(f" [q] Quit")
        print("-" * 50)

        choice = input("Select test to run: ").strip().lower()
        if choice == "q":
            print("Exiting.")
            break

        if choice in TEST_MODULES:
            name, module = TEST_MODULES[choice]
            print(f"\n>>> Running: {name}")
            print("-" * 40)
            rc = run_test(module)
            if rc == 0:
                print(f"\n {name}: PASSED")
            else:
                print(f"\n {name}: FAILED (exit code {rc})")
        else:
            print(f"Invalid choice: '{choice}'. Try again.")


if __name__ == "__main__":
    main()