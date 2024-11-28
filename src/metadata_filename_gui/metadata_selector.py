from PySide6.QtWidgets import QWidget, QHBoxLayout
from metadata_filename_gui.metadata_component_selector import MetadataComponentSelector
from metadata_filename_gui.metadata_custom_selector import MetadataCustomSelector

class MetadataSelector(QWidget):
    def __init__(self, metadatum: str, options: list[str], metadata_dict: dict[str, str],
                 master_metadata: dict[str, int]):
        super().__init__()
        self.metadatum = metadatum
        self.metadata_dict = metadata_dict
        self.master_metadata = master_metadata
        self.options = options
        current_option = metadata_dict.get(metadatum)
        if current_option is None or current_option in options:
            self.selector_widget = self.new_component_selector()
        else:
            self.selector_widget = self.new_custom_selector()

        # I can't seem to find any layout that just has one widget in so this will do for now.
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.selector_widget)

    def new_component_selector(self) -> MetadataComponentSelector:
        new_selector = MetadataComponentSelector(self.metadatum, self.metadata_dict, self.master_metadata)
        new_selector.custom_button_pressed.connect(self.handle_selector_change)
        new_selector.draw_options(self.options, self.metadata_dict.get(self.metadatum))
        return new_selector

    def new_custom_selector(self) -> MetadataCustomSelector:
        new_selector = MetadataCustomSelector(self.metadatum, self.metadata_dict, self.master_metadata)
        new_selector.from_filename_button.clicked.connect(self.handle_selector_change)
        return new_selector

    def handle_selector_change(self):
        # Need to keep this for when we delete it.
        if isinstance(self.selector_widget, MetadataComponentSelector):
            # TODO: Will eventually have args
            new_widget = self.new_custom_selector()
        elif isinstance(self.selector_widget, MetadataCustomSelector):
            new_widget = self.new_component_selector()
        else:
            # Shouldn't happen as selector widget should be either of the above.
            return
        self.layout.replaceWidget(self.selector_widget, new_widget)
        self.selector_widget.deleteLater()
        self.selector_widget = new_widget
