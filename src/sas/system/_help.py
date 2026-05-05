import logging
import webbrowser
from pathlib import Path

from packaging.version import parse

logger = logging.getLogger(__name__)


def _release_version(version_string: str) -> str:
    """Extract the release version (major.minor.micro) from a full version string.

    Strips dev/pre-release suffixes so the version matches deployed documentation URLs.
    """
    version = parse(version_string)
    return f"{version.major}.{version.minor}.{version.micro}"


def _online_doc_base(version_string: str) -> str:
    """Return the best online documentation base URL for a version string.

    Released documentation is archived under ``docs/old_docs/X.Y.Z``.
    Development and pre-release builds should point at the current docs root.
    """
    version = parse(version_string)
    if version.is_devrelease or version.is_prerelease:
        return "https://www.sasview.org/docs"

    return f"https://www.sasview.org/docs/old_docs/{_release_version(version_string)}"


class _HelpSystem:
    """Extensible storage for help-system-related paths and configuration"""

    def __init__(self) -> None:
        self.path: Path | None
        # self.example_data: Path   # perhaps?

    def show_help(self, url: str | Path) -> None:
        """Open documentation in the system's default web browser.

        Takes a relative documentation path (e.g.
        ``user/qtgui/Perspectives/Fitting/fitting_help.html#anchor``),
        resolves it against the local doc tree when available, and falls
        back to the online docs at www.sasview.org otherwise.
        """
        if isinstance(url, Path):
            url = url.as_posix()

        # Separate any fragment (#anchor) from the path so Path operations
        # don't treat it as part of the filename.
        fragment = ""
        if "#" in url:
            url, fragment = url.rsplit("#", 1)

        relative_path = Path(url)

        # Preserve absolute paths long enough to detect and strip the local
        # documentation root on POSIX platforms before normalizing relative
        # help paths that may be passed with leading slashes.
        if not relative_path.is_absolute():
            relative_path = Path(url.lstrip("/"))

        # Strip the local doc root if a caller accidentally passed an
        # absolute path that already includes it.
        if self.path and relative_path.is_absolute():
            try:
                relative_path = relative_path.relative_to(self.path)
            except ValueError:
                pass  # not under HELP_SYSTEM.path – use as-is

        try:
            if self.path:
                local_path = self.path / relative_path
                if local_path.exists():
                    target = local_path.as_uri()
                    if fragment:
                        target += "#" + fragment
                    webbrowser.open(target)
                    return

            # Fall back to online documentation
            webbrowser.open(self._online_url(relative_path, fragment))
        except Exception as ex:
            logger.warning("Cannot display help: %s", ex)

    def _online_url(self, relative_path: Path, fragment: str = "") -> str:
        """Construct the online documentation URL for the current version."""
        from sas.system.version import __version__

        base = _online_doc_base(__version__)
        url = f"{base}/{relative_path.as_posix()}"
        if fragment:
            url += "#" + fragment
        return url


HELP_SYSTEM = _HelpSystem()
