import logging
import math
import numpy as np




class WeightingFunctions():



    def calc_increase_factor(self, x_dict, error_dict, scaling, ignore_num=False):
        """
        :param x_dict: dict
            Dictionary with the tab number as the key, and an np.array of values on the x-axis,
            typically q value, as the value
        :param error_dict: dict
            Dictionary with the tab number as the key, and an np.array of values for errors
            for data points on the y-axis.
        :param scaling:
        :return:
        """

        increase_factors = {key: {} for key in x_dict.keys()}

        # Keys are x ranges
        for x_limit, weighting_ratio in scaling.items():
            stat_weight_per_tab = {}
            total_error_per_tab = {}
            for tab_id in x_dict.keys():
                x_array = x_dict[tab_id]
                error_array = error_dict[tab_id]
                total_error_per_tab[tab_id] = np.sum(error_array)
                stat_weight = 0
                for i in range(len(x_array)):
                    x_val = x_array[i]
                    err_x = error_array[i]
                    if x_val < x_limit:
                        stat_weight += 1.0 / (err_x ** 2)
                    else:
                        break
                stat_weight_per_tab[tab_id] = stat_weight

            num_tabs = len(stat_weight_per_tab.keys())
            fixed_stat_weight = None

            for tab_id in stat_weight_per_tab.keys():
                if weighting_ratio[tab_id] is "fixed":
                    increase_factors[tab_id][x_limit] = 1
                    fixed_stat_weight = stat_weight_per_tab[tab_id] / len(x_dict[tab_id])
            if fixed_stat_weight is None:
                fixed_stat_weight = (sum([stat_weight for stat_weight in stat_weight_per_tab.values()]) / 2.0)

            for tab_id in stat_weight_per_tab.keys():
                if weighting_ratio[tab_id] is not "fixed":
                    current_stat_weight = stat_weight_per_tab[tab_id] / len(x_dict[tab_id])
                    desired_stat_weight = fixed_stat_weight * weighting_ratio[tab_id]
                    rt_desired_stat_weight = math.sqrt(desired_stat_weight / current_stat_weight)
                    increase_factor = (1.0 / num_tabs) * (1 / rt_desired_stat_weight)
                    increase_factors[tab_id][x_limit] = increase_factor

        return increase_factors



    def increase_error(self, x_array, y_array, error_array, increase_factor):
        """
        Increase errors in a dataset to decrease weight of points when simultaneously fitting with other data. The
        error is increased by a multiplier, which can be different in different data ranges.

        :param x_array: np.array
            Data on the x-axis, typically q value
        :param error_array: np.array
            Errors for data points on the y-axis.
        :param increase_factor: dict
            Error multiplier in specific x value ranges
        :return result_array: np.array
            Modified errors, multiplied by a factor provided by increase_factor, for data points on the y-axis.
        """

        # Errors after applying scaling factor
        modified_error = []

        # Iterate over x values
        for i in range(len(x_array)):
            x_val = x_array[i]
            y_val = y_array[i]
            err = error_array[i]
            for key, value in increase_factor.items():
                if x_val > key:
                    continue
                else:
                    if y_val == 0.0:
                        modified_error.append(1.0)
                    else:
                        modified_error.append(err * value)
                    break

        return np.array(modified_error)
