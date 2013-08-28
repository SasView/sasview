// -*- C++ -*-
#include <Python.h>

#include <vector>
#include <cstring>
#include <stdexcept>
#include "Point3D.h"
#include "misc.h"
#include "lores_model.h"
#include "pdb_model.h"
#include "complex_model.h"
#include "geo_shape.h"
#include "iq.h"

// copyright

char pypointsmodelpy_copyright__doc__[] = "";
char pypointsmodelpy_copyright__name__[] = "copyright";

static char pypointsmodelpy_copyright_note[] = 
    "pointsmodelpy python module: Copyright (c) 2007 University of Tennessee";


PyObject * pypointsmodelpy_copyright(PyObject *, PyObject *)
{
    return Py_BuildValue("s", pypointsmodelpy_copyright_note);
}
    
// new_loresmodel 
//wrapper for LORESModel constructor LORESModel(double density)

char pypointsmodelpy_new_loresmodel__doc__[] = "Low-resolution shapes:real space geometric complex models";
char pypointsmodelpy_new_loresmodel__name__[] = "new_loresmodel";

PyObject * pypointsmodelpy_new_loresmodel(PyObject *, PyObject *args)
{
  double density = 0;

  int ok = PyArg_ParseTuple(args, "d",&density);
  if(!ok) return NULL;

  LORESModel *newlores = new LORESModel(density);
  return PyCObject_FromVoidPtr(newlores, PyDelLores);
}
    
void PyDelLores(void *ptr){
  LORESModel * oldlores = static_cast<LORESModel *>(ptr);
  delete oldlores;
  return;
}

//LORESModel methods add(GeoShape &, double sld)
char pypointsmodelpy_lores_add__name__[] = "lores_add";
char pypointsmodelpy_lores_add__doc__[] = "loresmodel method:add(Geoshape &,sld)";

PyObject * pypointsmodelpy_lores_add(PyObject *, PyObject *args){
  double sld = 1;
  PyObject *pyloresmodel = 0, *pyshape = 0;
  int ok = PyArg_ParseTuple(args, "OOd", &pyloresmodel, &pyshape, &sld);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyloresmodel);
  void *temp2 = PyCObject_AsVoidPtr(pyshape);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  GeoShape * thisshape = static_cast<GeoShape *>(temp2);

  thislores->Add(*thisshape, sld);

  return Py_BuildValue("i", 0);
}

//LORESModel methods GetPoints(vector<Point3D> &)
char pypointsmodelpy_get_lorespoints__name__[] = "get_lorespoints";
char pypointsmodelpy_get_lorespoints__doc__[] = "get the points from the lores model";

PyObject * pypointsmodelpy_get_lorespoints(PyObject *, PyObject *args){
  PyObject *pyloresmodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pyloresmodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyloresmodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  int npts = thislores->GetPoints(*thisvec);
  //temporary
  thislores->WritePoints2File(*thisvec);
  return Py_BuildValue("i", npts);
}

// new_pdbmodel 
//wrapper for PDBModel constructor PDBModel()

char pypointsmodelpy_new_pdbmodel__doc__[] = "PDB model: contain atomic coordinate from PDB file & Scattering length density";
char pypointsmodelpy_new_pdbmodel__name__[] = "new_pdbmodel";

PyObject * pypointsmodelpy_new_pdbmodel(PyObject *, PyObject *args)
{
  PDBModel *newpdb = new PDBModel();
  return PyCObject_FromVoidPtr(newpdb, PyDelPDB);
}
    
void PyDelPDB(void *ptr){
  PDBModel * oldpdb = static_cast<PDBModel *>(ptr);
  delete oldpdb;
  return;
}

//PDBModel methods AddPDB(char * pdbfile) 
char pypointsmodelpy_pdbmodel_add__name__[] = "pdbmodel_add";
char pypointsmodelpy_pdbmodel_add__doc__[] = "Add a structure from PDB";

PyObject * pypointsmodelpy_pdbmodel_add(PyObject *, PyObject *args){
  PyObject *pypdbmodel = 0;
  char * pdbfile;

  int ok = PyArg_ParseTuple(args, "Os", &pypdbmodel, &pdbfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pypdbmodel);

  PDBModel * thispdb = static_cast<PDBModel *>(temp);

  thispdb->AddPDB(pdbfile);

  return Py_BuildValue("i", 0);
}

//PDBModel methods GetPoints(Point3DVector &) 
char pypointsmodelpy_get_pdbpoints__name__[] = "get_pdbpoints";
char pypointsmodelpy_get_pdbpoints__doc__[] = "Get atomic points from pdb with SLD";

PyObject * pypointsmodelpy_get_pdbpoints(PyObject *, PyObject *args){
  PyObject *pypdbmodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pypdbmodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pypdbmodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);

  PDBModel * thispdb = static_cast<PDBModel *>(temp);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  int npts = thispdb->GetPoints(*thisvec);

  return Py_BuildValue("i", npts);
}

// new_complexmodel 
//wrapper for ComplexModel constructor ComplexModel()

char pypointsmodelpy_new_complexmodel__doc__[] = "COMPLEX model: contain LORES and PDB models";
char pypointsmodelpy_new_complexmodel__name__[] = "new_complexmodel";

PyObject * pypointsmodelpy_new_complexmodel(PyObject *, PyObject *args)
{
  ComplexModel *newcomplex = new ComplexModel();
  return PyCObject_FromVoidPtr(newcomplex, PyDelComplex);
}
    
void PyDelComplex(void *ptr){
  ComplexModel * oldcomplex = static_cast<ComplexModel *>(ptr);
  delete oldcomplex;
  return;
}

//ComplexModel methods Add(PointsModel *) 
char pypointsmodelpy_complexmodel_add__name__[] = "complexmodel_add";
char pypointsmodelpy_complexmodel_add__doc__[] = "Add LORES model or PDB Model,type has to be specified (either PDB or LORES)";

PyObject * pypointsmodelpy_complexmodel_add(PyObject *, PyObject *args){
  PyObject *pycomplexmodel = 0, *pymodel = 0;
  char * modeltype;

  int ok = PyArg_ParseTuple(args, "OOs", &pycomplexmodel,&pymodel, &modeltype);
  if(!ok) return NULL;

  void *temp2 = PyCObject_AsVoidPtr(pycomplexmodel);
  ComplexModel *thiscomplex = static_cast<ComplexModel *>(temp2);

  void *temp = PyCObject_AsVoidPtr(pymodel);
  if (strcmp(modeltype,"LORES") == 0){
    LORESModel * thislores = static_cast<LORESModel *>(temp);
    thiscomplex->Add(thislores);
  }
  else if (strcmp(modeltype,"PDB") == 0){
    PDBModel * thispdb = static_cast<PDBModel *>(temp);
    thiscomplex->Add(thispdb);
  }
  else{
    throw runtime_error("The model type is either PDB or LORES");
  }

  return Py_BuildValue("i", 0);
}

//ComplexModel methods GetPoints(Point3DVector &) 
char pypointsmodelpy_get_complexpoints__name__[] = "get_complexpoints";
char pypointsmodelpy_get_complexpoints__doc__[] = "Get points from complex model (container for LORES & PDB model)";

PyObject * pypointsmodelpy_get_complexpoints(PyObject *, PyObject *args){
  PyObject *pycomplexmodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pycomplexmodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pycomplexmodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  int npts = thiscomplex->GetPoints(*thisvec);

  return Py_BuildValue("i", npts);
}

//create a new vector that holds of class Point3D objects 
char pypointsmodelpy_new_point3dvec__doc__[] = "";
char pypointsmodelpy_new_point3dvec__name__[] = "new_point3dvec";

PyObject * pypointsmodelpy_new_point3dvec(PyObject *, PyObject *args)
{
  PyObject *pyvec = 0;

  vector<Point3D> *newvec = new vector<Point3D>();

  return PyCObject_FromVoidPtr(newvec, PyDelPoint3DVec);
}

void PyDelPoint3DVec(void *ptr)
{
  vector<Point3D> * oldvec = static_cast<vector<Point3D> *>(ptr);
  delete oldvec;
  return;

}

//LORESModel method distribution(point3dvec)
char pypointsmodelpy_get_lores_pr__name__[] = "get_lores_pr";
char pypointsmodelpy_get_lores_pr__doc__[] = "calculate distance distribution function";

PyObject * pypointsmodelpy_get_lores_pr(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  double rmax = thislores->DistDistribution(*thisvec);
  
  return Py_BuildValue("d", rmax);
}

//LORESModel method distribution_xy(point3dvec)
char pypointsmodelpy_distdistribution_xy__name__[] = "distdistribution_xy";
char pypointsmodelpy_distdistribution_xy__doc__[] = "calculate distance distribution function on XY plane";

PyObject * pypointsmodelpy_distdistribution_xy(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);

  LORESModel * thislores = static_cast<LORESModel *>(temp);

  Py_BEGIN_ALLOW_THREADS
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);
  thislores->DistDistributionXY(*thisvec);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i", 0);
}

//PDBModel method distribution_xy(point3dvec)
char pypointsmodelpy_get_pdb_pr_xy__name__[] = "get_pdb_pr_xy";
char pypointsmodelpy_get_pdb_pr_xy__doc__[] = "calculate distance distribution function on XY plane";

PyObject * pypointsmodelpy_get_pdb_pr_xy(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  PDBModel * thispdb = static_cast<PDBModel *>(temp);
  thispdb->DistDistributionXY(*thisvec);

  return Py_BuildValue("i", 0);
}

//PDBModel method distribution(point3dvec)
char pypointsmodelpy_get_pdb_pr__name__[] = "get_pdb_pr";
char pypointsmodelpy_get_pdb_pr__doc__[] = "calculate distance distribution function";

PyObject * pypointsmodelpy_get_pdb_pr(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  Py_BEGIN_ALLOW_THREADS
  PDBModel * thispdb = static_cast<PDBModel *>(temp);
  thispdb->DistDistribution(*thisvec);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i", 0);
}

//ComplexModel method distribution(point3dvec)
char pypointsmodelpy_get_complex_pr__name__[] = "get_complex_pr";
char pypointsmodelpy_get_complex_pr__doc__[] = "calculate distance distribution function";

PyObject * pypointsmodelpy_get_complex_pr(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pypoint3dvec = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pypoint3dvec);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  Py_BEGIN_ALLOW_THREADS
  thiscomplex->DistDistribution(*thisvec);
  Py_END_ALLOW_THREADS
  return Py_BuildValue("i", 0);
}

//LORESModel method CalculateIQ(iq)
char pypointsmodelpy_get_lores_iq__name__[] = "get_lores_iq";
char pypointsmodelpy_get_lores_iq__doc__[] = "calculate scattering intensity";

PyObject * pypointsmodelpy_get_lores_iq(PyObject *, PyObject *args)
{
  PyObject *pylores = 0, *pyiq = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pylores, &pyiq);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  void *temp2 = PyCObject_AsVoidPtr(pyiq);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  IQ * thisiq = static_cast<IQ *>(temp2);

  Py_BEGIN_ALLOW_THREADS
  thislores->CalculateIQ(thisiq);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i",0);
}

//LORESModel method CalculateIQ(q)
char pypointsmodelpy_get_lores_i__name__[] = "get_lores_i";
char pypointsmodelpy_get_lores_i__doc__[] = "calculate averaged scattering intensity from a single q";

PyObject * pypointsmodelpy_get_lores_i(PyObject *, PyObject *args)
{
  PyObject *pylores = 0;
  double q = 0;
  int ok = PyArg_ParseTuple(args, "Od", &pylores, &q);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  
  double I = 0.0;
  Py_BEGIN_ALLOW_THREADS
  I = thislores->CalculateIQ(q);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

// method calculateIQ_2D(iq)
char pypointsmodelpy_calculateIQ_2D__name__[] = "calculateIQ_2D";
char pypointsmodelpy_calculateIQ_2D__doc__[] = "calculate scattering intensity";

PyObject * pypointsmodelpy_calculateIQ_2D(PyObject *, PyObject *args)
{
  PyObject *pylores = 0, *pyiq = 0;
  double theta = 0;
  int ok = PyArg_ParseTuple(args, "OOd", &pylores, &pyiq,&theta);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  void *temp2 = PyCObject_AsVoidPtr(pyiq);

  LORESModel * thislores = static_cast<LORESModel *>(temp);
  IQ * thisiq = static_cast<IQ *>(temp2);
  
  Py_BEGIN_ALLOW_THREADS
  thislores->CalculateIQ_2D(thisiq,theta);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i",0);
}

// method calculateI_Qxy(Qx,Qy)
char pypointsmodelpy_calculateI_Qxy__name__[] = "calculateI_Qxy";
char pypointsmodelpy_calculateI_Qxy__doc__[] = "calculate scattering intensity on a 2D pixel";

PyObject * pypointsmodelpy_calculateI_Qxy(PyObject *, PyObject *args)
{
  PyObject *pylores = 0;
  double qx = 0, qy = 0;
  double I = 0;

  int ok = PyArg_ParseTuple(args, "Odd", &pylores, &qx,&qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  LORESModel * thislores = static_cast<LORESModel *>(temp);
  
  Py_BEGIN_ALLOW_THREADS
  I = thislores->CalculateIQ_2D(qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

// method calculateI_Qxy(poitns, Qx,Qy)
char pypointsmodelpy_calculateI_Qvxy__name__[] = "calculateI_Qvxy";
char pypointsmodelpy_calculateI_Qvxy__doc__[] = "calculate scattering intensity on a 2D pixel";

PyObject * pypointsmodelpy_calculateI_Qvxy(PyObject *, PyObject *args)
{
  PyObject *pylores = 0, *pypoint3dvec = 0;
  double qx = 0, qy = 0;
  double I = 0;

  int ok = PyArg_ParseTuple(args, "OOdd", &pylores, &pypoint3dvec, &qx,&qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  LORESModel * thislores = static_cast<LORESModel *>(temp);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);
  
  Py_BEGIN_ALLOW_THREADS
  I = thislores->CalculateIQ_2D(*thisvec, qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

// PDBModel method calculateIQ(iq)
char pypointsmodelpy_get_pdb_iq__name__[] = "get_pdb_iq";
char pypointsmodelpy_get_pdb_iq__doc__[] = "calculate scattering intensity for PDB model";

PyObject * pypointsmodelpy_get_pdb_iq(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pyiq = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pyiq);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pyiq);

  PDBModel * thispdb = static_cast<PDBModel *>(temp);
  IQ * thisiq = static_cast<IQ *>(temp2);

  Py_BEGIN_ALLOW_THREADS
  thispdb->CalculateIQ(thisiq);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i",0);
}

// PDBModel method calculateIQ_2D(qx,qy)
char pypointsmodelpy_get_pdb_Iqxy__name__[] = "get_pdb_Iqxy";
char pypointsmodelpy_get_pdb_Iqxy__doc__[] = "calculate scattering intensity by a given (qx,qy) for PDB model";

PyObject * pypointsmodelpy_get_pdb_Iqxy(PyObject *, PyObject *args)
{
  PyObject *pypdb = 0;
  double qx = 0, qy = 0;
  double I = 0;

  int ok = PyArg_ParseTuple(args, "Odd", &pypdb, &qx,&qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pypdb);
  PDBModel * thispdb = static_cast<PDBModel *>(temp);

  Py_BEGIN_ALLOW_THREADS
  I = thispdb->CalculateIQ_2D(qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

// PDBModel method calculateIQ_2Dv(points,qx,qy)
char pypointsmodelpy_get_pdb_Iqvxy__name__[] = "get_pdb_Iqvxy";
char pypointsmodelpy_get_pdb_Iqvxy__doc__[] = "calculate scattering intensity by a given (qx,qy) for PDB model";

PyObject * pypointsmodelpy_get_pdb_Iqvxy(PyObject *, PyObject *args)
{
  PyObject *pypdb = 0, *pypoint3dvec = 0;
  double qx = 0, qy = 0;
  double I = 0;

  int ok = PyArg_ParseTuple(args, "OOdd", &pypdb, &pypoint3dvec, &qx,&qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pypdb);
  PDBModel * thispdb = static_cast<PDBModel *>(temp);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  Py_BEGIN_ALLOW_THREADS
  I = thispdb->CalculateIQ_2D(*thisvec,qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

// ComplexModel method calculateIQ(iq)
char pypointsmodelpy_get_complex_iq__name__[] = "get_complex_iq";
char pypointsmodelpy_get_complex_iq__doc__[] = "calculate scattering intensity for COMPLEX model";

PyObject * pypointsmodelpy_get_complex_iq(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0, *pyiq = 0;
  int ok = PyArg_ParseTuple(args, "OO", &pymodel, &pyiq);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);
  void *temp2 = PyCObject_AsVoidPtr(pyiq);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  IQ * thisiq = static_cast<IQ *>(temp2);

  Py_BEGIN_ALLOW_THREADS
  thiscomplex->CalculateIQ(thisiq);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("i",0);
}

//LORESModel method CalculateIQ_2D(points,qx,qy) 
char pypointsmodelpy_get_complex_Iqxy__name__[] = "get_complex_iq_2D";
char pypointsmodelpy_get_complex_Iqxy__doc__[] = "calculate averaged scattering intensity from a single q";

PyObject * pypointsmodelpy_get_complex_Iqxy(PyObject *, PyObject *args)
{
  PyObject *pylores = 0, *pypoint3dvec = 0;
  double qx = 0, qy = 0;
  int ok = PyArg_ParseTuple(args, "OOdd", &pylores, &pypoint3dvec, &qx, &qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  double I = 0.0;
  Py_BEGIN_ALLOW_THREADS
  I = thiscomplex->CalculateIQ_2D(*thisvec,qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

//LORESModel method CalculateIQ_2D_Error(points,qx,qy) 
char pypointsmodelpy_get_complex_Iqxy_err__name__[] = "get_complex_iq_2D_err";
char pypointsmodelpy_get_complex_Iqxy_err__doc__[] = "calculate averaged scattering intensity from a single q";

PyObject * pypointsmodelpy_get_complex_Iqxy_err(PyObject *, PyObject *args)
{
  PyObject *pylores = 0, *pypoint3dvec = 0;
  double qx = 0, qy = 0;
  int ok = PyArg_ParseTuple(args, "OOdd", &pylores, &pypoint3dvec, &qx, &qy);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);
  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  double I = 0.0;
  Py_BEGIN_ALLOW_THREADS
  I = thiscomplex->CalculateIQ_2D_Error(*thisvec,qx,qy);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

//LORESModel method CalculateIQ(q) 
char pypointsmodelpy_get_complex_i__name__[] = "get_complex_i";
char pypointsmodelpy_get_complex_i__doc__[] = "calculate averaged scattering intensity from a single q";

PyObject * pypointsmodelpy_get_complex_i(PyObject *, PyObject *args)
{
  PyObject *pylores = 0;
  double q = 0;
  int ok = PyArg_ParseTuple(args, "Od", &pylores, &q);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);
  
  double I = 0.0;
  Py_BEGIN_ALLOW_THREADS
  I = thiscomplex->CalculateIQ(q);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}

char pypointsmodelpy_get_complex_i_error__name__[] = "get_complex_i_error";
char pypointsmodelpy_get_complex_i_error__doc__[] = "calculate error on averaged scattering intensity from a single q";

PyObject * pypointsmodelpy_get_complex_i_error(PyObject *, PyObject *args)
{
  PyObject *pylores = 0;
  double q = 0;
  int ok = PyArg_ParseTuple(args, "Od", &pylores, &q);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pylores);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);

  double I = 0.0;
  Py_BEGIN_ALLOW_THREADS
  I = thiscomplex->CalculateIQError(q);
  Py_END_ALLOW_THREADS
  
  return Py_BuildValue("d",I);
}




//method outputPR(string filename)
char pypointsmodelpy_outputPR__name__[] = "outputPR";
char pypointsmodelpy_outputPR__doc__[] = "print out P(R) to a file";

PyObject * pypointsmodelpy_outputPR(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "Os", &pymodel, &outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);

  LORESModel * thislores = static_cast<LORESModel *>(temp);

  thislores->OutputPR(outfile);

  return Py_BuildValue("i", 0);
}


//method get_pr()
char pypointsmodelpy_getPR__name__[] = "get_pr";
char pypointsmodelpy_getPR__doc__[] = "Return P(r) as a list of points";

PyObject * pypointsmodelpy_getPR(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "O", &pymodel);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);

  LORESModel * thislores = static_cast<LORESModel *>(temp);

  // Get the P(r) array
  Array2D<double> pr_ = thislores->GetPr();

  // Create two lists to store the r and P(r) values
  PyObject* r_list  = PyList_New(0);
  PyObject* pr_list = PyList_New(0);

  double sum = 0.0;
  double r_stepsize = 1.0;
  if (pr_.dim1()>2) r_stepsize = pr_[1][0] - pr_[0][0];

  for (int i = 0;  i < pr_.dim1(); ++i){
	  sum += pr_[i][1]*r_stepsize;
  }

  for (int i = 0;  i < pr_.dim1(); ++i){
	  if (pr_[i][1]==0) continue;
	  int r_append  = PyList_Append(r_list, Py_BuildValue("d", pr_[i][0]));
	  int pr_append = PyList_Append(pr_list, Py_BuildValue("d", pr_[i][1]/sum));
	  if (r_append+pr_append<0) return NULL;
  }

  return Py_BuildValue("OO", r_list, pr_list);
}



//method outputPR_xy(string filename)
char pypointsmodelpy_outputPR_xy__name__[] = "outputPR_xy";
char pypointsmodelpy_outputPR_xy__doc__[] = "print out P(R) to a file";

PyObject * pypointsmodelpy_outputPR_xy(PyObject *, PyObject *args)
{
  PyObject *pyloresmodel = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "Os", &pyloresmodel, &outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyloresmodel);

  LORESModel * thislores = static_cast<LORESModel *>(temp);

  thislores->OutputPR_XY(outfile);

  return Py_BuildValue("i", 0);
}

//PDBModel method outputPR(string filename)
char pypointsmodelpy_save_pdb_pr__name__[] = "save_pdb_pr";
char pypointsmodelpy_save_pdb_pr__doc__[] = "print out P(R) to a file";

PyObject * pypointsmodelpy_save_pdb_pr(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "Os", &pymodel, &outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);

  PDBModel * thispdb = static_cast<PDBModel *>(temp);

  thispdb->OutputPR(outfile);

  return Py_BuildValue("i", 0);
}

//ComplexModel method outputPR(string filename)
char pypointsmodelpy_save_complex_pr__name__[] = "save_complex_pr";
char pypointsmodelpy_save_complex_pr__doc__[] = "print out P(R) to a file";

PyObject * pypointsmodelpy_save_complex_pr(PyObject *, PyObject *args)
{
  PyObject *pymodel = 0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "Os", &pymodel, &outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pymodel);

  ComplexModel * thiscomplex = static_cast<ComplexModel *>(temp);

  thiscomplex->OutputPR(outfile);

  return Py_BuildValue("i", 0);
}


//method outputPDB(string filename)
char pypointsmodelpy_outputPDB__name__[] = "outputPDB";
char pypointsmodelpy_outputPDB__doc__[] = "save the monte-carlo distributed points of the geomodel into a PDB format file.\
                                           a .pdb extension will be automatically added";

PyObject * pypointsmodelpy_outputPDB(PyObject *, PyObject *args)
{
  PyObject *pyloresmodel = 0, *pypoint3dvec=0;
  char *outfile;
  int ok = PyArg_ParseTuple(args, "OOs", &pyloresmodel, &pypoint3dvec,&outfile);
  if(!ok) return NULL;

  void *temp = PyCObject_AsVoidPtr(pyloresmodel);

  LORESModel * thislores = static_cast<LORESModel *>(temp);

  void *temp2 = PyCObject_AsVoidPtr(pypoint3dvec);
  vector<Point3D> * thisvec = static_cast<vector<Point3D> *>(temp2);

  thislores->OutputPDB(*thisvec,outfile);

  return Py_BuildValue("i", 0);
}

// version
// $Id$

// End of file
