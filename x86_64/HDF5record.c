/* Created by Language version: 7.7.0 */
/* NOT VECTORIZED */
#define NRN_VECTORIZED 0
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "scoplib_ansi.h"
#undef PI
#define nil 0
#include "md1redef.h"
#include "section.h"
#include "nrniv_mf.h"
#include "md2redef.h"
 
#if METHOD3
extern int _method3;
#endif

#if !NRNGPU
#undef exp
#define exp hoc_Exp
extern double hoc_Exp(double);
#endif
 
#define nrn_init _nrn_init__HDF5Record
#define _nrn_initial _nrn_initial__HDF5Record
#define nrn_cur _nrn_cur__HDF5Record
#define _nrn_current _nrn_current__HDF5Record
#define nrn_jacob _nrn_jacob__HDF5Record
#define nrn_state _nrn_state__HDF5Record
#define _net_receive _net_receive__HDF5Record 
#define addmapping addmapping__HDF5Record 
#define addvar addvar__HDF5Record 
#define consolidateTiming consolidateTiming__HDF5Record 
#define restartEvent restartEvent__HDF5Record 
#define recdata recdata__HDF5Record 
#define writeMeta writeMeta__HDF5Record 
 
#define _threadargscomma_ /**/
#define _threadargsprotocomma_ /**/
#define _threadargs_ /**/
#define _threadargsproto_ /**/
 	/*SUPPRESS 761*/
	/*SUPPRESS 762*/
	/*SUPPRESS 763*/
	/*SUPPRESS 765*/
	 extern double *getarg();
 static double *_p; static Datum *_ppvar;
 
#define t nrn_threads->_t
#define dt nrn_threads->_dt
#define mpirank _p[0]
#define Dt _p[1]
#define tstart _p[2]
#define tstop _p[3]
#define rpts _p[4]
#define _tsav _p[5]
#define _nd_area  *_ppvar[0]._pval
#define pntr	*_ppvar[2]._pval
#define _p_pntr	_ppvar[2]._pval
 
#if MAC
#if !defined(v)
#define v _mlhv
#endif
#if !defined(h)
#define h _mlhh
#endif
#endif
 
#if defined(__cplusplus)
extern "C" {
#endif
 static int hoc_nrnpointerindex =  2;
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_addmapping();
 static double _hoc_addvar();
 static double _hoc_consolidateTiming();
 static double _hoc_newMapping();
 static double _hoc_newReport();
 static double _hoc_printInfo();
 static double _hoc_restartEvent();
 static double _hoc_recdata();
 static double _hoc_writeMeta();
 static int _mechtype;
extern void _nrn_cacheloop_reg(int, int);
extern void hoc_register_prop_size(int, int, int);
extern void hoc_register_limits(int, HocParmLimits*);
extern void hoc_register_units(int, HocParmUnits*);
extern void nrn_promote(Prop*, int, int);
extern Memb_func* memb_func;
 
#define NMODL_TEXT 1
#if NMODL_TEXT
static const char* nmodl_file_text;
static const char* nmodl_filename;
extern void hoc_reg_nmodl_text(int, const char*);
extern void hoc_reg_nmodl_filename(int, const char*);
#endif

 extern Prop* nrn_point_prop_;
 static int _pointtype;
 static void* _hoc_create_pnt(_ho) Object* _ho; { void* create_point_process();
 return create_point_process(_pointtype, _ho);
}
 static void _hoc_destroy_pnt();
 static double _hoc_loc_pnt(_vptr) void* _vptr; {double loc_point_process();
 return loc_point_process(_pointtype, _vptr);
}
 static double _hoc_has_loc(_vptr) void* _vptr; {double has_loc_point();
 return has_loc_point(_vptr);
}
 static double _hoc_get_loc_pnt(_vptr)void* _vptr; {
 double get_loc_point_process(); return (get_loc_point_process(_vptr));
}
 extern void _nrn_setdata_reg(int, void(*)(Prop*));
 static void _setdata(Prop* _prop) {
 _p = _prop->param; _ppvar = _prop->dparam;
 }
 static void _hoc_setdata(void* _vptr) { Prop* _prop;
 _prop = ((Point_process*)_vptr)->_prop;
   _setdata(_prop);
 }
 /* connect user functions to hoc names */
 static VoidFunc hoc_intfunc[] = {
 0,0
};
 static Member_func _member_func[] = {
 "loc", _hoc_loc_pnt,
 "has_loc", _hoc_has_loc,
 "get_loc", _hoc_get_loc_pnt,
 "addmapping", _hoc_addmapping,
 "addvar", _hoc_addvar,
 "consolidateTiming", _hoc_consolidateTiming,
 "newMapping", _hoc_newMapping,
 "newReport", _hoc_newReport,
 "printInfo", _hoc_printInfo,
 "restartEvent", _hoc_restartEvent,
 "recdata", _hoc_recdata,
 "writeMeta", _hoc_writeMeta,
 0, 0
};
#define newMapping newMapping_HDF5Record
#define newReport newReport_HDF5Record
#define printInfo printInfo_HDF5Record
 extern double newMapping( );
 extern double newReport( );
 extern double printInfo( );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt", "ms",
 "tstart", "ms",
 "tstop", "ms",
 0,0
};
 static double v = 0;
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 0,0
};
 static DoubVec hoc_vdoub[] = {
 0,0,0
};
 static double _sav_indep;
 static void nrn_alloc(Prop*);
static void  nrn_init(_NrnThread*, _Memb_list*, int);
static void nrn_state(_NrnThread*, _Memb_list*, int);
 static void _hoc_destroy_pnt(_vptr) void* _vptr; {
   destroy_point_process(_vptr);
}
 static void _destructor(Prop*);
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"HDF5Record",
 "mpirank",
 "Dt",
 "tstart",
 "tstop",
 "rpts",
 0,
 0,
 0,
 "pntr",
 0};
 
extern Prop* need_memb(Symbol*);

static void nrn_alloc(Prop* _prop) {
	Prop *prop_ion;
	double *_p; Datum *_ppvar;
  if (nrn_point_prop_) {
	_prop->_alloc_seq = nrn_point_prop_->_alloc_seq;
	_p = nrn_point_prop_->param;
	_ppvar = nrn_point_prop_->dparam;
 }else{
 	_p = nrn_prop_data_alloc(_mechtype, 6, _prop);
 	/*initialize range parameters*/
 	mpirank = 0;
 	Dt = 0.1;
 	tstart = 0;
 	tstop = 0;
 	rpts = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 6;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 4, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 
#define _tqitem &(_ppvar[3]._pvoid)
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _HDF5record_reg() {
	int _vectorized = 0;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 0,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 	register_destructor(_destructor);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 6, 4);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "pointer");
  hoc_register_dparam_semantics(_mechtype, 3, "netsend");
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 HDF5Record /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/HDF5record.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int addmapping();
static int addvar();
static int consolidateTiming();
static int restartEvent();
static int recdata();
static int writeMeta();
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{    _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   recdata ( _threadargs_ ) ;
   if ( t < tstop ) {
     net_send ( _tqitem, _args, _pnt, t +  Dt , 1.0 ) ;
     }
   } }
 
/*VERBATIM*/

#include <stdlib.h>
#include <math.h>

#ifndef DISABLE_HDF5
#undef pntr
#define H5_USE_16_API 1
#undef dt
#include "hdf5.h"
#define dt nrn_threads->_dt

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
    void* nextReport_;
    int handle_;
    char neuronName_[256];
    char rptName_[256];
    char path_[512];
    char fn_[256];
    int tstep_;
    int tsteps_;
    double tstart_;
    double tstop_;
    double Dt_;
    double** ptrs_; /* list of pointers to hoc variables */
    float* buf_;
    float* map_;
    int np_;
    int nm_;
    int tp_; /* temporary indicator of passed variable pointers */
    int mp_; /* temporary indicator of passed variable pointers */

    /* hdf5 version */
    hid_t file_;
    hid_t neuron_;
    hid_t rpt_;
    hid_t dataspace_;
    hid_t mem_space_;
    hid_t file_space_;
    hid_t data_;
    hid_t mapping_;
//    hid_t mapping_space_;
//    hid_t map_mem_space_;
//    hid_t map_file_space_;
    int groupCreated_;

} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_pntr))

#define dp double*
extern void nrn_register_recalc_ptr_callback(void (*f)());
extern Point_process* ob2pntproc(Object*);
extern double* nrn_recalc_ptr(double*);

static void recalcptr(Info* info, int cnt, double** old_vp, double* new_v) {
    int i;
    /*printf("recalcptr np_=%d %s\n", info->np_, info->path_);*/
}

static void recalc_ptr_callback() {
    Symbol* sym;
    int i;
    hoc_List* instances;
    hoc_Item* q;
    /*printf("ASCIIrecord.mod recalc_ptr_callback\n");*/
    /* hoc has a list of the ASCIIRecord instances */
    sym = hoc_lookup("HDF5Record");
    instances = sym->u.template->olist;
    ITERATE(q, instances) {
        Info* InfoPtr;
        Point_process* pnt;
        Object* o = OBJ(q);
        /*printf("callback for %s\n", hoc_object_name(o));*/
        pnt = ob2pntproc(o);
        _ppvar = pnt->_prop->dparam;
        INFOCAST;

        for (InfoPtr = *ip; InfoPtr != 0; InfoPtr = (Info*) InfoPtr->nextReport_)
            for (i=0; i < InfoPtr->np_; ++i)
                InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);
    }
}

#endif  // ifndef DISABLE_HDF5
 
static int  restartEvent (  ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    const double etime = *getarg(1);
    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
#endif
  return 0; }
 
static double _hoc_restartEvent(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 restartEvent (  );
 return(_r);
}
 
double printInfo (  ) {
   double _lprintInfo;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* ttt = *ip;
    for (ttt = *ip; ttt != 0; ttt = (Info*) ttt->nextReport_) {
        printf("Info-Structure Debugging (%s->%s)\n", ttt->rptName_, ttt->neuronName_);
        printf("========================\n");
        printf("nextReport_= \t\t%p\n", (void*)ttt->nextReport_);
        printf("handle_ = \t\t%d\n", ttt->handle_);
        printf("neuronName = \t\t%s\n", ttt->neuronName_);
        printf("rptName =\t\t%s\n", ttt->rptName_);
        printf("path_=\t\t%s\n", ttt->path_);
        printf("fn_ =\t\t%s\n",ttt->fn_);
        printf("tstep_ =\t\t%d\n",ttt->tstep_);
        printf("tsteps_=\t\t%d\n",ttt->tsteps_);
        printf("tstart_=\t\t%g\n",ttt->tstart_);
        printf("tstop_ =\t\t%g\n",ttt->tstop_);
        printf("Dt_=\t\t%g\n", ttt->Dt_);
        printf("ptrs_=\t\t%p\n",  (void*) ttt->ptrs_); /* list of pointers to hoc variables */
        printf("buf_=\t\t%p\n",(void*)ttt->buf_);
        printf("map_=\t\t%p\n", (void*)ttt->map_);
        printf("np_=\t\t%d\n", ttt->np_);
        printf("nm_=\t\t%d\n", ttt->nm_);
        printf("tp_=\t\t%d\n", ttt->tp_); /* temporary indicator of passed variable pointers */
        printf("mp_=\t\t%d\n", ttt->mp_); /* temporary indicator of passed variable pointers */

        /* hdf5 version */
        printf("file_=\t\t%lld\n", ttt->file_);
        printf("neuron_=\t\t%lld\n", ttt->neuron_);
        printf("rpt_=\t\t%lld\n", ttt->rpt_);
        printf("dataspace_=\t\t%lld\n", ttt->dataspace_);
        printf("mem_space_=\t\t%lld\n", ttt->mem_space_);
        printf("file_space_=\t\t%lld\n", ttt->file_space_);
        printf("data_=\t\t%lld\n", ttt->data_);
        printf("mapping_=\t\t%lld\n", ttt->mapping_);
        printf("groupCreated_=\t\t%d\n", ttt->groupCreated_);
    }
#endif
 
return _lprintInfo;
 }
 
static double _hoc_printInfo(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  printInfo (  );
 return(_r);
}
 
double newReport (  ) {
   double _lnewReport;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* iPtr;
    Info* info;
    for (iPtr = *ip; iPtr->nextReport_ != 0; iPtr = (Info*) iPtr->nextReport_) {}
    int newRpt = 0;
    int trial = 0;
    int fileOpen = 0;
    char fn[1024];

    if (iPtr->handle_ == -1) {
        if (hoc_is_str_arg(1)) sprintf(iPtr->neuronName_, "%s", gargstr(1));
        else sprintf(iPtr->neuronName_, "neuron");

        if (hoc_is_str_arg(2)) sprintf(iPtr->rptName_, "%s", gargstr(2));
        else sprintf(iPtr->rptName_, "report");

        sprintf(fn, "%s/%s.h5", iPtr->path_, iPtr->fn_);
        // printf("the filename is: %s\n", fn);
        hid_t plist = H5Pcreate(H5P_FILE_CREATE);
            H5Pset_fapl_stdio(plist);
        // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
        iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);
        // plist = H5Pcreate(H5P_DATASET_XFER);
        // H5Pset_buffer(plist, 2097152, 0, 0);

        while ((iPtr->file_ < 0) && (trial < 20)) {
            // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
            iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);
            trial += 1;
            // printf("trial %d\n", trial);
        }
        if (iPtr->file_>=0) fileOpen = 1;
        // plist = H5Pcreate(H5P_DATASET_XFER);
        // H5Pset_buffer(plist, 16777216, 0, 0);
        iPtr->handle_ = 0;
    }

    // there already is a report --> need to create a new info struct
    else {
        newRpt = 1;

        Info* info = 0;
        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
        info->handle_ = 0;
        info->nextReport_ = 0;
        info->neuronName_[0]= 0;
        info->rptName_[0]= 0;
        info->path_[0]=0;
        info->neuron_ = 0;
        info->tstart_ = 0;
        info->tstop_ = 0;
        info->Dt_ = 0;
        info->rpt_ = 0;
        info->ptrs_ = 0;
        info->np_ = 0;
        info->nm_ = 0;
        info->tp_ = 0;
        info->mp_ = 0;
        info->tstep_ = 0;
        info->tsteps_ = 0;
        info->map_ = 0;
        info->groupCreated_ = 1;
        info->data_ = 0;
        info->mapping_ = 0;

        if (hoc_is_str_arg(1)) sprintf(info->neuronName_, "%s", gargstr(1));
        else sprintf(info->neuronName_, "neuron");

        if (hoc_is_str_arg(2)) sprintf(info->rptName_, "%s", gargstr(2));
        else sprintf(info->rptName_, "report");

        sprintf(info->fn_, "%s", (*ip)->fn_);
        sprintf(info->path_, "%s", (*ip)->path_);

        info->file_ = (*ip)->file_;
        iPtr=info;
        fileOpen = 1;
    }
    if (!fileOpen) {
        fprintf(stderr, "Rank %.0f: file creation failed!", mpirank);
        return 0;
    }

    char tmp[256];
    char unitStr[5];

    if (ifarg(3)) {
        iPtr->np_   = (int) *getarg(3);
        iPtr->ptrs_ = (double**)hoc_Ecalloc(iPtr->np_, sizeof(double*)); hoc_malchk();
        iPtr->buf_  = (float*)hoc_Ecalloc(iPtr->np_, sizeof(float)); hoc_malchk();
    }

    if (ifarg(4) && ifarg(5) && ifarg(6)) {
        iPtr->tstart_   = *getarg(4);
        iPtr->tstop_    = *getarg(5);
        iPtr->Dt_       = *getarg(6);
        // printf("tstart = %g\n", iPtr->tstart_);
        // printf("tstop = %g\n", iPtr->tstop_);
        // printf("Dt = %g\n", iPtr->Dt_);
        iPtr->tsteps_   = (int) (((iPtr->tstop_-iPtr->tstart_)/iPtr->Dt_)+.5);
        // printf("steps = %d\n", info->tsteps_);
        // iPtr->tsteps_ += 1;
        // printf("steps = %d\n", iPtr->tsteps_);
    }

    if (hoc_is_str_arg(7)) {
        sprintf(unitStr, "%s", gargstr(7));
    } else {
        sprintf(unitStr, "xx");
    }

    tstart = iPtr->tstart_;
    tstop  = iPtr->tstop_;
    Dt = iPtr->Dt_;

    /*****************************************************/
    /* hdf5                                              */
    /*****************************************************/
    // neuron name
    sprintf(tmp, "/%s", iPtr->neuronName_);

    if (iPtr->groupCreated_ ==0) {
        // printf("create group: %s\n", tmp);
        iPtr->neuron_ = H5Gcreate(iPtr->file_, tmp, 0);
    }

    // report name
    sprintf(tmp, "/%s/%s", iPtr->neuronName_, iPtr->rptName_);
    // printf("create group: %s\n", tmp);
    iPtr->rpt_ = H5Gcreate(iPtr->file_, tmp, 0);

    // printf("info->np_=%d\n", info->np_);

    // create data set
    hsize_t dims[2]; dims[0] = iPtr->tsteps_; dims[1] = iPtr->np_;
    iPtr->dataspace_ = H5Screate_simple(2, dims, NULL);
    sprintf(tmp, "/%s/%s/data", iPtr->neuronName_, iPtr->rptName_);
    iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_FLOAT, iPtr->dataspace_, H5P_DEFAULT);
    // iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_DOUBLE, iPtr->dataspace_, H5P_DEFAULT);

    // select hyperslab for writing each time step separately into dataset
    hsize_t off[2]; off[0] = 0; off[1] = 0;
    hsize_t size[2]; size[0] = 1; size[1] = iPtr->np_;
    hsize_t start[2]; start[0] = 0; start[1] = 0;
    iPtr->file_space_ = H5Dget_space(iPtr->data_);
    iPtr->mem_space_ = H5Screate_simple(2, size, NULL);
    H5Sselect_hyperslab(iPtr->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);

    // write attributes
    hid_t atype, attr;

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "rank", H5T_NATIVE_INT, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_INT, &mpirank);
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "tstart", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstart_));
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "tstop", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstop_));
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "Dt", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->Dt_));
    H5Aclose(attr);

    // attribute
    hid_t astring;
    atype  = H5Screate(H5S_SCALAR);
    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 5);
    attr = H5Acreate(iPtr->data_, "dunit", astring, atype, H5P_DEFAULT);
    H5Awrite(attr, astring, unitStr);
    H5Aclose(attr);

    // attribute
    atype  = H5Screate(H5S_SCALAR);
    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 2);
    attr = H5Acreate(iPtr->data_, "tunit", astring, atype, H5P_DEFAULT);
    H5Awrite(attr, astring, "ms");
    H5Aclose(attr);

    // if (!newRpt) *ip = info;
    if (newRpt == 1) {
        Info* tPtr; int hd = 1;
        for (tPtr = *ip; tPtr->nextReport_ != 0; tPtr = (Info*) tPtr->nextReport_, hd++) {}
        tPtr->nextReport_ = iPtr;
        iPtr->handle_ = hd;
    }
    rpts += 1;

    return iPtr->handle_;
#endif
 
return _lnewReport;
 }
 
static double _hoc_newReport(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  newReport (  );
 return(_r);
}
 
double newMapping (  ) {
   double _lnewMapping;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
//printf("newMapping\n");
    INFOCAST; Info* iPtr = 0; Info* info = 0;
    hsize_t dims[2];
    char tmp[256];
    hid_t atype, attr, astring;
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    if (hoc_is_str_arg(2)) {
        if (strncmp(gargstr(2), "point", 5) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_*3, sizeof(float)); hoc_malchk();
            dims[0]=3; dims[1]=info->np_;
        }
        else if (strncmp(gargstr(2), "compartment3D", 13) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_*4, sizeof(float)); hoc_malchk();
            dims[0]=4; dims[1]=info->np_;
        }
        else if (strncmp(gargstr(2), "compartment", 11) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_, sizeof(float)); hoc_malchk();
            dims[0]=1; dims[1]=info->np_;
        }
        info->nm_ = dims[0]*dims[1];
    }

    if(info->file_>=0) {
        // create mapping data set
        hid_t map = H5Screate_simple(2, dims, NULL);
        sprintf(tmp, "/%s/%s/mapping", info->neuronName_, info->rptName_);
        info->mapping_= H5Dcreate(info->file_, tmp, H5T_NATIVE_FLOAT, map, H5P_DEFAULT);

        // hsize_t size[2]; size[0] = 1; size[1] = dim[1]*dim[0];
        // info->map_mem_space_ = H5Screate_simple(2, size, NULL);
        // H5Sselect_hyperslab(info->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);

        if (strncmp(gargstr(2), "point", 5) == 0) {
            // attribute
            atype  = H5Screate(H5S_SCALAR);
            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);
            attr = H5Acreate(info->mapping_, "type", astring, atype, H5P_DEFAULT);
            H5Awrite(attr, astring, "point");
            H5Aclose(attr);
        }
        else if (strncmp(gargstr(2), "compartment", 11) == 0) {
            int sec, soma, axon, basal, apic;
            sec = soma = axon = basal = apic = 0;

            if (ifarg(3)) {
                sec = (int) *getarg(3);
            }
            if (ifarg(4)) {
                soma = (int) *getarg(4);
            }
            if (ifarg(5)) {
                axon = (int) *getarg(5);
            }
            if (ifarg(6)) {
                basal = (int) *getarg(6);
            }
            if (ifarg(7)) {
                apic = (int) *getarg(7);
            }

            // attribute
            atype  = H5Screate(H5S_SCALAR);
            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);
            attr = H5Acreate(info->mapping_, "type", astring, atype, H5P_DEFAULT);
            H5Awrite(attr, astring, gargstr(2));
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "sections", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &sec);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "soma", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &soma);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "axon", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &axon);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "basal", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &basal);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "apic", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &apic);
            H5Aclose(attr);

        }

    }
#endif
 
return _lnewMapping;
 }
 
static double _hoc_newMapping(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  newMapping (  );
 return(_r);
}
 
static int  addvar (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = 0; Info* iPtr = 0;
    //printf("addVar\n");
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    if (info->tp_ < info->np_) {
        info->ptrs_[info->tp_] = hoc_pgetarg(2);
        ++info->tp_;
    }
#endif
  return 0; }
 
static double _hoc_addvar(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 addvar (  );
 return(_r);
}
 
static int  addmapping (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = 0; Info* iPtr = 0;
    //printf("addMapping\n");
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    // printf("getarg(2) = %g\n", *getarg(2));
    if (info->mp_ < info->np_) {
        // printf("info->mp_ = %d\n", info->mp_);
        if (ifarg(2)) {
            info->map_[info->mp_] = (float) *getarg(2);
            // printf("info->map = %g\n", info->map_[info->mp_]);
        }
        if (ifarg(3)) {
            info->map_[info->mp_+info->np_] = (float) *getarg(3);
        }
        if (ifarg(4)) {
            info->map_[info->mp_+info->np_*2] = (float) *getarg(4);
        }
        if (ifarg(5)) {
            info->map_[info->mp_+info->np_*3] = (float) *getarg(5);
        }
        ++info->mp_;
    }
#endif
  return 0; }
 
static double _hoc_addmapping(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 addmapping (  );
 return(_r);
}
 
static int  recdata (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if ((t >= info->tstart_) && (t < info->tstop_) && (info->tstep_ < info->tsteps_)) {

            /*****************************************************/
            /* HDF5                                              */
            /*****************************************************/

            if ((info->file_>=0) && (info->data_)) {
                hsize_t off[2] = {info->tstep_, 0};
                hsize_t size[2] = {1, info->np_};

                H5Sselect_hyperslab(info->file_space_, H5S_SELECT_SET, off, NULL, size, NULL);

                float* tt = info->buf_;
                int i;
                for(i=0; i< info->tp_; i++,tt++) {
                    *tt = (float)(*info->ptrs_[i]);
                }
                H5Dwrite(info->data_, H5T_NATIVE_FLOAT, info->mem_space_, info->file_space_, H5P_DEFAULT, info->buf_);
            }

            ++info->tstep_;
        }
    }
#endif
  return 0; }
 
static double _hoc_recdata(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 recdata (  );
 return(_r);
}
 
static int  writeMeta (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    char tmp[256];
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->map_) {
            /*****************************************************/
            /* HDF5                                              */
            /*****************************************************/
            if (info->file_ >= 0) {
                if (info->mapping_)
                    H5Dwrite(info->mapping_, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, info->map_);
            }
        }
    }
#endif
  return 0; }
 
static double _hoc_writeMeta(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 writeMeta (  );
 return(_r);
}
 
static int  consolidateTiming (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    //printf("consolidateTiming()\n");
    double tmin = tstart; // values of last report!
    double tmax = tstop; // values of last report!
    double myeps=1e-10;
    double commonDt = Dt;
    //printf("tmin=%g\n", tmin);
    //printf("tmax=%g\n", tmax);
    //printf("Dt=%g\n", Dt);
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->tstart_ < tmin) tmin = info->tstart_;
        if (info->tstop_ > tmax) tmax = info->tstop_;
        if (info->Dt_ != Dt) {
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Dt is not the same throughout reports! Setting Dt to %g\n", Dt);
            info->Dt_ = Dt;
        }
    }
    //printf("tmin=%g\n", tmin);
    //printf("tmax=%g\n", tmax);
    //printf("Dt=%g\n", Dt);

    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        int steps2start = (int)((info->tstart_-tmin)/Dt+.5);
        double dsteps2start = (info->tstart_-tmin)/Dt;
        if (fabs(dsteps2start - (double)(steps2start)) > myeps) {
            info->tstart_ = tmin + steps2start*Dt;
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting start time to %g\n", info->tstart_);
        }
        int steps2stop = (int)((info->tstop_-tmin)/Dt+.5);
        double dsteps2stop = (info->tstop_-tmin)/Dt;
        if (fabs(dsteps2stop - (double)(steps2stop)) > myeps) {
            info->tstop_ = tmin + steps2stop*Dt;
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting stop time to %g\n", info->tstop_);
        }
    }

    tstart = tmin;
    tstop = tmax;
#endif
  return 0; }
 
static double _hoc_consolidateTiming(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 consolidateTiming (  );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    static int first = 1;
    if (first) {
        first = 0;
        nrn_register_recalc_ptr_callback(recalc_ptr_callback);
    }

    if (ifarg(2)) {
        mpirank = floor(*getarg(2));
    }

    if (ifarg(3) && hoc_is_str_arg(3)) {
        INFOCAST;
        Info* info = 0;

        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
        info->nextReport_ = 0;
        info->neuronName_[0]= 0;
        info->rptName_[0]= 0;
        info->path_[0]=0;
        info->handle_ = -1;
        info->neuron_ = 0;
        info->tstart_ = 0;
        info->tstop_ = 0;
        info->Dt_ = 0;
        info->rpt_ = 0;
        info->ptrs_ = 0;
        info->np_ = 0;
        info->nm_ = 0;
        info->tp_ = 0;
        info->mp_ = 0;
        info->tstep_ = 0;
        info->tsteps_ = 0;
        info->groupCreated_ = 0;
        info->data_ = 0;
        info->mapping_ = 0;
        info->map_ =0;

        *ip = info;
        sprintf((*ip)->path_, "%s", gargstr(3));
        sprintf((*ip)->fn_, "%s", gargstr(4));
    }
#else
    if (ifarg(2)) {
        fprintf(stderr, "%s\n", "HDF5 is Disabled, HDF5 reports are not available");
        exit(-1);
    }
#endif
 }
 
}
}
 
static void _destructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    /* need to close datasets etc */
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->data_) {
            H5Sclose(info->file_space_);
            H5Sclose(info->mem_space_);
            H5Dclose(info->data_);
            H5Dclose(info->mapping_);
        }
        H5Fclose(info->file_);
    }
#endif
 }
 
}
}

static void initmodel() {
  int _i; double _save;_ninits++;
{
 {
   writeMeta ( _threadargs_ ) ;
   consolidateTiming ( _threadargs_ ) ;
   net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  tstart , 1.0 ) ;
   }

}
}

static void nrn_init(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 _tsav = -1e20;
#if CACHEVEC
  if (use_cachevec) {
    _v = VEC_V(_ni[_iml]);
  }else
#endif
  {
    _nd = _ml->_nodelist[_iml];
    _v = NODEV(_nd);
  }
 v = _v;
 initmodel();
}}

static double _nrn_current(double _v){double _current=0.;v=_v;{
} return _current;
}

static void nrn_state(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v = 0.0; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 _nd = _ml->_nodelist[_iml];
#if CACHEVEC
  if (use_cachevec) {
    _v = VEC_V(_ni[_iml]);
  }else
#endif
  {
    _nd = _ml->_nodelist[_iml];
    _v = NODEV(_nd);
  }
 v=_v;
{
}}

}

static void terminal(){}

static void _initlists() {
 int _i; static int _first = 1;
  if (!_first) return;
_first = 0;
}

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/HDF5record.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * If the local variable step method is used then the only variables that should\n"
  " * be added are variables of the cell in which this FileRecord\n"
  " * has been instantiated.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    POINT_PROCESS HDF5Record\n"
  "    POINTER pntr\n"
  "    RANGE mpirank : rank of processor\n"
  "    RANGE Dt\n"
  "    RANGE tstart\n"
  "    RANGE tstop\n"
  "    RANGE rpts\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "    mpirank = 0\n"
  "    Dt = .1 (ms)\n"
  "    tstart = 0 (ms)\n"
  "    tstop  = 0 (ms)\n"
  "    rpts = 0\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "    pntr\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "    writeMeta()\n"
  "    consolidateTiming()\n"
  "    net_send(tstart, 1)\n"
  "}\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "    recdata()\n"
  "    if (t<tstop) {\n"
  "        net_send(Dt, 1)\n"
  "    }\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#include <stdlib.h>\n"
  "#include <math.h>\n"
  "\n"
  "#ifndef DISABLE_HDF5\n"
  "#undef pntr\n"
  "#define H5_USE_16_API 1\n"
  "#undef dt\n"
  "#include \"hdf5.h\"\n"
  "#define dt nrn_threads->_dt\n"
  "\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int nrnmpi_numprocs;\n"
  "extern int nrnmpi_myid;\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "\n"
  "typedef struct {\n"
  "    void* nextReport_;\n"
  "    int handle_;\n"
  "    char neuronName_[256];\n"
  "    char rptName_[256];\n"
  "    char path_[512];\n"
  "    char fn_[256];\n"
  "    int tstep_;\n"
  "    int tsteps_;\n"
  "    double tstart_;\n"
  "    double tstop_;\n"
  "    double Dt_;\n"
  "    double** ptrs_; /* list of pointers to hoc variables */\n"
  "    float* buf_;\n"
  "    float* map_;\n"
  "    int np_;\n"
  "    int nm_;\n"
  "    int tp_; /* temporary indicator of passed variable pointers */\n"
  "    int mp_; /* temporary indicator of passed variable pointers */\n"
  "\n"
  "    /* hdf5 version */\n"
  "    hid_t file_;\n"
  "    hid_t neuron_;\n"
  "    hid_t rpt_;\n"
  "    hid_t dataspace_;\n"
  "    hid_t mem_space_;\n"
  "    hid_t file_space_;\n"
  "    hid_t data_;\n"
  "    hid_t mapping_;\n"
  "//    hid_t mapping_space_;\n"
  "//    hid_t map_mem_space_;\n"
  "//    hid_t map_file_space_;\n"
  "    int groupCreated_;\n"
  "\n"
  "} Info;\n"
  "\n"
  "#define INFOCAST Info** ip = (Info**)(&(_p_pntr))\n"
  "\n"
  "#define dp double*\n"
  "extern void nrn_register_recalc_ptr_callback(void (*f)());\n"
  "extern Point_process* ob2pntproc(Object*);\n"
  "extern double* nrn_recalc_ptr(double*);\n"
  "\n"
  "static void recalcptr(Info* info, int cnt, double** old_vp, double* new_v) {\n"
  "    int i;\n"
  "    /*printf(\"recalcptr np_=%d %s\\n\", info->np_, info->path_);*/\n"
  "}\n"
  "\n"
  "static void recalc_ptr_callback() {\n"
  "    Symbol* sym;\n"
  "    int i;\n"
  "    hoc_List* instances;\n"
  "    hoc_Item* q;\n"
  "    /*printf(\"ASCIIrecord.mod recalc_ptr_callback\\n\");*/\n"
  "    /* hoc has a list of the ASCIIRecord instances */\n"
  "    sym = hoc_lookup(\"HDF5Record\");\n"
  "    instances = sym->u.template->olist;\n"
  "    ITERATE(q, instances) {\n"
  "        Info* InfoPtr;\n"
  "        Point_process* pnt;\n"
  "        Object* o = OBJ(q);\n"
  "        /*printf(\"callback for %s\\n\", hoc_object_name(o));*/\n"
  "        pnt = ob2pntproc(o);\n"
  "        _ppvar = pnt->_prop->dparam;\n"
  "        INFOCAST;\n"
  "\n"
  "        for (InfoPtr = *ip; InfoPtr != 0; InfoPtr = (Info*) InfoPtr->nextReport_)\n"
  "            for (i=0; i < InfoPtr->np_; ++i)\n"
  "                InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);\n"
  "    }\n"
  "}\n"
  "\n"
  "#endif  // ifndef DISABLE_HDF5\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "CONSTRUCTOR { : double - loc of point process, int mpirank, string path, string filename\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    static int first = 1;\n"
  "    if (first) {\n"
  "        first = 0;\n"
  "        nrn_register_recalc_ptr_callback(recalc_ptr_callback);\n"
  "    }\n"
  "\n"
  "    if (ifarg(2)) {\n"
  "        mpirank = floor(*getarg(2));\n"
  "    }\n"
  "\n"
  "    if (ifarg(3) && hoc_is_str_arg(3)) {\n"
  "        INFOCAST;\n"
  "        Info* info = 0;\n"
  "\n"
  "        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "        info->nextReport_ = 0;\n"
  "        info->neuronName_[0]= 0;\n"
  "        info->rptName_[0]= 0;\n"
  "        info->path_[0]=0;\n"
  "        info->handle_ = -1;\n"
  "        info->neuron_ = 0;\n"
  "        info->tstart_ = 0;\n"
  "        info->tstop_ = 0;\n"
  "        info->Dt_ = 0;\n"
  "        info->rpt_ = 0;\n"
  "        info->ptrs_ = 0;\n"
  "        info->np_ = 0;\n"
  "        info->nm_ = 0;\n"
  "        info->tp_ = 0;\n"
  "        info->mp_ = 0;\n"
  "        info->tstep_ = 0;\n"
  "        info->tsteps_ = 0;\n"
  "        info->groupCreated_ = 0;\n"
  "        info->data_ = 0;\n"
  "        info->mapping_ = 0;\n"
  "        info->map_ =0;\n"
  "\n"
  "        *ip = info;\n"
  "        sprintf((*ip)->path_, \"%s\", gargstr(3));\n"
  "        sprintf((*ip)->fn_, \"%s\", gargstr(4));\n"
  "    }\n"
  "#else\n"
  "    if (ifarg(2)) {\n"
  "        fprintf(stderr, \"%s\\n\", \"HDF5 is Disabled, HDF5 reports are not available\");\n"
  "        exit(-1);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = *ip;\n"
  "    /* need to close datasets etc */\n"
  "    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "        if (info->data_) {\n"
  "            H5Sclose(info->file_space_);\n"
  "            H5Sclose(info->mem_space_);\n"
  "            H5Dclose(info->data_);\n"
  "            H5Dclose(info->mapping_);\n"
  "        }\n"
  "        H5Fclose(info->file_);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * Resume the event delivery loop for NEURON restore. Call from Hoc only (there's param)\n"
  " *\n"
  " * @param t The initial time\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE restartEvent() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    const double etime = *getarg(1);\n"
  "    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION printInfo() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* ttt = *ip;\n"
  "    for (ttt = *ip; ttt != 0; ttt = (Info*) ttt->nextReport_) {\n"
  "        printf(\"Info-Structure Debugging (%s->%s)\\n\", ttt->rptName_, ttt->neuronName_);\n"
  "        printf(\"========================\\n\");\n"
  "        printf(\"nextReport_= \\t\\t%p\\n\", (void*)ttt->nextReport_);\n"
  "        printf(\"handle_ = \\t\\t%d\\n\", ttt->handle_);\n"
  "        printf(\"neuronName = \\t\\t%s\\n\", ttt->neuronName_);\n"
  "        printf(\"rptName =\\t\\t%s\\n\", ttt->rptName_);\n"
  "        printf(\"path_=\\t\\t%s\\n\", ttt->path_);\n"
  "        printf(\"fn_ =\\t\\t%s\\n\",ttt->fn_);\n"
  "        printf(\"tstep_ =\\t\\t%d\\n\",ttt->tstep_);\n"
  "        printf(\"tsteps_=\\t\\t%d\\n\",ttt->tsteps_);\n"
  "        printf(\"tstart_=\\t\\t%g\\n\",ttt->tstart_);\n"
  "        printf(\"tstop_ =\\t\\t%g\\n\",ttt->tstop_);\n"
  "        printf(\"Dt_=\\t\\t%g\\n\", ttt->Dt_);\n"
  "        printf(\"ptrs_=\\t\\t%p\\n\",  (void*) ttt->ptrs_); /* list of pointers to hoc variables */\n"
  "        printf(\"buf_=\\t\\t%p\\n\",(void*)ttt->buf_);\n"
  "        printf(\"map_=\\t\\t%p\\n\", (void*)ttt->map_);\n"
  "        printf(\"np_=\\t\\t%d\\n\", ttt->np_);\n"
  "        printf(\"nm_=\\t\\t%d\\n\", ttt->nm_);\n"
  "        printf(\"tp_=\\t\\t%d\\n\", ttt->tp_); /* temporary indicator of passed variable pointers */\n"
  "        printf(\"mp_=\\t\\t%d\\n\", ttt->mp_); /* temporary indicator of passed variable pointers */\n"
  "\n"
  "        /* hdf5 version */\n"
  "        printf(\"file_=\\t\\t%lld\\n\", ttt->file_);\n"
  "        printf(\"neuron_=\\t\\t%lld\\n\", ttt->neuron_);\n"
  "        printf(\"rpt_=\\t\\t%lld\\n\", ttt->rpt_);\n"
  "        printf(\"dataspace_=\\t\\t%lld\\n\", ttt->dataspace_);\n"
  "        printf(\"mem_space_=\\t\\t%lld\\n\", ttt->mem_space_);\n"
  "        printf(\"file_space_=\\t\\t%lld\\n\", ttt->file_space_);\n"
  "        printf(\"data_=\\t\\t%lld\\n\", ttt->data_);\n"
  "        printf(\"mapping_=\\t\\t%lld\\n\", ttt->mapping_);\n"
  "        printf(\"groupCreated_=\\t\\t%d\\n\", ttt->groupCreated_);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION newReport() { : string neuronname, string setname, double vars, double tstart, double tstop, double dt, string unit\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* iPtr;\n"
  "    Info* info;\n"
  "    for (iPtr = *ip; iPtr->nextReport_ != 0; iPtr = (Info*) iPtr->nextReport_) {}\n"
  "    int newRpt = 0;\n"
  "    int trial = 0;\n"
  "    int fileOpen = 0;\n"
  "    char fn[1024];\n"
  "\n"
  "    if (iPtr->handle_ == -1) {\n"
  "        if (hoc_is_str_arg(1)) sprintf(iPtr->neuronName_, \"%s\", gargstr(1));\n"
  "        else sprintf(iPtr->neuronName_, \"neuron\");\n"
  "\n"
  "        if (hoc_is_str_arg(2)) sprintf(iPtr->rptName_, \"%s\", gargstr(2));\n"
  "        else sprintf(iPtr->rptName_, \"report\");\n"
  "\n"
  "        sprintf(fn, \"%s/%s.h5\", iPtr->path_, iPtr->fn_);\n"
  "        // printf(\"the filename is: %s\\n\", fn);\n"
  "        hid_t plist = H5Pcreate(H5P_FILE_CREATE);\n"
  "            H5Pset_fapl_stdio(plist);\n"
  "        // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);\n"
  "        iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);\n"
  "        // plist = H5Pcreate(H5P_DATASET_XFER);\n"
  "        // H5Pset_buffer(plist, 2097152, 0, 0);\n"
  "\n"
  "        while ((iPtr->file_ < 0) && (trial < 20)) {\n"
  "            // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);\n"
  "            iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);\n"
  "            trial += 1;\n"
  "            // printf(\"trial %d\\n\", trial);\n"
  "        }\n"
  "        if (iPtr->file_>=0) fileOpen = 1;\n"
  "        // plist = H5Pcreate(H5P_DATASET_XFER);\n"
  "        // H5Pset_buffer(plist, 16777216, 0, 0);\n"
  "        iPtr->handle_ = 0;\n"
  "    }\n"
  "\n"
  "    // there already is a report --> need to create a new info struct\n"
  "    else {\n"
  "        newRpt = 1;\n"
  "\n"
  "        Info* info = 0;\n"
  "        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "        info->handle_ = 0;\n"
  "        info->nextReport_ = 0;\n"
  "        info->neuronName_[0]= 0;\n"
  "        info->rptName_[0]= 0;\n"
  "        info->path_[0]=0;\n"
  "        info->neuron_ = 0;\n"
  "        info->tstart_ = 0;\n"
  "        info->tstop_ = 0;\n"
  "        info->Dt_ = 0;\n"
  "        info->rpt_ = 0;\n"
  "        info->ptrs_ = 0;\n"
  "        info->np_ = 0;\n"
  "        info->nm_ = 0;\n"
  "        info->tp_ = 0;\n"
  "        info->mp_ = 0;\n"
  "        info->tstep_ = 0;\n"
  "        info->tsteps_ = 0;\n"
  "        info->map_ = 0;\n"
  "        info->groupCreated_ = 1;\n"
  "        info->data_ = 0;\n"
  "        info->mapping_ = 0;\n"
  "\n"
  "        if (hoc_is_str_arg(1)) sprintf(info->neuronName_, \"%s\", gargstr(1));\n"
  "        else sprintf(info->neuronName_, \"neuron\");\n"
  "\n"
  "        if (hoc_is_str_arg(2)) sprintf(info->rptName_, \"%s\", gargstr(2));\n"
  "        else sprintf(info->rptName_, \"report\");\n"
  "\n"
  "        sprintf(info->fn_, \"%s\", (*ip)->fn_);\n"
  "        sprintf(info->path_, \"%s\", (*ip)->path_);\n"
  "\n"
  "        info->file_ = (*ip)->file_;\n"
  "        iPtr=info;\n"
  "        fileOpen = 1;\n"
  "    }\n"
  "    if (!fileOpen) {\n"
  "        fprintf(stderr, \"Rank %.0f: file creation failed!\", mpirank);\n"
  "        return 0;\n"
  "    }\n"
  "\n"
  "    char tmp[256];\n"
  "    char unitStr[5];\n"
  "\n"
  "    if (ifarg(3)) {\n"
  "        iPtr->np_   = (int) *getarg(3);\n"
  "        iPtr->ptrs_ = (double**)hoc_Ecalloc(iPtr->np_, sizeof(double*)); hoc_malchk();\n"
  "        iPtr->buf_  = (float*)hoc_Ecalloc(iPtr->np_, sizeof(float)); hoc_malchk();\n"
  "    }\n"
  "\n"
  "    if (ifarg(4) && ifarg(5) && ifarg(6)) {\n"
  "        iPtr->tstart_   = *getarg(4);\n"
  "        iPtr->tstop_    = *getarg(5);\n"
  "        iPtr->Dt_       = *getarg(6);\n"
  "        // printf(\"tstart = %g\\n\", iPtr->tstart_);\n"
  "        // printf(\"tstop = %g\\n\", iPtr->tstop_);\n"
  "        // printf(\"Dt = %g\\n\", iPtr->Dt_);\n"
  "        iPtr->tsteps_   = (int) (((iPtr->tstop_-iPtr->tstart_)/iPtr->Dt_)+.5);\n"
  "        // printf(\"steps = %d\\n\", info->tsteps_);\n"
  "        // iPtr->tsteps_ += 1;\n"
  "        // printf(\"steps = %d\\n\", iPtr->tsteps_);\n"
  "    }\n"
  "\n"
  "    if (hoc_is_str_arg(7)) {\n"
  "        sprintf(unitStr, \"%s\", gargstr(7));\n"
  "    } else {\n"
  "        sprintf(unitStr, \"xx\");\n"
  "    }\n"
  "\n"
  "    tstart = iPtr->tstart_;\n"
  "    tstop  = iPtr->tstop_;\n"
  "    Dt = iPtr->Dt_;\n"
  "\n"
  "    /*****************************************************/\n"
  "    /* hdf5                                              */\n"
  "    /*****************************************************/\n"
  "    // neuron name\n"
  "    sprintf(tmp, \"/%s\", iPtr->neuronName_);\n"
  "\n"
  "    if (iPtr->groupCreated_ ==0) {\n"
  "        // printf(\"create group: %s\\n\", tmp);\n"
  "        iPtr->neuron_ = H5Gcreate(iPtr->file_, tmp, 0);\n"
  "    }\n"
  "\n"
  "    // report name\n"
  "    sprintf(tmp, \"/%s/%s\", iPtr->neuronName_, iPtr->rptName_);\n"
  "    // printf(\"create group: %s\\n\", tmp);\n"
  "    iPtr->rpt_ = H5Gcreate(iPtr->file_, tmp, 0);\n"
  "\n"
  "    // printf(\"info->np_=%d\\n\", info->np_);\n"
  "\n"
  "    // create data set\n"
  "    hsize_t dims[2]; dims[0] = iPtr->tsteps_; dims[1] = iPtr->np_;\n"
  "    iPtr->dataspace_ = H5Screate_simple(2, dims, NULL);\n"
  "    sprintf(tmp, \"/%s/%s/data\", iPtr->neuronName_, iPtr->rptName_);\n"
  "    iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_FLOAT, iPtr->dataspace_, H5P_DEFAULT);\n"
  "    // iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_DOUBLE, iPtr->dataspace_, H5P_DEFAULT);\n"
  "\n"
  "    // select hyperslab for writing each time step separately into dataset\n"
  "    hsize_t off[2]; off[0] = 0; off[1] = 0;\n"
  "    hsize_t size[2]; size[0] = 1; size[1] = iPtr->np_;\n"
  "    hsize_t start[2]; start[0] = 0; start[1] = 0;\n"
  "    iPtr->file_space_ = H5Dget_space(iPtr->data_);\n"
  "    iPtr->mem_space_ = H5Screate_simple(2, size, NULL);\n"
  "    H5Sselect_hyperslab(iPtr->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);\n"
  "\n"
  "    // write attributes\n"
  "    hid_t atype, attr;\n"
  "\n"
  "    // attribute\n"
  "    atype = H5Screate(H5S_SCALAR);\n"
  "    attr  = H5Acreate(iPtr->data_, \"rank\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, H5T_NATIVE_INT, &mpirank);\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // attribute\n"
  "    atype = H5Screate(H5S_SCALAR);\n"
  "    attr  = H5Acreate(iPtr->data_, \"tstart\", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstart_));\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // attribute\n"
  "    atype = H5Screate(H5S_SCALAR);\n"
  "    attr  = H5Acreate(iPtr->data_, \"tstop\", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstop_));\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // attribute\n"
  "    atype = H5Screate(H5S_SCALAR);\n"
  "    attr  = H5Acreate(iPtr->data_, \"Dt\", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->Dt_));\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // attribute\n"
  "    hid_t astring;\n"
  "    atype  = H5Screate(H5S_SCALAR);\n"
  "    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 5);\n"
  "    attr = H5Acreate(iPtr->data_, \"dunit\", astring, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, astring, unitStr);\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // attribute\n"
  "    atype  = H5Screate(H5S_SCALAR);\n"
  "    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 2);\n"
  "    attr = H5Acreate(iPtr->data_, \"tunit\", astring, atype, H5P_DEFAULT);\n"
  "    H5Awrite(attr, astring, \"ms\");\n"
  "    H5Aclose(attr);\n"
  "\n"
  "    // if (!newRpt) *ip = info;\n"
  "    if (newRpt == 1) {\n"
  "        Info* tPtr; int hd = 1;\n"
  "        for (tPtr = *ip; tPtr->nextReport_ != 0; tPtr = (Info*) tPtr->nextReport_, hd++) {}\n"
  "        tPtr->nextReport_ = iPtr;\n"
  "        iPtr->handle_ = hd;\n"
  "    }\n"
  "    rpts += 1;\n"
  "\n"
  "    return iPtr->handle_;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION newMapping() { : double rptHd, string mapping\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "//printf(\"newMapping\\n\");\n"
  "    INFOCAST; Info* iPtr = 0; Info* info = 0;\n"
  "    hsize_t dims[2];\n"
  "    char tmp[256];\n"
  "    hid_t atype, attr, astring;\n"
  "    if (ifarg(1)) {\n"
  "        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "        if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "        else info=iPtr;\n"
  "    }\n"
  "\n"
  "    if (hoc_is_str_arg(2)) {\n"
  "        if (strncmp(gargstr(2), \"point\", 5) == 0) {\n"
  "            info->map_  = (float*)hoc_Ecalloc(info->np_*3, sizeof(float)); hoc_malchk();\n"
  "            dims[0]=3; dims[1]=info->np_;\n"
  "        }\n"
  "        else if (strncmp(gargstr(2), \"compartment3D\", 13) == 0) {\n"
  "            info->map_  = (float*)hoc_Ecalloc(info->np_*4, sizeof(float)); hoc_malchk();\n"
  "            dims[0]=4; dims[1]=info->np_;\n"
  "        }\n"
  "        else if (strncmp(gargstr(2), \"compartment\", 11) == 0) {\n"
  "            info->map_  = (float*)hoc_Ecalloc(info->np_, sizeof(float)); hoc_malchk();\n"
  "            dims[0]=1; dims[1]=info->np_;\n"
  "        }\n"
  "        info->nm_ = dims[0]*dims[1];\n"
  "    }\n"
  "\n"
  "    if(info->file_>=0) {\n"
  "        // create mapping data set\n"
  "        hid_t map = H5Screate_simple(2, dims, NULL);\n"
  "        sprintf(tmp, \"/%s/%s/mapping\", info->neuronName_, info->rptName_);\n"
  "        info->mapping_= H5Dcreate(info->file_, tmp, H5T_NATIVE_FLOAT, map, H5P_DEFAULT);\n"
  "\n"
  "        // hsize_t size[2]; size[0] = 1; size[1] = dim[1]*dim[0];\n"
  "        // info->map_mem_space_ = H5Screate_simple(2, size, NULL);\n"
  "        // H5Sselect_hyperslab(info->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);\n"
  "\n"
  "        if (strncmp(gargstr(2), \"point\", 5) == 0) {\n"
  "            // attribute\n"
  "            atype  = H5Screate(H5S_SCALAR);\n"
  "            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);\n"
  "            attr = H5Acreate(info->mapping_, \"type\", astring, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, astring, \"point\");\n"
  "            H5Aclose(attr);\n"
  "        }\n"
  "        else if (strncmp(gargstr(2), \"compartment\", 11) == 0) {\n"
  "            int sec, soma, axon, basal, apic;\n"
  "            sec = soma = axon = basal = apic = 0;\n"
  "\n"
  "            if (ifarg(3)) {\n"
  "                sec = (int) *getarg(3);\n"
  "            }\n"
  "            if (ifarg(4)) {\n"
  "                soma = (int) *getarg(4);\n"
  "            }\n"
  "            if (ifarg(5)) {\n"
  "                axon = (int) *getarg(5);\n"
  "            }\n"
  "            if (ifarg(6)) {\n"
  "                basal = (int) *getarg(6);\n"
  "            }\n"
  "            if (ifarg(7)) {\n"
  "                apic = (int) *getarg(7);\n"
  "            }\n"
  "\n"
  "            // attribute\n"
  "            atype  = H5Screate(H5S_SCALAR);\n"
  "            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);\n"
  "            attr = H5Acreate(info->mapping_, \"type\", astring, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, astring, gargstr(2));\n"
  "            H5Aclose(attr);\n"
  "\n"
  "            // attribute\n"
  "            atype = H5Screate(H5S_SCALAR);\n"
  "            attr  = H5Acreate(info->mapping_, \"sections\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, H5T_NATIVE_INT, &sec);\n"
  "            H5Aclose(attr);\n"
  "\n"
  "            // attribute\n"
  "            atype = H5Screate(H5S_SCALAR);\n"
  "            attr  = H5Acreate(info->mapping_, \"soma\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, H5T_NATIVE_INT, &soma);\n"
  "            H5Aclose(attr);\n"
  "\n"
  "            // attribute\n"
  "            atype = H5Screate(H5S_SCALAR);\n"
  "            attr  = H5Acreate(info->mapping_, \"axon\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, H5T_NATIVE_INT, &axon);\n"
  "            H5Aclose(attr);\n"
  "\n"
  "            // attribute\n"
  "            atype = H5Screate(H5S_SCALAR);\n"
  "            attr  = H5Acreate(info->mapping_, \"basal\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, H5T_NATIVE_INT, &basal);\n"
  "            H5Aclose(attr);\n"
  "\n"
  "            // attribute\n"
  "            atype = H5Screate(H5S_SCALAR);\n"
  "            attr  = H5Acreate(info->mapping_, \"apic\", H5T_NATIVE_INT, atype, H5P_DEFAULT);\n"
  "            H5Awrite(attr, H5T_NATIVE_INT, &apic);\n"
  "            H5Aclose(attr);\n"
  "\n"
  "        }\n"
  "\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE addvar() { : int rptHD, double* pd\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = 0; Info* iPtr = 0;\n"
  "    //printf(\"addVar\\n\");\n"
  "    if (ifarg(1)) {\n"
  "        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "        if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "        else info=iPtr;\n"
  "    }\n"
  "\n"
  "    if (info->tp_ < info->np_) {\n"
  "        info->ptrs_[info->tp_] = hoc_pgetarg(2);\n"
  "        ++info->tp_;\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE addmapping() { : int rptHD, double var1, double var2, double var3\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = 0; Info* iPtr = 0;\n"
  "    //printf(\"addMapping\\n\");\n"
  "    if (ifarg(1)) {\n"
  "        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "        if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "        else info=iPtr;\n"
  "    }\n"
  "\n"
  "    // printf(\"getarg(2) = %g\\n\", *getarg(2));\n"
  "    if (info->mp_ < info->np_) {\n"
  "        // printf(\"info->mp_ = %d\\n\", info->mp_);\n"
  "        if (ifarg(2)) {\n"
  "            info->map_[info->mp_] = (float) *getarg(2);\n"
  "            // printf(\"info->map = %g\\n\", info->map_[info->mp_]);\n"
  "        }\n"
  "        if (ifarg(3)) {\n"
  "            info->map_[info->mp_+info->np_] = (float) *getarg(3);\n"
  "        }\n"
  "        if (ifarg(4)) {\n"
  "            info->map_[info->mp_+info->np_*2] = (float) *getarg(4);\n"
  "        }\n"
  "        if (ifarg(5)) {\n"
  "            info->map_[info->mp_+info->np_*3] = (float) *getarg(5);\n"
  "        }\n"
  "        ++info->mp_;\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE recdata() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = *ip;\n"
  "    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "        if ((t >= info->tstart_) && (t < info->tstop_) && (info->tstep_ < info->tsteps_)) {\n"
  "\n"
  "            /*****************************************************/\n"
  "            /* HDF5                                              */\n"
  "            /*****************************************************/\n"
  "\n"
  "            if ((info->file_>=0) && (info->data_)) {\n"
  "                hsize_t off[2] = {info->tstep_, 0};\n"
  "                hsize_t size[2] = {1, info->np_};\n"
  "\n"
  "                H5Sselect_hyperslab(info->file_space_, H5S_SELECT_SET, off, NULL, size, NULL);\n"
  "\n"
  "                float* tt = info->buf_;\n"
  "                int i;\n"
  "                for(i=0; i< info->tp_; i++,tt++) {\n"
  "                    *tt = (float)(*info->ptrs_[i]);\n"
  "                }\n"
  "                H5Dwrite(info->data_, H5T_NATIVE_FLOAT, info->mem_space_, info->file_space_, H5P_DEFAULT, info->buf_);\n"
  "            }\n"
  "\n"
  "            ++info->tstep_;\n"
  "        }\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE writeMeta() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = *ip;\n"
  "    char tmp[256];\n"
  "    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "        if (info->map_) {\n"
  "            /*****************************************************/\n"
  "            /* HDF5                                              */\n"
  "            /*****************************************************/\n"
  "            if (info->file_ >= 0) {\n"
  "                if (info->mapping_)\n"
  "                    H5Dwrite(info->mapping_, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, info->map_);\n"
  "            }\n"
  "        }\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * currently, consolidateTiming() has a simple logic:\n"
  " *  1. go through all reports and get minimum start time and maximum stop time\n"
  " *  2. check whether all reports have same Dt\n"
  " *  3. check whether the start and stop times are consistent with common Dt\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE consolidateTiming() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = *ip;\n"
  "    //printf(\"consolidateTiming()\\n\");\n"
  "    double tmin = tstart; // values of last report!\n"
  "    double tmax = tstop; // values of last report!\n"
  "    double myeps=1e-10;\n"
  "    double commonDt = Dt;\n"
  "    //printf(\"tmin=%g\\n\", tmin);\n"
  "    //printf(\"tmax=%g\\n\", tmax);\n"
  "    //printf(\"Dt=%g\\n\", Dt);\n"
  "    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "        if (info->tstart_ < tmin) tmin = info->tstart_;\n"
  "        if (info->tstop_ > tmax) tmax = info->tstop_;\n"
  "        if (info->Dt_ != Dt) {\n"
  "            if (mpirank == 0) printf(\"[ASCIIrecord] Warning: Dt is not the same throughout reports! Setting Dt to %g\\n\", Dt);\n"
  "            info->Dt_ = Dt;\n"
  "        }\n"
  "    }\n"
  "    //printf(\"tmin=%g\\n\", tmin);\n"
  "    //printf(\"tmax=%g\\n\", tmax);\n"
  "    //printf(\"Dt=%g\\n\", Dt);\n"
  "\n"
  "    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "        int steps2start = (int)((info->tstart_-tmin)/Dt+.5);\n"
  "        double dsteps2start = (info->tstart_-tmin)/Dt;\n"
  "        if (fabs(dsteps2start - (double)(steps2start)) > myeps) {\n"
  "            info->tstart_ = tmin + steps2start*Dt;\n"
  "            if (mpirank == 0) printf(\"[ASCIIrecord] Warning: Adjusting reporting start time to %g\\n\", info->tstart_);\n"
  "        }\n"
  "        int steps2stop = (int)((info->tstop_-tmin)/Dt+.5);\n"
  "        double dsteps2stop = (info->tstop_-tmin)/Dt;\n"
  "        if (fabs(dsteps2stop - (double)(steps2stop)) > myeps) {\n"
  "            info->tstop_ = tmin + steps2stop*Dt;\n"
  "            if (mpirank == 0) printf(\"[ASCIIrecord] Warning: Adjusting reporting stop time to %g\\n\", info->tstop_);\n"
  "        }\n"
  "    }\n"
  "\n"
  "    tstart = tmin;\n"
  "    tstop = tmax;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  ;
#endif
