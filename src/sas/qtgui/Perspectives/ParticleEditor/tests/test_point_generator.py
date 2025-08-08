
from pytest import mark

from sas.qtgui.Perspectives.ParticleEditor.sampling.points import Grid, PointGeneratorStepper, RandomCube


@mark.parametrize("splits", [42, 100, 381,999])
@mark.parametrize("npoints", [100,1000,8001])
def test_with_grid(npoints, splits):
    point_generator = Grid(100, npoints)
    n_measured = 0
    for x, y, z in PointGeneratorStepper(point_generator, splits):
        n_measured += len(x)

    assert n_measured == point_generator.n_points # desired points may not be the same as n_points

@mark.parametrize("splits", [42, 100, 381, 999])
@mark.parametrize("npoints", [100, 1000, 8001])
def test_with_random_cube(npoints, splits):
    point_generator = RandomCube(100, npoints)
    n_measured = 0
    for x, y, z in PointGeneratorStepper(point_generator, splits):
        n_measured += len(x)

    assert n_measured == npoints



