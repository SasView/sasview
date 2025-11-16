#!/usr/bin/env python3
"""
Build documentation for sasmodels, sasdata, and sasview

Usage:
    python build_docs.py [options]

Options:
    --clean          Clean build directories before building
    --sasmodels-only Build only sasmodels documentation
    --sasdata-only   Build only sasdata documentation
    --sasview-only   Build only sasview documentation (requires sasmodels/sasdata docs)
    --format FORMAT  Build format: html (default), pdf, epub, singlehtml
    --open           Open the built documentation in a browser (HTML only)
    --help           Show this help message
"""

import argparse
import importlib.metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_step(message):
    print(f"{Colors.BLUE}==>{Colors.NC} {message}")


def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_error(message):
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def is_editable_install(package_name):
    """Check if a package is installed in editable mode"""
    try:
        dist = importlib.metadata.distribution(package_name)
        # Check if it's an editable install
        try:
            return dist.origin.dir_info.editable
        except AttributeError:
            # Try alternative method
            if hasattr(dist, 'files'):
                # Editable installs typically have a .pth file or direct link
                for file in dist.files or []:
                    if file.name.endswith('.pth'):
                        return True
            return False
    except importlib.metadata.PackageNotFoundError:
        return False


def find_source_directory(script_dir, package_name):
    """Find source directory for a package in development mode
    
    Looks for sibling directories (../sasmodels, ../sasdata) as per
    the development environment setup in INSTALL.md
    """
    # Common locations for development setup
    possible_locations = [
        script_dir.parent / package_name,  # ../sasmodels, ../sasdata
        script_dir / package_name,        # ./sasmodels, ./sasdata
        Path.home() / package_name,       # ~/sasmodels, ~/sasdata
    ]
    
    for location in possible_locations:
        if location.exists() and location.is_dir():
            # Check if it looks like the package source (has pyproject.toml or setup.py)
            if (location / "pyproject.toml").exists() or (location / "setup.py").exists():
                return location
    
    return None


def check_prerequisites():
    """Check if required tools are available"""
    print_step("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 12):
        print_error(f"Python 3.12+ required, found {sys.version}")
        return False
    
    # Check sphinx-build
    try:
        subprocess.run(["sphinx-build", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("sphinx-build not found. Please install Sphinx:")
        print("  pip install -r build_tools/requirements-dev.txt")
        return False
    
    # Check if sasmodels and sasdata are installed
    sasmodels_installed = False
    sasdata_installed = False
    
    try:
        __import__("sasmodels")
        sasmodels_installed = True
        if is_editable_install("sasmodels"):
            print("  sasmodels: installed in editable mode (development)")
        else:
            print("  sasmodels: installed (regular)")
    except ImportError:
        print_warning("sasmodels not found. Documentation extraction may fail.")
    
    try:
        __import__("sasdata")
        sasdata_installed = True
        if is_editable_install("sasdata"):
            print("  sasdata: installed in editable mode (development)")
        else:
            print("  sasdata: installed (regular)")
    except ImportError:
        print_warning("sasdata not found. Documentation extraction may fail.")
    
    print_success("Prerequisites checked")
    return True


def clean_build(clean, build_dir, sphinx_docs):
    """Clean build directories if requested"""
    if not clean:
        return
    
    print_step("Cleaning build directories...")
    
    dirs_to_clean = [
        build_dir,
        sphinx_docs / "tmp",
        sphinx_docs / "source-temp",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    print_success("Build directories cleaned")


def build_sasmodels_docs(script_dir, sasview_src, sasmodels_docs):
    """Extract sasmodels documentation
    
    In development mode, tries to use source directory if available.
    Otherwise extracts from installed package.
    """
    print_step("Building sasmodels documentation...")
    
    sasmodels_docs.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if sasmodels is in editable mode and find source directory
    source_dir = None
    if is_editable_install("sasmodels"):
        source_dir = find_source_directory(script_dir, "sasmodels")
        if source_dir:
            print(f"  Found sasmodels source directory: {source_dir}")
            print("  Using source directory for documentation (development mode)")
    
    resources_script = sasview_src / "sas" / "system" / "resources.py"
    
    # Try extracting from installed package (works for both editable and regular installs)
    try:
        result = subprocess.run(
            [sys.executable, str(resources_script), 
             "-r", "sasmodels", "docs-source", str(sasmodels_docs)],
            capture_output=True,
            text=True,
            check=True
        )
        print_success("sasmodels documentation extracted")
        return True
    except subprocess.CalledProcessError as e:
        print_error("Failed to extract sasmodels documentation")
        if source_dir:
            print_warning(f"Source directory found at {source_dir} but extraction failed")
            print_warning("Make sure sasmodels is properly installed: pip install -e ../sasmodels")
        else:
            print_warning("Make sure sasmodels is installed:")
            print_warning("  For development: pip install -e ../sasmodels")
            print_warning("  For regular use: pip install sasmodels")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print_error(f"resources.py not found at {resources_script}")
        return False


def build_sasdata_docs(script_dir, sasview_src, sasdata_docs):
    """Extract sasdata documentation
    
    In development mode, tries to use source directory if available.
    Otherwise extracts from installed package.
    """
    print_step("Building sasdata documentation...")
    
    sasdata_docs.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if sasdata is in editable mode and find source directory
    source_dir = None
    if is_editable_install("sasdata"):
        source_dir = find_source_directory(script_dir, "sasdata")
        if source_dir:
            print(f"  Found sasdata source directory: {source_dir}")
            print("  Using source directory for documentation (development mode)")
    
    resources_script = sasview_src / "sas" / "system" / "resources.py"
    
    # Extract docs
    try:
        result = subprocess.run(
            [sys.executable, str(resources_script),
             "-r", "sasdata", "docs-source", str(sasdata_docs)],
            capture_output=True,
            text=True,
            check=True
        )
        print_success("sasdata documentation extracted")
    except subprocess.CalledProcessError as e:
        print_error("Failed to extract sasdata documentation")
        if source_dir:
            print_warning(f"Source directory found at {source_dir} but extraction failed")
            print_warning("Make sure sasdata is properly installed: pip install -e ../sasdata")
        else:
            print_warning("Make sure sasdata is installed:")
            print_warning("  For development: pip install -e ../sasdata")
            print_warning("  For regular use: pip install sasdata")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False
    
    # Extract example data
    print_step("Extracting sasdata example data...")
    example_data_dir = sasview_src / "sas" / "example_data"
    example_data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(
            [sys.executable, str(resources_script),
             "-r", "sasdata", "example_data", str(example_data_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        print_success("sasdata example data extracted")
    except subprocess.CalledProcessError:
        print_warning("Failed to extract sasdata example data (non-critical)")
    
    return True


def build_sasview_docs(script_dir, sphinx_docs, build_dir, format_type, open_docs):
    """Build sasview documentation"""
    print_step("Collecting sasview documentation sources...")
    
    # Set PYTHONPATH
    env = os.environ.copy()
    pythonpath = str(script_dir / "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{pythonpath}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = pythonpath
    
    # Run collect_sphinx_sources.py
    collect_script = sphinx_docs / "collect_sphinx_sources.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(collect_script)],
            cwd=str(sphinx_docs),
            env=env,
            check=True
        )
        print_success("Documentation sources collected")
    except subprocess.CalledProcessError as e:
        print_error("Failed to collect documentation sources")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False
    
    # Build documentation using make
    print_step(f"Building sasview documentation (format: {format_type})...")
    
    try:
        # Check if make is available
        subprocess.run(["make", "--version"], 
                      capture_output=True, check=True)
        
        result = subprocess.run(
            ["make", format_type],
            cwd=str(sphinx_docs),
            check=True
        )
        
        print_success("sasview documentation built successfully")
        print()
        print(f"Documentation location: {build_dir / format_type}")
        
        # Open in browser if requested
        if format_type == "html" and open_docs:
            print_step("Opening documentation in browser...")
            html_file = build_dir / "html" / "index.html"
            
            if sys.platform == "darwin":
                # macOS
                subprocess.run(["open", str(html_file)])
            elif sys.platform == "linux":
                # Linux
                for cmd in ["xdg-open", "sensible-browser", "firefox"]:
                    try:
                        subprocess.run([cmd, str(html_file)], 
                                     check=False, 
                                     capture_output=True)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    print(f"Please open: {html_file}")
            elif sys.platform == "win32":
                # Windows
                os.startfile(str(html_file))
            else:
                print(f"Please open: {html_file}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error("Failed to build sasview documentation")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print_error("'make' command not found. Please install make.")
        print("  On macOS: Xcode Command Line Tools")
        print("  On Linux: sudo apt-get install build-essential")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build documentation for sasmodels, sasdata, and sasview",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--sasmodels-only",
        action="store_true",
        help="Build only sasmodels documentation"
    )
    parser.add_argument(
        "--sasdata-only",
        action="store_true",
        help="Build only sasdata documentation"
    )
    parser.add_argument(
        "--sasview-only",
        action="store_true",
        help="Build only sasview documentation"
    )
    parser.add_argument(
        "--format",
        default="html",
        choices=["html", "pdf", "epub", "singlehtml", "latex"],
        help="Build format (default: html)"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the built documentation in a browser (HTML only)"
    )
    
    args = parser.parse_args()
    
    # Determine what to build
    if args.sasmodels_only:
        build_sasmodels = True
        build_sasdata = False
        build_sasview = False
    elif args.sasdata_only:
        build_sasmodels = False
        build_sasdata = True
        build_sasview = False
    elif args.sasview_only:
        build_sasmodels = False
        build_sasdata = False
        build_sasview = True
    else:
        build_sasmodels = True
        build_sasdata = True
        build_sasview = True
    
    # Get script directory (repository root)
    script_dir = Path(__file__).parent.resolve()
    
    # Define paths
    sasview_src = script_dir / "src"
    sphinx_docs = script_dir / "docs" / "sphinx-docs"
    sasmodels_docs = sphinx_docs / "tmp" / "sasmodels" / "docs"
    sasdata_docs = sphinx_docs / "tmp" / "sasdata" / "docs"
    build_dir = script_dir / "build" / "doc"
    
    # Print header
    print("=" * 42)
    print("  SasView Documentation Builder")
    print("=" * 42)
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Clean if requested
    clean_build(args.clean, build_dir, sphinx_docs)
    
    success = True
    
    # Build sasmodels docs
    if build_sasmodels:
        if not build_sasmodels_docs(script_dir, sasview_src, sasmodels_docs):
            success = False
    
    # Build sasdata docs
    if build_sasdata:
        if not build_sasdata_docs(script_dir, sasview_src, sasdata_docs):
            success = False
    
    # Build sasview docs
    if build_sasview:
        if not build_sasview_docs(script_dir, sphinx_docs, build_dir, 
                                 args.format, args.open):
            success = False
    
    print()
    print("=" * 42)
    if success:
        print_success("Documentation build complete!")
    else:
        print_error("Documentation build completed with errors")
    print("=" * 42)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

