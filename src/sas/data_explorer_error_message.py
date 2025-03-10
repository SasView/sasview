from PySide6.QtWidgets import QMessageBox, QWidget


class DataExplorerErrorMessage(QMessageBox):
    def __init__(self, parent: QWidget, errors: list[ValueError]):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setWindowTitle('Data Error')
        if len(errors) == 1:
            error = errors[0]
            self.setText(str(error))
        else:
            full_error_msg = "Some data could not be removed due to the following errors:\n"
            error_msg_set = set([str(err) for err in errors])
            error_msg_str = '\n'.join(error_msg_set)
            full_error_msg += f"\n{error_msg_str}"
            self.setText(full_error_msg)
