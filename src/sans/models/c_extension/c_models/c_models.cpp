/** c_models
 *
 * Module containing all SANS model extensions
 *
 * @author   M.Doucet / UTK
 */
#include <Python.h>
#include <parameters.hh>
#define PY_ARRAY_UNIQUE_SYMBOL PyArray_API_sans
#include "arrayobject.h"


 // adding generated code 
void addCLinearPearlsModel(PyObject *module); 
void addCRaspBerryModel(PyObject *module); 
void addCCore2ndMomentModel(PyObject *module); 
void addCStackedDisksModel(PyObject *module); 
void addCCoreShellCylinderModel(PyObject *module); 
void addCReflModel(PyObject *module); 
void addCSphereSLDModel(PyObject *module); 
void addCFractalModel(PyObject *module); 
void addCLogNormal(PyObject *module); 
void addCPringlesModel(PyObject *module); 
void addCCappedCylinderModel(PyObject *module); 
void addCLorentzian(PyObject *module); 
void addCBCCrystalModel(PyObject *module); 
void addCPearlNecklaceModel(PyObject *module); 
void addCSCCrystalModel(PyObject *module); 
void addCGaussian(PyObject *module); 
void addCLamellarModel(PyObject *module); 
void addCLamellarPCrystalModel(PyObject *module); 
void addCMassFractalModel(PyObject *module); 
void addCPoly_GaussCoil(PyObject *module); 
void addCTeubnerStreyModel(PyObject *module); 
void addCOnionModel(PyObject *module); 
void addCHollowCylinderModel(PyObject *module); 
void addCTriaxialEllipsoidModel(PyObject *module); 
void addCEllipticalCylinderModel(PyObject *module); 
void addCSchulz(PyObject *module); 
void addCLamellarPSHGModel(PyObject *module); 
void addCDABModel(PyObject *module); 
void addCStarPolymer(PyObject *module); 
void addCFuzzySphereModel(PyObject *module); 
void addCParallelepipedModel(PyObject *module); 
void addCMassSurfaceFractal(PyObject *module); 
void addCVesicleModel(PyObject *module); 
void addCGelFitModel(PyObject *module); 
void addCCoreShellEllipsoidModel(PyObject *module); 
void addCRPAModel(PyObject *module); 
void addCHayterMSAStructure(PyObject *module); 
void addCCSParallelepipedModel(PyObject *module); 
void addCFractalO_Z(PyObject *module); 
void addCMultiShellModel(PyObject *module); 
void addCLamellarPSModel(PyObject *module); 
void addCEllipsoidModel(PyObject *module); 
void addCTwoYukawaModel(PyObject *module); 
void addCDiamEllipFunc(PyObject *module); 
void addCHardsphereStructure(PyObject *module); 
void addCLamellarFFHGModel(PyObject *module); 
void addCCoreShellBicelleModel(PyObject *module); 
void addCFCCrystalModel(PyObject *module); 
void addCFlexibleCylinderModel(PyObject *module); 
void addCSurfaceFractalModel(PyObject *module); 
void addCDiamCylFunc(PyObject *module); 
void addCCoreFourShellModel(PyObject *module); 
void addCStickyHSStructure(PyObject *module); 
void addCReflAdvModel(PyObject *module); 
void addCSphereModel(PyObject *module); 
void addCFlexCylEllipXModel(PyObject *module); 
void addCSquareWellStructure(PyObject *module); 
void addCSLDCalFunc(PyObject *module); 
void addCCoreShellModel(PyObject *module); 
void addCBarBellModel(PyObject *module); 
void addCBinaryHSModel(PyObject *module); 
void addCCylinderModel(PyObject *module); 
 // end generated code 



extern "C" {
  void addDisperser(PyObject *module);
}

/**
 * Delete a dispersion model object
 */
void del_dispersion_model(void *ptr){
  DispersionModel * disp = static_cast<DispersionModel *>(ptr);
  delete disp;
  return;
}

/**
 * Create a dispersion model as a python object
 */
PyObject * new_dispersion_model(PyObject *, PyObject *args) {
  DispersionModel *disp = new DispersionModel();
  return PyCObject_FromVoidPtr(disp, del_dispersion_model);
}


/**
 * Delete a lognormal dispersion model object
 */
void del_lognormal_dispersion(void *ptr){
  LogNormalDispersion * disp = static_cast<LogNormalDispersion *>(ptr);
  delete disp;
  return;
}

/**
 * Create a lognormal dispersion model as a python object
 */
PyObject * new_lognormal_dispersion(PyObject *, PyObject *args) {
  LogNormalDispersion *disp = new LogNormalDispersion();
  return PyCObject_FromVoidPtr(disp, del_lognormal_dispersion);
}

/**
 * Delete a gaussian dispersion model object
 */
void del_gaussian_dispersion(void *ptr){
  GaussianDispersion * disp = static_cast<GaussianDispersion *>(ptr);
  delete disp;
  return;
}

/**
 * Create a gaussian dispersion model as a python object
 */
PyObject * new_gaussian_dispersion(PyObject *, PyObject *args) {
  GaussianDispersion *disp = new GaussianDispersion();
  return PyCObject_FromVoidPtr(disp, del_gaussian_dispersion);
}


/**
 * Delete a rectangle dispersion model object
 */
void del_rectangle_dispersion(void *ptr){
  RectangleDispersion * disp = static_cast<RectangleDispersion *>(ptr);
  delete disp;
  return;
}

/**
 * Create a rectangle dispersion model as a python object
 */
PyObject * new_rectangle_dispersion(PyObject *, PyObject *args) {
  RectangleDispersion *disp = new RectangleDispersion();
  return PyCObject_FromVoidPtr(disp, del_rectangle_dispersion);
}


/**
 * Delete a schulz dispersion model object
 */
void del_schulz_dispersion(void *ptr){
  SchulzDispersion * disp = static_cast<SchulzDispersion *>(ptr);
  delete disp;
  return;
}
/**
 * Create a schulz dispersion model as a python object
 */
PyObject * new_schulz_dispersion(PyObject *, PyObject *args) {
  SchulzDispersion *disp = new SchulzDispersion();
  return PyCObject_FromVoidPtr(disp, del_schulz_dispersion);
}


/**
 * Delete an array dispersion model object
 */
void del_array_dispersion(void *ptr){
  ArrayDispersion * disp = static_cast<ArrayDispersion *>(ptr);
  delete disp;
  return;
}

/**
 * Create an array dispersion model as a python object
 */
PyObject * new_array_dispersion(PyObject *, PyObject *args) {
  ArrayDispersion *disp = new ArrayDispersion();
  return PyCObject_FromVoidPtr(disp, del_array_dispersion);
}

#define INVECTOR(obj,buf,len)										\
    do { \
      int err = PyObject_AsReadBuffer(obj, (const void **)(&buf), &len); \
      if (err < 0) return NULL; \
      len /= sizeof(*buf); \
    } while (0)

/**
 * Sets weights from a numpy array
 */
PyObject * set_weights(PyObject *, PyObject *args) {
  PyObject *val_obj;
  PyObject *wei_obj;
  PyObject *disp;
  Py_ssize_t nval;
  Py_ssize_t nwei;
  double *values;
  double *weights;
  //int i;

  if (!PyArg_ParseTuple(args, "OOO", &disp, &val_obj, &wei_obj)) return NULL;
  INVECTOR(val_obj, values, nval);
  INVECTOR(wei_obj, weights, nwei);

  // Sanity check
  if(nval!=nwei) return NULL;

  // Set the array pointers
  void *temp = PyCObject_AsVoidPtr(disp);
  DispersionModel * dispersion = static_cast<DispersionModel *>(temp);
  dispersion->set_weights(nval, values, weights);

  return Py_BuildValue("i",1);
}



/**
 * Define empty module
 */
static PyMethodDef module_methods[] = {
    {"new_dispersion_model", (PyCFunction)new_dispersion_model     , METH_VARARGS,
        "Create a new DispersionModel object"},
        {"new_gaussian_model",   (PyCFunction)new_gaussian_dispersion, METH_VARARGS,
            "Create a new GaussianDispersion object"},
            {"new_rectangle_model",   (PyCFunction)new_rectangle_dispersion, METH_VARARGS,
                "Create a new RectangleDispersion object"},
                {"new_lognormal_model",   (PyCFunction)new_lognormal_dispersion, METH_VARARGS,
                    "Create a new LogNormalDispersion object"},
                    {"new_schulz_model",   (PyCFunction)new_schulz_dispersion, METH_VARARGS,
                        "Create a new SchulzDispersion object"},
                        {"new_array_model",      (PyCFunction)new_array_dispersion  , METH_VARARGS,
                            "Create a new ArrayDispersion object"},
                            {"set_dispersion_weights",(PyCFunction)set_weights  , METH_VARARGS,
                                "Create the dispersion weight arrays for an Array Dispersion object"},
                                {NULL}
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initc_models(void)
{
  PyObject* m;

  m = Py_InitModule3("c_models", module_methods,
      "C extension module for SANS scattering models.");
  import_array();


 // adding generated code 
addCLinearPearlsModel(m); 
addCRaspBerryModel(m); 
addCCore2ndMomentModel(m); 
addCStackedDisksModel(m); 
addCCoreShellCylinderModel(m); 
addCReflModel(m); 
addCSphereSLDModel(m); 
addCFractalModel(m); 
addCLogNormal(m); 
addCPringlesModel(m); 
addCCappedCylinderModel(m); 
addCLorentzian(m); 
addCBCCrystalModel(m); 
addCPearlNecklaceModel(m); 
addCSCCrystalModel(m); 
addCGaussian(m); 
addCLamellarModel(m); 
addCLamellarPCrystalModel(m); 
addCMassFractalModel(m); 
addCPoly_GaussCoil(m); 
addCTeubnerStreyModel(m); 
addCOnionModel(m); 
addCHollowCylinderModel(m); 
addCTriaxialEllipsoidModel(m); 
addCEllipticalCylinderModel(m); 
addCSchulz(m); 
addCLamellarPSHGModel(m); 
addCDABModel(m); 
addCStarPolymer(m); 
addCFuzzySphereModel(m); 
addCParallelepipedModel(m); 
addCMassSurfaceFractal(m); 
addCVesicleModel(m); 
addCGelFitModel(m); 
addCCoreShellEllipsoidModel(m); 
addCRPAModel(m); 
addCHayterMSAStructure(m); 
addCCSParallelepipedModel(m); 
addCFractalO_Z(m); 
addCMultiShellModel(m); 
addCLamellarPSModel(m); 
addCEllipsoidModel(m); 
addCTwoYukawaModel(m); 
addCDiamEllipFunc(m); 
addCHardsphereStructure(m); 
addCLamellarFFHGModel(m); 
addCCoreShellBicelleModel(m); 
addCFCCrystalModel(m); 
addCFlexibleCylinderModel(m); 
addCSurfaceFractalModel(m); 
addCDiamCylFunc(m); 
addCCoreFourShellModel(m); 
addCStickyHSStructure(m); 
addCReflAdvModel(m); 
addCSphereModel(m); 
addCFlexCylEllipXModel(m); 
addCSquareWellStructure(m); 
addCSLDCalFunc(m); 
addCCoreShellModel(m); 
addCBarBellModel(m); 
addCBinaryHSModel(m); 
addCCylinderModel(m); 
addDisperser(m); 

 // end generated code 

}

