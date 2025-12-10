"""
Unit tests for SASBDB export functionality
"""
import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from PySide6 import QtWidgets

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBBuffer,
    SASBDBExportData,
    SASBDBFit,
    SASBDBGuinier,
    SASBDBInstrument,
    SASBDBModel,
    SASBDBMolecule,
    SASBDBPDDF,
    SASBDBProject,
    SASBDBSample,
)
from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector
from sas.qtgui.Utilities.SASBDB.sasbdb_exporter import SASBDBExporter


class TestSASBDBData:
    """Test SASBDB data structures"""

    def test_project_creation(self):
        """Test creating a SASBDBProject"""
        project = SASBDBProject()
        assert project.published is False
        assert project.pubmed_pmid is None
        assert project.doi is None
        assert project.project_title is None

    def test_project_with_data(self):
        """Test creating a SASBDBProject with data"""
        project = SASBDBProject(
            published=True,
            pubmed_pmid="12345678",
            doi="10.1234/example",
            project_title="Test Project"
        )
        assert project.published is True
        assert project.pubmed_pmid == "12345678"
        assert project.doi == "10.1234/example"
        assert project.project_title == "Test Project"

    def test_sample_creation(self):
        """Test creating a SASBDBSample"""
        sample = SASBDBSample()
        assert sample.sample_title is None
        assert sample.molecule is None
        assert sample.buffer is None
        assert sample.fits == []

    def test_molecule_creation(self):
        """Test creating a SASBDBMolecule"""
        molecule = SASBDBMolecule(
            type="Protein",
            long_name="Test Protein",
            fasta_sequence="MKTAYIAKQR",
            monomer_mw_kda=10.5,
            number_of_molecules=1
        )
        assert molecule.type == "Protein"
        assert molecule.long_name == "Test Protein"
        assert molecule.fasta_sequence == "MKTAYIAKQR"
        assert molecule.monomer_mw_kda == 10.5
        assert molecule.number_of_molecules == 1

    def test_buffer_creation(self):
        """Test creating a SASBDBBuffer"""
        buffer = SASBDBBuffer(
            description="PBS buffer",
            ph=7.4,
            comment="Standard buffer"
        )
        assert buffer.description == "PBS buffer"
        assert buffer.ph == 7.4
        assert buffer.comment == "Standard buffer"

    def test_guinier_creation(self):
        """Test creating a SASBDBGuinier"""
        guinier = SASBDBGuinier(
            rg=2.5,
            rg_error=0.1,
            i0=100.0,
            range_start=0.01,
            range_end=0.05
        )
        assert guinier.rg == 2.5
        assert guinier.rg_error == 0.1
        assert guinier.i0 == 100.0
        assert guinier.range_start == 0.01
        assert guinier.range_end == 0.05

    def test_instrument_creation(self):
        """Test creating a SASBDBInstrument"""
        instrument = SASBDBInstrument(
            source_type="X-ray synchrotron",
            beamline_name="BL12",
            synchrotron_name="ESRF",
            detector_manufacturer="Pilatus",
            detector_type="2D",
            detector_resolution="0.172 mm",
            city="Grenoble",
            country="France"
        )
        assert instrument.source_type == "X-ray synchrotron"
        assert instrument.beamline_name == "BL12"
        assert instrument.synchrotron_name == "ESRF"
        assert instrument.detector_manufacturer == "Pilatus"
        assert instrument.city == "Grenoble"
        assert instrument.country == "France"

    def test_fit_creation(self):
        """Test creating a SASBDBFit"""
        fit = SASBDBFit(
            software="SasView",
            software_version="6.0.0",
            chi_squared=1.5,
            cormap_pvalue=0.05,
            angular_units="1/A"
        )
        assert fit.software == "SasView"
        assert fit.software_version == "6.0.0"
        assert fit.chi_squared == 1.5
        assert fit.cormap_pvalue == 0.05
        assert fit.angular_units == "1/A"
        assert fit.models == []

    def test_model_creation(self):
        """Test creating a SASBDBModel"""
        model = SASBDBModel(
            software_or_db="SasView",
            software_version="6.0.0",
            model_data="model.dat",
            comment="Test model"
        )
        assert model.software_or_db == "SasView"
        assert model.software_version == "6.0.0"
        assert model.model_data == "model.dat"
        assert model.comment == "Test model"

    def test_export_data_creation(self):
        """Test creating a SASBDBExportData"""
        export_data = SASBDBExportData()
        assert export_data.project is None
        assert export_data.samples == []
        assert export_data.instruments == []

    def test_export_data_with_content(self):
        """Test creating a SASBDBExportData with content"""
        project = SASBDBProject(project_title="Test Project")
        sample = SASBDBSample(sample_title="Test Sample")
        instrument = SASBDBInstrument(beamline_name="BL12")
        
        export_data = SASBDBExportData()
        export_data.project = project
        export_data.samples.append(sample)
        export_data.instruments.append(instrument)
        
        assert export_data.project == project
        assert len(export_data.samples) == 1
        assert len(export_data.instruments) == 1


class TestSASBDBDataCollector:
    """Test SASBDBDataCollector"""

    @pytest.fixture
    def collector(self):
        """Create a collector instance"""
        return SASBDBDataCollector()

    def test_collector_initialization(self, collector):
        """Test collector initialization"""
        assert collector.export_data is not None
        assert isinstance(collector.export_data, SASBDBExportData)

    def test_collect_from_data_basic(self, collector):
        """Test collecting basic data from Data1D"""
        data = Data1D(x=[0.01, 0.02, 0.03], y=[100, 50, 25])
        data.name = "Test Data"
        data.filename = "test.dat"
        data._xunit = "1/A"
        data._yunit = "1/cm"
        
        sample, instrument = collector.collect_from_data(data)
        
        assert isinstance(sample, SASBDBSample)
        assert sample.sample_title == "Test Data"
        assert sample.experimental_curve == "test.dat"
        assert sample.angular_units == "1/A"
        assert sample.intensity_units == "1/cm"
        assert sample.curve_type == "Single concentration"
        assert sample.experiment_date is not None

    def test_collect_from_data_with_metadata(self, collector):
        """Test collecting data with metadata"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        data.meta_data = {
            'experiment_date': '2024-01-15',
            'beamline': 'BL12',
            'concentration': 5.0,
            'molecular_weight': 50.0,
            'exposure_time': 1.0,
            'number_of_frames': 10
        }
        
        sample, instrument = collector.collect_from_data(data)
        
        assert sample.experiment_date == '2024-01-15'
        assert sample.beamline_instrument == 'BL12'
        assert sample.concentration == 5.0
        assert sample.experimental_molecular_weight == 50.0
        assert sample.exposure_time == 1.0
        assert sample.number_of_frames == 10

    def test_collect_from_data_with_source(self, collector):
        """Test collecting data with source information"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        source = MagicMock()
        source.wavelength = 1.54  # Angstrom
        data.source = source
        
        sample, instrument = collector.collect_from_data(data)
        
        # Wavelength should be converted from Angstrom to nm
        assert sample.wavelength is not None
        assert sample.wavelength < 1.54  # Should be converted

    def test_collect_from_data_with_detector(self, collector):
        """Test collecting data with detector information"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        detector = MagicMock()
        detector.distance = 2000  # mm
        pixel_size = MagicMock()
        pixel_size.x = 0.172  # mm
        detector.pixel_size = pixel_size
        data.detector = [detector]
        
        sample, instrument = collector.collect_from_data(data)
        
        # Distance should be converted from mm to m
        assert sample.sample_detector_distance == 2.0

    def test_collect_from_data_with_sample_temperature(self, collector):
        """Test collecting data with sample temperature"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        sample_obj = MagicMock()
        sample_obj.temperature = 298.15  # Kelvin
        data.sample = sample_obj
        
        sample, instrument = collector.collect_from_data(data)
        
        # Temperature should be converted from Kelvin to Celsius
        assert sample.cell_temperature is not None
        assert abs(sample.cell_temperature - 25.0) < 1.0

    def test_collect_from_data_with_instrument_string(self, collector):
        """Test collecting data with instrument string"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        data.instrument = "BL12 - ESRF"
        
        sample, instrument = collector.collect_from_data(data)
        
        assert sample.beamline_instrument == "BL12 - ESRF"

    def test_collect_instrument_from_data(self, collector):
        """Test collecting instrument information"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        data.instrument = "BL12"
        
        source = MagicMock()
        source.radiation = "X-ray synchrotron"
        source.name = "ESRF"
        data.source = source
        
        detector = MagicMock()
        pixel_size = MagicMock()
        pixel_size.x = 0.172
        detector.pixel_size = pixel_size
        detector.name = "Pilatus"
        data.detector = [detector]
        
        data.meta_data = {
            'city': 'Grenoble',
            'country': 'France'
        }
        
        instrument = collector.collect_instrument_from_data(data)
        
        assert instrument is not None
        assert instrument.beamline_name == "BL12"
        assert instrument.source_type == "X-ray synchrotron"
        assert instrument.synchrotron_name == "ESRF"
        assert instrument.detector_manufacturer == "Pilatus"
        assert instrument.city == "Grenoble"
        assert instrument.country == "France"

    def test_collect_instrument_from_data_no_data(self, collector):
        """Test collecting instrument information when no data available"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        
        instrument = collector.collect_instrument_from_data(data)
        
        assert instrument is None

    def test_collect_from_fit(self, collector):
        """Test collecting fit information"""
        fit_data = {
            'chi2': 1.5,
            'cormap_pvalue': 0.05
        }
        model_name = "sphere"
        optimizer_name = "Levenberg-Marquardt"
        model_parameters = [
            [True, 'radius', 10.0, '', [True, 0.5], '', '', 'nm'],
            [True, 'sld', 1.0e-6, '', [True, 0.1e-6], '', '', '1/A^2']
        ]
        
        fit = collector.collect_from_fit(fit_data, model_name, optimizer_name, model_parameters)
        
        assert isinstance(fit, SASBDBFit)
        assert fit.software == "SasView"
        assert fit.chi_squared == 1.5
        assert fit.cormap_pvalue == 0.05
        assert len(fit.models) == 1
        
        model = fit.models[0]
        assert model.software_or_db == "sphere"
        assert model.log is not None
        assert "radius" in model.log
        assert "sld" in model.log

    def test_collect_from_fit_zero_cormap_pvalue(self, collector):
        """Test collecting fit information with zero CorMap p-value"""
        fit_data = {
            'chi2': 1.5,
            'cormap_pvalue': 0.0  # Valid zero value
        }
        
        fit = collector.collect_from_fit(fit_data)
        
        assert fit.cormap_pvalue == 0.0

    def test_collect_from_data_angular_units_detection(self, collector):
        """Test detection of angular units from various formats"""
        # Test 1/A format
        data1 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data1._xunit = "1/A"
        sample1, _ = collector.collect_from_data(data1)
        assert sample1.angular_units == "1/A"
        
        # Test 1/nm format
        data2 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data2._xunit = "1/nm"
        sample2, _ = collector.collect_from_data(data2)
        assert sample2.angular_units == "1/nm"
        
        # Test arbitrary format
        data3 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data3._xunit = "arbitrary"
        sample3, _ = collector.collect_from_data(data3)
        assert sample3.angular_units == "arbitrary"
        
        # Test no unit attribute
        data4 = Data1D(x=[0.01, 0.02], y=[100, 50])
        sample4, _ = collector.collect_from_data(data4)
        assert sample4.angular_units == "arbitrary"

    def test_collect_from_data_intensity_units_detection(self, collector):
        """Test detection of intensity units"""
        # Test 1/cm format
        data1 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data1._yunit = "1/cm"
        sample1, _ = collector.collect_from_data(data1)
        assert sample1.intensity_units == "1/cm"
        
        # Test arbitrary format
        data2 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data2._yunit = "arbitrary"
        sample2, _ = collector.collect_from_data(data2)
        assert sample2.intensity_units == "arbitrary"

    def test_collect_from_data_wavelength_conversion(self, collector):
        """Test wavelength conversion from Angstrom to nm"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        source = MagicMock()
        source.wavelength = 1.54  # Angstrom (typical X-ray)
        data.source = source
        
        sample, _ = collector.collect_from_data(data)
        
        # Should convert from Angstrom to nm (divide by 10)
        assert sample.wavelength is not None
        assert abs(sample.wavelength - 0.154) < 0.001
        
        # Test wavelength already in nm (small value)
        source2 = MagicMock()
        source2.wavelength = 0.154  # Already in nm
        data2 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data2.source = source2
        
        sample2, _ = collector.collect_from_data(data2)
        assert abs(sample2.wavelength - 0.154) < 0.001

    def test_collect_from_data_temperature_conversion(self, collector):
        """Test temperature conversion from Kelvin to Celsius"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        sample_obj = MagicMock()
        sample_obj.temperature = 298.15  # Kelvin
        data.sample = sample_obj
        
        sample, _ = collector.collect_from_data(data)
        
        # Should convert from Kelvin to Celsius
        assert sample.cell_temperature is not None
        assert abs(sample.cell_temperature - 25.0) < 0.1
        
        # Test temperature already in Celsius
        sample_obj2 = MagicMock()
        sample_obj2.temperature = 25.0  # Already Celsius
        data2 = Data1D(x=[0.01, 0.02], y=[100, 50])
        data2.sample = sample_obj2
        
        sample2, _ = collector.collect_from_data(data2)
        assert abs(sample2.cell_temperature - 25.0) < 0.1

    def test_collect_from_data_detector_distance_conversion(self, collector):
        """Test detector distance conversion from mm to m"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        detector = MagicMock()
        detector.distance = 2000  # mm
        data.detector = [detector]
        
        sample, _ = collector.collect_from_data(data)
        
        # Should convert from mm to m
        assert sample.sample_detector_distance == 2.0

    def test_collect_from_data_metadata_variations(self, collector):
        """Test collecting metadata with various key names"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        
        # Test 'date' instead of 'experiment_date'
        data.meta_data = {'date': '2024-01-15'}
        sample1, _ = collector.collect_from_data(data)
        assert sample1.experiment_date == '2024-01-15'
        
        # Test 'instrument' instead of 'beamline'
        data.meta_data = {'instrument': 'BL12'}
        sample2, _ = collector.collect_from_data(data)
        assert sample2.beamline_instrument == 'BL12'
        
        # Test 'mw' instead of 'molecular_weight'
        data.meta_data = {'mw': 50.0}
        sample3, _ = collector.collect_from_data(data)
        assert sample3.experimental_molecular_weight == 50.0
        
        # Test 'frames' instead of 'number_of_frames'
        data.meta_data = {'frames': 10}
        sample4, _ = collector.collect_from_data(data)
        assert sample4.number_of_frames == 10

    def test_collect_from_data_metadata_error_handling(self, collector):
        """Test error handling for invalid metadata values"""
        data = Data1D(x=[0.01, 0.02], y=[100, 50])
        
        # Test invalid concentration (should not crash)
        data.meta_data = {'concentration': 'invalid'}
        sample, _ = collector.collect_from_data(data)
        assert sample.concentration is None
        
        # Test invalid molecular weight
        data.meta_data = {'molecular_weight': 'invalid'}
        sample2, _ = collector.collect_from_data(data)
        assert sample2.experimental_molecular_weight is None
        
        # Test invalid exposure_time
        data.meta_data = {'exposure_time': 'invalid'}
        sample3, _ = collector.collect_from_data(data)
        assert sample3.exposure_time is None

    def test_collect_from_fit_chi2_variations(self, collector):
        """Test collecting chi-squared with various key names"""
        # Test 'chi2' key
        fit_data1 = {'chi2': 1.5}
        fit1 = collector.collect_from_fit(fit_data1)
        assert fit1.chi_squared == 1.5
        
        # Test 'chi_squared' key
        fit_data2 = {'chi_squared': 2.0}
        fit2 = collector.collect_from_fit(fit_data2)
        assert fit2.chi_squared == 2.0
        
        # Test 'chi2_value' key
        fit_data3 = {'chi2_value': 2.5}
        fit3 = collector.collect_from_fit(fit_data3)
        assert fit3.chi_squared == 2.5

    def test_collect_from_fit_model_parameters_formatting(self, collector):
        """Test formatting of model parameters"""
        fit_data = {'chi2': 1.5}
        model_parameters = [
            [True, 'radius', 10.0, '', [True, 0.5], '', '', 'nm'],
            [True, 'sld', 1.0e-6, '', [False, None], '', '', '1/A^2'],
            [True, 'scale', 1.0, '', [True, 0.1], '', '', '']
        ]
        
        fit = collector.collect_from_fit(fit_data, "sphere", None, model_parameters)
        
        assert len(fit.models) == 1
        model = fit.models[0]
        assert model.log is not None
        assert "radius = 10.0 ± 0.5 nm" in model.log
        assert "sld = 1e-06" in model.log  # No error for this one
        assert "scale = 1.0 ± 0.1" in model.log

    def test_collect_pddf_from_corfunc(self, collector):
        """Test collecting PDDF information"""
        pddf = collector.collect_pddf_from_corfunc(
            dmax=10.0,
            rg=2.5,
            i0=100.0,
            porod_volume=50.0,
            software="ATSAS"
        )
        
        assert isinstance(pddf, SASBDBPDDF)
        assert pddf.dmax == 10.0
        assert pddf.rg == 2.5
        assert pddf.i0 == 100.0
        assert pddf.porod_volume == 50.0
        assert pddf.software == "ATSAS"

    def test_create_default_instrument(self, collector):
        """Test creating default instrument"""
        instrument = collector.create_default_instrument()
        assert isinstance(instrument, SASBDBInstrument)
        assert instrument.source_type == "X-ray synchrotron"

    def test_collect_guinier_from_linear_fit(self, collector):
        """Test collecting Guinier from linear fit"""
        guinier = collector.collect_guinier_from_linear_fit(
            rg=2.5,
            i0=100.0,
            range_start=0.01,
            range_end=0.05
        )
        
        assert isinstance(guinier, SASBDBGuinier)
        assert guinier.rg == 2.5
        assert guinier.i0 == 100.0
        assert guinier.range_start == 0.01
        assert guinier.range_end == 0.05

    @patch('sas.qtgui.Utilities.SASBDB.sasbdb_data_collector.auto_guinier')
    def test_collect_guinier_from_freesas(self, mock_auto_guinier, collector):
        """Test collecting Guinier using FreeSAS"""
        # Mock FreeSAS auto_guinier result
        mock_result = MagicMock()
        mock_result.Rg = 2.5
        mock_result.sigma_Rg = 0.1
        mock_result.I0 = 100.0
        mock_result.start_point = 5
        mock_result.end_point = 15
        mock_auto_guinier.return_value = mock_result
        
        data = Data1D(x=np.linspace(0.01, 0.1, 20), y=np.ones(20) * 100)
        data.dy = np.ones(20) * 5
        data._xunit = "1/A"
        
        guinier = collector.collect_guinier_from_freesas(data)
        
        assert guinier is not None
        assert isinstance(guinier, SASBDBGuinier)
        assert guinier.rg == 2.5
        assert guinier.rg_error == 0.1
        assert guinier.i0 == 100.0

    def test_collect_guinier_from_freesas_no_freesas(self, collector):
        """Test collecting Guinier when FreeSAS is not available"""
        with patch('sas.qtgui.Utilities.SASBDB.sasbdb_data_collector.auto_guinier', side_effect=ImportError()):
            data = Data1D(x=[0.01, 0.02], y=[100, 50])
            guinier = collector.collect_guinier_from_freesas(data)
            assert guinier is None

    def test_collect_guinier_from_freesas_invalid_data(self, collector):
        """Test collecting Guinier with invalid data"""
        data = Data1D(x=[], y=[])  # Empty data
        guinier = collector.collect_guinier_from_freesas(data)
        assert guinier is None

    def test_create_default_project(self, collector):
        """Test creating default project"""
        project = collector.create_default_project()
        assert isinstance(project, SASBDBProject)
        assert project.published is False
        assert project.project_title is not None

    def test_create_default_molecule(self, collector):
        """Test creating default molecule"""
        molecule = collector.create_default_molecule()
        assert isinstance(molecule, SASBDBMolecule)
        assert molecule.type is not None

    def test_create_default_buffer(self, collector):
        """Test creating default buffer"""
        buffer = collector.create_default_buffer()
        assert isinstance(buffer, SASBDBBuffer)
        assert buffer.description is not None


class TestSASBDBExporter:
    """Test SASBDBExporter"""

    @pytest.fixture
    def export_data(self):
        """Create sample export data"""
        project = SASBDBProject(
            published=False,
            project_title="Test Project"
        )
        
        molecule = SASBDBMolecule(
            type="Protein",
            long_name="Test Protein",
            fasta_sequence="MKTAYIAKQR",
            monomer_mw_kda=10.5,
            number_of_molecules=1
        )
        
        buffer = SASBDBBuffer(
            description="PBS buffer",
            ph=7.4
        )
        
        guinier = SASBDBGuinier(
            rg=2.5,
            rg_error=0.1,
            i0=100.0
        )
        
        instrument = SASBDBInstrument(
            source_type="X-ray synchrotron",
            beamline_name="BL12",
            synchrotron_name="ESRF",
            detector_manufacturer="Pilatus",
            detector_resolution="0.172 mm",
            city="Grenoble",
            country="France"
        )
        
        model = SASBDBModel(
            software_or_db="SasView",
            software_version="6.0.0",
            model_data="model.dat"
        )
        
        fit = SASBDBFit(
            software="SasView",
            software_version="6.0.0",
            chi_squared=1.5,
            cormap_pvalue=0.05,
            angular_units="1/A"
        )
        fit.models.append(model)
        
        sample = SASBDBSample(
            sample_title="Test Sample",
            molecule=molecule,
            buffer=buffer,
            guinier=guinier,
            angular_units="1/A",
            intensity_units="1/cm",
            experimental_molecular_weight=50.0,
            experiment_date="2024-01-15",
            beamline_instrument="BL12"
        )
        sample.fits.append(fit)
        
        export_data = SASBDBExportData()
        export_data.project = project
        export_data.samples.append(sample)
        export_data.instruments.append(instrument)
        
        return export_data

    def test_exporter_initialization(self, export_data):
        """Test exporter initialization"""
        exporter = SASBDBExporter(export_data)
        assert exporter.export_data == export_data

    def test_to_dict(self, export_data):
        """Test converting export data to dictionary"""
        exporter = SASBDBExporter(export_data)
        result = exporter.to_dict()
        
        assert isinstance(result, dict)
        assert 'project' in result
        assert 'samples' in result
        assert 'instruments' in result
        assert len(result['samples']) == 1
        assert len(result['instruments']) == 1
        
        sample_dict = result['samples'][0]
        assert sample_dict['sample_title'] == "Test Sample"
        assert 'molecule' in sample_dict
        assert 'buffer' in sample_dict
        assert 'guinier' in sample_dict
        assert len(sample_dict['fits']) == 1
        
        fit_dict = sample_dict['fits'][0]
        assert fit_dict['chi_squared'] == 1.5
        assert fit_dict['cormap_pvalue'] == 0.05
        assert len(fit_dict['models']) == 1

    def test_to_dict_empty_data(self):
        """Test converting empty export data to dictionary"""
        export_data = SASBDBExportData()
        exporter = SASBDBExporter(export_data)
        result = exporter.to_dict()
        
        assert isinstance(result, dict)
        assert 'samples' in result
        assert 'instruments' in result
        assert result['samples'] == []
        assert result['instruments'] == []

    def test_export_to_json(self, export_data):
        """Test exporting to JSON file"""
        exporter = SASBDBExporter(export_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            success = exporter.export_to_json(filepath)
            assert success is True
            
            # Verify file was created and contains valid JSON
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert 'project' in data
            assert 'samples' in data
            assert 'instruments' in data
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_to_json_removes_none_values(self, export_data):
        """Test that None values are removed from JSON export"""
        # Create export data with some None values
        export_data.project.pubmed_pmid = None
        export_data.samples[0].description = None
        
        exporter = SASBDBExporter(export_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            exporter.export_to_json(filepath)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check that None values are not in the JSON
            project_dict = data['project']
            assert 'pubmed_pmid' not in project_dict or project_dict['pubmed_pmid'] is not None
            
            sample_dict = data['samples'][0]
            assert 'description' not in sample_dict or sample_dict['description'] is not None
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_experimental_data_1d(self, export_data):
        """Test exporting experimental data for Data1D"""
        data = Data1D(x=[0.01, 0.02, 0.03], y=[100, 50, 25])
        data.dy = [10, 5, 2.5]
        data.name = "Test Data"
        data.filename = "test.dat"
        
        exporter = SASBDBExporter(export_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            filepath = f.name
        
        try:
            success = exporter.export_experimental_data(data, filepath)
            assert success is True
            
            # Verify file was created and contains data
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                content = f.read()
            
            assert "SASBDB Experimental Data Export" in content
            assert "Test Data" in content
            assert "test.dat" in content
            assert "Q\tI\tdI" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_experimental_data_2d(self, export_data):
        """Test exporting experimental data for Data2D"""
        data = Data2D()
        data.qx_data = np.array([0.01, 0.02])
        data.qy_data = np.array([0.01, 0.02])
        data.data = np.array([100, 50])
        data.err_data = np.array([10, 5])
        data.name = "Test Data 2D"
        data.filename = "test2d.dat"
        
        exporter = SASBDBExporter(export_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            filepath = f.name
        
        try:
            success = exporter.export_experimental_data(data, filepath)
            assert success is True
            
            # Verify file was created
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                content = f.read()
            
            assert "SASBDB Experimental Data Export" in content
            assert "Qx\tQy\tI\tdI" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_experimental_data_error(self, export_data):
        """Test exporting experimental data with error"""
        exporter = SASBDBExporter(export_data)
        
        # Pass invalid data object
        invalid_data = "not a data object"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            filepath = f.name
        
        try:
            success = exporter.export_experimental_data(invalid_data, filepath)
            assert success is False
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_remove_none_values(self, export_data):
        """Test removing None values from dictionary"""
        exporter = SASBDBExporter(export_data)
        
        test_dict = {
            'key1': 'value1',
            'key2': None,
            'key3': {
                'nested_key1': 'nested_value',
                'nested_key2': None
            },
            'key4': [1, 2, None, 4],
            'key5': []
        }
        
        cleaned = exporter._remove_none_values(test_dict)
        
        assert 'key1' in cleaned
        assert 'key2' not in cleaned
        assert 'key3' in cleaned
        assert 'nested_key2' not in cleaned['key3']
        assert None not in cleaned['key4']
        assert 'key5' not in cleaned  # Empty list should be removed


class TestSASBDBIntegration:
    """Integration tests for SASBDB functionality"""

    def test_full_collection_and_export(self):
        """Test full workflow: collect data, create export, and export to JSON"""
        # Create test data
        data = Data1D(x=np.linspace(0.01, 0.1, 20), y=np.ones(20) * 100)
        data.name = "Integration Test Data"
        data.filename = "integration_test.dat"
        data._xunit = "1/A"
        data._yunit = "1/cm"
        data.meta_data = {
            'experiment_date': '2024-01-15',
            'beamline': 'BL12',
            'concentration': 5.0,
            'molecular_weight': 50.0
        }
        
        # Collect data
        collector = SASBDBDataCollector()
        sample, instrument = collector.collect_from_data(data)
        sample.molecule = collector.create_default_molecule()
        sample.buffer = collector.create_default_buffer()
        
        export_data = collector.export_data
        export_data.project = collector.create_default_project()
        export_data.samples.append(sample)
        if instrument:
            export_data.instruments.append(instrument)
        
        # Create fit
        fit_data = {'chi2': 1.5, 'cormap_pvalue': 0.05}
        fit = collector.collect_from_fit(fit_data, "sphere", "Levenberg-Marquardt")
        sample.fits.append(fit)
        
        # Export to JSON
        exporter = SASBDBExporter(export_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            success = exporter.export_to_json(filepath)
            assert success is True
            
            # Verify JSON structure
            with open(filepath, 'r') as f:
                json_data = json.load(f)
            
            assert 'project' in json_data
            assert len(json_data['samples']) == 1
            assert json_data['samples'][0]['sample_title'] == "Integration Test Data"
            assert len(json_data['samples'][0]['fits']) == 1
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

