from PySide6.QtWidgets import QMessageBox, QWidget


class DataExplorerErrorMessage(QMessageBox):
    base_error_message = "Errors occurred:\n"
    def __init__(self, parent: QWidget, errors: list[ValueError]):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setWindowTitle('Data Error')
        self.format_message(errors)

    def format_message(self, errors: list[ValueError]):
        if len(errors) == 1:
            error = errors[0]
            self.setText(str(error))
        else:
            full_error_msg = self.base_error_message
            error_msg_set = set([str(err) for err in errors])
            error_msg_str = '\n'.join(error_msg_set)
            full_error_msg += f"\n{error_msg_str}"
            self.setText(full_error_msg)


class DataExplorerRemoveMessage(DataExplorerErrorMessage):
    base_error_message = "Some data could not be removed due to the following errors:\n"
    def __init__(self, parent: QWidget, errors: list[ValueError]):
        super().__init__(parent, errors)


class DataExplorerImportMessage(DataExplorerErrorMessage):
    base_error_message = "Some data could not be imported due to the following errors:\n"
    def __init__(self, parent: QWidget, errors: list[ValueError]):
        super().__init__(parent, errors)
