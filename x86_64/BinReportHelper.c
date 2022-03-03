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
 
#define nrn_init _nrn_init__BinReportHelper
#define _nrn_initial _nrn_initial__BinReportHelper
#define nrn_cur _nrn_cur__BinReportHelper
#define _nrn_current _nrn_current__BinReportHelper
#define nrn_jacob _nrn_jacob__BinReportHelper
#define nrn_state _nrn_state__BinReportHelper
#define _net_receive _net_receive__BinReportHelper 
#define clear clear__BinReportHelper 
#define disable_auto_flush disable_auto_flush__BinReportHelper 
#define flush flush__BinReportHelper 
#define make_comm make_comm__BinReportHelper 
#define pre_savestate pre_savestate__BinReportHelper 
#define restorestate restorestate__BinReportHelper 
#define restoretime restoretime__BinReportHelper 
#define restartEvent restartEvent__BinReportHelper 
#define savestate savestate__BinReportHelper 
#define set_max_buffer_size_hint set_max_buffer_size_hint__BinReportHelper 
#define set_steps_to_buffer set_steps_to_buffer__BinReportHelper 
 
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
 static double _hoc_clear();
 static double _hoc_disable_auto_flush();
 static double _hoc_flush();
 static double _hoc_make_comm();
 static double _hoc_pre_savestate();
 static double _hoc_redirect();
 static double _hoc_restorestate();
 static double _hoc_restoretime();
 static double _hoc_restartEvent();
 static double _hoc_savestate();
 static double _hoc_set_max_buffer_size_hint();
 static double _hoc_set_steps_to_buffer();
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
 "clear", _hoc_clear,
 "disable_auto_flush", _hoc_disable_auto_flush,
 "flush", _hoc_flush,
 "make_comm", _hoc_make_comm,
 "pre_savestate", _hoc_pre_savestate,
 "redirect", _hoc_redirect,
 "restorestate", _hoc_restorestate,
 "restoretime", _hoc_restoretime,
 "restartEvent", _hoc_restartEvent,
 "savestate", _hoc_savestate,
 "set_max_buffer_size_hint", _hoc_set_max_buffer_size_hint,
 "set_steps_to_buffer", _hoc_set_steps_to_buffer,
 0, 0
};
#define redirect redirect_BinReportHelper
 extern double redirect( _threadargsproto_ );
 /* declare global and static user variables */
#define Dt Dt_BinReportHelper
 double Dt = 0.1;
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt_BinReportHelper", "ms",
 0,0
};
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 "Dt_BinReportHelper", &Dt_BinReportHelper,
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
"BinReportHelper",
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

 void _BinReportHelper_reg() {
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
 	ivoc_help("help ?1 BinReportHelper /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/BinReportHelper.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int clear(_threadargsproto_);
static int disable_auto_flush(_threadargsproto_);
static int flush(_threadargsproto_);
static int make_comm(_threadargsproto_);
static int pre_savestate(_threadargsproto_);
static int restorestate(_threadargsproto_);
static int restoretime(_threadargsproto_);
static int restartEvent(_threadargsproto_);
static int savestate(_threadargsproto_);
static int set_max_buffer_size_hint(_threadargsproto_);
static int set_steps_to_buffer(_threadargsproto_);
 
/*VERBATIM*/

#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include "reportinglib/Records.h"
#include "reportinglib/isc/iscAPI.h"
#ifndef DISABLE_MPI
#include <mpi.h>
#endif

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
extern double* nrn_recalc_ptr(double*);
extern void nrn_register_recalc_ptr_callback(void (*f)(void));

extern Object** hoc_objgetarg();
extern void* bbss_buffer_counts( int*, int**, int**, int* );
extern void bbss_save_global( void*, char*, int );
extern void bbss_restore_global( void*, char*, int );
extern void bbss_save( void*, int, char*, int );
extern void bbss_restore( void*, int, int, char*, int );
extern void bbss_save_done( void* );
extern void bbss_restore_done( void* );

extern int nrnmpi_myid;

void refreshPointers() { //callback function to update data locations before runtime
	records_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function
        isc_refresh_pointers(nrn_recalc_ptr);
}
#endif

//int len=0, *gids=0, *sizes=0, global_size=0, pieceCount=0;
void *bbss_ref = NULL;

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
    records_rec(activeStep);
    isc_send_data(activeStep);

    activeStep++;
#endif
#endif
 artcell_net_send ( _tqitem, _args, _pnt, t +  Dt , 1.0 ) ;
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
 
static int  make_comm ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	records_setup_communicator();
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
 
static int  disable_auto_flush ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    records_set_auto_flush(0);
#endif
#endif
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
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int nsteps = (int) *getarg(1);
    records_set_steps_to_buffer( nsteps );
#endif
#endif
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
    int buf_size = (int) *getarg(1);
    records_set_max_buffer_size_hint(buf_size);
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
	records_flush( t );
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
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int len, *gids, *sizes, global_size;
    char* gbuffer;
    char* saveFile = gargstr(1);

    //get sizes
    bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );

    //pass arrays to bin report library for header creation
    gbuffer = records_saveinit( saveFile, len, gids, sizes, global_size );

    //have neuron fill in global data for rank 0
    if( global_size ) {
        bbss_save_global( bbss_ref, gbuffer, global_size );
        records_saveglobal();
    }

    //for each gid, get the buffer from the bin report lib and give to NEURON layer
    int gidIndex=0;
    for( gidIndex=0; gidIndex<len; gidIndex++ ) {
        char *buffer = records_savebuffer( gids[gidIndex] );
        bbss_save( bbss_ref, gids[gidIndex], buffer, sizes[gidIndex] );
    }

    if(len) {
        free(gids);
        free(sizes);
    }

#endif
#endif
}
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
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    if(nrnmpi_myid == 0) {
        printf(" Call to ReportingLib for MPI I/O\n");
    }

    //all buffers populated, have lib execute final MPI-IO operations
    records_savestate();

    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it
    bbss_save_done( bbss_ref );
#endif
#endif
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
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    void *bbss_ref = NULL;
    int len=0, *gids, *sizes, global_size, pieceCount;
    char* gbuffer = NULL;
    char* saveFile = gargstr(1);

    //get sizes - actually care about gid info for restore
    if( len == 0 ) {
        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );
    }

    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save
    gbuffer = records_restoreinit( saveFile, &global_size );
    bbss_restore_global( bbss_ref, gbuffer, global_size );

    if(len) {
        free(gids);
        free(sizes);
    }
#endif
#endif
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
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
{
    void *bbss_ref = NULL;
    int len=0, *gids, *sizes, global_size, pieceCount;
    char* gbuffer = NULL;
    char *saveFile = gargstr(1);

    //get sizes - actually care about gid info for restore
    if( len == 0 ) {
        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );
    }

    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save
    gbuffer = records_restoreinit( saveFile, &global_size );
    bbss_restore_global( bbss_ref, gbuffer, global_size );

    int nbytes = 0, gidIndex=0;
    //for each gid, get the buffer from the bin report lib and give to NEURON layer
    for( gidIndex=0; gidIndex<len; gidIndex++ ) {
        if( gids[gidIndex] != 0 ) {
            gbuffer = records_restore( gids[gidIndex], &pieceCount, &nbytes );
            //printf( "restore %d with %d pieces in %d bytes\n", gids[gidIndex], pieceCount, nbytes );
            bbss_restore( bbss_ref, gids[gidIndex], pieceCount, gbuffer, nbytes );
        }
    }

    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it
    bbss_restore_done( bbss_ref );

    if(len) {
        free(gids);
        free(sizes);
    }
}
#endif
#endif
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
 
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    FILE *fout;
    char fname[128];

    int mpi_size=1, mpi_rank=0;

#ifndef DISABLE_MPI
    // get MPI info
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);
#endif

    sprintf( fname, "NodeFiles/%d.%dnode.out", mpi_rank, mpi_size );
    fout = freopen( fname, "w", stdout );
    if( !fout ) {
        fprintf( stderr, "failed to redirect.  Terminating\n" );
        exit(0);
    }

    sprintf( fname, "NodeFiles/%d.%dnode.err", mpi_rank, mpi_size );
    fout = freopen( fname, "w", stderr );
    setbuf( fout, NULL );
#endif
#endif
}
 
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
        records_clear();
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
    if( !ifarg(1) ) return;
    Dt = *getarg(1);

    records_set_atomic_step(Dt);
    isc_set_sim_dt(Dt);

    int register_recalc_ptr = 1;
    if( ifarg(2) ) register_recalc_ptr = (int)*getarg(2);
    if( register_recalc_ptr ) {
        nrn_register_recalc_ptr_callback( refreshPointers );
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/BinReportHelper.mod";
static const char* nmodl_file_text = 
  "NEURON {\n"
  "        THREADSAFE\n"
  "        ARTIFICIAL_CELL BinReportHelper\n"
  "        RANGE initialStep, activeStep\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "#include \"reportinglib/Records.h\"\n"
  "#include \"reportinglib/isc/iscAPI.h\"\n"
  "#ifndef DISABLE_MPI\n"
  "#include <mpi.h>\n"
  "#endif\n"
  "\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "extern double* nrn_recalc_ptr(double*);\n"
  "extern void nrn_register_recalc_ptr_callback(void (*f)(void));\n"
  "\n"
  "extern Object** hoc_objgetarg();\n"
  "extern void* bbss_buffer_counts( int*, int**, int**, int* );\n"
  "extern void bbss_save_global( void*, char*, int );\n"
  "extern void bbss_restore_global( void*, char*, int );\n"
  "extern void bbss_save( void*, int, char*, int );\n"
  "extern void bbss_restore( void*, int, int, char*, int );\n"
  "extern void bbss_save_done( void* );\n"
  "extern void bbss_restore_done( void* );\n"
  "\n"
  "extern int nrnmpi_myid;\n"
  "\n"
  "void refreshPointers() { //callback function to update data locations before runtime\n"
  "	records_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function\n"
  "        isc_refresh_pointers(nrn_recalc_ptr);\n"
  "}\n"
  "#endif\n"
  "\n"
  "//int len=0, *gids=0, *sizes=0, global_size=0, pieceCount=0;\n"
  "void *bbss_ref = NULL;\n"
  "\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "PARAMETER {\n"
  "    Dt = .1 (ms)\n"
  "    activeStep = 0\n"
  "    initialStep = 0\n"
  "}\n"
  "\n"
  "\n"
  "INITIAL {\n"
  "    activeStep = initialStep\n"
  "    net_send(initialStep*Dt, 1)\n"
  "}\n"
  "\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    records_rec(activeStep);\n"
  "    isc_send_data(activeStep);\n"
  "\n"
  "    activeStep++;\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "    net_send(Dt, 1)\n"
  "}\n"
  "\n"
  "\n"
  "CONSTRUCTOR  {\n"
  "VERBATIM {\n"
  "/**\n"
  " * \\param 1: Dt (double, optional). If not given no initializaton is performed\n"
  " * \\param 2: register_recalc_ptr (double, optional). By default will invoke\n"
  " *    nrn_register_recalc_ptr_callback, which can be disabled by passing 0\n"
  " */\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    if( !ifarg(1) ) return;\n"
  "    Dt = *getarg(1);\n"
  "\n"
  "    records_set_atomic_step(Dt);\n"
  "    isc_set_sim_dt(Dt);\n"
  "\n"
  "    int register_recalc_ptr = 1;\n"
  "    if( ifarg(2) ) register_recalc_ptr = (int)*getarg(2);\n"
  "    if( register_recalc_ptr ) {\n"
  "        nrn_register_recalc_ptr_callback( refreshPointers );\n"
  "    }\n"
  "#endif\n"
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
  "PROCEDURE make_comm() {\n"
  "VERBATIM\n"
  "{\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "	records_setup_communicator();\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE disable_auto_flush() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    records_set_auto_flush(0);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE set_steps_to_buffer() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    int nsteps = (int) *getarg(1);\n"
  "    records_set_steps_to_buffer( nsteps );\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE set_max_buffer_size_hint() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    int buf_size = (int) *getarg(1);\n"
  "    records_set_max_buffer_size_hint(buf_size);\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE flush() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "        // Note: flush uses actual time (t) whereas recData uses timestep.  Should try to only use one or the other in the future\n"
  "	records_flush( t );\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  ":Populate buffers from NEURON for savestate\n"
  ": @param SaveState object\n"
  "PROCEDURE pre_savestate() {\n"
  "VERBATIM\n"
  "{\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    int len, *gids, *sizes, global_size;\n"
  "    char* gbuffer;\n"
  "    char* saveFile = gargstr(1);\n"
  "\n"
  "    //get sizes\n"
  "    bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );\n"
  "\n"
  "    //pass arrays to bin report library for header creation\n"
  "    gbuffer = records_saveinit( saveFile, len, gids, sizes, global_size );\n"
  "\n"
  "    //have neuron fill in global data for rank 0\n"
  "    if( global_size ) {\n"
  "        bbss_save_global( bbss_ref, gbuffer, global_size );\n"
  "        records_saveglobal();\n"
  "    }\n"
  "\n"
  "    //for each gid, get the buffer from the bin report lib and give to NEURON layer\n"
  "    int gidIndex=0;\n"
  "    for( gidIndex=0; gidIndex<len; gidIndex++ ) {\n"
  "        char *buffer = records_savebuffer( gids[gidIndex] );\n"
  "        bbss_save( bbss_ref, gids[gidIndex], buffer, sizes[gidIndex] );\n"
  "    }\n"
  "\n"
  "    if(len) {\n"
  "        free(gids);\n"
  "        free(sizes);\n"
  "    }\n"
  "\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ":Call ReportingLib for saving SaveState data using MPI I/O\n"
  "PROCEDURE savestate() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "\n"
  "    if(nrnmpi_myid == 0) {\n"
  "        printf(\" Call to ReportingLib for MPI I/O\\n\");\n"
  "    }\n"
  "\n"
  "    //all buffers populated, have lib execute final MPI-IO operations\n"
  "    records_savestate();\n"
  "\n"
  "    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it\n"
  "    bbss_save_done( bbss_ref );\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  ": only restore global data for the purposes of getting the post retore time\n"
  "PROCEDURE restoretime() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    void *bbss_ref = NULL;\n"
  "    int len=0, *gids, *sizes, global_size, pieceCount;\n"
  "    char* gbuffer = NULL;\n"
  "    char* saveFile = gargstr(1);\n"
  "\n"
  "    //get sizes - actually care about gid info for restore\n"
  "    if( len == 0 ) {\n"
  "        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );\n"
  "    }\n"
  "\n"
  "    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save\n"
  "    gbuffer = records_restoreinit( saveFile, &global_size );\n"
  "    bbss_restore_global( bbss_ref, gbuffer, global_size );\n"
  "\n"
  "    if(len) {\n"
  "        free(gids);\n"
  "        free(sizes);\n"
  "    }\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "    initialStep = t/Dt\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  ": @param SaveState object\n"
  "PROCEDURE restorestate() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "{\n"
  "    void *bbss_ref = NULL;\n"
  "    int len=0, *gids, *sizes, global_size, pieceCount;\n"
  "    char* gbuffer = NULL;\n"
  "    char *saveFile = gargstr(1);\n"
  "\n"
  "    //get sizes - actually care about gid info for restore\n"
  "    if( len == 0 ) {\n"
  "        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );\n"
  "    }\n"
  "\n"
  "    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save\n"
  "    gbuffer = records_restoreinit( saveFile, &global_size );\n"
  "    bbss_restore_global( bbss_ref, gbuffer, global_size );\n"
  "\n"
  "    int nbytes = 0, gidIndex=0;\n"
  "    //for each gid, get the buffer from the bin report lib and give to NEURON layer\n"
  "    for( gidIndex=0; gidIndex<len; gidIndex++ ) {\n"
  "        if( gids[gidIndex] != 0 ) {\n"
  "            gbuffer = records_restore( gids[gidIndex], &pieceCount, &nbytes );\n"
  "            //printf( \"restore %d with %d pieces in %d bytes\\n\", gids[gidIndex], pieceCount, nbytes );\n"
  "            bbss_restore( bbss_ref, gids[gidIndex], pieceCount, gbuffer, nbytes );\n"
  "        }\n"
  "    }\n"
  "\n"
  "    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it\n"
  "    bbss_restore_done( bbss_ref );\n"
  "\n"
  "    if(len) {\n"
  "        free(gids);\n"
  "        free(sizes);\n"
  "    }\n"
  "}\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "    activeStep = t/Dt\n"
  "}\n"
  "\n"
  "FUNCTION redirect() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    FILE *fout;\n"
  "    char fname[128];\n"
  "\n"
  "    int mpi_size=1, mpi_rank=0;\n"
  "\n"
  "#ifndef DISABLE_MPI\n"
  "    // get MPI info\n"
  "    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);\n"
  "    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);\n"
  "#endif\n"
  "\n"
  "    sprintf( fname, \"NodeFiles/%d.%dnode.out\", mpi_rank, mpi_size );\n"
  "    fout = freopen( fname, \"w\", stdout );\n"
  "    if( !fout ) {\n"
  "        fprintf( stderr, \"failed to redirect.  Terminating\\n\" );\n"
  "        exit(0);\n"
  "    }\n"
  "\n"
  "    sprintf( fname, \"NodeFiles/%d.%dnode.err\", mpi_rank, mpi_size );\n"
  "    fout = freopen( fname, \"w\", stderr );\n"
  "    setbuf( fout, NULL );\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE clear() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "        records_clear();\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ;
#endif
