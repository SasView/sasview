# Available perspectives.
# When adding a new perspective, this dictionary needs to be updated

from Fitting.FittingPerspective import FittingWindow
from Invariant.InvariantPerspective import InvariantWindow
from PrInversion.PrInversionPerspective import PrInversionWindow

PERSPECTIVES = {
    FittingWindow.name: FittingWindow,
    InvariantWindow.name: InvariantWindow,
    PrInversionWindow.name: PrInversionWindow,
}