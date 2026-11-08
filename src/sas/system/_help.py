import logging
import re
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


def _release_version(version_string: str) -> str:
    """Extract the release version (major.minor.micro) from a full version string.

    Strips dev/pre-release suffixes so the version matches deployed documentation URLs.
    """
    from packaging.version import parse

    version = parse(version_string)
    return f"{version.major}.{version.minor}.{version.micro}"


class _HelpSystem:
    """Extensible storage for help-system-related paths and configuration"""

    def __init__(self) -> None:
        self.path: Path | None
        # self.example_data: Path   # perhaps?

    def show_help(self, url: str | Path) -> None:
        """Open documentation in the system's default web browser.

        :param url: a documentation path within the documentation tree (e.g.
            ``/user/qtgui/Perspectives/Fitting/fitting_help.html#anchor``),
            or an absolute path on the filesystem (e.g. ``/home/user/.sasview``)

        The provided documentation path is resolved in the following order:
        1. check if path exists within the documentation tree
        2. check if the path exists on disk exactly as provided
        3. fall back to online docs at www.sasview.org
        """
        logger.info("Help URL: %s", url)

        # get a POSIX (forward-slash) version of the resource if a WindowsPath
        # was provided
        if isinstance(url, Path):
            url = url.as_posix()

        # Remove multiple / at the start of the path (would look like a
        # UNC path on Windows)
        url = re.sub("^/{2,}", "/", url)

        fragment = ""
        if "#" in url:
            url, fragment = url.rsplit("#", 1)

        try:
            local_path = self._local_url(url)
            if local_path:
                target = local_path.as_uri()
                if fragment:
                    target += "#" + fragment
                webbrowser.open(target)
                return

            # Fall back to online documentation
            webbrowser.open(self._online_url(url, fragment))
        except Exception as ex:
            logger.warning("Cannot display help: %s", ex)

    def _local_url(self, resource: str) -> Path | None:
        """turn a resource name into a file path for local resources

        returns None if resource cannot be found locally
        """
        if self.path:
            relative_path = Path(resource.lstrip("/"))
            doc_path = self.path / relative_path
            if doc_path.exists():
                logger.debug("Resolved help resource %s to doc_path %s", resource, doc_path)
                return doc_path

        full_path = Path(resource)
        if full_path.exists():
            logger.debug("Resolved help resource %s to absolute path %s", resource, full_path)
            return full_path

        logger.debug("Resolved help resource %s not resolved", resource)
        return None

    def _online_url(self, resource: str, fragment: str = "") -> str:
        """Construct the online documentation URL for the current version."""
        from sas.system.version import __version__

        # Strip the local doc root if a caller accidentally passed an
        # absolute path that already includes it.
        relative_path = Path(resource)
        if self.path and relative_path.is_absolute():
            try:
                relative_path = relative_path.relative_to(self.path)
            except ValueError:
                pass  # not under HELP_SYSTEM.path – use as-is

        remote_resource = relative_path.as_posix().lstrip("/")

        version = _release_version(__version__)
        base = f"https://www.sasview.org/docs/v{version}"
        url = f"{base}/{remote_resource}"
        if fragment:
            url += "#" + fragment
        return url


HELP_SYSTEM = _HelpSystem()
