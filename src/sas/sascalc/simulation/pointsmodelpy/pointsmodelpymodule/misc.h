#if !defined(pypointsmodelpy_misc_h)
#define pypointsmodelpy_misc_h

// @copyright: University of Tennessee, for the DANSE project
extern char pypointsmodelpy_copyright__name__[];
extern char pypointsmodelpy_copyright__doc__[];
extern "C"
PyObject * pypointsmodelpy_copyright(PyObject *, PyObject *);

// LORESModel constructor LORESModel(double density)
extern char pypointsmodelpy_new_loresmodel__name__[];
extern char pypointsmodelpy_new_loresmodel__doc__[];
extern "C"
PyObject * pypointsmodelpy_new_loresmodel(PyObject *, PyObject *);

//Clean LORESModel constructor memory usage
static void PyDelLores(void *);

//LORESModel methods add(GeoShapes &, double sld)
extern char pypointsmodelpy_lores_add__name__[];
extern char pypointsmodelpy_lores_add__doc__[];
extern "C"
PyObject * pypointsmodelpy_lores_add(PyObject *, PyObject *);

//LORESModel methods GetPoints(vector<Point3D> &)
extern char pypointsmodelpy_get_lorespoints__name__[];
extern char pypointsmodelpy_get_lorespoints__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_lorespoints(PyObject *, PyObject *);

//PDBModel constructor PDBModel()
extern char pypointsmodelpy_new_pdbmodel__name__[];
extern char pypointsmodelpy_new_pdbmodel__doc__[];
extern "C"
PyObject * pypointsmodelpy_new_pdbmodel(PyObject *, PyObject *);

//Clean PDBModel constructor memory usage
static void PyDelPDB(void *);

//PDBModel method AddPDB(string)
extern char pypointsmodelpy_pdbmodel_add__name__[];
extern char pypointsmodelpy_pdbmodel_add__doc__[];
extern "C"
PyObject * pypointsmodelpy_pdbmodel_add(PyObject *, PyObject *);

//PDBModel method GetPoints(Point3DVector &)
extern char pypointsmodelpy_get_pdbpoints__name__[];
extern char pypointsmodelpy_get_pdbpoints__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdbpoints(PyObject *, PyObject *);

//ComplexModel constructor ComplexModel()
extern char pypointsmodelpy_new_complexmodel__name__[];
extern char pypointsmodelpy_new_complexmodel__doc__[];
extern "C"
PyObject * pypointsmodelpy_new_complexmodel(PyObject *, PyObject *);

//Clean Complexodel constructor memory usage
static void PyDelComplex(void *);

//ComplexModel method AddComplex(string)
extern char pypointsmodelpy_complexmodel_add__name__[];
extern char pypointsmodelpy_complexmodel_add__doc__[];
extern "C"
PyObject * pypointsmodelpy_complexmodel_add(PyObject *, PyObject *);

//ComplexModel method GetPoints(Point3DVector &)
extern char pypointsmodelpy_get_complexpoints__name__[];
extern char pypointsmodelpy_get_complexpoints__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complexpoints(PyObject *, PyObject *);

//generate a new vector of points3d
extern char pypointsmodelpy_new_point3dvec__name__[];
extern char pypointsmodelpy_new_point3dvec__doc__[];
extern "C"
PyObject * pypointsmodelpy_new_point3dvec(PyObject *, PyObject *);

//clean new_point3dvec
static void PyDelPoint3DVec(void *);

// method FillPoints(loresmodel, point3dvec)
//extern char pypointsmodelpy_fillpoints__name__[];
//extern char pypointsmodelpy_fillpoints__doc__[];
//extern "C"
//PyObject * pypointsmodelpy_fillpoints(PyObject *, PyObject *);

// LORESModel method distdistribution(point3dvec)
extern char pypointsmodelpy_get_lores_pr__name__[];
extern char pypointsmodelpy_get_lores_pr__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_lores_pr(PyObject *, PyObject *);

// method distdistribution_xy(point3dvec)
extern char pypointsmodelpy_distdistribution_xy__name__[];
extern char pypointsmodelpy_distdistribution_xy__doc__[];
extern "C"
PyObject * pypointsmodelpy_distdistribution_xy(PyObject *, PyObject *);

// PDBModel method distdistribution(point3dvec)
extern char pypointsmodelpy_get_pdb_pr__name__[];
extern char pypointsmodelpy_get_pdb_pr__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdb_pr(PyObject *, PyObject *);

// PDBModel method distdistribution_xy(point3dvec)
extern char pypointsmodelpy_get_pdb_pr_xy__name__[];
extern char pypointsmodelpy_get_pdb_pr_xy__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdb_pr_xy(PyObject *, PyObject *);

// ComplexModel method distdistribution(point3dvec)
extern char pypointsmodelpy_get_complex_pr__name__[];
extern char pypointsmodelpy_get_complex_pr__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_pr(PyObject *, PyObject *);

// LORESModel method calculateIQ(iq)
extern char pypointsmodelpy_get_lores_iq__name__[];
extern char pypointsmodelpy_get_lores_iq__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_lores_iq(PyObject *, PyObject *);

// LORESModel method CalculateIQ(q)
extern char pypointsmodelpy_get_lores_i__name__[];
extern char pypointsmodelpy_get_lores_i__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_lores_i(PyObject *, PyObject *);

// ComplexModel method CalculateIQ(q)
extern char pypointsmodelpy_get_complex_i__name__[];
extern char pypointsmodelpy_get_complex_i__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_i(PyObject *, PyObject *);

// ComplexModel method CalculateIQError(q)
extern char pypointsmodelpy_get_complex_i_error__name__[];
extern char pypointsmodelpy_get_complex_i_error__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_i_error(PyObject *, PyObject *);

// method calculateIQ_2D(iq,theta)
extern char pypointsmodelpy_calculateIQ_2D__name__[];
extern char pypointsmodelpy_calculateIQ_2D__doc__[];
extern "C"
PyObject * pypointsmodelpy_calculateIQ_2D(PyObject *, PyObject *);

// method calculateI_Qxy(Qx,Qy)
extern char pypointsmodelpy_calculateI_Qxy__name__[];
extern char pypointsmodelpy_calculateI_Qxy__doc__[];
extern "C"
PyObject * pypointsmodelpy_calculateI_Qxy(PyObject *, PyObject *);

// method calculateI_Qvxy(points,Qx,Qy)
extern char pypointsmodelpy_calculateI_Qvxy__name__[];
extern char pypointsmodelpy_calculateI_Qvxy__doc__[];
extern "C"
PyObject * pypointsmodelpy_calculateI_Qvxy(PyObject *, PyObject *);

// PDBModel method calculateIQ(iq)
extern char pypointsmodelpy_get_pdb_iq__name__[];
extern char pypointsmodelpy_get_pdb_iq__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdb_iq(PyObject *, PyObject *);

// PDBModel method calculateIQ_2D(qx,qy)
extern char pypointsmodelpy_get_pdb_Iqxy__name__[];
extern char pypointsmodelpy_get_pdb_Iqxy__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdb_Iqxy(PyObject *, PyObject *);

// PDBModel method calculateIQ_2D(pts,qx,qy)
extern char pypointsmodelpy_get_pdb_Iqvxy__name__[];
extern char pypointsmodelpy_get_pdb_Iqvxy__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_pdb_Iqvxy(PyObject *, PyObject *);

// ComplexModel method calculateIQ_2D(pts,qx,qy)
extern char pypointsmodelpy_get_complex_Iqxy__name__[];
extern char pypointsmodelpy_get_complex_Iqxy__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_Iqxy(PyObject *, PyObject *);

// ComplexModel method calculateIQ_2D_Error(pts,qx,qy)
extern char pypointsmodelpy_get_complex_Iqxy_err__name__[];
extern char pypointsmodelpy_get_complex_Iqxy_err__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_Iqxy_err(PyObject *, PyObject *);

// ComplexModel method calculateIQ(iq)
extern char pypointsmodelpy_get_complex_iq__name__[];
extern char pypointsmodelpy_get_complex_iq__doc__[];
extern "C"
PyObject * pypointsmodelpy_get_complex_iq(PyObject *, PyObject *);

// method outputPR
extern char pypointsmodelpy_outputPR__name__[];
extern char pypointsmodelpy_outputPR__doc__[];
extern "C"
PyObject * pypointsmodelpy_outputPR(PyObject *, PyObject *);

//method get_pr()
extern char pypointsmodelpy_getPR__name__[];
extern char pypointsmodelpy_getPR__doc__[];
extern "C"
PyObject * pypointsmodelpy_getPR(PyObject *, PyObject *);


// method outputPR_xy
extern char pypointsmodelpy_outputPR_xy__name__[];
extern char pypointsmodelpy_outputPR_xy__doc__[];
extern "C"
PyObject * pypointsmodelpy_outputPR_xy(PyObject *, PyObject *);

// PDBModel method outputPR
extern char pypointsmodelpy_save_pdb_pr__name__[];
extern char pypointsmodelpy_save_pdb_pr__doc__[];
extern "C"
PyObject * pypointsmodelpy_save_pdb_pr(PyObject *, PyObject *);

// ComplexModel method outputPR
extern char pypointsmodelpy_save_complex_pr__name__[];
extern char pypointsmodelpy_save_complex_pr__doc__[];
extern "C"
PyObject * pypointsmodelpy_save_complex_pr(PyObject *, PyObject *);

// method outputPDB
extern char pypointsmodelpy_outputPDB__name__[];
extern char pypointsmodelpy_outputPDB__doc__[];
extern "C"
PyObject * pypointsmodelpy_outputPDB(PyObject *, PyObject *);

#endif

// version
// $Id$

// End of file
