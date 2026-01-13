"""Extract resources from a Python module

Python modules can have resources such as icons or source code within them.
The resources will often be sitting beside the Python files in the source
tree or when installed, with the exception of PEP 660 editable installs where
the resources can be sitting inside a tree in site-packages, while the source
code remains in the original source directory.

These utilities can transparently extract resources from the appropriate
location.

The approach is:

   1. Look in the distribution file manifest via importlib.metadata;
      these are the files that have been installed into site-packages and
      have been recorded in the dist-info/RECORD manifest. This code calls
      them "recorded" files.
   2. Look at the files that are part of the module tree as sitting on disk
      via importlib.resources; in the case of an installed module, this will
      cover the same files as #1, but for an editable install, it will only
      include the files that are in the source tree and not the files in
      site-packages. This code calls them "adjacent" files.

The approach described above prioritises files that are installed (hence
part of a wheel distribution, known to pip, and can be removed when
uninstalling).

This module is extensible for future work to
   - remove path calculation of the location of resources
   - provide filehandles to resources rather than copies of resources
   - deduplicate some resources across the codebase
"""
# TODO:
#   - CRUFT: python 3.13 introduced pathlib.Path.full_match for recursive
#     glob matching; until we're using that, we have some messier regular
#     expressions in the code below.

import contextlib
import enum
import functools
import importlib.metadata
import importlib.resources
import itertools
import logging
import re
import tempfile
from collections.abc import Generator
from pathlib import Path, PurePath

logger = logging.getLogger(__name__)


class _ResType(enum.Flag):
    FILE = enum.auto()
    DIR = enum.auto()


class ModuleResources:
    """Locate and extract resources in Python modules"""

    def __init__(self, module: str):
        """Create a resource extractor with a module name.

        Parameters:
            module: The importable name of the module to extract resources from.

        For SasView, the module name would be "sas", while, the distribution name (dist_name)
        that is calculated from it is "sasview".
        """
        self.module = module

    def extract_resource(self, src: str | PurePath, dest: Path | str) -> bool:
        """Extract a single resource from the module.

        Parameters:
            src: The source path for the file within the module (does not include the module name)
            dest: The destination path to which the resource will be copied (including filename).

        Returns: True if resource was extracted
        """
        dest = Path(dest)
        src = _clean_path(src)
        if dest.exists() and dest.is_dir():
            raise ValueError(f"Specified destination path must include the filename: {dest}")

        if self._extract_resource_recorded(src, dest):
            return True

        if self._extract_resource_adjacent(src, dest):
            return True

        raise FileNotFoundError(f"Resource {src} not found in module {self.module}")

    def extract_resource_tree(self, src: str | PurePath, dest: Path | str) -> bool:
        """Extract a tree of resources from the module.

        Parameters:
            src: The source path for the directory within the module
            (does not include the module name)
            dest: The destination path to which the resources will be copied recursively.
        """
        dest = Path(dest)
        src = _clean_path(src)
        if self._extract_resource_tree_recorded(src, dest):
            return True

        if self._extract_resource_tree_adjacent(src, dest):
            return True

        raise NotADirectoryError(f"Resource tree {src} not found in module {self.module}")

    @contextlib.contextmanager
    def resource(self, src: str | PurePath) -> Generator[Path, None, None]:
        """Provide a filesystem path to a file resource, in a temporary directory if needed

        If the resource is already available on the filesystem, then provide
        the path to it directly; if it is available as an extractable resource,
        then provide it in a temporary directory that will get cleaned up
        when the context manager is completed.

        If the resource can't be found by any means, then a FileNotFoundError
        is raised.
        """
        # step 1: look for the resource already on disk
        try:
            path = self.path_to_resource(src)
            yield path
            return
        except FileNotFoundError:
            pass

        # step 2: if not already on disk then it's time for a temp dir
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / Path(src).name
            self.extract_resource(src, tmp_path)
            yield tmp_path

    def path_to_resource(self, src: str | PurePath) -> Path:
        """Provide the filesystem path to a file resource

        If the resource is already available on the filesystem, then provide
        the path to it directly; if it is not available, then a FileNotFoundError
        is raised and the caller should extract into a filesystem location that
        they can clean up after use.
        """
        src = _clean_path(src)
        path = self._path_to_resource_recorded(src) or self._path_to_resource_adjacent(src)

        if path:
            return path

        raise FileNotFoundError(f"Resource {src} not found in module {self.module}")

    def path_to_resource_directory(self, src: str | PurePath) -> Path:
        """Provide the filesystem path to a file resource directory

        If the resource is already available on the filesystem, then provide
        the path to it directly; if it is not available, then a NotADirectoryError
        is raised and the caller should extract into a filesystem location that
        they can clean up after use.

        Note that completely empty directories might not be found by this method
        as they are not recorded in the dist-info/RECORD.
        """
        src = _clean_path(src).rstrip("/")
        path = self._path_to_resource_recorded(src + "/**")
        if path:
            # this will be a entry within the directory or possibly even a subdirectory
            # need to walk up to find the entry we really want
            match = f"/{self.module}/{src}"   # pathlib.Path directories don't end in /
            for part in itertools.chain([path], path.parents):
                if str(part).endswith(match):
                    return part
            # if the upwards search falls through to here, then something went wrong
            # with the original filtering of the RECORD data, but allow it to try
            # importlib.resources before raising the exception

        path = self._path_to_resource_adjacent(src, accept=_ResType.DIR)
        if path:
            return path

        raise NotADirectoryError(f"Resource directory {src} not found in module {self.module}")

    # ### Methods for "Recorded" files

    @property
    def _dist_name(self) -> str | None:
        return _dist_name(self.module)

    @property
    def _distribution(self) -> importlib.metadata.Distribution:
        return _distribution(self._dist_name)

    @property
    def _is_zip_distribution(self) -> bool:
        return _is_zip_distribution(self._dist_name)

    @property
    def _incompatible_with_recorded(self) -> bool:
        return not self._dist_name or self._is_zip_distribution

    def _distribution_files(self) -> list[importlib.metadata.PackagePath] | None:
        return _distribution_files(self._dist_name)

    def _path_to_resource_recorded(self, src: str) -> Path | None:
        """calculate the filesystem path to the recorded resource if it exists"""
        if self._incompatible_with_recorded:
            return None

        pth = self._locate_resource_recorded(src)
        return Path(pth.locate()) if pth else None

    def _locate_resource_recorded(self, src: str) -> importlib.metadata.PackagePath | None:
        """obtain the PackagePath record for the resource if it exists"""
        resources = self._distribution_files()
        # CRUFT: the regex can be replaced with the glob in Python 3.13
        # search = f"{self.module}/{src}"
        search_re = re.compile(rf"^{self.module}/{src.replace('**', '.*')}/?")
        for resource in resources or ():
            if search_re.fullmatch(str(resource)):
            # if resource.full_match(search):
                return resource
        return None

    def _extract_resource_recorded(self, src: str, dest: Path) -> bool:
        """extract the recorded resource (if it exists) to the destination filename

        dest must be a file path including the target filename
        """
        if self._incompatible_with_recorded:
            return False

        resource = self._locate_resource_recorded(src)
        if resource:
            self._copy_resource_recorded(resource, dest)
            return True
        return False

    def _extract_resource_tree_recorded(self, src: str, dest: Path) -> bool:
        """extract the recorded resource tree (if it exists) to the destination directory

        dest must be a directory
        """
        if self._incompatible_with_recorded:
            return False

        # normalise the representation
        dpth = Path(dest)
        dpth.mkdir(exist_ok=True, parents=True)

        resources = self._distribution_files()
        base = f"{self.module}/{src}"
        # CRUFT: the regex can be replaced with the glob in Python 3.13
        # search = f"{base}/**"
        search_re = re.compile(rf"^{base}/.*/?")
        found = False
        for resource in resources or ():
            if "__pycache__" in str(resource):
                continue
            if search_re.fullmatch(str(resource)):
            # if resource.full_match(search):
                dest_name = dpth / resource.relative_to(base)
                self._copy_resource_recorded(resource, dest_name)
                found = True
        return found

    def _copy_resource_recorded(self, resource: importlib.metadata.PackagePath, dest: Path) -> None:
        """copy the resource to the filesystem

        dest needs to be the file path including the filename
        """
        src = resource.locate()

        if not dest.parent.exists():
            dest.parent.mkdir(exist_ok=True, parents=True)

        if not dest.exists():
            logger.debug("Found recorded: %s", resource)
            with open(src, "rb") as sh, open(dest, "wb") as dh:
                dh.write(sh.read())

    # ### Methods for "Adjacent" files

    def _path_to_resource_adjacent(self, src: str, accept: _ResType = _ResType.FILE) -> Path | None:
        """calculate the filesystem path to the recorded resource if it exists"""
        resource = importlib.resources.files(self.module) / src

        # importlib.resources will always return something... but it might
        # not exist, so the is_file() check is needed.
        # If the resource is on disk, then importlib.resources.readers.FileReader
        # will return a pathlib.Path object directly to the resource which is
        # all that is needed here

        result = None

        if isinstance(resource, Path):
            if (resource.is_file() and _ResType.FILE in accept) or (resource.is_dir() and _ResType.DIR in accept):
                result = resource

        if result:
            logger.debug("Found adjacent: %s", resource)

        return result

    def _extract_resource_adjacent(self, src: str, dest: Path) -> bool:
        """extract the adjacent resource (if it exists) to the destination filename

        dest must be a file path including the target filename

        This method should should transparently access resources in zip bundles
        """
        resource_path = importlib.resources.files(self.module) / src
        if not resource_path.is_file():
            return False

        if not dest.parent.exists():
            dest.parent.mkdir(exist_ok=True, parents=True)

        with importlib.resources.as_file(resource_path) as file_path:
            logger.debug("Found adjacent: %s", resource_path)
            dest.write_bytes(file_path.read_bytes())
        return True

    def _extract_resource_tree_adjacent(self, src: str | Path, dest: Path) -> bool:
        """extract the adjacent resource tree (if it exists) to the destination directory

        dest must be a directory
        """
        # normalise the representation
        spth = Path(src)
        src = str(spth)

        dpth = Path(dest)
        dpth.mkdir(exist_ok=True, parents=True)

        found = False
        try:
            for resource in importlib.resources.files(self.module).joinpath(src).iterdir():
                f_name = dpth / resource.name
                s_name = spth / resource.name
                if "__pycache__" in resource.name:
                    continue

                if resource.is_dir():
                    # recurse into the directory
                    found |= self._extract_resource_tree_adjacent(s_name, f_name)
                elif resource.is_file():
                    if not f_name.exists():
                        logger.debug("Found adjacent: %s", s_name)
                        with open(f_name, "wb") as dh:
                            dh.write(resource.read_bytes())
                    found = True
                else:
                    logger.warning("Skipping %s (unknown type)", str(s_name))
        except FileNotFoundError:
            # specified path does not exist or is not a directory
            return False

        return found


def _clean_path(src: str | PurePath) -> str:
    if isinstance(src, PurePath):
        return src.as_posix()
    else:
        return src


@functools.cache
def _dist_name(module: str) -> str | None:
    try:
        return importlib.metadata.packages_distributions()[module][0]
    except KeyError:
        # In strange environments like pyinstaller, the module might not be found
        return None


@functools.cache
def _distribution(dist_name: str) -> importlib.metadata.Distribution:
    return importlib.metadata.distribution(dist_name)


@functools.cache
def _distribution_files(dist_name: str) -> list[importlib.metadata.PackagePath] | None:
    return _distribution(dist_name).files


@functools.cache
def _is_zip_distribution(dist_name: str) -> bool:
    """identify whether the module is inside a zip bundle or whl"""
    dist = _distribution(dist_name)
    dummy_file = dist.locate_file("")
    return dummy_file.__class__.__module__.startswith("zipfile")


# ### Command line interface for extracting module data


def main(argv: list[str]) -> bool:
    """Extract a resource from a Python module.

    Extracts resources such as config files, icons, data files that are part
    of a Python module.

    The Python module is specified via its importable name (not the
    distribution name).

    Resources shipped in the following ways are supported:

    - resources that are installed on-disk in a normal pip installed module;
      these are in site-packages and recorded within the dist-info.

    - resources that are still adjacent to the code and not in site-packages,
      such as in an editable install.

    - resources that are inside a wheel file (whl) that has been added to
      PYTHONPATH

    - resources that are inside a module shipped in zip-bundle form
    """
    import argparse
    import textwrap

    description, _, epilog = main.__doc__.partition("\n")
    parser = argparse.ArgumentParser(
        description=description,
        epilog=textwrap.dedent(epilog).strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively extract the resources",
    )
    parser.add_argument(
        "module",
        help="Python module name to extract from; this is the importable name "
        "not the name of the distribution",
    )
    parser.add_argument(
        "src",
        help="Name of the resource inside the module, expressed as a path-like structure with '/' "
        "as the separator (not '.')",
    )
    parser.add_argument(
        "dest",
        help="Destination path on the local filesystem to extract the resource to; the destination "
        "must include the filename for an individual resource, "
        "and must be a directory when extracting recursively",
    )

    args = parser.parse_args(argv[1:])

    resources = ModuleResources(args.module)

    if args.recursive:
        success = resources.extract_resource_tree(args.src, args.dest)
    else:
        success = resources.extract_resource(args.src, args.dest)

    return not success


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
