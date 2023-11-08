from typing import List

from sas.system import config
from sas.system.themes import load_theme, find_available_themes, format_font_size


class StyleSheet:
    """
    Class used to manage all available themes.

    Built-in themes are available in sas.system.themes. User themes should live in ~/.sasview/themes.

    *CSS Order of operations:*
    Each operation overrides any previous operation to allow user themes to take precedence over any built-in thematic
    elements.
        1. The default font size and fonts are set.
        2. The base style sheet is set -> typically either classic.css for user themes or themes.STYLE_BASE for built-in
        3. Color palettes are applied (Dark or Light), if applicable.
        4. User theme elements are applied.
    """

    def __init__(self):
        self._available_themes = find_available_themes()
        self.theme = config.THEME
        self._font_size = config.FONT_SIZE
        self._css = ""
        self._create_full_theme()

    @property
    def css(self) -> str:
        """A property that exposes the css string to the public."""
        self.theme = config.THEME
        self.font_size = config.FONT_SIZE
        self._create_full_theme()
        return self._css

    @css.setter
    def css(self, theme: str):
        """A way to set the theme from outside the class. This attempts to load the theme and will throw an
        exception for undefined themes."""
        self.theme = theme
        self._create_full_theme()

    @property
    def font_size(self) -> float:
        """A property that exposes the font size to the public."""
        self._font_size = config.FONT_SIZE
        return self._font_size

    @font_size.setter
    def font_size(self, font_size: float):
        """Set the font size and create the theme."""
        self._font_size = font_size

    def update_theme_list(self):
        """A helper method to find the latest list of themes.
        Potential future use includes monitoring user theme changes."""
        self._available_themes = find_available_themes()

    def get_theme_names(self) -> List[str]:
        """Return a list of theme names for use by an external system."""
        return list(self._available_themes.keys())

    def _create_full_theme(self):
        """Private method that combines settings to allow fonts and color palettes to be set separately."""
        css = load_theme(self.theme)
        font_str = format_font_size(self.font_size)
        self._css = f"{font_str}{css}"


style_sheet = StyleSheet()
