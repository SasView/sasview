import numpy as np
from scipy.optimize import curve_fit
from scipy import integrate
from scipy import special


class DatasetCreator:
    def __init__(self):
        self.combobox_index = -1

    def func_2d(self, q, scale, radius, height):
        x = self.func(q[0], scale, radius, height)
        y = self.func(q[1], scale, radius, height)
        z = np.matmul(x, y)
        return z

    def func(self, q, scale, radius, height):
        if self.combobox_index == 0:
            volume = 4 / 3 * np.pi * radius**3
            return scale / volume * (3*volume*(np.sin(q*radius)-q*radius*np.cos(q*radius)) / (q*radius)**3)**2
        elif self.combobox_index == 1:
            volume = height * np.pi * radius**2
            return 4 * scale * volume * (special.jv(1, q*radius))**2 / (q*radius)**2

    def createRandomDataset(self, scale, radius, height, combobox_index, fit=False, second_dimension=False):
        self.combobox_index = combobox_index
        size = 100
        intensity_fit = np.array([])
        if second_dimension:
            q = np.linspace(start=1, stop=10, num=size).reshape(size, 1)
            q_vec = (q, q.T)
            intensity_no_err = self.func_2d(q_vec, scale, radius, height)
            err = intensity_no_err * (np.random.random() - 0.5) * 2
            intensity = intensity_no_err + err
            if fit:
                intensity_1d = intensity.reshape(size*size)
                q_1d = np.tile(q, size)
                q_stack = np.vstack((q_1d, q_1d))
                p_opt, p_cov = curve_fit(f=self.func_2d, xdata=q_stack, ydata=intensity_1d, p0=(1.5, 1.5, 1.5))
                intensity_fit = self.func_2d(q_vec, *p_opt)
            q = np.meshgrid(q, q)

        else:
            q = np.linspace(start=1, stop=10, num=size)
            intensity = np.empty(shape=size)
            intensity_no_err = self.func(q, scale, radius, height)
            err = (np.random.random(size)-0.5) * intensity_no_err

            intensity = intensity_no_err + err
            if fit:
                p_opt, p_cov = curve_fit(f=self.func, xdata=q, ydata=intensity, p0=(1.5, 1.5, 1.5))
                intensity_fit = self.func(q, *p_opt)
        return q, intensity, intensity_fit
