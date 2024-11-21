from PySide6.QtWidgets import QWidget, QHBoxLayout
from metadata_filename_gui.metadata_component_selector import MetadataComponentSelector
from metadata_filename_gui.metadata_custom_selector import MetadataCustomSelector

class MetadataSelector(QWidget):
    def __init__(self, metadatum: str, options: list[str], metadata_dict: dict[str, str]):
        super().__init__()
        self.metadatum = metadatum
        self.metadata_dict = metadata_dict
        self.options = options
        # Default to the name selector
        self.selector_widget: QWidget = MetadataComponentSelector(metadatum, metadata_dict)
        self.selector_widget.custom_button_pressed.connect(self.handle_selector_change)
        self.selector_widget.draw_options(self.options, metadata_dict.get(metadatum))

        # I can't seem to find any layou that just has one widgt in so this will do for now.
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.selector_widget)

    def handle_selector_change(self):
        # Need to keep this for when we delete it.
        if isinstance(self.selector_widget, MetadataComponentSelector):
            # TODO: Will eventually have args
            new_widget = MetadataCustomSelector()
            new_widget.from_filename_button.clicked.connect(self.handle_selector_change)
        elif isinstance(self.selector_widget, MetadataCustomSelector):
            new_widget = MetadataComponentSelector(self.metadatum, self.metadata_dict)
            self.selector_widget = new_widget
        else:
            # Shouldn't happen as selector widget should be either of the above.
            return
        self.layout.replaceWidget(self.selector_widget, new_widget)
        self.selector_widget.deleteLater()
        self.selector_widget = new_widget
