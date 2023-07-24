# Create your tests here.
from django.test import TestCase
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient, force_authenticate, APITestCase

from sasmodels.data import empty_data1D
from sasdata.dataloader.loader import Loader
import numpy as np

from data.models import Data
from .models import (
    Fit,
    FitParameter
)
from .views import (
    start,
    start_fit,
)

factory = APIRequestFactory()

# Create your tests here.
class TestLists(APITestCase):
    def setUp(self):
        public_test_data = Data.objects.create(id = 1, file = "cyl_400_20.txt", is_public = True)
        self.user = User.objects.create_user(username="testUser", password="secret", id = 2)
        private_test_data = Data.objects.create(id = 3, current_user = self.user, file = "another.txt", is_public = False)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    #working
    def get_model_list(self):
        request = self.client.post('/v1/analyze/fit/models/')
        self.assertEqual(request.data, {"all models":['adsorbed_layer', 'barbell', 'bcc_paracrystal', 'be_polyelectrolyte', 'binary_hard_sphere', 'broad_peak', 'capped_cylinder', 'core_multi_shell', 'core_shell_bicelle', 'core_shell_bicelle_elliptical', 'core_shell_bicelle_elliptical_belt_rough', 'core_shell_cylinder', 'core_shell_ellipsoid', 'core_shell_parallelepiped', 'core_shell_sphere', 'correlation_length', 'cylinder', 'dab', 'ellipsoid', 'elliptical_cylinder', 'fcc_paracrystal', 'flexible_cylinder', 'flexible_cylinder_elliptical', 'fractal', 'fractal_core_shell', 'fuzzy_sphere', 'gauss_lorentz_gel', 'gaussian_peak', 'gel_fit', 'guinier', 'guinier_porod', 'hardsphere', 'hayter_msa', 'hollow_cylinder', 'hollow_rectangular_prism', 'hollow_rectangular_prism_thin_walls', 'lamellar', 'lamellar_hg', 'lamellar_hg_stack_caille', 'lamellar_stack_caille', 'lamellar_stack_paracrystal', 'line', 'linear_pearls', 'lorentz', 'mass_fractal', 'mass_surface_fractal', 'mono_gauss_coil', 'multilayer_vesicle', 'onion', 'parallelepiped', 'peak_lorentz', 'pearl_necklace', 'poly_gauss_coil', 'polymer_excl_volume', 'polymer_micelle', 'porod', 'power_law', 'pringle', 'raspberry', 'rectangular_prism', 'rpa', 'sc_paracrystal', 'sphere', 'spherical_sld', 'spinodal', 'squarewell', 'stacked_disks', 'star_polymer', 'stickyhardsphere', 'superball', 'surface_fractal', 'teubner_strey', 'triaxial_ellipsoid', 'two_lorentzian', 'two_power_law', 'unified_power_Rg', 'vesicle']})
    
    #working
    def get_model_list_category(self):
        data = {
            "category":"Cylinder"
        }
        request = self.client.post('/v1/analyze/fit/models/', data, format='json')
        self.assertEqual(request.data, {"Cylinder models":[['barbell', True], ['capped_cylinder', True], ['core_shell_bicelle', True], ['core_shell_bicelle_elliptical', True], ['core_shell_bicelle_elliptical_belt_rough', True], ['core_shell_cylinder', True], ['cylinder', True], ['elliptical_cylinder', True], ['flexible_cylinder', True], ['flexible_cylinder_elliptical', True], ['hollow_cylinder', True], ['pearl_necklace', True], ['pringle', True], ['stacked_disks', True]]})

    #working
    def get_model_list_kind(self):
        data = {
            "kind":"py"
        }
        request = self.client.post('/v1/analyze/fit/models/', data, format='json')
        self.assertEqual(request.data, {"py models":['adsorbed_layer', 'be_polyelectrolyte', 'broad_peak', 'correlation_length', 'gauss_lorentz_gel', 'guinier_porod', 'line', 'peak_lorentz', 'poly_gauss_coil', 'polymer_excl_volume', 'porod', 'power_law', 'spinodal', 'teubner_strey', 'two_lorentzian', 'two_power_law', 'unified_power_Rg']})

    def get_optimizer_list(self):
        request = self.client.get('/v1/analyze/fit/optimizers/')
        self.assertEqual(request.data, {"public_file_ids":1})

class TestFitStart(TestCase):
    def setUp(self):
        public_test_data = Data.objects.create(id = 1, file = "cyl_400_20.txt", is_public = True)
        self.user = User.objects.create_user(username="testUser", password="secret", id = 2)
        private_test_data = Data.objects.create(id = 3, current_user = self.user, file = "another.txt", is_public = False)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    fixtures = ['data/fixtures/example_data.json',]
    def can_fit_start_give_correct_answer(self):
        pars_limit = { 
                        "radius":{
                            "lower_limit":1,
                            "upper_limit":50
                        },
                        "length":{
                            "lower_limit":1,
                            "upper_limit":500
                        },
        }
        params = dict(
            radius = 35,
            length = 350,
            background = 0.0,
            scale = 1.0,
            sld = 4.0,
            sld_solvent = 1.0
        )
        data = Data.objects.get(is_public = True)
        chisq = start_fit("cylinder", params=params)
        self.assertEqual(chisq, "0.03(13)")

class TestLoader(TestCase):
    fixtures = ['data/fixtures/example_data.json',]

    def testing_loader(self):
        test_data = get_object_or_404(Data, is_public=True)
        loader = Loader()
        loader.load(test_data.file.path)
