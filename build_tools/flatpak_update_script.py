#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "click>=8.4.2",
#     "requirements-parser>=0.13.1",
# ]
# ///


import subprocess
from sys import stderr, exit
from pathlib import Path
from click import command, option


@command
@option("--output-dir", default=Path.cwd() / "outputs")
def main(output_dir: Path):
    try:
        subprocess.call(["flatpak-pip-generator", "--help"])
    except FileNotFoundError:
        print(
            "Error: you need to have the program 'flatpak-pip-generator' on your path. See the README for more information.",
            file=stderr,
        )
        exit(1)
    requirements_file = Path("./requirements-release-ubuntu-latest.txt")
    requirements_dev_file = Path("./requirements-dev.txt")
    prefer_wheels_file = Path("./prefer_wheels.txt")
    if not (requirements_file.exists() and requirements_dev_file.exists() and prefer_wheels_file.exists()):
        print("Your working directory needs to be the same as the requirements files.", file=stderr)
        exit(1)
