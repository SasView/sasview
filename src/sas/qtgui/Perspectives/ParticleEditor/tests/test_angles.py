import numpy as np
from pytest import mark

from sas.qtgui.Perspectives.ParticleEditor.sampling.geodesic import Geodesic


@mark.parametrize("n_divisions", [1,2,3,4,5])
def test_point_number_prediction(n_divisions):
    """ Geodesic point number function should give the number of points the generating function returns"""
    geodesic_points, _ = Geodesic.by_divisions(n_divisions)

    assert geodesic_points.shape[0] == Geodesic.points_for_division_amount(n_divisions)


@mark.parametrize("n_divisions", [1,2,3,4,5])
def test_inverse_point_calc_exact(n_divisions):
    """ Check the calculation of divisions for point number works, when it is an exact input"""
    assert n_divisions == Geodesic.minimal_divisions_for_points(Geodesic.points_for_division_amount(n_divisions))


@mark.parametrize("n_divisions", [1,2,3,4,5])
def test_inverse_point_calc_minimally_greater(n_divisions):
    """ Check the calculation of divisions rounds correctly (up) when it is one more than an exact input"""
    assert n_divisions + 1 == Geodesic.minimal_divisions_for_points(Geodesic.points_for_division_amount(n_divisions) + 1)


@mark.parametrize("n_divisions", [1,2,3,4,5])
def test_inverse_point_calc_maximally_greater(n_divisions):
    """ Check the calculation of divisions rounds correctly (up) when it is one less than the next exact input"""
    assert n_divisions + 1 == Geodesic.minimal_divisions_for_points(Geodesic.points_for_division_amount(n_divisions + 1) - 1)


@mark.parametrize("vector", [
    [ 1, 2, 3],
    [ 7, 2, 0],
    [-1, 0, 0],
    [ 0, 1, 0],
    [ 0, 0, 1]])
def test_rotation_to_z(vector):
    """ Check the method that rotates vectors to the z axis"""
    m = Geodesic._rotation_matrix_to_z_vector(np.array(vector))

    v_test = np.matmul(m, vector)

    assert np.abs(v_test[0]) < 1e-9
    assert np.abs(v_test[1]) < 1e-9


@mark.parametrize("n_divisions", [1,2,3,4,5,6])
def test_total_weights(n_divisions):
    """ Total weights should add to 4pi"""
    points, weights = Geodesic.by_divisions(n_divisions)

    assert abs(sum(weights) - 4*np.pi) < 1e-9
