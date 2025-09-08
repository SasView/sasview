# Create your tests here.
import json
import shutil

from data.models import Data
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from sasdata.dataloader.loader import Loader

from .views import (
    start_fit,
)

factory = APIRequestFactory()

# Create your tests here.
class TestLists(APITestCase):
    """def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="secret", id = 2)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)"""

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
        self.assertEqual(request.data, {"optimizers": [['amoeba', 'de', 'dream', 'newton', 'scipy.leastsq', 'lm']]})


class TestFitStart(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="secret", id = 1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.public_test_data = Data.objects.create(id = 2, file_name = "cyl_400_20.txt", is_public = True)
        self.public_test_data.file.save("cyl_400_20.txt", open(r"../src/sas/example_data/1d_data/cyl_400_20.txt"))

        #self.private_test_data = Data.objects.create(id = 3, current_user = self.user, file_name = "another.txt", is_public = False)
        #self.private_test_data.file.save("another.txt",open(r""))

        """self.fit = Fit.objects.create(id = 4, current_user = self.user, data_id = self.public_test_data, model = "cylinder", optimizer = "amoeba")
        self.radius = FitParameter.objects.create(id = 5, base_id = self.fit, name = "radius", value = 35, data_type = "int", lower_limit = 1, upper_limit = 50)
        self.length = FitParameter.objects.create(id = 6, base_id = self.fit, name = "length", value = 350, data_type = "int", lower_limit = 1, upper_limit = 500)
        self.background = FitParameter.objects.create(id = 7, base_id = self.fit, name = "background", value = 0.0, data_type = "float")
        self.scale = FitParameter.objects.create(id = 8, base_id = self.fit, name = "scale", value = 1.0, data_type = "float")
        self.sld = FitParameter.objects.create(id = 9, base_id = self.fit, name = "sld", value = 4.0, data_type = "float")
        self.sld_solvent = FitParameter.objects.create(id = 10, base_id = self.fit, name = "sld_solvent", value = 1.0, data_type = "float")
        self.all_params = [self.radius, self.length, self.background, self.scale, self.sld, self.sld_solvent]"""

    def test_can_fit_start_give_correct_answer(self):
        data = Data.objects.get(is_public = True)
        chisq = start_fit(fit_db=self.fit, par_dbs=self.all_params)
        self.assertEqual(chisq,"0.03(13)")

    def test_can_fit_give_right_answer(self):
        data = {
            "model":"cylinder",
            "data_id":2,
            "optimizer":"amoeba",
            "parameters" :
            [
                {
                    "name":"radius",
                    "value":35,
                    "data_type":"int",
                    "lower_limit":1,
                    "upper_limit":50
                },
                {
                    "name":"length",
                    "value":350,
                    "data_type":"int",
                    "lower_limit":1,
                    "upper_limit":500
                },
                {
                    "name":"background",
                    "value":0.0,
                    "data_type":"float"
                },
                {
                    "name":"scale",
                    "value":1.0,
                    "data_type":"float"
                },
                {
                    "name":"sld",
                    "value":4.0,
                    "data_type":"float"
                },
                {
                    "name":"sld_solvent",
                    "value":1.0,
                    "data_type":"float"
                }
            ]
        }
        request = self.client.post('/v1/analyze/fit/', data=json.dumps(data), content_type="application/json")
        self.assertEqual(request.data,{'authenticated': True, 'fit_id': 1, 'results': '0.03(13)'})

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)

class TestLoader(TestCase):

    def testing_loader(self):
        test_data = get_object_or_404(Data, is_public=True)
        loader = Loader()
        loader.load(test_data.file.path)

    def testing_syntax(self):
        test_data = Data.objects.create(id = 2, is_public = True)
        self.assertEqual("cyl_400_20.txt",test_data.current_user)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)
