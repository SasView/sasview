#!/usr/bin/python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

from mako.template import Template

# Define Mako template for HTML output
html_template = Template(
    r"""
<html>
<head>
    <meta charset="UTF-8">
    <title>SasView Dependencies</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 1em; }
        h1 { font-size: 1.3em; }
        h2 { margin-top: 2em; font-size: 1.2em; }
        pre { background-color: #f4f4f4; padding: 0.8em; white-space: pre-wrap; }
        ul { line-height: 1.6; }
        a { text-decoration: none; color: #0645ad; }
    </style>
</head>
<body>
    <h1>SasView Dependencies</h1>
    SasView is built upon a foundation of free and open-source software packages.
    % if minimal:
        The following modules are part of this release of SasView.
    % else:
        The following modules are used as part of the build process and are bundled
        in the binary distributions that are released.
    % endif
    <ul>
    % for pkg in modules:
        <li><a href="#${pkg['Name']}">${pkg['Name']}</a></li>
    % endfor
    </ul>

    % for pkg in modules:
        <h2 id="${pkg['Name']}">${pkg['Name']}</h2>
        <p><strong>Author(s):</strong> ${pkg.get('Author', 'N/A')}</p>
        <p><strong>License:</strong> ${pkg.get('License', 'N/A')}</p>
        <pre>${pkg.get('LicenseText', 'No license text available.')}</pre>
    % endfor
</body>
</html>
"""
)


# minimal list of modules to include when distributing only in wheel form
minimal_modules = [
    "sasdata",
    "sasmodels",
    "sasview",
]


def get_modules():
    """Load pip-licenses JSON output"""
    result = subprocess.run(
        [
            "pip-licenses",
            "--format=json",
            "--with-system",
            "--with-authors",
            "--with-license-file",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    modules = json.loads(result.stdout)
    # Sort the data by package name (case-insensitive)
    modules.sort(key=lambda pkg: pkg["Name"].lower())
    return modules


def filter_modules(modules, included):
    """Filter the list of packages to only include the specified packages"""
    return [m for m in modules if m["Name"].lower() in included]


def format_html(filename, modules, minimal):
    """Create the HTML output"""
    # Render the template with license data
    html_output = html_template.render(modules=modules, minimal=minimal)

    # Save the HTML to a file
    Path(filename).write_text(html_output, encoding="utf-8")


def main(argv):
    parser = argparse.ArgumentParser(
        description="Extract license information for modules in the environment",
    )

    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Only include information about a minimal set of modules",
    )
    parser.add_argument(
        "filename",
        help="output filename",
        metavar="OUTPUT",
    )

    args = parser.parse_args(argv)

    minimal = args.minimal
    filename = args.filename

    modules = get_modules()

    if minimal:
        modules = filter_modules(modules, minimal_modules)

    format_html(filename, modules, minimal)

    return True


if __name__ == "__main__":
    sys.exit(not main(sys.argv[1:]))
