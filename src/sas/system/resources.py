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

import functools
import importlib.metadata
import importlib.resources
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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

    def extract_resource(self, src: str, dest: Path | str) -> bool:
        """Extract a single resource from the module.

        Parameters:
            src: The source path for the file within the module (does not include the module name)
            dest: The destination path to which the resource will be copied (including filename).

        Returns: True if resource was extracted
        """
        dest = Path(dest)
        if dest.exists() and dest.is_dir():
            raise ValueError(f"Specified destination path must include the filename: {dest}")

        if self._extract_resource_recorded(src, dest):
            return True

        if self._extract_resource_adjacent(src, dest):
            return True

        raise FileNotFoundError(f"Resource {src} not found in module {self.module}")

    def extract_resource_tree(self, src: str, dest: Path | str) -> bool:
        """Extract a tree of resources from the module.

        Parameters:
            src: The source path for the directory within the module
            (does not include the module name)
            dest: The destination path to which the resources will be copied recursively.
        """
        dest = Path(dest)
        if self._extract_resource_tree_recorded(src, dest):
            return True

        if self._extract_resource_tree_adjacent(src, dest):
            return True

        raise NotADirectoryError(f"Resource tree {src} not found in module {self.module}")

    # ### Methods for "Recorded" files

    @property
    def _dist_name(self) -> str:
        return _dist_name(self.module)

    @property
    def _distribution(self) -> importlib.metadata.Distribution:
        return _distribution(self._dist_name)

    def _distribution_files(self) -> list[importlib.metadata.PackagePath] | None:
        return _distribution_files(self.module)

    def _extract_resource_recorded(self, src: str, dest: Path) -> bool:
        resources = self._distribution_files()
        search = f"{self.module}/{src}"
        for resource in resources or ():
            if resource.full_match(search):
                self._copy_resource_recorded(resource, dest)
                return True

        return False

    def _extract_resource_tree_recorded(self, src: str, dest: Path) -> bool:
        # normalise the representation
        spth = Path(src)
        src = str(spth)
        dpth = Path(dest)
        dpth.mkdir(exist_ok=True, parents=True)

        resources = self._distribution_files()
        base = f"{self.module}/{src}"
        search = f"{base}/**"
        found = False
        for resource in resources or ():
            if "__pycache__" in str(resource):
                continue
            if resource.full_match(search):
                dest_name = dpth / resource.relative_to(base)
                self._copy_resource_recorded(resource, dest_name)
                found = True
        return found

    def _copy_resource_recorded(self, resource: importlib.metadata.PackagePath, dest: Path) -> None:
        """copy the resource to the filesystem

        dest needs to be the full path and filename
        """
        src = resource.locate()

        if not dest.parent.exists():
            dest.parent.mkdir(exist_ok=True, parents=True)

        if not dest.exists():
            logger.debug("Found recorded: %s", resource)
            with open(src, "rb") as sh, open(dest, "wb") as dh:
                dh.write(sh.read())

    # ### Methods for "Adjacent" files

    def _extract_resource_adjacent(self, src: str, dest: Path) -> bool:
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
        # normalise paths
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
                        # logger.debug("Copied: %s", s_name)
                        with open(f_name, "wb") as dh:
                            dh.write(resource.read_bytes())
                    found = True
                else:
                    logger.warning("Skipping %s (unknown type)", str(s_name))
        except FileNotFoundError:
            # specified path does not exist or is not a directory
            return False

        return found


@functools.cache
def _dist_name(module: str) -> str:
    return importlib.metadata.packages_distributions()[module][0]


@functools.cache
def _distribution(module: str) -> importlib.metadata.Distribution:
    return importlib.metadata.distribution(_dist_name(module))


@functools.cache
def _distribution_files(module: str) -> list[importlib.metadata.PackagePath] | None:
    return _distribution(module).files


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

    The following should also work but are untested:

    - resources that are inside a wheel file (whl) that has been added to
      PYTHONPATH

    - resources that are inside a module shipped in zip form
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
