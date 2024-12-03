from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ViewerPlotDesign:
    """Values affecting the illustrative aspect of Viewer"""
    colour: Optional[List[str]]


