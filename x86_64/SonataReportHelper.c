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
 
#define nrn_init _nrn_init__SonataReportHelper
#define _nrn_initial _nrn_initial__SonataReportHelper
#define nrn_cur _nrn_cur__SonataReportHelper
#define _nrn_current _nrn_current__SonataReportHelper
#define nrn_jacob _nrn_jacob__SonataReportHelper
#define nrn_state _nrn_state__SonataReportHelper
#define _net_receive _net_receive__SonataReportHelper 
#define add_spikes_population add_spikes_population__SonataReportHelper 
#define close_spikefile close_spikefile__SonataReportHelper 
#define create_spikefile create_spikefile__SonataReportHelper 
#define clear clear__SonataReportHelper 
#define disable_auto_flush disable_auto_flush__SonataReportHelper 
#define flush flush__SonataReportHelper 
#define make_comm make_comm__SonataReportHelper 
#define pre_savestate pre_savestate__SonataReportHelper 
#define prepare_datasets prepare_datasets__SonataReportHelper 
#define restorestate restorestate__SonataReportHelper 
#define restoretime restoretime__SonataReportHelper 
#define savestate savestate__SonataReportHelper 
#define set_max_buffer_size_hint set_max_buffer_size_hint__SonataReportHelper 
#define set_steps_to_buffer set_steps_to_buffer__SonataReportHelper 
#define write_spikes write_spikes__SonataReportHelper 
#define write_spike_populations write_spike_populations__SonataReportHelper 
 
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
#define activeStep _p[0]
#define initialStep _p[1]
#define v _p[2]
#define _tsav _p[3]
#define _nd_area  *_ppvar[0]._pval
 
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
 static int hoc_nrnpointerindex =  -1;
 static Datum* _extcall_thread;
 static Prop* _extcall_prop;
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_add_spikes_population();
 static double _hoc_close_spikefile();
 static double _hoc_create_spikefile();
 static double _hoc_clear();
 static double _hoc_disable_auto_flush();
 static double _hoc_flush();
 static double _hoc_make_comm();
 static double _hoc_pre_savestate();
 static double _hoc_prepare_datasets();
 static double _hoc_redirect();
 static double _hoc_restorestate();
 static double _hoc_restoretime();
 static double _hoc_savestate();
 static double _hoc_set_max_buffer_size_hint();
 static double _hoc_set_steps_to_buffer();
 static double _hoc_write_spikes();
 static double _hoc_write_spike_populations();
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
 "add_spikes_population", _hoc_add_spikes_population,
 "close_spikefile", _hoc_close_spikefile,
 "create_spikefile", _hoc_create_spikefile,
 "clear", _hoc_clear,
 "disable_auto_flush", _hoc_disable_auto_flush,
 "flush", _hoc_flush,
 "make_comm", _hoc_make_comm,
 "pre_savestate", _hoc_pre_savestate,
 "prepare_datasets", _hoc_prepare_datasets,
 "redirect", _hoc_redirect,
 "restorestate", _hoc_restorestate,
 "restoretime", _hoc_restoretime,
 "savestate", _hoc_savestate,
 "set_max_buffer_size_hint", _hoc_set_max_buffer_size_hint,
 "set_steps_to_buffer", _hoc_set_steps_to_buffer,
 "write_spikes", _hoc_write_spikes,
 "write_spike_populations", _hoc_write_spike_populations,
 0, 0
};
#define redirect redirect_SonataReportHelper
 extern double redirect( _threadargsproto_ );
 /* declare global and static user variables */
#define Dt Dt_SonataReportHelper
 double Dt = 0.1;
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt_SonataReportHelper", "ms",
 0,0
};
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 "Dt_SonataReportHelper", &Dt_SonataReportHelper,
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
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"SonataReportHelper",
 "activeStep",
 "initialStep",
 0,
 0,
 0,
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
 	activeStep = 0;
 	initialStep = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 4;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 
#define _tqitem &(_ppvar[2]._pvoid)
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _SonataReportHelper_reg() {
	int _vectorized = 1;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 1,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 4, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "netsend");
 add_nrn_artcell(_mechtype, 2);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 SonataReportHelper /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SonataReportHelper.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int add_spikes_population(_threadargsproto_);
static int close_spikefile(_threadargsproto_);
static int create_spikefile(_threadargsproto_);
static int clear(_threadargsproto_);
static int disable_auto_flush(_threadargsproto_);
static int flush(_threadargsproto_);
static int make_comm(_threadargsproto_);
static int pre_savestate(_threadargsproto_);
static int prepare_datasets(_threadargsproto_);
static int restorestate(_threadargsproto_);
static int restoretime(_threadargsproto_);
static int savestate(_threadargsproto_);
static int set_max_buffer_size_hint(_threadargsproto_);
static int set_steps_to_buffer(_threadargsproto_);
static int write_spikes(_threadargsproto_);
static int write_spike_populations(_threadargsproto_);
 
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include <stdint.h>
#include <bbp/sonata/reports.h>
#include <mpi.h>
    extern int ifarg(int iarg);
    extern double* getarg(int iarg);
    extern double* nrn_recalc_ptr(double*);
    extern void nrn_register_recalc_ptr_callback(void (*f)(void));
    extern double* vector_vec();
    extern int vector_capacity();
    extern void* vector_arg(int);

    void sonataRefreshPointers() { //callback function to update data locations before runtime
        sonata_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function
    }
#endif
#endif
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_record_data(activeStep);
    activeStep++;
#endif
#endif
 artcell_net_send ( _tqitem, _args, _pnt, t +  Dt , 1.0 ) ;
   } }
 
static int  make_comm ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_setup_communicators();
#endif
#endif
}
  return 0; }
 
static double _hoc_make_comm(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 make_comm ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  prepare_datasets ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_prepare_datasets();
#endif
#endif
}
  return 0; }
 
static double _hoc_prepare_datasets(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 prepare_datasets ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  disable_auto_flush ( _threadargsproto_ ) {
    return 0; }
 
static double _hoc_disable_auto_flush(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 disable_auto_flush ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  set_steps_to_buffer ( _threadargsproto_ ) {
    return 0; }
 
static double _hoc_set_steps_to_buffer(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 set_steps_to_buffer ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  set_max_buffer_size_hint ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int buffer_size = (int) *getarg(1);
    sonata_set_max_buffer_size_hint(buffer_size);
#endif
#endif
  return 0; }
 
static double _hoc_set_max_buffer_size_hint(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 set_max_buffer_size_hint ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  flush ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    // Note: flush uses actual time (t) whereas recData uses timestep.  Should try to only use one or the other in the future
    sonata_flush( t );
#endif
#endif
  return 0; }
 
static double _hoc_flush(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 flush ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  pre_savestate ( _threadargsproto_ ) {
    return 0; }
 
static double _hoc_pre_savestate(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 pre_savestate ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  savestate ( _threadargsproto_ ) {
    return 0; }
 
static double _hoc_savestate(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 savestate ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  restoretime ( _threadargsproto_ ) {
   initialStep = t / Dt ;
    return 0; }
 
static double _hoc_restoretime(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 restoretime ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  restorestate ( _threadargsproto_ ) {
   activeStep = t / Dt ;
    return 0; }
 
static double _hoc_restorestate(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 restorestate ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double redirect ( _threadargsproto_ ) {
   double _lredirect;
 
return _lredirect;
 }
 
static double _hoc_redirect(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  redirect ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  clear ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_clear();
#endif
#endif
  return 0; }
 
static double _hoc_clear(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 clear ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  create_spikefile ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    char output_dir[256] = ".";
    // output dir
    if (ifarg(1)) {
        sprintf(output_dir,"%s", gargstr(1));
    }
    sonata_create_spikefile(output_dir);
#endif
#endif
  return 0; }
 
static double _hoc_create_spikefile(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 create_spikefile ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_spike_populations ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_write_spike_populations();
#endif
#endif
  return 0; }
 
static double _hoc_write_spike_populations(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_spike_populations ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  close_spikefile ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_close_spikefile();
#endif
#endif
  return 0; }
 
static double _hoc_close_spikefile(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 close_spikefile ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_spikes ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    char output_dir[256] = ".";
    char population_name[256] = "All";
    double *time = NULL, *gid = NULL;
    int num_spikes = 0;
    int num_gids = 0;
    void* v1;
    void* v2;

    // first vector is time of spikes
    if (ifarg(1)) {
        v1 = vector_arg(1);
        time = vector_vec(v1);
        num_spikes = vector_capacity(v1);
    }

    // second vector is associated gids
    if (ifarg(2)) {
        v2 = vector_arg(2);
        gid = vector_vec(v2);
        num_gids = vector_capacity(v2);
    }

    // output dir
    if (ifarg(3)) {
        sprintf(output_dir,"%s", gargstr(3));
    }

    if (ifarg(4)) {
        sprintf(population_name,"%s", gargstr(4));
    }

    int* int_gid = malloc(num_gids * sizeof(int));
    int i;
    for(i=0; i<num_spikes; ++i) {
        int_gid[i] = (int)gid[i];
    }
    sonata_create_spikefile(output_dir);
    sonata_add_spikes_population(population_name, 0, time, num_spikes, int_gid, num_gids);
    sonata_write_spike_populations();
    sonata_close_spikefile();
    free(int_gid);
#endif
#endif
  return 0; }
 
static double _hoc_write_spikes(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_spikes ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  add_spikes_population ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    char population_name[256] = "All";
    int population_offset = 0;
    double *time = NULL, *gid = NULL;
    int num_spikes = 0;
    int num_gids = 0;
    void* v1;
    void* v2;

    // first vector is time of spikes
    if (ifarg(1)) {
        v1 = vector_arg(1);
        time = vector_vec(v1);
        num_spikes = vector_capacity(v1);
    }

    // second vector is associated gids
    if (ifarg(2)) {
        v2 = vector_arg(2);
        gid = vector_vec(v2);
        num_gids = vector_capacity(v2);
    }

    if (ifarg(3)) {
        sprintf(population_name,"%s", gargstr(3));
    }

    if (ifarg(4)) {
        population_offset = (int) *getarg(4);
    }

    int* int_gid = malloc(num_gids * sizeof(int));
    int i;
    for(i=0; i<num_spikes; ++i) {
        int_gid[i] = (int)gid[i];
    }
    sonata_add_spikes_population(population_name, population_offset, time, num_spikes, int_gid, num_gids);
    free(int_gid);
#endif
#endif
  return 0; }
 
static double _hoc_add_spikes_population(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 add_spikes_population ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
/**
* \param 1: Dt (double, optional). If not given no initializaton is performed
* \param 2: register_recalc_ptr (double, optional). By default will invoke
*    nrn_register_recalc_ptr_callback, which can be disabled by passing 0
*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    if( !ifarg(1) ) {
        return;
    }
    Dt = *getarg(1);
    sonata_set_atomic_step(Dt);

    int register_recalc_ptr = 1;
    if( ifarg(2) ) {
        register_recalc_ptr = (int)*getarg(2);
    }
    if( register_recalc_ptr ) {
        nrn_register_recalc_ptr_callback( sonataRefreshPointers );
    }
#endif
#endif
}
 }
 
}
}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
 {
   activeStep = initialStep ;
   artcell_net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  initialStep * Dt , 1.0 ) ;
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SonataReportHelper.mod";
static const char* nmodl_file_text = 
  "NEURON {\n"
  "        THREADSAFE\n"
  "        ARTIFICIAL_CELL SonataReportHelper\n"
  "        RANGE initialStep, activeStep\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "#include <stdint.h>\n"
  "#include <bbp/sonata/reports.h>\n"
  "#include <mpi.h>\n"
  "    extern int ifarg(int iarg);\n"
  "    extern double* getarg(int iarg);\n"
  "    extern double* nrn_recalc_ptr(double*);\n"
  "    extern void nrn_register_recalc_ptr_callback(void (*f)(void));\n"
  "    extern double* vector_vec();\n"
  "    extern int vector_capacity();\n"
  "    extern void* vector_arg(int);\n"
  "\n"
  "    void sonataRefreshPointers() { //callback function to update data locations before runtime\n"
  "        sonata_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function\n"
  "    }\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "PARAMETER {\n"
  "    Dt = .1 (ms)\n"
  "    activeStep = 0\n"
  "    initialStep = 0\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "    activeStep = initialStep\n"
  "    net_send(initialStep*Dt, 1)\n"
  "}\n"
  "\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_record_data(activeStep);\n"
  "    activeStep++;\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "    net_send(Dt, 1)\n"
  "}\n"
  "\n"
  "CONSTRUCTOR  {\n"
  "VERBATIM {\n"
  "/**\n"
  "* \\param 1: Dt (double, optional). If not given no initializaton is performed\n"
  "* \\param 2: register_recalc_ptr (double, optional). By default will invoke\n"
  "*    nrn_register_recalc_ptr_callback, which can be disabled by passing 0\n"
  "*/\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    if( !ifarg(1) ) {\n"
  "        return;\n"
  "    }\n"
  "    Dt = *getarg(1);\n"
  "    sonata_set_atomic_step(Dt);\n"
  "\n"
  "    int register_recalc_ptr = 1;\n"
  "    if( ifarg(2) ) {\n"
  "        register_recalc_ptr = (int)*getarg(2);\n"
  "    }\n"
  "    if( register_recalc_ptr ) {\n"
  "        nrn_register_recalc_ptr_callback( sonataRefreshPointers );\n"
  "    }\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE make_comm() {\n"
  "VERBATIM\n"
  "{\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_setup_communicators();\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE prepare_datasets() {\n"
  "VERBATIM\n"
  "{\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_prepare_datasets();\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE disable_auto_flush() {\n"
  "}\n"
  "\n"
  "PROCEDURE set_steps_to_buffer() {\n"
  "}\n"
  "\n"
  "PROCEDURE set_max_buffer_size_hint() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    int buffer_size = (int) *getarg(1);\n"
  "    sonata_set_max_buffer_size_hint(buffer_size);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE flush() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    // Note: flush uses actual time (t) whereas recData uses timestep.  Should try to only use one or the other in the future\n"
  "    sonata_flush( t );\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ":Populate buffers from NEURON for savestate\n"
  ": @param SaveState object\n"
  "PROCEDURE pre_savestate() {\n"
  "}\n"
  "\n"
  ":Call ReportingLib for saving SaveState data using MPI I/O\n"
  "PROCEDURE savestate() {\n"
  "}\n"
  "\n"
  ": only restore global data for the purposes of getting the post retore time\n"
  "PROCEDURE restoretime() {\n"
  "    initialStep = t/Dt\n"
  "}\n"
  "\n"
  ": @param SaveState object\n"
  "PROCEDURE restorestate() {\n"
  "    activeStep = t/Dt\n"
  "}\n"
  "\n"
  "FUNCTION redirect() {\n"
  "}\n"
  "\n"
  "PROCEDURE clear() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_clear();\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE create_spikefile() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    char output_dir[256] = \".\";\n"
  "    // output dir\n"
  "    if (ifarg(1)) {\n"
  "        sprintf(output_dir,\"%s\", gargstr(1));\n"
  "    }\n"
  "    sonata_create_spikefile(output_dir);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE write_spike_populations() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_write_spike_populations();\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE close_spikefile() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    sonata_close_spikefile();\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE write_spikes() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "\n"
  "    char output_dir[256] = \".\";\n"
  "    char population_name[256] = \"All\";\n"
  "    double *time = NULL, *gid = NULL;\n"
  "    int num_spikes = 0;\n"
  "    int num_gids = 0;\n"
  "    void* v1;\n"
  "    void* v2;\n"
  "\n"
  "    // first vector is time of spikes\n"
  "    if (ifarg(1)) {\n"
  "        v1 = vector_arg(1);\n"
  "        time = vector_vec(v1);\n"
  "        num_spikes = vector_capacity(v1);\n"
  "    }\n"
  "\n"
  "    // second vector is associated gids\n"
  "    if (ifarg(2)) {\n"
  "        v2 = vector_arg(2);\n"
  "        gid = vector_vec(v2);\n"
  "        num_gids = vector_capacity(v2);\n"
  "    }\n"
  "\n"
  "    // output dir\n"
  "    if (ifarg(3)) {\n"
  "        sprintf(output_dir,\"%s\", gargstr(3));\n"
  "    }\n"
  "\n"
  "    if (ifarg(4)) {\n"
  "        sprintf(population_name,\"%s\", gargstr(4));\n"
  "    }\n"
  "\n"
  "    int* int_gid = malloc(num_gids * sizeof(int));\n"
  "    int i;\n"
  "    for(i=0; i<num_spikes; ++i) {\n"
  "        int_gid[i] = (int)gid[i];\n"
  "    }\n"
  "    sonata_create_spikefile(output_dir);\n"
  "    sonata_add_spikes_population(population_name, 0, time, num_spikes, int_gid, num_gids);\n"
  "    sonata_write_spike_populations();\n"
  "    sonata_close_spikefile();\n"
  "    free(int_gid);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE add_spikes_population() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "\n"
  "    char population_name[256] = \"All\";\n"
  "    int population_offset = 0;\n"
  "    double *time = NULL, *gid = NULL;\n"
  "    int num_spikes = 0;\n"
  "    int num_gids = 0;\n"
  "    void* v1;\n"
  "    void* v2;\n"
  "\n"
  "    // first vector is time of spikes\n"
  "    if (ifarg(1)) {\n"
  "        v1 = vector_arg(1);\n"
  "        time = vector_vec(v1);\n"
  "        num_spikes = vector_capacity(v1);\n"
  "    }\n"
  "\n"
  "    // second vector is associated gids\n"
  "    if (ifarg(2)) {\n"
  "        v2 = vector_arg(2);\n"
  "        gid = vector_vec(v2);\n"
  "        num_gids = vector_capacity(v2);\n"
  "    }\n"
  "\n"
  "    if (ifarg(3)) {\n"
  "        sprintf(population_name,\"%s\", gargstr(3));\n"
  "    }\n"
  "\n"
  "    if (ifarg(4)) {\n"
  "        population_offset = (int) *getarg(4);\n"
  "    }\n"
  "\n"
  "    int* int_gid = malloc(num_gids * sizeof(int));\n"
  "    int i;\n"
  "    for(i=0; i<num_spikes; ++i) {\n"
  "        int_gid[i] = (int)gid[i];\n"
  "    }\n"
  "    sonata_add_spikes_population(population_name, population_offset, time, num_spikes, int_gid, num_gids);\n"
  "    free(int_gid);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ;
#endif
