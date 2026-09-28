import RandomDatasetCreator
from Dataset import Dataset
from PySide6 import QtWidgets


class DataCollector:
    """
    This class keeps track of all generated datasets. When the update_dataset is called through onCalculate
    from MainWindow, either a new dataset can be created or the existing dataset is adjusted with respect to
    the currently displayed SpinBox Values from the Fitpage.
    """
    def __init__(self):
        self._datasets: list[Dataset] = []
        self.datasetcreator = RandomDatasetCreator.DatasetCreator()

    def update_dataset(self, main_window: QtWidgets.QMainWindow, fitpage_index: int,
                       create_fit: bool, checked_2d: bool):
        """
        Search for an existing dataset saved in here. If no dataset for the corresponding fitpage exists: create new
        data.
        """

        # search for an existing dataset with the right fitpage_index
        existing_dataset_index = -1
        for i, dataset in enumerate(self._datasets):
            if dataset.fitpage_index == fitpage_index:
                existing_dataset_index = i

        if existing_dataset_index == -1:
            # create new dataset in case it does not exist
            x_data, y_data, y_fit = self.simulate_data(main_window, create_fit, checked_2d)
            plotpage_index = -1

            dataset = Dataset(fitpage_index, x_data, y_data, y_fit, checked_2d, plotpage_index)
            self._datasets.append(dataset)
        else:
            # update values for existing dataset with respect to the number boxes in the fitpage
            x_data, y_data, y_fit = self.simulate_data(main_window, create_fit, checked_2d)
            self._datasets[existing_dataset_index].x_data = x_data
            self._datasets[existing_dataset_index].y_data = y_data
            self._datasets[existing_dataset_index].y_fit = y_fit
            self._datasets[existing_dataset_index].is_data_2d = checked_2d

    def simulate_data(self, main_window: QtWidgets.QMainWindow, create_fit: bool, checked_2d: bool):
        """
        Collect all information from the FitPage from the MainWindow hat is needed to calculate the test data.
        Feed this information to the DatasetCreator and return the values.
        """
        combobox_index = main_window.fittingTabs.currentWidget().get_combobox_index()
        param_scale = main_window.fittingTabs.currentWidget().doubleSpinBox_scale.value()
        param_radius = main_window.fittingTabs.currentWidget().doubleSpinBox_radius.value()
        param_height = main_window.fittingTabs.currentWidget().doubleSpinBox_height.value()

        x_data, y_data, y_fit = self.datasetcreator.createRandomDataset(param_scale, param_radius, param_height,
                                                                        combobox_index, create_fit, checked_2d)

        return x_data, y_data, y_fit

    @property
    def datasets(self) -> list:
        return self._datasets

    def find_object_by_property(self, obj_list: list, property_name: str, property_value: int):
        for obj in obj_list:
            if hasattr(obj, property_name) and getattr(obj, property_name) == property_value:
                return obj

        return None

    def get_data_by_fp(self, fitpage_index: int) -> Dataset:
        """
        Get the dataset for a certain fitpage
        """
        return self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)

    def get_data_by_id(self, data_id: int) -> Dataset:
        """
        Get the dataset for certain id
        """
        return self.find_object_by_property(self._datasets, "data_id", data_id)

    def get_x_data(self, fitpage_index: int) -> list:
        """
        Get x data for certain fitpage index
        """
        dataset = self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)
        return dataset.x_data

    def get_y_data(self, fitpage_index: int) -> list:
        """
        Get y data for certain fitpage index
        """
        dataset = self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)
        return dataset.y_data

    def get_y_fit_data(self, fitpage_index: int) -> list:
        """
        Get y fit data for certain fitpage index
        """
        dataset = self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)
        return dataset.y_fit

    def get_plotpage_index(self, fitpage_index: int) -> int:
        """
        Get the plotpage index for a certain fitpage index: Plotpage index refers to the index of the major tabs in
        the plotting widget in which the data is displayed.
        """
        dataset = self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)
        return dataset.plotpage_index

    def set_plot_index(self, fitpage_index: int, plot_index: int):
        """
        Set the plotpage index for the dataset for a certain fitpage index. Plotpage index refers to the index of the
        major tabs in the plotting widget in which the data is displayed.
        """
        dataset = self.find_object_by_property(self._datasets, "fitpage_index", fitpage_index)
        dataset.plotpage_index = plot_index

