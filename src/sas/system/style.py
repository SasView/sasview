import os
import pkg_resources
import sys

from sas.system import user

DEFAULT_STYLE_SHEET_NAME = 'sasview.css'


class StyleSheet:
    """
    The directory where the per-user style sheet is stored.

    Returns ~/.sasview/sasview.css, creating it if it does not already exist.
    """
    def __init__(self):
        self.style_sheet = None
        self._find_style_sheet()
        self.save()

    def style_sheet_filename(self):
        """Filename for saving config items"""
        user_dir = user.get_user_dir()
        self.style_sheet = os.path.join(user_dir, DEFAULT_STYLE_SHEET_NAME)

    def save(self):
        self._find_style_sheet()
        sheet = self()
        self.style_sheet_filename()
        with open(self.style_sheet, 'w') as file:
            file.write(sheet)

    def _find_style_sheet(self, filename=DEFAULT_STYLE_SHEET_NAME):
        '''
        The style sheet is in:
        User directory ~/.sasview/
        Debug .
        Packaging: sas/sasview/
        Packaging / production does not work well with absolute paths
        thus the multiple paths below
        '''
        self.style_sheet_filename()
        places_to_look_for_conf_file = [
            self.style_sheet,
            os.path.join(os.path.abspath(os.path.dirname(__file__)), filename),
            filename,
            os.path.join("sas", "system", filename),
            os.path.join(os.getcwd(), "sas", "system", filename),
            os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), filename)  #For OSX app
        ]

        # To avoid the exception in OSx
        # NotImplementedError: resource_filename() only supported for .egg, not .zip
        try:
            places_to_look_for_conf_file.append(
                pkg_resources.resource_filename(__name__, filename))
        except NotImplementedError:
            pass

        for filepath in places_to_look_for_conf_file:
            if os.path.exists(filepath):
                self.style_sheet = filepath
                return
        print(f"'{filename}' not found.", file=sys.stderr)
        self.style_sheet = None

    def __call__(self, *args, **kwargs):
        with open(self.style_sheet) as f:
            style = f.read()
        return style


style_sheet = StyleSheet()
