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
        self.css = load_theme(self.theme)

    def update_theme_list(self):
        self._available_themes = find_available_themes()

    def get_theme_names(self) -> List[str]:
        return list(self._available_themes.keys())

    def change_theme(self, theme: str):
        self.theme = theme
        self.css = load_theme(self.theme)


style_sheet = StyleSheet()
