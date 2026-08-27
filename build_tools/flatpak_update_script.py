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
from os import environ
from pathlib import Path
from platform import system
from string import Template
from sys import exit, stderr
from typing import cast

import requirements
from click import Path as ClickPath
from click import command, option


class ManifestTemplate(Template):
    """This class is required because Template by default uses $ as the
    delimiter but this symbol is already used in the manifest for a few things,
    including Flatpak macros. So this subclass uses @ instead.

    """

    delimiter = "@"


def packages_str(path: Path) -> str:
    """This loads the contents of the prefer_wheels, or ignore_packages file,
    and formats it so it can be passed into the CLI of the flatpak tool as a cli
    arg.

    """
    with open(path) as f:
        file_contents = f.readlines()
    return ",".join([content.strip() for content in file_contents])


def generate_requirements(
    requirements_path: Path, output_path: Path, prefer_wheels: str, ignore_pkgs: str, qt_version: str
):
    """Runs the Flatpak pip generator script on a given set of requirements."""
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
            f"org.kde.Sdk//{qt_version}",
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
    new_lines = [l for l in lines if "-r " not in l and "-e " not in l]
    new_path = output_directory / Path("processed_requirements") / file_path.name
    new_path.parent.mkdir(parents=True, exist_ok=True)
    with open(new_path, "w") as f:
        f.writelines(new_lines)
    return new_path


def get_qt_version(requirements_file: Path) -> tuple[str, str]:
    """Retrieves the version of QT we are using from the PySide dependency that
    is being used.

    """
    with open(requirements_file) as f:
        for req in requirements.parse(f):
            if cast(str, req.name).lower() == "pyside6":
                _, raw_version_str = req.specs[0]
                # Only get the major, and minor numbers; ignore the patch number.
                return ".".join(raw_version_str.split(".")[:2]), raw_version_str
    raise ValueError("PySide6 is missing in the supplied requirements file.")


def generate_main_manifest(
    input_manifest_file: Path, output_directory: Path, qt_version: str, qt_version_with_patch: str, sasview_version: str
):
    """Generates the org.sasview.sasview.yml manifest file from the template. It
    bumps the QT package, and runtime to use the correct QT version, and also
    bumps the SasView version with the one provided by the user."""
    with open(input_manifest_file) as f:
        template_manifest_contents = f.read()
    template = ManifestTemplate(template_manifest_contents)
    new_manifest_contents = template.substitute(
        qt_version=qt_version, qt_version_with_patch=qt_version_with_patch, sasview_version=sasview_version
    )
    with open(output_directory / input_manifest_file.name.removesuffix(".in"), "w") as f:
        f.write(new_manifest_contents)


def install_sdk(qt_version: str):
    subprocess.call(["flatpak", "--user", "-y", "install", f"org.kde.Sdk//{qt_version}"])


def check_platform() -> bool:
    if system() != "Linux":
        print(
            "ERROR: You appear to be running this script outside of Linux. "
            "This script needs to be run on linux because it needs to check "
            "the contents of the SDK to determine which wheels to pull in, "
            "and it can only do this on Linux. If you are not on Linux, "
            "please consult the documentation for advice."
        )
        return False
    return True


# TODO: Add strings for the help message.
@command
@option(
    "--output-dir",
    type=ClickPath(path_type=Path),
    default=Path.cwd() / "outputs",
    help="The directory where the generated files will be placed.",
)
@option(
    "--sasview-version",
    required=True,
    help="The version of SasView the Flatpak is being built for. This should be the tag (excluding the 'v') of SasView the Flatpak will build.",
)
def main(output_dir: Path, sasview_version: str):
    """This command will update the Flatpak manifest files which are in turn
    used to build the Flatpak. It will update all the Python depdendencies to
    match the pins which are specified in the requirements files, and update the
    version of QT."""
    if not check_platform():
        exit(1)
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
    flatpak_requirements_file = process_requirements_file(Path("flatpak_requirements.txt"), output_dir)
    prefer_wheels_file = Path("prefer_wheels.txt")
    ignore_pkgs_file = Path("ignore_packages.txt")
    input_manifest_file = Path("org.sasview.sasview.yml.in")
    if not (
        requirements_file.exists()
        and requirements_dev_file.exists()
        and prefer_wheels_file.exists()
        and flatpak_requirements_file.exists()
    ):
        print("Your working directory needs to be the same as the requirements files.", file=stderr)
        exit(1)
    qt_version, qt_version_with_patch = get_qt_version(requirements_file)
    install_sdk(qt_version)
    prefer_wheels = packages_str(prefer_wheels_file)
    ignore_pkgs = packages_str(ignore_pkgs_file)
    if not output_dir.is_dir():
        output_dir.mkdir()
    generate_requirements(
        flatpak_requirements_file,
        output_dir / "python3-requirements-source-build.json",
        prefer_wheels,
        ignore_pkgs,
        qt_version,
    )
    generate_requirements(
        requirements_dev_file, output_dir / "python3-requirements-dev.json", prefer_wheels, ignore_pkgs, qt_version
    )
    generate_requirements(
        requirements_file, output_dir / "python3-requirements.json", prefer_wheels, ignore_pkgs, qt_version
    )
    generate_main_manifest(input_manifest_file, output_dir, qt_version, qt_version_with_patch, sasview_version)


if __name__ == "__main__":
    main()
