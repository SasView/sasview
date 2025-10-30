from pathlib import Path


class _HelpSystem:
    """Extensible storage for help-system-related paths and configuration"""

    def __init__(self) -> None:
        self.path: Path
        # self.example_data: Path   # perhaps?


HELP_SYSTEM = _HelpSystem()
