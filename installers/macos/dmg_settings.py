import os

app_name = defines.get("app_name", "SasView6.app")  # noqa: F821
staging_dir = defines["staging_dir"]  # noqa: F821

format = "UDBZ"

files = [os.path.join(staging_dir, app_name)]
symlinks = {"Applications": "/Applications"}
hide_extensions = [app_name]

background = defines["background"]  # noqa: F821
window_rect = ((200, 120), (600, 400))
default_view = "icon-view"
include_icon_view_settings = True
icon_size = 128
icon_locations = {
    app_name: (
        int(defines.get("app_icon_x", 175)),  # noqa: F821
        int(defines.get("app_icon_y", 180)),  # noqa: F821
    ),
    "Applications": (
        int(defines.get("applications_icon_x", 425)),  # noqa: F821
        int(defines.get("applications_icon_y", 180)),  # noqa: F821
    ),
}
