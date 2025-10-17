import time


class Dataset:
    """
    Generic dataset class to hold all of the generated data for one fitpage with its generated id in one place.
    The generated id is a timestamp with the fitpage number that the dataset belongs to as a prefix.
    """
    def __init__(self, fitpage_index: int, x_data: list, y_data: list, y_fit: list, is_data_2d: list[list],
                 plotpage_index: int = 0):
        self._fitpage_index = fitpage_index
        self._x_data = x_data
        self._y_data = y_data
        self._y_fit = y_fit
        self._plotpage_index = plotpage_index
        self._is_data_2d = is_data_2d
        self._data_id = self.__generate_id(self._fitpage_index)

    def __generate_id(self, fitpage_index: int):
        a = str(int(time.time()))
        b = len(a)
        new_id = int(str(fitpage_index) + a[5:b])
        return new_id

    @property
    def data_id(self) -> int:
        return self._data_id

    @property
    def fitpage_index(self) -> int:
        return self._fitpage_index

    @property
    def x_data(self) -> list:
        return self._x_data

    @property
    def y_data(self) -> list:
        return self._y_data

    @property
    def y_fit(self) -> list:
        return self._y_fit

    def has_y_fit(self) -> bool:
        if self._y_fit.size == 0:
            return False
        else:
            return True

    @property
    def plotpage_index(self) -> int:
        return self._plotpage_index

    @plotpage_index.setter
    def plotpage_index(self, plotpage_index: int):
        if isinstance(plotpage_index, int):
            self._plotpage_index = plotpage_index
        else:
            print("no integer")

    @x_data.setter
    def x_data(self, x_data: list):
        self._x_data = x_data

    @y_data.setter
    def y_data(self, y_data: list):
        self._y_data = y_data

    @y_fit.setter
    def y_fit(self, y_fit: list):
        self._y_fit = y_fit

    @property
    def is_data_2d(self) -> bool:
        return self._is_data_2d

    @is_data_2d.setter
    def is_data_2d(self, is_data_2d: bool):
        self._is_data_2d = is_data_2d

