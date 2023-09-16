"""The base themes shipped with SasView."""
import os
import logging
from typing import Dict
from pathlib import Path

from sas.system import user

logger = logging.getLogger()


def load_theme(theme: str = None) -> str:
    """Using a theme name, load the associated CSS file.
    :param theme: The key value in ALL_THEMES
    :return: The loaded CSS
    """
    if not theme or theme not in ALL_THEMES:
        logger.warning(f"Invalid theme name provided: {theme}")
        theme = 'Default'
    path = get_user_theme_path(theme) if 'User:' in theme else Path(os.path.join('.', OPTIONS.get(theme)))
    with open(path) as fd:
        css = fd.read()
    return css


def get_user_theme_path(theme: str) -> Path:
    """Helper method to find the user file in the user directory"""
    return Path(os.path.join(user.get_user_dir(), 'themes', theme.replace('User:', '')))


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


OPTIONS = {'Default': Path('default.css')}
ALL_THEMES = find_available_themes()
