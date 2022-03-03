/* Created by Language version: 7.7.0 */
/* VECTORIZED */
#define NRN_VECTORIZED 1
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
 
#define nrn_init _nrn_init__ALU
#define _nrn_initial _nrn_initial__ALU
#define nrn_cur _nrn_cur__ALU
#define _nrn_current _nrn_current__ALU
#define nrn_jacob _nrn_jacob__ALU
#define nrn_state _nrn_state__ALU
#define _net_receive _net_receive__ALU 
#define average average__ALU 
#define addvar addvar__ALU 
#define constant constant__ALU 
#define restartEvent restartEvent__ALU 
#define setop setop__ALU 
#define summation summation__ALU 
 
#define _threadargscomma_ _p, _ppvar, _thread, _nt,
#define _threadargsprotocomma_ double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt,
#define _threadargs_ _p, _ppvar, _thread, _nt
#define _threadargsproto_ double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt
 	/*SUPPRESS 761*/
	/*SUPPRESS 762*/
	/*SUPPRESS 763*/
	/*SUPPRESS 765*/
	 extern double *getarg();
 /* Thread safe. No static _p or _ppvar. */
 
#define t _nt->_t
#define dt _nt->_dt
#define Dt _p[0]
#define output _p[1]
#define v _p[2]
#define _tsav _p[3]
#define _nd_area  *_ppvar[0]._pval
#define ptr	*_ppvar[2]._pval
#define _p_ptr	_ppvar[2]._pval
 
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
 static Datum* _extcall_thread;
 static Prop* _extcall_prop;
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_average();
 static double _hoc_addvar();
 static double _hoc_constant();
 static double _hoc_restartEvent();
 static double _hoc_setop();
 static double _hoc_summation();
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
 _extcall_prop = _prop;
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
 "average", _hoc_average,
 "addvar", _hoc_addvar,
 "constant", _hoc_constant,
 "restartEvent", _hoc_restartEvent,
 "setop", _hoc_setop,
 "summation", _hoc_summation,
 0, 0
};
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt", "ms",
 0,0
};
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
"ALU",
 "Dt",
 "output",
 0,
 0,
 0,
 "ptr",
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
 	_p = nrn_prop_data_alloc(_mechtype, 4, _prop);
 	/*initialize range parameters*/
 	Dt = 0.1;
 	output = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 4;
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
 static void bbcore_write(double*, int*, int*, int*, _threadargsproto_);
 extern void hoc_reg_bbcore_write(int, void(*)(double*, int*, int*, int*, _threadargsproto_));
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _ALU_reg() {
	int _vectorized = 1;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 1,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 	register_destructor(_destructor);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
   hoc_reg_bbcore_write(_mechtype, bbcore_write);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 4, 4);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
  hoc_register_dparam_semantics(_mechtype, 3, "netsend");
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 ALU /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ALU.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int average(_threadargsproto_);
static int addvar(_threadargsproto_);
static int constant(_threadargsproto_);
static int restartEvent(_threadargsproto_);
static int setop(_threadargsproto_);
static int summation(_threadargsproto_);
 
/*VERBATIM*/

#ifndef CORENEURON_BUILD
extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern int ifarg(int iarg);

typedef struct {
    //! list of pointers to hoc variables
    double** ptrs_;

    /*! list of scalars to apply to corresponding variables; useful for making units of variables
     * from different sources consistent (e.g. i current sources may be distributed, mA/cm^2, or point processes, nA)
     */
    double * scalars_;

    //! number of elements stored in the vectors
    int np_;

    //! number of slots allocated to the vectors
    int psize_;

    //! function pointer to execute when net_receive is triggered
    int (*process)(_threadargsproto_);
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

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
    sym = hoc_lookup("ALU");
    instances = sym->u.template->olist;
    ITERATE(q, instances) {
        Info* InfoPtr;
        Point_process* pnt;
        Object* o = OBJ(q);
        /*printf("callback for %s\n", hoc_object_name(o));*/
        pnt = ob2pntproc(o);
        Datum* _ppvar = pnt->_prop->dparam;
        INFOCAST;
        InfoPtr = *ip;
        for (i=0; i < InfoPtr->np_; ++i)
            InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);
    }
}
#endif
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    info->process(_threadargs_);
#endif
}
 net_send ( _tqitem, _args, _pnt, t +  Dt - 1e-5 , 1.0 ) ;
   } }
 
static int  restartEvent ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    const double etime = *getarg(1);
    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
#endif
  return 0; }
 
static double _hoc_restartEvent(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 restartEvent ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  addvar ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
	if (info->np_ >= info->psize_) {
		info->psize_ += 10;
		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();
        info->scalars_ = (double*) hoc_Erealloc(info->scalars_, info->psize_*sizeof(double)); hoc_malchk();
	}

	info->ptrs_[info->np_] = hoc_pgetarg(1);
    if( ifarg(2)) {
        info->scalars_[info->np_] = *getarg(2);
    } else {
        info->scalars_[info->np_] = 1;
    }

	++info->np_;
    //printf("I have %d values.. (new = %g * %g)\n", info->np_, *(info->ptrs_[info->np_-1]), info->scalars_[info->np_-1] );
#endif
}
  return 0; }
 
static double _hoc_addvar(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 addvar ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  constant ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    if( info->np_ > 0 ) {
        output = info->scalars_[0];
    } else {
        output = 0;
    }
#endif
}
  return 0; }
 
static double _hoc_constant(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 constant ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  average ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
	int i;
	double n = 0;
	for (i=0; i < info->np_; ++i) {
      //  printf("%f", (*info->ptrs_[i] * info->scalars_[i]) );
		n += (*info->ptrs_[i] * info->scalars_[i]);
	}
    //printf("\n");
//	output = n/info->np_;
	if (info->np_ > 0)
	  output = n/info->np_;
	else output = 0;
#endif
}
  return 0; }
 
static double _hoc_average(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 average ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  summation ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST; Info* info = *ip;
	int i;
	double n = 0;
	for (i=0; i < info->np_; ++i) {
        //printf("%f = %f * %f\n", (*info->ptrs_[i] * info->scalars_[i]), *info->ptrs_[i], info->scalars_[i] );
		n += (*info->ptrs_[i] * info->scalars_[i]);
	}

    output = n;
#endif
}
  return 0; }
 
static double _hoc_summation(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 summation ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  setop ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    INFOCAST; Info* info = *ip;

    char *opname = NULL;
    if (!hoc_is_str_arg(1)) {
        exit(0);
    }

    opname = gargstr(1);
    if( strcmp( opname, "summation" ) == 0 ) {
        info->process = &summation;
    } else if ( strcmp( opname, "average" ) == 0 ) {
        info->process = &average;
    } else if ( strcmp( opname, "constant" ) == 0 ) {
        info->process = &constant;
    } else {
        fprintf( stderr, "Error: unknown operation '%s' for ALU object.  Terminating.\n", opname );
        exit(0);
    }
#endif
}
  return 0; }
 
static double _hoc_setop(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 setop ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
/** not executed in coreneuron and hence need empty stubs only */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
 
static void _constructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
    static int first = 1;
    if (first) {
        first = 0;
        nrn_register_recalc_ptr_callback(recalc_ptr_callback);
    }

    INFOCAST;
    Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
    info->psize_ = 10;
    info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();
    info->scalars_ = (double*)hoc_Ecalloc(info->psize_, sizeof(double)); hoc_malchk();
    info->np_ = 0;
    *ip = info;

    if (ifarg(2)) {
        Dt = *getarg(2);
    }

    //default operation is average
    info->process = &average;
#endif
}
 }
 
}
}
 
static void _destructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
	INFOCAST;
    Info* info = *ip;
	free(info->ptrs_);
	free(info);
#endif
}
 }
 
}
}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
 {
   net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  0.0 , 1.0 ) ;
   }

}
}

static void nrn_init(_NrnThread* _nt, _Memb_list* _ml, int _type){
double* _p; Datum* _ppvar; Datum* _thread;
Node *_nd; double _v; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
_thread = _ml->_thread;
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
 initmodel(_p, _ppvar, _thread, _nt);
}
}

static double _nrn_current(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt, double _v){double _current=0.;v=_v;{
} return _current;
}

static void nrn_state(_NrnThread* _nt, _Memb_list* _ml, int _type) {
double* _p; Datum* _ppvar; Datum* _thread;
Node *_nd; double _v = 0.0; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
_thread = _ml->_thread;
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

static void _initlists(){
 double _x; double* _p = &_x;
 int _i; static int _first = 1;
  if (!_first) return;
_first = 0;
}

#if defined(__cplusplus)
} /* extern "C" */
#endif

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ALU.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "If the local variable step method is used then the only variables that should\n"
  "be added are variables of the cell in which this ALU has been instantiated.\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "	THREADSAFE\n"
  "	POINT_PROCESS ALU\n"
  "	BBCOREPOINTER ptr\n"
  "	RANGE Dt\n"
  "	RANGE output\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "	Dt = .1 (ms)\n"
  "	output = 0\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "	ptr\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "	net_send(0, 1)\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#ifndef CORENEURON_BUILD\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern int ifarg(int iarg);\n"
  "\n"
  "typedef struct {\n"
  "    //! list of pointers to hoc variables\n"
  "    double** ptrs_;\n"
  "\n"
  "    /*! list of scalars to apply to corresponding variables; useful for making units of variables\n"
  "     * from different sources consistent (e.g. i current sources may be distributed, mA/cm^2, or point processes, nA)\n"
  "     */\n"
  "    double * scalars_;\n"
  "\n"
  "    //! number of elements stored in the vectors\n"
  "    int np_;\n"
  "\n"
  "    //! number of slots allocated to the vectors\n"
  "    int psize_;\n"
  "\n"
  "    //! function pointer to execute when net_receive is triggered\n"
  "    int (*process)(_threadargsproto_);\n"
  "} Info;\n"
  "\n"
  "#define INFOCAST Info** ip = (Info**)(&(_p_ptr))\n"
  "\n"
  "#define dp double*\n"
  "extern void nrn_register_recalc_ptr_callback(void (*f)());\n"
  "extern Point_process* ob2pntproc(Object*);\n"
  "extern double* nrn_recalc_ptr(double*);\n"
  "\n"
  "static void recalcptr(Info* info, int cnt, double** old_vp, double* new_v) {\n"
  "    int i;\n"
  "    /*printf(\"recalcptr np_=%d %s\\n\", info->np_, info->path_);*/\n"
  "\n"
  "}\n"
  "static void recalc_ptr_callback() {\n"
  "    Symbol* sym;\n"
  "    int i;\n"
  "    hoc_List* instances;\n"
  "    hoc_Item* q;\n"
  "    /*printf(\"ASCIIrecord.mod recalc_ptr_callback\\n\");*/\n"
  "    /* hoc has a list of the ASCIIRecord instances */\n"
  "    sym = hoc_lookup(\"ALU\");\n"
  "    instances = sym->u.template->olist;\n"
  "    ITERATE(q, instances) {\n"
  "        Info* InfoPtr;\n"
  "        Point_process* pnt;\n"
  "        Object* o = OBJ(q);\n"
  "        /*printf(\"callback for %s\\n\", hoc_object_name(o));*/\n"
  "        pnt = ob2pntproc(o);\n"
  "        Datum* _ppvar = pnt->_prop->dparam;\n"
  "        INFOCAST;\n"
  "        InfoPtr = *ip;\n"
  "        for (i=0; i < InfoPtr->np_; ++i)\n"
  "            InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);\n"
  "    }\n"
  "}\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    info->process(_threadargs_);\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "    net_send(Dt - 1e-5, 1)\n"
  "}\n"
  "\n"
  "CONSTRUCTOR {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    static int first = 1;\n"
  "    if (first) {\n"
  "        first = 0;\n"
  "        nrn_register_recalc_ptr_callback(recalc_ptr_callback);\n"
  "    }\n"
  "\n"
  "    INFOCAST;\n"
  "    Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "    info->psize_ = 10;\n"
  "    info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();\n"
  "    info->scalars_ = (double*)hoc_Ecalloc(info->psize_, sizeof(double)); hoc_malchk();\n"
  "    info->np_ = 0;\n"
  "    *ip = info;\n"
  "\n"
  "    if (ifarg(2)) {\n"
  "        Dt = *getarg(2);\n"
  "    }\n"
  "\n"
  "    //default operation is average\n"
  "    info->process = &average;\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "	INFOCAST;\n"
  "    Info* info = *ip;\n"
  "	free(info->ptrs_);\n"
  "	free(info);\n"
  "#endif\n"
  "}\n"
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
  "COMMENT\n"
  "/*!\n"
  " * Include another variable in the arithmetic operation\n"
  " * @param variable pointers\n"
  " * @param scalar (optional, 1 by default)\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE addvar() { : double* pd\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "	if (info->np_ >= info->psize_) {\n"
  "		info->psize_ += 10;\n"
  "		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();\n"
  "        info->scalars_ = (double*) hoc_Erealloc(info->scalars_, info->psize_*sizeof(double)); hoc_malchk();\n"
  "	}\n"
  "\n"
  "	info->ptrs_[info->np_] = hoc_pgetarg(1);\n"
  "    if( ifarg(2)) {\n"
  "        info->scalars_[info->np_] = *getarg(2);\n"
  "    } else {\n"
  "        info->scalars_[info->np_] = 1;\n"
  "    }\n"
  "\n"
  "	++info->np_;\n"
  "    //printf(\"I have %d values.. (new = %g * %g)\\n\", info->np_, *(info->ptrs_[info->np_-1]), info->scalars_[info->np_-1] );\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "COMMENT\n"
  "/*!\n"
  " * Ignore the ptr and instead just report the constant value.  This is a hack to allow reporting of the\n"
  " * area of a section.  A better solution should be created\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE constant() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    if( info->np_ > 0 ) {\n"
  "        output = info->scalars_[0];\n"
  "    } else {\n"
  "        output = 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/*!\n"
  " * Take an average of all the variables assigned to this ALU object\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE average() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "	int i;\n"
  "	double n = 0;\n"
  "	for (i=0; i < info->np_; ++i) {\n"
  "      //  printf(\"%f\", (*info->ptrs_[i] * info->scalars_[i]) );\n"
  "		n += (*info->ptrs_[i] * info->scalars_[i]);\n"
  "	}\n"
  "    //printf(\"\\n\");\n"
  "//	output = n/info->np_;\n"
  "	if (info->np_ > 0)\n"
  "	  output = n/info->np_;\n"
  "	else output = 0;\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "COMMENT\n"
  "/*!\n"
  " * Take a summation of all the variables assigned to this ALU object\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE summation() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST; Info* info = *ip;\n"
  "	int i;\n"
  "	double n = 0;\n"
  "	for (i=0; i < info->np_; ++i) {\n"
  "        //printf(\"%f = %f * %f\\n\", (*info->ptrs_[i] * info->scalars_[i]), *info->ptrs_[i], info->scalars_[i] );\n"
  "		n += (*info->ptrs_[i] * info->scalars_[i]);\n"
  "	}\n"
  "\n"
  "    output = n;\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "COMMENT\n"
  "/*!\n"
  " * Set the operation performed when NET_RECEIVE block executes\n"
  " *\n"
  " * @param opname The name of the function to be executed\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE setop() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "    INFOCAST; Info* info = *ip;\n"
  "\n"
  "    char *opname = NULL;\n"
  "    if (!hoc_is_str_arg(1)) {\n"
  "        exit(0);\n"
  "    }\n"
  "\n"
  "    opname = gargstr(1);\n"
  "    if( strcmp( opname, \"summation\" ) == 0 ) {\n"
  "        info->process = &summation;\n"
  "    } else if ( strcmp( opname, \"average\" ) == 0 ) {\n"
  "        info->process = &average;\n"
  "    } else if ( strcmp( opname, \"constant\" ) == 0 ) {\n"
  "        info->process = &constant;\n"
  "    } else {\n"
  "        fprintf( stderr, \"Error: unknown operation '%s' for ALU object.  Terminating.\\n\", opname );\n"
  "        exit(0);\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "/** not executed in coreneuron and hence need empty stubs only */\n"
  "static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "ENDVERBATIM\n"
  ;
#endif
