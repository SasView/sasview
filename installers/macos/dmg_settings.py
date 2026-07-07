import os

app_name = defines.get("app_name", "SasView6.app")  # noqa: F821
staging_dir = defines["staging_dir"]  # noqa: F821

format = "UDBZ"

files = [os.path.join(staging_dir, app_name)]
symlinks = {"Applications": "/Applications"}
hide_extensions = [app_name]

# Built-in drag-to-Applications background (no custom PNG assets).
background = "builtin-arrow"

window_rect = ((200, 120), (600, 400))
default_view = "icon-view"
include_icon_view_settings = True
icon_size = 128

# Positions matched to builtin-arrow for a 600x400 window.
icon_locations = {
    app_name: (180, 170),
    "Applications": (430, 170),
}
