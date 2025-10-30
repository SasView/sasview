"""Unit tests for system/resources.py"""

import importlib.metadata
from pathlib import Path

import pytest

import sas.system.resources

# Determine if sasview is installed as an editable install, since that is
# what is needed for this test; also handle the odd case where sasview as
# a distribution can't be found (likely unpacked but not installed source)
SASVIEW_EDITABLE_INSTALL = False
try:
    dist = importlib.metadata.distribution("sasview")
    try:
        SASVIEW_EDITABLE_INSTALL = dist.origin.dir_info.editable
    except AttributeError:
        pass
except importlib.metadata.PackageNotFoundError:
    pytest.mark.skip(reason="Couldn't locate sasview as a distribution")

pytest.mark.skipif(SASVIEW_EDITABLE_INSTALL, reason="sasview not an editable install")


# type converters for the tests - need to hold Windows hand
def _as_str(src: str | Path) -> str:
    if isinstance(src, str):
        return src
    return src.as_posix()


def _as_path(src: str | Path) -> Path:
    return Path(src)


@pytest.mark.parametrize("input_type", [_as_str, _as_path])
class TestRecorded:
    """Tests of the "Recorded" type resources"""

    def test_path_to_resource(self, input_type):
        """Test extracting single resource recorded by installed module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "docs/index.html"
        src = input_type(source)

        pth = resources.path_to_resource(src)
        assert pth
        assert pth.is_absolute()
        assert Path(str(pth)).exists()
        assert Path(str(pth)).is_file()
        assert pth.as_posix().endswith(source)
        assert pth.stat().st_size > 1000

    def test_path_to_resource_directory(self, input_type):
        """Test extracting single resource recorded by installed module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "docs/user"
        src = input_type(source)

        pth = resources.path_to_resource_directory(src)
        assert pth
        assert pth.is_absolute()
        assert Path(str(pth)).exists()
        assert Path(str(pth)).is_dir()
        assert len(list(pth.iterdir())) > 10

    def test_resource(self, tmp_path, input_type):
        """Test extracting single resource recorded by installed module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = Path("docs/index.html")
        src = input_type(source)

        dest = tmp_path / source.name
        assert resources.extract_resource(src, dest)
        assert dest.stat().st_size > 1000

        # test magic subdirs
        dest = tmp_path / "subdir10" / "subdir11" / source.name
        assert resources.extract_resource(src, dest)
        assert dest.stat().st_size > 1000

    def test_resource_tree(self, tmp_path, input_type):
        """Test extracting resource tree recorded by installed module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "docs/user"
        src = input_type(source)
        dest = tmp_path

        assert resources.extract_resource_tree(src, dest)
        assert len(list(dest.iterdir())) > 10

        # test magic subdirs
        dest = tmp_path / "subdir20" / "subdir21" / "subdir22"
        assert resources.extract_resource_tree(src, dest)
        assert len(list(dest.iterdir())) > 10


@pytest.mark.parametrize("input_type", [_as_str, _as_path])
class TestAdjacent:
    """Tests of the "Adjacent" type resources"""

    def test_path_to_resource(self, input_type):
        """Test extracting single resource adjacent to code in module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "qtgui/images/ball.ico"
        src = input_type(source)

        pth = resources.path_to_resource(src)
        assert pth
        assert pth.is_absolute()
        assert Path(str(pth)).exists()
        assert Path(str(pth)).is_file()
        assert pth.as_posix().endswith(source)
        assert pth.stat().st_size > 1000

    def test_path_to_resource_directory(self, input_type):
        """Test extracting single resource adjacent to code in module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "docs/user"
        src = input_type(source)

        pth = resources.path_to_resource_directory(src)
        assert pth
        assert pth.is_absolute()
        assert Path(str(pth)).exists()
        assert Path(str(pth)).is_dir()
        assert len(list(pth.iterdir())) > 10

    def test_resource(self, tmp_path, input_type):
        """Test extracting single resource adjacent to code in module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = Path("qtgui/images/ball.ico")
        src = input_type(source)
        dest = tmp_path / source.name

        assert resources.extract_resource(src, dest)
        assert dest.stat().st_size > 1000

        # test magic subdirs
        dest = tmp_path / "subdir40" / "subdir41" / source.name
        assert resources.extract_resource(src, dest)
        assert dest.stat().st_size > 1000

    def test_resource_tree(self, tmp_path, input_type):
        """Test extracting resource tree adjacent to code in module"""
        resources = sas.system.resources.ModuleResources("sas")

        source = "qtgui/images"
        src = input_type(source)
        dest = tmp_path

        assert resources.extract_resource_tree(src, dest)
        assert len(list(dest.iterdir())) > 10

        # test magic subdirs
        src = "qtgui/images"
        dest = tmp_path / "subdir50" / "subdir51" / "subdir53"
        assert resources.extract_resource_tree(src, dest)
        assert len(list(dest.iterdir())) > 10


@pytest.mark.parametrize("input_type", [_as_str, _as_path])
class TestExceptions:
    """Tests of the exception generation from resource handler"""

    check_paths = [
        "sas/docs/index.html",  # "sas" prefix should not be included in the resource
        "no-such-path-exists",
    ]

    def test_nonexisting_path_to_resource(self, input_type):
        """Test exception raised for finding path to non-existent resource"""
        resources = sas.system.resources.ModuleResources("sas")

        for pth in self.check_paths:
            with pytest.raises(FileNotFoundError):
                src = input_type(pth)
                assert resources.path_to_resource(src)

    def test_nonexisting_extract_resource(self, tmp_path, input_type):
        """Test exception raised for extracting non-existent resource"""
        resources = sas.system.resources.ModuleResources("sas")
        dest = tmp_path / "dummy"

        for pth in self.check_paths:
            with pytest.raises(FileNotFoundError):
                src = input_type(pth)
                assert resources.extract_resource(src, dest)

    def test_nonexisting_extract_resource_tree(self, tmp_path, input_type):
        """Test exception raised for extracting non-existent resource tree"""
        resources = sas.system.resources.ModuleResources("sas")
        dest = tmp_path / "dummy"

        for pth in self.check_paths + ["sas/docs/"]:
            with pytest.raises(NotADirectoryError):
                src = input_type(pth)
                assert resources.extract_resource_tree(src, dest)
