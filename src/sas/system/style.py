from typing import List

from sas.system import config
from sas.system.themes import load_theme, find_available_themes


class StyleSheet:
    """
    Class used to manage all available themes.

    Built-in themes are available in sas.system.themes. User themes should live in ~/.sasview/themes.
    """

    def __init__(self):
        self._available_themes = find_available_themes()
        self.theme = config.THEME
        self._css = load_theme(self.theme)

    @property
    def css(self) -> str:
        """A property that exposes the css string to the public."""
        self.theme = config.THEME
        self._css = load_theme(self.theme)
        return self._css

    @css.setter
    def css(self, theme: str):
        """A way to set the theme from outside the class. This attempts to load the theme and will throw an
        exception for undefined themes."""
        self.theme = theme
        self._css = load_theme(theme)

    def update_theme_list(self):
        """A helper method to find the latest list of themes.
        Potential future use includes monitoring user theme changes."""
        self._available_themes = find_available_themes()

    def get_theme_names(self) -> List[str]:
        """Return a list of theme names for use by an external system."""
        return list(self._available_themes.keys())


style_sheet = StyleSheet()
