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


def prefer_wheels_str(prefer_wheels_file: Path) -> str:
    with open(prefer_wheels_file) as f:
        file_contents = f.readlines()
    return ",".join(file_contents)


def generate_requirements(requirements_path: Path, output_path: Path, prefer_wheels: str):
    subprocess.call(
        [
            "flatpak-pip-generator",
            "-r",
            requirements_path,
            "-o",
            output_path,
            "--prefer-wheels",
            prefer_wheels,
            "--runtime",
            "org.kde.Sdk//6.11",
        ]
    )


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
    prefer_wheels = prefer_wheels_str(prefer_wheels_file)
    if not output_dir.is_dir():
        output_dir.mkdir()
    generate_requirements(requirements_file, output_dir / "python3-requirements.json", prefer_wheels)
    generate_requirements(requirements_dev_file, output_dir / "python3-requirements-dev.json", prefer_wheels)
