#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "click>=8.4.2",
#     "packaging>=26.3",
#     "requirements-parser>=0.13.1",
# ]
# ///


from typing import cast
import subprocess
import requirements
from sys import stderr, exit
from pathlib import Path
from click import command, option
from click import Path as ClickPath
from os import environ, getcwd


def packages_str(path: Path) -> str:
    with open(path) as f:
        file_contents = f.readlines()
    return ",".join(file_contents)


def generate_requirements(requirements_path: Path, output_path: Path, prefer_wheels: str, ignore_pkgs: str):
    env = environ.copy()
    env["FLATPAK_PIP_GENERATOR_ALLOW_RESTRICTED_MODULES"] = "1"
    subprocess.call(
        [
            "flatpak-pip-generator",
            "-r",
            requirements_path,
            "-o",
            output_path,
            "--prefer-wheels",
            prefer_wheels,
            "--ignore-pkg",
            ignore_pkgs,
            "--runtime",
            "org.kde.Sdk//6.11",  # FIXME: The version of KDE needs to match the PySide version.
        ],
        stderr=subprocess.STDOUT,
        env=env,
    )


def process_requirements_file(file_path: Path, output_directory: Path) -> Path:
    """This function is needed to remove references to other requirement files
    because the Flatpak builder tool needs to read each file in an isolated
    container. This function completely strips these references because SasView
    can be built without them. Later, its also possible the requirements can
    just be copied where these references appears."""
    with open(file_path) as f:
        lines = f.readlines()
    new_lines = [l for l in lines if "-r" not in l]
    new_path = output_directory / Path("processed_requirements") / file_path.name
    new_path.parent.mkdir(parents=True, exist_ok=True)
    with open(new_path, "w") as f:
        f.writelines(new_lines)
    return new_path


def get_qt_version(requirements_file: Path) -> str:
    with open(requirements_file, "r") as f:
        for req in requirements.parse(f):
            if cast(str, req.name).lower() == "pyside6":
                _, raw_version_str = req.specs[0]
                # Only get the major, and minor numbers; ignore the patch number.
                return ".".join(raw_version_str.split(".")[:2])
    raise ValueError("PySide6 is missing in the supplied requirements file.")


@command
@option("--output-dir", type=ClickPath(path_type=Path), default=Path.cwd() / "outputs")
def main(output_dir: Path):
    try:
        subprocess.call(
            ["flatpak-pip-generator", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print(
            "Error: you need to have the program 'flatpak-pip-generator' on your path. See the README for more information.",
            file=stderr,
        )
        exit(1)
    requirements_dev_file = process_requirements_file(Path("requirements-dev.txt"), output_dir)
    requirements_file = process_requirements_file(Path("requirements-release-ubuntu-latest.txt"), output_dir)
    prefer_wheels_file = Path("prefer_wheels.txt")
    ignore_pkgs_file = Path("ignore_packages.txt")
    if not (requirements_file.exists() and requirements_dev_file.exists() and prefer_wheels_file.exists()):
        print("Your working directory needs to be the same as the requirements files.", file=stderr)
        exit(1)
    prefer_wheels = packages_str(prefer_wheels_file)
    ignore_pkgs = packages_str(ignore_pkgs_file)
    if not output_dir.is_dir():
        output_dir.mkdir()
    generate_requirements(
        requirements_dev_file, output_dir / "python3-requirements-dev.json", prefer_wheels, ignore_pkgs
    )
    generate_requirements(requirements_file, output_dir / "python3-requirements.json", prefer_wheels, ignore_pkgs)


if __name__ == "__main__":
    main()
