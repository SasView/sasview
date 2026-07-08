import os

_settings_dir = defines["settings_dir"]  # noqa: F821

app_name = defines.get("app_name", "SasView6.app")  # noqa: F821
staging_dir = defines["staging_dir"]  # noqa: F821

format = "UDBZ"

files = [os.path.join(staging_dir, app_name)]
symlinks = {"Applications": "/Applications"}
hide_extensions = [app_name]

background = os.path.join(_settings_dir, "dmg_background.png")

window_rect = ((200, 120), (640, 280))
default_view = "icon-view"
include_icon_view_settings = True
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
icon_size = 128

icon_locations = {
    app_name: (140, 120),
    "Applications": (500, 120),
}
