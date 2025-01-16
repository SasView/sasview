# Available perspectives.
# When adding a new perspective, this dictionary needs to be updated

from .Fitting.FittingPerspective import FittingWindow
from .Invariant.InvariantPerspective import InvariantWindow
from .Inversion.InversionPerspective import InversionWindow
from .Corfunc.CorfuncPerspective import CorfuncWindow

PERSPECTIVES = {
    FittingWindow.name: FittingWindow,
    InvariantWindow.name: InvariantWindow,
    InversionWindow.name: InversionWindow,
    CorfuncWindow.name: CorfuncWindow,
}