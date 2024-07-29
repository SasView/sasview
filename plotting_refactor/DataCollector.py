from PySide6 import QtWidgets
import RandomDatasetCreator
from Dataset import Dataset

class DataCollector:
    """
    This class keeps track of all generated datasets. When the update_dataset is called through onCalculate
    from MainWindow, either a new dataset can be created or the existing dataset is adjusted with respect to
    the currently displayed SpinBox Values from the Fitpage.
    """
    def __init__(self):
        self.datasets: list[Dataset] = []
        self.datasetcreator = RandomDatasetCreator.DatasetCreator()

    def update_dataset(self, main_window: QtWidgets.QMainWindow, fitpage_index: int,
                       create_fit: bool, checked_2d: bool):
        """
        Search for an existing dataset saved in here. If no dataset for the corresponding fitpage exists: create new
        data.
        """

        # search for an existing dataset with the right fitpage_index
        existing_dataset_index = -1
        for i, dataset in enumerate(self.datasets):
            if dataset.get_fitpage_index() == fitpage_index:
                existing_dataset_index = i

        if existing_dataset_index == -1:
            # create new dataset in case it does not exist
            x_data, y_data, y_fit = self.simulate_data(main_window, create_fit, checked_2d)
            plotpage_index = -1

            dataset = Dataset(fitpage_index, x_data, y_data, y_fit, checked_2d, plotpage_index)
            self.datasets.append(dataset)
        else:
            # update values for existing dataset with respect to the number boxes in the fitpage
            x_data, y_data, y_fit = self.simulate_data(main_window, create_fit, checked_2d)
            self.datasets[existing_dataset_index].set_x_data(x_data)
            self.datasets[existing_dataset_index].set_y_data(y_data)
            self.datasets[existing_dataset_index].set_y_fit(y_fit)
            self.datasets[existing_dataset_index].set_2d(checked_2d)

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

    def get_datasets(self) -> list:
        return self.datasets

    def get_data_fp(self, fitpage_index: int) -> Dataset:
        """
        Get the dataset for a certain fitpage
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                return dataset

    def get_data_id(self, data_id: int) -> Dataset:
        """
        Get the dataset for certain id
        """
        for dataset in self.datasets:
            if data_id == dataset.get_data_id():
                return dataset

    def get_x_data(self, fitpage_index: int) -> list:
        """
        Get x data for certain fitpage index
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                return dataset.get_x_data()

    def get_y_data(self, fitpage_index: int) -> list:
        """
        Get y data for certain fitpage index
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                return dataset.get_y_data()

    def get_y_fit_data(self, fitpage_index: int) -> list:
        """
        Get y fit data for certain fitpage index
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                return dataset.get_y_fit()

    def get_plotpage_index(self, fitpage_index: int) -> int:
        """
        Get the plotpage index for a certain fitpage index: Plotpage index refers to the index of the major tabs in
        the plotting widget in which the data is displayed.
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                return dataset.get_plotpage_index()

    def set_plot_index(self, fitpage_index: int, plot_index: int):
        """
        Set the plotpage index for the dataset for a certain fitpage index. Plotpage index refers to the index of the
        major tabs in the plotting widget in which the data is displayed.
        """
        for dataset in self.datasets:
            if fitpage_index == dataset.get_fitpage_index():
                dataset.set_plotpage_index(plot_index)

