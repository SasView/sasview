import pickle
from sas.models.CylinderModel import CylinderModel
import copy

model = CylinderModel()
model.setParam('cyl_theta', 1.234)
p = copy.deepcopy(model)

assert p.getParam('cyl_theta') == model.getParam('cyl_theta')
