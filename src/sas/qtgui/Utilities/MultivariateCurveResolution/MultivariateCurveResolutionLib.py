import logging
import os
import os.path

from typing import Optional, List, Tuple

import numpy as np
import matplotlib.pylab as pl
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QFileDialog

from sasdata.dataloader.loader import Loader

import sas.qtgui.Utilities.MultivariateCurveResolution.constants as const


# --------------------------------------------------------------------------------
# Import pycosmics from local directory. For release, pycosmics will most likely be imported as PyPi package
import importlib.machinery

class CustomFinder(importlib.machinery.PathFinder):
    _path = ["../pyCOSMiCS"]

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        return super().find_spec(fullname, cls._path, target)

import sys
sys.meta_path.append(CustomFinder)

import cosmics.main as pycosmics
# From answer to: https://stackoverflow.com/questions/44786278/how-to-import-a-directory-as-python-module by a_guest
# --------------------------------------------------------------------------------

class Curve:
    """ Contains and handles changes in spectra profile data """

    ID: int

    name: str
    file_name: str
    default_units: str
    units: str

    is_removed: bool = False
    is_resampled: bool = False
    is_auto_scaled: bool = False

    data: Optional[np.ndarray] = None

    def __init__(self, ID: int, file_name: str, default_units: str = "", name: str = "", units: str = "", data: Optional[np.ndarray] = None):
        self.ID = ID

        if units == "":
            units = default_units

        self.name = name
        self.file_name = file_name
        self.default_units = default_units
        self.units = units
        self.data = data

    def setUnits(self, units: str):
        self.units = units

    def resetUnits(self):
        self.units = self.default_units

    def getData(self) -> np.ndarray:
        return self.data.copy() * [const.XUNIT_FACTORS[self.units], 1, 1]

    def plotAbsolute(self, ax: plt.Axes, units: str = "", a_cut: float = 0, error_bars: bool = False, color = const.A_DEF_COLOR, semilog: bool = True):
        if units == "":
            units = self.units
        if self.data is None:
            return

        x = self.data[:, 0].copy() * const.XUNIT_FACTORS[units]
        y = self.data[:, 1].copy()
        dy = self.data[:, 2].copy()

        if semilog:
            ax.semilogy(x, y, color=color)
        else:
            ax.plot(x, y, color=color)
        
        if error_bars:
            ax.fill_between(x, (y-dy), (y+dy), color=color, alpha=.25)
    
    def plotHoltzer(self, ax: plt.Axes, units: str = "", h_cut: float = 0, error_bars: bool = False, color = const.H_DEF_COLOR):
        if units == "":
            units = self.units
        if self.data is None:
            return

        x = self.data[:, 0].copy() * const.XUNIT_FACTORS[units]
        y = self.data[:, 1].copy()
        dy = self.data[:, 2].copy()

        ax.plot(x, y * x, color=color)
        if error_bars:
            ax.fill_between(x, (y-dy) * x, (y+dy) * x, color=color, alpha=.25)
    
    def plotKratky(self, ax: plt.Axes, units: str = "", k_cut: float = 0, error_bars: bool = False, color = const.K_DEF_COLOR):
        if units == "":
            units = self.units
        if self.data is None:
            return

        x = self.data[:, 0].copy() * const.XUNIT_FACTORS[units]
        y = self.data[:, 1].copy()
        dy = self.data[:, 2].copy()

        ax.plot(x, y * (x ** 2), color=color)
        if error_bars:
            ax.fill_between(x, (y-dy) * (x ** 2), (y+dy) * (x ** 2), color=color, alpha=.25)
    
    def plotPorod(self, ax: plt.Axes, units: str = "", p_cut: float = 0, error_bars: bool = False, color = const.P_DEF_COLOR):
        if units == "":
            units = self.units
        if self.data is None:
            return

        x = self.data[:, 0].copy() * const.XUNIT_FACTORS[units]
        y = self.data[:, 1].copy()
        dy = self.data[:, 2].copy()

        ax.plot(x, y * (x ** 4), color=color)
        if error_bars:
            ax.fill_between(x, (y-dy) * (x ** 4), (y+dy) * (x ** 4), color=color, alpha=.25)

    def __str__(self):
        # Nice printout
        return "".join([
            "Curve:\n",
            f"    ID: {self.ID}\n",
            f"    filename: {self.file_name}\n",
            f"    name: {self.name}\n",
            f"    default units: {const.DISPLAY_UNITS_TEXT[self.default_units]}\n",
            f"    units: {const.DISPLAY_UNITS_TEXT[self.units]}\n",
            f"  Flags:\n",
            f"    removed: {self.is_removed}\n",
            f"    resampled: {self.is_resampled}\n",
            f"    scaled: {self.is_auto_scaled}\n",
            f"  Data:\n",
            str(self.data)
        ])


class CurveContainer:
    """ Stores and handles spectra curves """

    tot_curves: int

    curves: dict[int, Curve]

    name2ID: dict[str, int]

    experiments: list[list[int]]

    def __init__(self):
        self.curves = {}
        self.tot_curves = 0
        self.name2ID = {}
        self.experiments = []

    def __get_next_unique_ID(self) -> int:
        ID = self.tot_curves
        self.tot_curves += 1
        return ID

    def __get_unique_name(self, name: str) -> str:
        name, dot, ext = name.rpartition(".")

        list_names = [curve.name.rpartition(".")[0] for curve in self.curves.values()]

        if name in list_names:
            suffix = 1
            while f"{name}({suffix})" in list_names:
                suffix += 1
            name += f"({suffix})"
        
        return name + dot + ext

    def addCurve(self, file_name: str, default_units: str = "", name: str = "", units: str = "", data: Optional[np.ndarray] = None) -> Curve:
        ID = self.__get_next_unique_ID()
        if name == "":
            name = file_name
        name = self.__get_unique_name(name)
        self.curves[ID] = Curve(ID, file_name, default_units, name, units, data)
        self.name2ID[name] = ID
        return self.curves[ID]

    def getIdFromName(self, name: str) -> int:
        return self.name2ID[name]


class ProcessContainer:
    """ Stores current settings and results for the MCR-ALS process """

    cosmics: pycosmics.RunCosmics
    id_to_cosmics_index: dict[int, int]
    cosmics_index_to_id: dict[int, int]

    a_cut: float
    h_cut: float
    k_cut: float
    p_cut: float

    list_curves: list[Curve]

    pca_significant_components: int
    pca_sc_variance: float
    n_species: int

    experiments: list[int]

    conc_file_name: str

    n_tot_curves: int
    n_curves: int
    unused_curves: int
    n_removed_curves: int

    combination: Optional[List[bool]] = None
    curve_container: CurveContainer

    n_pure_spectra: int
    pure_spectra: list[int]
    initial_estimates: list[int]
    initial_estimate_method: None

    constraints_preset: str
    constraints: list[int]

    convergence_criterion: float
    max_iterations: int
    elim_points: int

    done_error_estimation: bool
    error_iterations: int
    error_noise: str

    def __init__(self):
        self.cosmics = pycosmics.CosmicsWorkflow()

        self.id_to_cosmics_index = dict()
        self.cosmics_index_to_id = dict()

        self.curve_container = CurveContainer()

        self.experiments = []

        self.n_tot_curves = 0
        self.n_curves = 0
        self.n_removed_curves = 0

        self.pure_spectra = []
        self.initial_estimates = []
        self.constraints = []

        self.done_error_estimation = False

    def applyQCuts(self, a_cut: float, h_cut: float, k_cut: float, p_cut: float):
        self.a_cut = a_cut
        self.h_cut = h_cut
        self.k_cut = k_cut
        self.p_cut = p_cut

    def deleteCurve(self, curve: Curve) -> bool:
        if curve not in self.curve_container.curves.values():
            return False

        self.curve_container.name2ID.pop(curve.name)
        self.curve_container.curves.pop(curve.ID)

        return True

    def mapID(self, ID: int):
        return self.id_to_cosmics_index[ID]
    def mapIDs(self, IDs: list[int]):
        return list(self.id_to_cosmics_index[ID] for ID in IDs)

    def mapIndex(self, index: int):
        return self.cosmics_index_to_id[index]
    def mapIndices(self, indices: list[int]):
        return list(self.cosmics_index_to_id[idx] for idx in indices)


class MCRALSLib:
    """ Library methods supporting MCR-ALS, interfaces with pyCOSMiCS via the pycosmics.RunCosmics class """

    logger = logging.getLogger("MCRALS")

    @staticmethod
    def directory_popup() -> Optional[str]:
        directory: str  = QFileDialog.getExistingDirectory()

        directory.strip()

        if directory == "":
            return None
        else:
            return directory

    @staticmethod
    def files_popup() -> Optional[str]:
        files: List[str] = QFileDialog.getOpenFileNames()[0]

        files = [file.strip() for file in files]
        files = [file for file in files if file != ""]

        if len(files) == 0:
            return None
        else:
            return files

    @staticmethod
    def import_experiment_curves(process: ProcessContainer, files: List[str], paths: List[str]) -> List[Curve] | Exception:
        if (len(paths) != len(files)) or (len(paths) == 0):
            return []
        
        imported_curves: List[Curve] = []

        try:
            loader = Loader()

            input_data = loader.load(paths)

            for filename, data1d in zip(files, input_data):
                if isinstance(data1d, Exception):
                    return data1d

                curve_data = np.stack([data1d.x, data1d.y, data1d.dy], axis=1)

                if data1d._xunit in const.ANGSTROM_UNIT_STRINGS:
                    units = "A"
                elif data1d._xunit in const.NANOMETER_UNIT_STRINGS:
                    units = "N"
                else:
                    units = ""

                imported_curves.append(
                    process.curve_container.addCurve(
                        file_name=filename,
                        default_units=units,
                        name=filename,
                        data=curve_data
                    )
                )

        except Exception as e:
            return e

        return imported_curves

    @staticmethod
    def import_curve_files(process: ProcessContainer, input_directory: Optional[str] = None) -> Optional[List[List[Curve]]]:
        if (input_directory is None) or (not os.path.isdir(input_directory)):
            return

        directories_stack: List[List[str]] = [input_directory]

        imported_curves: List[List[Curve]] = []

        idx = 0
        while idx < len(directories_stack):
            directory = directories_stack[idx]
            
            directory_filenames = sorted([name for name in os.listdir(directory)])

            experiment_files, experiment_paths = [], []

            for filename in directory_filenames:
                path = os.path.join(directory, filename)
                if os.path.isdir(path):
                    directories_stack.append(path)
                else:
                    experiment_files.append(filename)
                    experiment_paths.append(path)

            experiment_curves = MCRALSLib.import_experiment_curves(
                process=process,
                files=experiment_files,
                paths=experiment_paths
            )

            if isinstance(experiment_curves, Exception):
                MCRALSLib.logger.error(f"Failed to load in data from {directory}: {repr(experiment_curves)}")
                return

            if len(experiment_curves) > 0:
                imported_curves.append(experiment_curves)

            idx += 1
        
        return imported_curves

    @staticmethod
    def load_data(process: ProcessContainer, output: str):
        process.list_curves = []
        all_data: list[np.ndarray] = []

        # Collect all active curves
        for curve in process.curve_container.curves.values():
            if not curve.is_removed:
                process.cosmics_index_to_id[len(all_data)] = curve.ID
                process.id_to_cosmics_index[curve.ID] = len(all_data)

                process.list_curves.append(curve)
                all_data.append(curve.getData())

        # Add active curves to the pyCOSMiCS process
        process.cosmics.load_data(
            output=output,
            all_curves=[all_data],
            all_names=[[curve.name for curve in process.list_curves]],
            n_experiments=1,
            silent=True
        )

        # Preprocess the data
        scale_mask: List[bool] = [curve.is_auto_scaled for curve in process.list_curves]
        process.cosmics.normalise(mask=scale_mask)

        process.cosmics.set_units(units="A")

        process.elim_points = 3

        process.cosmics.remove_leading_points(elim_points=process.elim_points)

        process.cosmics.qrange_cuts(
            cut_abs=process.a_cut,
            cut_holtzer=process.h_cut,
            cut_kratky=process.k_cut,
            cut_porod=process.p_cut,
            silent=True
        )

        process.cosmics.representation_matrices()

    @staticmethod
    def preview_data(process: ProcessContainer) -> plt.Figure:
        pass

    @staticmethod
    def preview_curve(process: ProcessContainer, curve_ID: int) -> plt.Figure:
        pass

    @staticmethod
    def PCA(process: ProcessContainer) -> plt.Figure:
        MCRALSLib.load_data(process, "src/sas/qtgui/Utilities/MultivariateCurveResolution/cosmics_results")

        # Run PCA
        process.pca_significant_components, process.pca_sc_variance = process.cosmics.pca()
        
        # Render the PCA-results as a plot
        figure: plt.Figure = process.cosmics.plot_pca_eigenvs(show=False)
        return figure

    @staticmethod
    def InitialEstimates(process: ProcessContainer, mode: int):
        """
        mode=0: use the given initial estimates
        mode=1: repeatedly select the most dissimilar curve to all initial estimates
        mode=2: chi-rank
        """

        process.cosmics.number_of_species(n_species=process.n_species)

        initial_estimates = process.cosmics.initial_estimates(
            init_method=mode,
            initial_estimates=process.mapIDs(process.initial_estimates),
            sort_by_index=True,
            silent=True
        )

        process.initial_estimates = process.mapIndices(initial_estimates)

        process.cosmics.set_pure_components(
            pure_components=process.mapIDs(process.pure_spectra)
        )

    @staticmethod
    def import_concentration_file(process: ProcessContainer) -> bool:
        path: str = QFileDialog.getOpenFileName()

        path = path[0].strip()

        if path in ["", None]:
            return False

        process.conc_file_name = path
        return True

    @staticmethod
    def MCRLAS(process: ProcessContainer):

        process.cosmics.constraint_type(
            constraints=process.constraints,
            experiment_type=const.EXPERIMENT_TYPES[process.constraints_preset],
            silent=True
        )

        process.cosmics.closure_input_files(closure_pattern=None)

        process.cosmics.convergence_settings(
            tolerance=process.convergence_criterion,
            max_iterations=process.max_iterations,
            silent=True
        )

        figs: list[plt.Figure] = process.cosmics.als_workflow(
            show_plots=False,
            auto_clean=False,
            silent=True
        )

    @staticmethod
    def plot_recovered_profiles(process: ProcessContainer) -> plt.Figure:
        pass

    @staticmethod
    def MonteCarlo(process: ProcessContainer) -> Tuple[plt.Figure, plt.Figure]:
        process.cosmics.monte_carlo(
            combination=const.RESULTS_LIST_COMBINATIONS[process.combination],
            iterations=process.error_iterations,
            confidence=0.95,
            silent=True
        )
        return process.cosmics.plot_monte_carlo(show=False)

    @staticmethod
    def GenerateReport(process: ProcessContainer):
        process.cosmics.save_info_file()

    @staticmethod
    def SaveHTML(process: ProcessContainer, directory: Optional[str]):
        process.cosmics.html_report(directory, silent=True)