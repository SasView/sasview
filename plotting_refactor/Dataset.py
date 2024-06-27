import time


class Dataset:
    def __init__(self, fitpage_index, x_data, y_data, y_fit, data_2d, plotpage_index=0):
        self.fitpage_index = fitpage_index
        self.x_data = x_data
        self.y_data = y_data
        self.y_fit = y_fit
        self.plotpage_index = plotpage_index
        self.data_2d = data_2d
        self.data_id = self.generate_id(self.fitpage_index)

    def generate_id(self, fitpage_index):
        a = str(int(time.time()))
        b = len(a)
        new_id = int(str(fitpage_index) + a[5:b])
        return new_id

    def get_data_id(self):
        return self.data_id

    def get_fitpage_index(self):
        return self.fitpage_index

    def get_x_data(self):
        return self.x_data

    def get_y_data(self):
        return self.y_data

    def get_y_fit(self):
        return self.y_fit

    def has_y_fit(self):
        if self.y_fit.size == 0:
            return False
        else:
            return True

    def get_plotpage_index(self):
        return self.plotpage_index

    def set_plotpage_index(self, plotpage_index):
        if isinstance(plotpage_index, int):
            self.plotpage_index = plotpage_index
        else:
            print("no integer")

    def set_x_data(self, x_data):
        self.x_data = x_data

    def set_y_data(self, y_data):
        self.y_data = y_data

    def set_y_fit(self, y_fit):
        self.y_fit = y_fit

    def is_2d(self):
        return self.data_2d


