#class to keep track of all datasets of fitpages and more
import RandomDatasetCreator
from Dataset import Dataset
from typing import List

class DataCollector:
    def __init__(self):
        self.datasets: List[Dataset] = []
        self.datasetcreator = RandomDatasetCreator.DatasetCreator()

    def update_dataset(self, main_window, fitpage_index, create_fit, checked_2d):
        # search for an existing dataset with the right fitpage_index
        existing_dataset_index = -1
        for i in range(len(self.datasets)):
            if self.datasets[i].get_fitpage_index() == fitpage_index:
                existing_dataset_index = i
        if existing_dataset_index == -1:
            # create new dataset in case it does not already exist
            x_data, y_data, y_fit = self.simulate_data(main_window, fitpage_index, create_fit, checked_2d)
            plotpage_index = -1

            dataset = Dataset(fitpage_index, x_data, y_data, y_fit, checked_2d, plotpage_index)
            self.datasets.append(dataset)
        else:
            # update values for existing dataset with respect to the number boxes in the fitpage
            x_data, y_data, y_fit = self.simulate_data(main_window, fitpage_index, create_fit, checked_2d)
            self.datasets[existing_dataset_index].set_x_data(x_data)
            self.datasets[existing_dataset_index].set_y_data(y_data)
            self.datasets[existing_dataset_index].set_y_fit(y_fit)

    def simulate_data(self, main_window, fitpage_index, create_fit, checked_2d):
        combobox_index = main_window.fittingTabs.currentWidget().get_combobox_index()
        param_scale = main_window.fittingTabs.currentWidget().doubleSpinBox_scale.value()
        param_radius = main_window.fittingTabs.currentWidget().doubleSpinBox_radius.value()
        param_height = main_window.fittingTabs.currentWidget().doubleSpinBox_height.value()

        x_data, y_data, y_fit = self.datasetcreator.createRandomDataset(param_scale, param_radius, param_height,
                                                                        combobox_index, create_fit, checked_2d)

        return x_data, y_data, y_fit

    def get_datasets(self) -> List:
        return self.datasets

    def get_data_fp(self, fitpage_index) -> Dataset:
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                return self.datasets[i]

    def get_data_id(self, data_id) -> Dataset:
        for i in range(len(self.datasets)):
            if data_id == self.datasets[i].get_data_id():
                return self.datasets[i]

    def get_x_data(self, fitpage_index) -> List:
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                return self.datasets[i].get_x_data()

    def get_y_data(self, fitpage_index) -> List:
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                return self.datasets[i].get_y_data()

    def get_y_fit_data(self, fitpage_index) -> List:
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                return self.datasets[i].get_y_fit()

    def get_plotpage_index(self, fitpage_index) -> int:
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                return self.datasets[i].get_plotpage_index()

    def set_plot_index(self, fitpage_index, plot_index):
        for i in range(len(self.datasets)):
            if fitpage_index == self.datasets[i].get_fitpage_index():
                self.datasets[i].set_plotpage_index(plot_index)

