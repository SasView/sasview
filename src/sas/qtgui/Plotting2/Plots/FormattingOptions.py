from typing import Union, Optional
from dataclasses import dataclass


@dataclass
class FormattingOptions:
    color: Optional[Union[str, tuple[float, float, float]]] = None
    marker_style: Optional[str] = None

    def override(self, base: "FormattingOptions"):
        return FormattingOptions(
            color=base.color if self.color is None else self.color,
            marker_style=base.marker_style if self.marker_style is None else self.marker_style)