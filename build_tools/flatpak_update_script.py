#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "click>=8.4.2",
#     "packaging>=26.3",
#     "requirements-parser>=0.13.1",
# ]
# ///


import subprocess
from sys import stderr, exit
from pathlib import Path
from click import command, option
from click import Path as ClickPath
from os import environ, getcwd


def prefer_wheels_str(prefer_wheels_file: Path) -> str:
    with open(prefer_wheels_file) as f:
        file_contents = f.readlines()
    return ",".join(file_contents)


def generate_requirements(requirements_path: Path, output_path: Path, prefer_wheels: str):
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
    with open(new_path) as f:
        f.writelines(new_lines)
    return new_path


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
    requirements_file = getcwd() / Path("requirements-release-ubuntu-latest.txt")
    requirements_dev_file = getcwd() / Path("requirements-dev.txt")
    prefer_wheels_file = getcwd() / Path("prefer_wheels.txt")
    if not (requirements_file.exists() and requirements_dev_file.exists() and prefer_wheels_file.exists()):
        print("Your working directory needs to be the same as the requirements files.", file=stderr)
        exit(1)
    prefer_wheels = prefer_wheels_str(prefer_wheels_file)
    if not output_dir.is_dir():
        output_dir.mkdir()
    generate_requirements(requirements_file, output_dir / "python3-requirements.json", prefer_wheels)
    generate_requirements(requirements_dev_file, output_dir / "python3-requirements-dev.json", prefer_wheels)


if __name__ == "__main__":
    main()
