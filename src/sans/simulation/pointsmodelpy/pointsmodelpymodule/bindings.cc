// -*- C++ -*-
// @copyright: University of Tennessee, for the DANSE project

//#include <portinfo>
#include <Python.h>

#include "bindings.h"

#include "misc.h"          // miscellaneous methods

// the method table

struct PyMethodDef pypointsmodelpy_methods[] = {

    // new_loresmodel
    {pypointsmodelpy_new_loresmodel__name__, pypointsmodelpy_new_loresmodel,
     METH_VARARGS, pypointsmodelpy_new_loresmodel__doc__},

    // LORESModel method:add(geoshape,sld)
    {pypointsmodelpy_lores_add__name__, pypointsmodelpy_lores_add,
     METH_VARARGS, pypointsmodelpy_lores_add__doc__},

    // LORESModel method:GetPoints(vector<Point3D> &)
    {pypointsmodelpy_get_lorespoints__name__, pypointsmodelpy_get_lorespoints,
     METH_VARARGS, pypointsmodelpy_get_lorespoints__doc__},

    // new_pdbmodel
    {pypointsmodelpy_new_pdbmodel__name__, pypointsmodelpy_new_pdbmodel,
     METH_VARARGS, pypointsmodelpy_new_pdbmodel__doc__},

    // PDBModel method: AddPDB(const char*)
    {pypointsmodelpy_pdbmodel_add__name__, pypointsmodelpy_pdbmodel_add,
     METH_VARARGS, pypointsmodelpy_pdbmodel_add__doc__},

    // PDBModel method: GetPoints(Point3DVector &)
    {pypointsmodelpy_get_pdbpoints__name__, pypointsmodelpy_get_pdbpoints,
     METH_VARARGS, pypointsmodelpy_get_pdbpoints__doc__},

    // new_complexmodel
    {pypointsmodelpy_new_complexmodel__name__, pypointsmodelpy_new_complexmodel,
     METH_VARARGS, pypointsmodelpy_new_complexmodel__doc__},

    // ComplexModel method: Add(PointsModel *)
    {pypointsmodelpy_complexmodel_add__name__, pypointsmodelpy_complexmodel_add,
     METH_VARARGS, pypointsmodelpy_complexmodel_add__doc__},

    // ComplexModel method: GetPoints(Point3DVector &)
    {pypointsmodelpy_get_complexpoints__name__, pypointsmodelpy_get_complexpoints,
     METH_VARARGS, pypointsmodelpy_get_complexpoints__doc__},

    //new_point3dvec
    {pypointsmodelpy_new_point3dvec__name__, pypointsmodelpy_new_point3dvec,
     METH_VARARGS, pypointsmodelpy_new_point3dvec__doc__},

    //fillpoints
    //{pypointsmodelpy_fillpoints__name__, pypointsmodelpy_fillpoints,
    //METH_VARARGS, pypointsmodelpy_fillpoints__doc__},

    //distdistribution calculation for LORES model
    {pypointsmodelpy_get_lores_pr__name__, pypointsmodelpy_get_lores_pr,
     METH_VARARGS, pypointsmodelpy_get_lores_pr__doc__},

    //distdistribution 2D (on xy plane)
    {pypointsmodelpy_distdistribution_xy__name__, pypointsmodelpy_distdistribution_xy,
     METH_VARARGS, pypointsmodelpy_distdistribution_xy__doc__},

    //distdistribution calculation for PDB model
    {pypointsmodelpy_get_pdb_pr__name__, pypointsmodelpy_get_pdb_pr,
     METH_VARARGS, pypointsmodelpy_get_pdb_pr__doc__},

    //distdistribution calculation on XY plane for PDB model
    {pypointsmodelpy_get_pdb_pr_xy__name__, pypointsmodelpy_get_pdb_pr_xy,
     METH_VARARGS, pypointsmodelpy_get_pdb_pr_xy__doc__},

    //distdistribution calculation for Complex model
    {pypointsmodelpy_get_complex_pr__name__, pypointsmodelpy_get_complex_pr,
     METH_VARARGS, pypointsmodelpy_get_complex_pr__doc__},

    //calculateIQ
    {pypointsmodelpy_get_lores_iq__name__, pypointsmodelpy_get_lores_iq,
     METH_VARARGS, pypointsmodelpy_get_lores_iq__doc__},

    //calculateI(single Q)
    {pypointsmodelpy_get_lores_i__name__, pypointsmodelpy_get_lores_i,
     METH_VARARGS, pypointsmodelpy_get_lores_i__doc__},

    //calculateI(single Q)
    {pypointsmodelpy_get_complex_i__name__, pypointsmodelpy_get_complex_i,
     METH_VARARGS, pypointsmodelpy_get_complex_i__doc__},

    //calculateI(single Q)
    {pypointsmodelpy_get_complex_i_error__name__, pypointsmodelpy_get_complex_i_error,
     METH_VARARGS, pypointsmodelpy_get_complex_i_error__doc__},

    //calculateIQ 2D
    {pypointsmodelpy_calculateIQ_2D__name__, pypointsmodelpy_calculateIQ_2D,
     METH_VARARGS, pypointsmodelpy_calculateIQ_2D__doc__},

     //calculateIQ 2D(points, Qx,Qy)
     {pypointsmodelpy_calculateI_Qvxy__name__, pypointsmodelpy_calculateI_Qvxy,
      METH_VARARGS, pypointsmodelpy_calculateI_Qvxy__doc__},

      //calculateIQ 2D(Qx,Qy)
      {pypointsmodelpy_calculateI_Qxy__name__, pypointsmodelpy_calculateI_Qxy,
       METH_VARARGS, pypointsmodelpy_calculateI_Qxy__doc__},

    //PDBModel calculateIQ
    {pypointsmodelpy_get_pdb_iq__name__, pypointsmodelpy_get_pdb_iq,
     METH_VARARGS, pypointsmodelpy_get_pdb_iq__doc__},

     //PDBModel calculateIQ(Qx,Qy)
     {pypointsmodelpy_get_pdb_Iqxy__name__, pypointsmodelpy_get_pdb_Iqxy,
      METH_VARARGS, pypointsmodelpy_get_pdb_Iqxy__doc__},

      //PDBModel calculateIQ(pts,Qx,Qy)
      {pypointsmodelpy_get_pdb_Iqvxy__name__, pypointsmodelpy_get_pdb_Iqvxy,
       METH_VARARGS, pypointsmodelpy_get_pdb_Iqvxy__doc__},

       //ComplexModel calculateIQ(pts,Qx,Qy)
       {pypointsmodelpy_get_complex_Iqxy__name__, pypointsmodelpy_get_complex_Iqxy,
        METH_VARARGS, pypointsmodelpy_get_complex_Iqxy__doc__},

        //ComplexModel calculateIQ_2D_Error(pts,Qx,Qy)
        {pypointsmodelpy_get_complex_Iqxy_err__name__, pypointsmodelpy_get_complex_Iqxy_err,
         METH_VARARGS, pypointsmodelpy_get_complex_Iqxy_err__doc__},

    //ComplexModel calculateIQ
    {pypointsmodelpy_get_complex_iq__name__, pypointsmodelpy_get_complex_iq,
     METH_VARARGS, pypointsmodelpy_get_complex_iq__doc__},

     //outputPR
     {pypointsmodelpy_outputPR__name__, pypointsmodelpy_outputPR,
      METH_VARARGS, pypointsmodelpy_outputPR__doc__},

    //getPR
    {pypointsmodelpy_getPR__name__, pypointsmodelpy_getPR,
     METH_VARARGS, pypointsmodelpy_getPR__doc__},

    //outputPR_xy
    {pypointsmodelpy_outputPR_xy__name__, pypointsmodelpy_outputPR_xy,
     METH_VARARGS, pypointsmodelpy_outputPR_xy__doc__},

    //PDBModel outputPR
    {pypointsmodelpy_save_pdb_pr__name__, pypointsmodelpy_save_pdb_pr,
     METH_VARARGS, pypointsmodelpy_save_pdb_pr__doc__},

    //ComplexModel outputPR
    {pypointsmodelpy_save_complex_pr__name__, pypointsmodelpy_save_complex_pr,
     METH_VARARGS, pypointsmodelpy_save_complex_pr__doc__},

    //outputPDB
    {pypointsmodelpy_outputPDB__name__, pypointsmodelpy_outputPDB,
     METH_VARARGS, pypointsmodelpy_outputPDB__doc__},

    {pypointsmodelpy_copyright__name__, pypointsmodelpy_copyright,
     METH_VARARGS, pypointsmodelpy_copyright__doc__},


// Sentinel
    {0, 0}
};

// version
// $Id$

// End of file
