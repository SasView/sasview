"""The base themes shipped with SasView."""
import os
import logging
from typing import Dict
from pathlib import Path

from sas.system import user

logger = logging.getLogger()

# The base dictionary mapping theme names to their location on disk.
OPTIONS = {
    'Default': Path(os.path.join(os.path.dirname(__file__), 'default.css')),
    'Dark': Path(os.path.join(os.path.dirname(__file__), 'dark.css')),
    'Classic': Path(os.path.join(os.path.dirname(__file__), 'classic.css')),
    'Large Font': Path(os.path.join(os.path.dirname(__file__), 'largefont.css')),
}


def load_theme(theme: str = None) -> str:
    """Using a theme name, load the associated CSS file. User themes will be based off the Classic theme.
    :param theme: The key value in OPTIONS
    :return: The CSS string loaded from file
    """
    themes = find_available_themes()
    css = ""
    if not theme or theme not in find_available_themes():
        logger.warning(f"Invalid theme name provided: {theme}")
        theme = 'Default'
    # User themes should use the classic theme as a basis and build on it from there
    if theme.startswith('User:'):
        with open(themes.get('Classic').absolute()) as fd:
            css += fd.read()
    with open(themes.get(theme).absolute()) as fd:
        css += fd.read()
    return css


def find_available_themes() -> Dict:
    """Find all available themes and return the list of options.

    The default themes should be shipped in the same directory as this file.
    User created themes should be kept in ~/.sasview/themes.
    """
    themes = OPTIONS.copy()
    user_path = os.path.join(user.get_user_dir(), 'themes')
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    for file in os.listdir(user_path):
        name = f'User:{file}'
        themes[name] = Path(os.path.join(user_path, file))
    return themes
