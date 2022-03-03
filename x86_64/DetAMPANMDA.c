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
 
#define nrn_init _nrn_init__DetAMPANMDA
#define _nrn_initial _nrn_initial__DetAMPANMDA
#define nrn_cur _nrn_cur__DetAMPANMDA
#define _nrn_current _nrn_current__DetAMPANMDA
#define nrn_jacob _nrn_jacob__DetAMPANMDA
#define nrn_state _nrn_state__DetAMPANMDA
#define _net_receive _net_receive__DetAMPANMDA 
#define state state__DetAMPANMDA 
#define setup_delay_vecs setup_delay_vecs__DetAMPANMDA 
 
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
#define tau_r_AMPA _p[0]
#define tau_d_AMPA _p[1]
#define tau_r_NMDA _p[2]
#define tau_d_NMDA _p[3]
#define Use _p[4]
#define Dep _p[5]
#define Fac _p[6]
#define e _p[7]
#define mg _p[8]
#define u0 _p[9]
#define NMDA_ratio _p[10]
#define synapseID _p[11]
#define verboseLevel _p[12]
#define conductance _p[13]
#define i _p[14]
#define i_AMPA _p[15]
#define i_NMDA _p[16]
#define g_AMPA _p[17]
#define g_NMDA _p[18]
#define g _p[19]
#define next_delay _p[20]
#define A_AMPA _p[21]
#define B_AMPA _p[22]
#define A_NMDA _p[23]
#define B_NMDA _p[24]
#define factor_AMPA _p[25]
#define factor_NMDA _p[26]
#define mggate _p[27]
#define DA_AMPA _p[28]
#define DB_AMPA _p[29]
#define DA_NMDA _p[30]
#define DB_NMDA _p[31]
#define v _p[32]
#define _g _p[33]
#define _tsav _p[34]
#define _nd_area  *_ppvar[0]._pval
#define delay_times	*_ppvar[2]._pval
#define _p_delay_times	_ppvar[2]._pval
#define delay_weights	*_ppvar[3]._pval
#define _p_delay_weights	_ppvar[3]._pval
 
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
 static double _hoc_setup_delay_vecs();
 static double _hoc_toggleVerbose();
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
 "setup_delay_vecs", _hoc_setup_delay_vecs,
 "toggleVerbose", _hoc_toggleVerbose,
 0, 0
};
#define toggleVerbose toggleVerbose_DetAMPANMDA
 extern double toggleVerbose( _threadargsproto_ );
 /* declare global and static user variables */
#define gmax gmax_DetAMPANMDA
 double gmax = 0.001;
#define nc_type_param nc_type_param_DetAMPANMDA
 double nc_type_param = 7;
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "gmax_DetAMPANMDA", "uS",
 "tau_r_AMPA", "ms",
 "tau_d_AMPA", "ms",
 "tau_r_NMDA", "ms",
 "tau_d_NMDA", "ms",
 "Use", "1",
 "Dep", "ms",
 "Fac", "ms",
 "e", "mV",
 "mg", "mM",
 "NMDA_ratio", "1",
 "i", "nA",
 "i_AMPA", "nA",
 "i_NMDA", "nA",
 "g_AMPA", "uS",
 "g_NMDA", "uS",
 "g", "uS",
 "next_delay", "ms",
 0,0
};
 static double A_NMDA0 = 0;
 static double A_AMPA0 = 0;
 static double B_NMDA0 = 0;
 static double B_AMPA0 = 0;
 static double delta_t = 0.01;
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 "gmax_DetAMPANMDA", &gmax_DetAMPANMDA,
 "nc_type_param_DetAMPANMDA", &nc_type_param_DetAMPANMDA,
 0,0
};
 static DoubVec hoc_vdoub[] = {
 0,0,0
};
 static double _sav_indep;
 static void nrn_alloc(Prop*);
static void  nrn_init(_NrnThread*, _Memb_list*, int);
static void nrn_state(_NrnThread*, _Memb_list*, int);
 static void nrn_cur(_NrnThread*, _Memb_list*, int);
static void  nrn_jacob(_NrnThread*, _Memb_list*, int);
 static void _hoc_destroy_pnt(_vptr) void* _vptr; {
   destroy_point_process(_vptr);
}
 
static int _ode_count(int);
static void _ode_map(int, double**, double**, double*, Datum*, double*, int);
static void _ode_spec(_NrnThread*, _Memb_list*, int);
static void _ode_matsol(_NrnThread*, _Memb_list*, int);
 
#define _cvode_ieq _ppvar[5]._i
 static void _ode_matsol_instance1(_threadargsproto_);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"DetAMPANMDA",
 "tau_r_AMPA",
 "tau_d_AMPA",
 "tau_r_NMDA",
 "tau_d_NMDA",
 "Use",
 "Dep",
 "Fac",
 "e",
 "mg",
 "u0",
 "NMDA_ratio",
 "synapseID",
 "verboseLevel",
 "conductance",
 0,
 "i",
 "i_AMPA",
 "i_NMDA",
 "g_AMPA",
 "g_NMDA",
 "g",
 "next_delay",
 0,
 "A_AMPA",
 "B_AMPA",
 "A_NMDA",
 "B_NMDA",
 0,
 "delay_times",
 "delay_weights",
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
 	_p = nrn_prop_data_alloc(_mechtype, 35, _prop);
 	/*initialize range parameters*/
 	tau_r_AMPA = 0.2;
 	tau_d_AMPA = 1.7;
 	tau_r_NMDA = 0.29;
 	tau_d_NMDA = 43;
 	Use = 1;
 	Dep = 100;
 	Fac = 10;
 	e = 0;
 	mg = 1;
 	u0 = 0;
 	NMDA_ratio = 0.71;
 	synapseID = 0;
 	verboseLevel = 0;
 	conductance = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 35;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 6, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 
}
 static void _initlists();
  /* some states have an absolute tolerance */
 static Symbol** _atollist;
 static HocStateTolerance _hoc_state_tol[] = {
 0,0
};
 
#define _tqitem &(_ppvar[4]._pvoid)
 static void _net_receive(Point_process*, double*, double);
 static void _net_init(Point_process*, double*, double);
 static void bbcore_write(double*, int*, int*, int*, _threadargsproto_);
 extern void hoc_reg_bbcore_write(int, void(*)(double*, int*, int*, int*, _threadargsproto_));
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _DetAMPANMDA_reg() {
	int _vectorized = 1;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,nrn_cur, nrn_jacob, nrn_state, nrn_init,
	 hoc_nrnpointerindex, 1,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
   hoc_reg_bbcore_write(_mechtype, bbcore_write);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 35, 6);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
  hoc_register_dparam_semantics(_mechtype, 3, "bbcorepointer");
  hoc_register_dparam_semantics(_mechtype, 4, "netsend");
  hoc_register_dparam_semantics(_mechtype, 5, "cvodeieq");
 	hoc_register_cvode(_mechtype, _ode_count, _ode_map, _ode_spec, _ode_matsol);
 	hoc_register_tolerance(_mechtype, _hoc_state_tol, &_atollist);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_init[_mechtype] = _net_init;
 pnt_receive_size[_mechtype] = 8;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 DetAMPANMDA /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/DetAMPANMDA.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "AMPA and NMDA receptor with presynaptic short-term plasticity";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int setup_delay_vecs(_threadargsproto_);
 
static int _ode_spec1(_threadargsproto_);
/*static int _ode_matsol1(_threadargsproto_);*/
 static int _slist1[4], _dlist1[4];
 static int state(_threadargsproto_);
 
/*VERBATIM*/

#ifndef CORENEURON_BUILD
extern int ifarg(int iarg);

extern void* vector_arg(int iarg);
extern double* vector_vec(void* vv);
extern int vector_capacity(void* vv);
#endif

 
static int  setup_delay_vecs ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    void** vv_delay_times = (void**)(&_p_delay_times);
    void** vv_delay_weights = (void**)(&_p_delay_weights);
    *vv_delay_times = (void*)NULL;
    *vv_delay_weights = (void*)NULL;
    if (ifarg(1)) {
        *vv_delay_times = vector_arg(1);
    }
    if (ifarg(2)) {
        *vv_delay_weights = vector_arg(2);
    }
#endif
  return 0; }
 
static double _hoc_setup_delay_vecs(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 setup_delay_vecs ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*CVODE*/
 static int _ode_spec1 (double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {int _reset = 0; {
   DA_AMPA = - A_AMPA / tau_r_AMPA ;
   DB_AMPA = - B_AMPA / tau_d_AMPA ;
   DA_NMDA = - A_NMDA / tau_r_NMDA ;
   DB_NMDA = - B_NMDA / tau_d_NMDA ;
   }
 return _reset;
}
 static int _ode_matsol1 (double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
 DA_AMPA = DA_AMPA  / (1. - dt*( ( - 1.0 ) / tau_r_AMPA )) ;
 DB_AMPA = DB_AMPA  / (1. - dt*( ( - 1.0 ) / tau_d_AMPA )) ;
 DA_NMDA = DA_NMDA  / (1. - dt*( ( - 1.0 ) / tau_r_NMDA )) ;
 DB_NMDA = DB_NMDA  / (1. - dt*( ( - 1.0 ) / tau_d_NMDA )) ;
  return 0;
}
 /*END CVODE*/
 static int state (double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) { {
    A_AMPA = A_AMPA + (1. - exp(dt*(( - 1.0 ) / tau_r_AMPA)))*(- ( 0.0 ) / ( ( - 1.0 ) / tau_r_AMPA ) - A_AMPA) ;
    B_AMPA = B_AMPA + (1. - exp(dt*(( - 1.0 ) / tau_d_AMPA)))*(- ( 0.0 ) / ( ( - 1.0 ) / tau_d_AMPA ) - B_AMPA) ;
    A_NMDA = A_NMDA + (1. - exp(dt*(( - 1.0 ) / tau_r_NMDA)))*(- ( 0.0 ) / ( ( - 1.0 ) / tau_r_NMDA ) - A_NMDA) ;
    B_NMDA = B_NMDA + (1. - exp(dt*(( - 1.0 ) / tau_d_NMDA)))*(- ( 0.0 ) / ( ( - 1.0 ) / tau_d_NMDA ) - B_NMDA) ;
   }
  return 0;
}
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   double _lresult ;
 _args[1] = _args[0] ;
   _args[2] = _args[0] * NMDA_ratio ;
   if ( t < 0.0 ) {
     
/*VERBATIM*/
        return;
 }
   if ( _lflag  == 1.0 ) {
     
/*VERBATIM*/
        // setup self events for delayed connections to change weights
        void *vv_delay_weights = *((void**)(&_p_delay_weights));
        if (vv_delay_weights && vector_capacity(vv_delay_weights)>=next_delay) {
          double* weights_v = vector_vec(vv_delay_weights);
          double next_delay_weight = weights_v[(int)next_delay];
 _args[0] = conductance * next_delay_weight ;
     next_delay = next_delay + 1.0 ;
     
/*VERBATIM*/
        }
        return;
 }
   if ( Fac > 0.0 ) {
     _args[5] = _args[5] * exp ( - ( t - _args[6] ) / Fac ) ;
     }
   else {
     _args[5] = Use ;
     }
   if ( Fac > 0.0 ) {
     _args[5] = _args[5] + Use * ( 1.0 - _args[5] ) ;
     }
   _args[3] = 1.0 - ( 1.0 - _args[3] ) * exp ( - ( t - _args[6] ) / Dep ) ;
   _args[4] = _args[5] * _args[3] ;
   _args[3] = _args[3] - _args[5] * _args[3] ;
   if ( verboseLevel > 0.0 ) {
     printf ( "Synapse %f at time %g: R = %g Pr = %g erand = %g\n" , synapseID , t , _args[3] , _args[4] , _lresult ) ;
     }
   _args[6] = t ;
     if (nrn_netrec_state_adjust && !cvode_active_){
    /* discon state adjustment for cnexp case (rate uses no local variable) */
    double __state = A_AMPA;
    double __primary = (A_AMPA + _args[4] * _args[1] * factor_AMPA) - __state;
     __primary += ( 1. - exp( 0.5*dt*( ( - 1.0 ) / tau_r_AMPA ) ) )*( - ( 0.0 ) / ( ( - 1.0 ) / tau_r_AMPA ) - __primary );
    A_AMPA += __primary;
  } else {
 A_AMPA = A_AMPA + _args[4] * _args[1] * factor_AMPA ;
     }
   if (nrn_netrec_state_adjust && !cvode_active_){
    /* discon state adjustment for cnexp case (rate uses no local variable) */
    double __state = B_AMPA;
    double __primary = (B_AMPA + _args[4] * _args[1] * factor_AMPA) - __state;
     __primary += ( 1. - exp( 0.5*dt*( ( - 1.0 ) / tau_d_AMPA ) ) )*( - ( 0.0 ) / ( ( - 1.0 ) / tau_d_AMPA ) - __primary );
    B_AMPA += __primary;
  } else {
 B_AMPA = B_AMPA + _args[4] * _args[1] * factor_AMPA ;
     }
   if (nrn_netrec_state_adjust && !cvode_active_){
    /* discon state adjustment for cnexp case (rate uses no local variable) */
    double __state = A_NMDA;
    double __primary = (A_NMDA + _args[4] * _args[2] * factor_NMDA) - __state;
     __primary += ( 1. - exp( 0.5*dt*( ( - 1.0 ) / tau_r_NMDA ) ) )*( - ( 0.0 ) / ( ( - 1.0 ) / tau_r_NMDA ) - __primary );
    A_NMDA += __primary;
  } else {
 A_NMDA = A_NMDA + _args[4] * _args[2] * factor_NMDA ;
     }
   if (nrn_netrec_state_adjust && !cvode_active_){
    /* discon state adjustment for cnexp case (rate uses no local variable) */
    double __state = B_NMDA;
    double __primary = (B_NMDA + _args[4] * _args[2] * factor_NMDA) - __state;
     __primary += ( 1. - exp( 0.5*dt*( ( - 1.0 ) / tau_d_NMDA ) ) )*( - ( 0.0 ) / ( ( - 1.0 ) / tau_d_NMDA ) - __primary );
    B_NMDA += __primary;
  } else {
 B_NMDA = B_NMDA + _args[4] * _args[2] * factor_NMDA ;
     }
 if ( verboseLevel > 0.0 ) {
     printf ( " vals %g %g %g %g\n" , A_AMPA , _args[1] , factor_AMPA , _args[0] ) ;
     }
   } }
 
static void _net_init(Point_process* _pnt, double* _args, double _lflag) {
       double* _p = _pnt->_prop->param;
    Datum* _ppvar = _pnt->_prop->dparam;
    Datum* _thread = (Datum*)0;
    _NrnThread* _nt = (_NrnThread*)_pnt->_vnt;
 _args[3] = 1.0 ;
   _args[5] = u0 ;
   _args[6] = t ;
   if ( _args[7]  == 0.0 ) {
     
/*VERBATIM*/
            // setup self events for delayed connections to change weights
            void *vv_delay_times = *((void**)(&_p_delay_times));
            void *vv_delay_weights = *((void**)(&_p_delay_weights));
            if (vv_delay_times && vector_capacity(vv_delay_times)>=1) {
              double* deltm_el = vector_vec(vv_delay_times);
              int delay_times_idx;
              next_delay = 0;
              for(delay_times_idx = 0; delay_times_idx < vector_capacity(vv_delay_times); ++delay_times_idx) {
                double next_delay_t = deltm_el[delay_times_idx];
 net_send ( _tqitem, _args, _pnt, t +  next_delay_t , 1.0 ) ;
     
/*VERBATIM*/
              }
            }
 }
   }
 
double toggleVerbose ( _threadargsproto_ ) {
   double _ltoggleVerbose;
 verboseLevel = 1.0 - verboseLevel ;
   
return _ltoggleVerbose;
 }
 
static double _hoc_toggleVerbose(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  toggleVerbose ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
static void bbcore_write(double* x, int* d, int* x_offset, int* d_offset, _threadargsproto_) {

  void *vv_delay_times = *((void**)(&_p_delay_times));
  void *vv_delay_weights = *((void**)(&_p_delay_weights));

  // serialize connection delay vectors
  if (vv_delay_times && vv_delay_weights &&
     (vector_capacity(vv_delay_times) >= 1) && (vector_capacity(vv_delay_weights) >= 1)) {
    if (d && x) {
      int* d_i = d + *d_offset;
      // store vector sizes for deserialization
      d_i[0] = vector_capacity(vv_delay_times);
      d_i[1] = vector_capacity(vv_delay_weights);

      double* delay_times_el = vector_vec(vv_delay_times);
      double* delay_weights_el = vector_vec(vv_delay_weights);
      double* x_i = x + *x_offset;
      int delay_vecs_idx;
      int x_idx = 0;
      for(delay_vecs_idx = 0; delay_vecs_idx < vector_capacity(vv_delay_times); ++delay_vecs_idx) {
         x_i[x_idx++] = delay_times_el[delay_vecs_idx];
         x_i[x_idx++] = delay_weights_el[delay_vecs_idx];
      }
    }
  } else {
    if (d) {
      int* d_i = d + *d_offset;
      d_i[0] = 0;
      d_i[1] = 0;
    }
  }
  // reserve space for delay connection vector sizes on serialization buffer
  *d_offset += 2;

  // reserve space for connection delay data on serialization buffer
  if (vv_delay_times && vv_delay_weights) {
    *x_offset += vector_capacity(vv_delay_times) + vector_capacity(vv_delay_weights);
  }
}

static void bbcore_read(double* x, int* d, int* x_offset, int* d_offset, _threadargsproto_) {
  assert(!_p_delay_times && !_p_delay_weights);

  // first get delay vector sizes
  int* d_i = d + *d_offset;
  int delay_times_sz = d_i[0];
  int delay_weights_sz = d_i[1];
  *d_offset += 2;

  if ((delay_times_sz > 0) && (delay_weights_sz > 0)) {
    double* x_i = x + *x_offset;

    // allocate vectors
    _p_delay_times = vector_new1(delay_times_sz);
    _p_delay_weights = vector_new1(delay_weights_sz);

    double* delay_times_el = vector_vec(_p_delay_times);
    double* delay_weights_el = vector_vec(_p_delay_weights);

    // copy data
    int x_idx;
    int vec_idx = 0;
    for(x_idx = 0; x_idx < delay_times_sz + delay_weights_sz; x_idx += 2) {
      delay_times_el[vec_idx] = x_i[x_idx];
      delay_weights_el[vec_idx++] = x_i[x_idx+1];
    }
    *x_offset += delay_times_sz + delay_weights_sz;
  }
}
 
static int _ode_count(int _type){ return 4;}
 
static void _ode_spec(_NrnThread* _nt, _Memb_list* _ml, int _type) {
   double* _p; Datum* _ppvar; Datum* _thread;
   Node* _nd; double _v; int _iml, _cntml;
  _cntml = _ml->_nodecount;
  _thread = _ml->_thread;
  for (_iml = 0; _iml < _cntml; ++_iml) {
    _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
    _nd = _ml->_nodelist[_iml];
    v = NODEV(_nd);
     _ode_spec1 (_p, _ppvar, _thread, _nt);
 }}
 
static void _ode_map(int _ieq, double** _pv, double** _pvdot, double* _pp, Datum* _ppd, double* _atol, int _type) { 
	double* _p; Datum* _ppvar;
 	int _i; _p = _pp; _ppvar = _ppd;
	_cvode_ieq = _ieq;
	for (_i=0; _i < 4; ++_i) {
		_pv[_i] = _pp + _slist1[_i];  _pvdot[_i] = _pp + _dlist1[_i];
		_cvode_abstol(_atollist, _atol, _i);
	}
 }
 
static void _ode_matsol_instance1(_threadargsproto_) {
 _ode_matsol1 (_p, _ppvar, _thread, _nt);
 }
 
static void _ode_matsol(_NrnThread* _nt, _Memb_list* _ml, int _type) {
   double* _p; Datum* _ppvar; Datum* _thread;
   Node* _nd; double _v; int _iml, _cntml;
  _cntml = _ml->_nodecount;
  _thread = _ml->_thread;
  for (_iml = 0; _iml < _cntml; ++_iml) {
    _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
    _nd = _ml->_nodelist[_iml];
    v = NODEV(_nd);
 _ode_matsol_instance1(_threadargs_);
 }}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
  A_NMDA = A_NMDA0;
  A_AMPA = A_AMPA0;
  B_NMDA = B_NMDA0;
  B_AMPA = B_AMPA0;
 {
   double _ltp_AMPA , _ltp_NMDA ;
 A_AMPA = 0.0 ;
   B_AMPA = 0.0 ;
   A_NMDA = 0.0 ;
   B_NMDA = 0.0 ;
   _ltp_AMPA = ( tau_r_AMPA * tau_d_AMPA ) / ( tau_d_AMPA - tau_r_AMPA ) * log ( tau_d_AMPA / tau_r_AMPA ) ;
   _ltp_NMDA = ( tau_r_NMDA * tau_d_NMDA ) / ( tau_d_NMDA - tau_r_NMDA ) * log ( tau_d_NMDA / tau_r_NMDA ) ;
   factor_AMPA = - exp ( - _ltp_AMPA / tau_r_AMPA ) + exp ( - _ltp_AMPA / tau_d_AMPA ) ;
   factor_AMPA = 1.0 / factor_AMPA ;
   factor_NMDA = - exp ( - _ltp_NMDA / tau_r_NMDA ) + exp ( - _ltp_NMDA / tau_d_NMDA ) ;
   factor_NMDA = 1.0 / factor_NMDA ;
   next_delay = - 1.0 ;
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

static double _nrn_current(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt, double _v){double _current=0.;v=_v;{ {
   mggate = 1.0 / ( 1.0 + exp ( 0.062 * - ( v ) ) * ( mg / 3.57 ) ) ;
   g_AMPA = gmax * ( B_AMPA - A_AMPA ) ;
   g_NMDA = gmax * ( B_NMDA - A_NMDA ) * mggate ;
   g = g_AMPA + g_NMDA ;
   i_AMPA = g_AMPA * ( v - e ) ;
   i_NMDA = g_NMDA * ( v - e ) ;
   i = i_AMPA + i_NMDA ;
   }
 _current += i;

} return _current;
}

static void nrn_cur(_NrnThread* _nt, _Memb_list* _ml, int _type) {
double* _p; Datum* _ppvar; Datum* _thread;
Node *_nd; int* _ni; double _rhs, _v; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
_thread = _ml->_thread;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
#if CACHEVEC
  if (use_cachevec) {
    _v = VEC_V(_ni[_iml]);
  }else
#endif
  {
    _nd = _ml->_nodelist[_iml];
    _v = NODEV(_nd);
  }
 _g = _nrn_current(_p, _ppvar, _thread, _nt, _v + .001);
 	{ _rhs = _nrn_current(_p, _ppvar, _thread, _nt, _v);
 	}
 _g = (_g - _rhs)/.001;
 _g *=  1.e2/(_nd_area);
 _rhs *= 1.e2/(_nd_area);
#if CACHEVEC
  if (use_cachevec) {
	VEC_RHS(_ni[_iml]) -= _rhs;
  }else
#endif
  {
	NODERHS(_nd) -= _rhs;
  }
 
}
 
}

static void nrn_jacob(_NrnThread* _nt, _Memb_list* _ml, int _type) {
double* _p; Datum* _ppvar; Datum* _thread;
Node *_nd; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
_thread = _ml->_thread;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml];
#if CACHEVEC
  if (use_cachevec) {
	VEC_D(_ni[_iml]) += _g;
  }else
#endif
  {
     _nd = _ml->_nodelist[_iml];
	NODED(_nd) += _g;
  }
 
}
 
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
 {   state(_p, _ppvar, _thread, _nt);
  }}}

}

static void terminal(){}

static void _initlists(){
 double _x; double* _p = &_x;
 int _i; static int _first = 1;
  if (!_first) return;
 _slist1[0] = &(A_AMPA) - _p;  _dlist1[0] = &(DA_AMPA) - _p;
 _slist1[1] = &(B_AMPA) - _p;  _dlist1[1] = &(DB_AMPA) - _p;
 _slist1[2] = &(A_NMDA) - _p;  _dlist1[2] = &(DA_NMDA) - _p;
 _slist1[3] = &(B_NMDA) - _p;  _dlist1[3] = &(DB_NMDA) - _p;
_first = 0;
}

#if defined(__cplusplus)
} /* extern "C" */
#endif

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/DetAMPANMDA.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file DetAMPANMDA.mod\n"
  " * @brief Adapted from ProbAMPANMDA_EMS.mod by Eilif, Michael and Srikanth\n"
  " * @author chindemi\n"
  " * @date 2014-05-25\n"
  " * @remark Copyright \n"
  "\n"
  " BBP/EPFL 2005-2014; All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "\n"
  "TITLE AMPA and NMDA receptor with presynaptic short-term plasticity\n"
  "\n"
  "\n"
  "COMMENT\n"
  "AMPA and NMDA receptor conductance using a dual-exponential profile\n"
  "presynaptic short-term plasticity based on Fuhrmann et al. 2002, deterministic\n"
  "version.\n"
  "ENDCOMMENT\n"
  "\n"
  "\n"
  "NEURON {\n"
  "    THREADSAFE\n"
  "\n"
  "    POINT_PROCESS DetAMPANMDA\n"
  "    RANGE tau_r_AMPA, tau_d_AMPA, tau_r_NMDA, tau_d_NMDA\n"
  "    RANGE Use, u, Dep, Fac, u0, mg, NMDA_ratio\n"
  "    RANGE i, i_AMPA, i_NMDA, g_AMPA, g_NMDA, g, e\n"
  "    NONSPECIFIC_CURRENT i\n"
  "    RANGE synapseID, verboseLevel\n"
  "    RANGE conductance\n"
  "    RANGE next_delay\n"
  "    BBCOREPOINTER delay_times, delay_weights\n"
  "    GLOBAL nc_type_param\n"
  "    : For debugging\n"
  "    :RANGE sgid, tgid\n"
  "}\n"
  "\n"
  "\n"
  "PARAMETER {\n"
  "    tau_r_AMPA = 0.2   (ms)  : Dual-exponential conductance profile\n"
  "    tau_d_AMPA = 1.7   (ms)  : IMPORTANT: tau_r < tau_d\n"
  "    tau_r_NMDA = 0.29  (ms)  : Dual-exponential conductance profile\n"
  "    tau_d_NMDA = 43    (ms)  : IMPORTANT: tau_r < tau_d\n"
  "    Use = 1.0          (1)   : Utilization of synaptic efficacy\n"
  "    Dep = 100          (ms)  : Relaxation time constant from depression\n"
  "    Fac = 10           (ms)  : Relaxation time constant from facilitation\n"
  "    e = 0              (mV)  : AMPA and NMDA reversal potential\n"
  "    mg = 1             (mM)  : Initial concentration of mg2+\n"
  "    gmax = .001        (uS)  : Weight conversion factor (from nS to uS)\n"
  "    u0 = 0                   : Initial value of u, which is the running value of Use\n"
  "    NMDA_ratio = 0.71  (1)   : The ratio of NMDA to AMPA\n"
  "    synapseID = 0\n"
  "    verboseLevel = 0\n"
  "    conductance = 0.0\n"
  "    nc_type_param = 7\n"
  "    :sgid = -1\n"
  "    :tgid = -1\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#ifndef CORENEURON_BUILD\n"
  "extern int ifarg(int iarg);\n"
  "\n"
  "extern void* vector_arg(int iarg);\n"
  "extern double* vector_vec(void* vv);\n"
  "extern int vector_capacity(void* vv);\n"
  "#endif\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "ASSIGNED {\n"
  "    v (mV)\n"
  "    i (nA)\n"
  "    i_AMPA (nA)\n"
  "    i_NMDA (nA)\n"
  "    g_AMPA (uS)\n"
  "    g_NMDA (uS)\n"
  "    g (uS)\n"
  "    factor_AMPA\n"
  "    factor_NMDA\n"
  "    mggate\n"
  "\n"
  "    : stuff for delayed connections\n"
  "    delay_times\n"
  "    delay_weights\n"
  "    next_delay (ms)\n"
  "}\n"
  "\n"
  "PROCEDURE setup_delay_vecs() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    void** vv_delay_times = (void**)(&_p_delay_times);\n"
  "    void** vv_delay_weights = (void**)(&_p_delay_weights);\n"
  "    *vv_delay_times = (void*)NULL;\n"
  "    *vv_delay_weights = (void*)NULL;\n"
  "    if (ifarg(1)) {\n"
  "        *vv_delay_times = vector_arg(1);\n"
  "    }\n"
  "    if (ifarg(2)) {\n"
  "        *vv_delay_weights = vector_arg(2);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "STATE {\n"
  "    A_AMPA       : AMPA state variable to construct the dual-exponential profile - decays with conductance tau_r_AMPA\n"
  "    B_AMPA       : AMPA state variable to construct the dual-exponential profile - decays with conductance tau_d_AMPA\n"
  "    A_NMDA       : NMDA state variable to construct the dual-exponential profile - decays with conductance tau_r_NMDA\n"
  "    B_NMDA       : NMDA state variable to construct the dual-exponential profile - decays with conductance tau_d_NMDA\n"
  "}\n"
  "\n"
  "\n"
  "INITIAL{\n"
  "    LOCAL tp_AMPA, tp_NMDA\n"
  "\n"
  "    A_AMPA = 0\n"
  "    B_AMPA = 0\n"
  "\n"
  "    A_NMDA = 0\n"
  "    B_NMDA = 0\n"
  "\n"
  "    tp_AMPA = (tau_r_AMPA*tau_d_AMPA)/(tau_d_AMPA-tau_r_AMPA)*log(tau_d_AMPA/tau_r_AMPA) :time to peak of the conductance\n"
  "    tp_NMDA = (tau_r_NMDA*tau_d_NMDA)/(tau_d_NMDA-tau_r_NMDA)*log(tau_d_NMDA/tau_r_NMDA) :time to peak of the conductance\n"
  "\n"
  "    factor_AMPA = -exp(-tp_AMPA/tau_r_AMPA)+exp(-tp_AMPA/tau_d_AMPA) :AMPA Normalization factor - so that when t = tp_AMPA, gsyn = gpeak\n"
  "    factor_AMPA = 1/factor_AMPA\n"
  "\n"
  "    factor_NMDA = -exp(-tp_NMDA/tau_r_NMDA)+exp(-tp_NMDA/tau_d_NMDA) :NMDA Normalization factor - so that when t = tp_NMDA, gsyn = gpeak\n"
  "    factor_NMDA = 1/factor_NMDA\n"
  "\n"
  "    next_delay = -1\n"
  "}\n"
  "\n"
  "\n"
  "BREAKPOINT {\n"
  "    SOLVE state METHOD cnexp\n"
  "    mggate = 1 / (1 + exp(0.062 (/mV) * -(v)) * (mg / 3.57 (mM))) :mggate kinetics - Jahr & Stevens 1990\n"
  "    g_AMPA = gmax*(B_AMPA-A_AMPA) :compute time varying conductance as the difference of state variables B_AMPA and A_AMPA\n"
  "    g_NMDA = gmax*(B_NMDA-A_NMDA) * mggate :compute time varying conductance as the difference of state variables B_NMDA and A_NMDA and mggate kinetics\n"
  "    g = g_AMPA + g_NMDA\n"
  "    i_AMPA = g_AMPA*(v-e) :compute the AMPA driving force based on the time varying conductance, membrane potential, and AMPA reversal\n"
  "    i_NMDA = g_NMDA*(v-e) :compute the NMDA driving force based on the time varying conductance, membrane potential, and NMDA reversal\n"
  "    i = i_AMPA + i_NMDA\n"
  "}\n"
  "\n"
  "\n"
  "DERIVATIVE state{\n"
  "    A_AMPA' = -A_AMPA/tau_r_AMPA\n"
  "    B_AMPA' = -B_AMPA/tau_d_AMPA\n"
  "    A_NMDA' = -A_NMDA/tau_r_NMDA\n"
  "    B_NMDA' = -B_NMDA/tau_d_NMDA\n"
  "}\n"
  "\n"
  "\n"
  "NET_RECEIVE (weight, weight_AMPA, weight_NMDA, R, Pr, u, tsyn (ms), nc_type){\n"
  "    LOCAL result\n"
  "    weight_AMPA = weight\n"
  "    weight_NMDA = weight * NMDA_ratio\n"
  "\n"
  "    INITIAL{\n"
  "        R=1\n"
  "        u=u0\n"
  "        tsyn=t\n"
  "\n"
  "        if (nc_type == 0) {\n"
  "            : nc_type {\n"
  "            :   0 = presynaptic netcon\n"
  "            :   1 = spontmini netcon\n"
  "            :   2 = replay netcon\n"
  "            : }\n"
  "    VERBATIM\n"
  "            // setup self events for delayed connections to change weights\n"
  "            void *vv_delay_times = *((void**)(&_p_delay_times));\n"
  "            void *vv_delay_weights = *((void**)(&_p_delay_weights));\n"
  "            if (vv_delay_times && vector_capacity(vv_delay_times)>=1) {\n"
  "              double* deltm_el = vector_vec(vv_delay_times);\n"
  "              int delay_times_idx;\n"
  "              next_delay = 0;\n"
  "              for(delay_times_idx = 0; delay_times_idx < vector_capacity(vv_delay_times); ++delay_times_idx) {\n"
  "                double next_delay_t = deltm_el[delay_times_idx];\n"
  "    ENDVERBATIM\n"
  "                net_send(next_delay_t, 1)\n"
  "    VERBATIM\n"
  "              }\n"
  "            }\n"
  "    ENDVERBATIM\n"
  "        }\n"
  "    }\n"
  "\n"
  "    : Disable in case of t < 0 (in case of ForwardSkip) which causes numerical\n"
  "    : instability if synapses are activated.\n"
  "    if(t < 0 ) {\n"
  "    VERBATIM\n"
  "        return;\n"
  "    ENDVERBATIM\n"
  "    }\n"
  "\n"
  "    if (flag == 1) {\n"
  "        : self event to set next weight at delay\n"
  "    VERBATIM\n"
  "        // setup self events for delayed connections to change weights\n"
  "        void *vv_delay_weights = *((void**)(&_p_delay_weights));\n"
  "        if (vv_delay_weights && vector_capacity(vv_delay_weights)>=next_delay) {\n"
  "          double* weights_v = vector_vec(vv_delay_weights);\n"
  "          double next_delay_weight = weights_v[(int)next_delay];\n"
  "    ENDVERBATIM\n"
  "          weight = conductance*next_delay_weight\n"
  "          next_delay = next_delay + 1\n"
  "    VERBATIM\n"
  "        }\n"
  "        return;\n"
  "    ENDVERBATIM\n"
  "    }\n"
  "    : flag == 0, i.e. a spike has arrived\n"
  "\n"
  "    : calc u at event-\n"
  "    if (Fac > 0) {\n"
  "        u = u*exp(-(t - tsyn)/Fac) :update facilitation variable if Fac>0 Eq. 2 in Fuhrmann et al.\n"
  "    } else {\n"
  "        u = Use\n"
  "    }\n"
  "    if(Fac > 0){\n"
  "        u = u + Use*(1-u) :update facilitation variable if Fac>0 Eq. 2 in Fuhrmann et al.\n"
  "    }\n"
  "\n"
  "    R  = 1 - (1-R) * exp(-(t-tsyn)/Dep) :Probability R for a vesicle to be available for release, analogous to the pool of synaptic\n"
  "                                        :resources available for release in the deterministic model. Eq. 3 in Fuhrmann et al.\n"
  "    Pr  = u * R                         :Pr is calculated as R * u (running value of Use)\n"
  "    R  = R - u * R                      :update R as per Eq. 3 in Fuhrmann et al.\n"
  "\n"
  "    if( verboseLevel > 0 ) {\n"
  "        printf(\"Synapse %f at time %g: R = %g Pr = %g erand = %g\\n\", synapseID, t, R, Pr, result )\n"
  "    }\n"
  "\n"
  "    tsyn = t\n"
  "\n"
  "    A_AMPA = A_AMPA + Pr*weight_AMPA*factor_AMPA\n"
  "    B_AMPA = B_AMPA + Pr*weight_AMPA*factor_AMPA\n"
  "    A_NMDA = A_NMDA + Pr*weight_NMDA*factor_NMDA\n"
  "    B_NMDA = B_NMDA + Pr*weight_NMDA*factor_NMDA\n"
  "\n"
  "    if( verboseLevel > 0 ) {\n"
  "        printf( \" vals %g %g %g %g\\n\", A_AMPA, weight_AMPA, factor_AMPA, weight )\n"
  "    }\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION toggleVerbose() {\n"
  "    verboseLevel = 1-verboseLevel\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "static void bbcore_write(double* x, int* d, int* x_offset, int* d_offset, _threadargsproto_) {\n"
  "\n"
  "  void *vv_delay_times = *((void**)(&_p_delay_times));\n"
  "  void *vv_delay_weights = *((void**)(&_p_delay_weights));\n"
  "\n"
  "  // serialize connection delay vectors\n"
  "  if (vv_delay_times && vv_delay_weights &&\n"
  "     (vector_capacity(vv_delay_times) >= 1) && (vector_capacity(vv_delay_weights) >= 1)) {\n"
  "    if (d && x) {\n"
  "      int* d_i = d + *d_offset;\n"
  "      // store vector sizes for deserialization\n"
  "      d_i[0] = vector_capacity(vv_delay_times);\n"
  "      d_i[1] = vector_capacity(vv_delay_weights);\n"
  "\n"
  "      double* delay_times_el = vector_vec(vv_delay_times);\n"
  "      double* delay_weights_el = vector_vec(vv_delay_weights);\n"
  "      double* x_i = x + *x_offset;\n"
  "      int delay_vecs_idx;\n"
  "      int x_idx = 0;\n"
  "      for(delay_vecs_idx = 0; delay_vecs_idx < vector_capacity(vv_delay_times); ++delay_vecs_idx) {\n"
  "         x_i[x_idx++] = delay_times_el[delay_vecs_idx];\n"
  "         x_i[x_idx++] = delay_weights_el[delay_vecs_idx];\n"
  "      }\n"
  "    }\n"
  "  } else {\n"
  "    if (d) {\n"
  "      int* d_i = d + *d_offset;\n"
  "      d_i[0] = 0;\n"
  "      d_i[1] = 0;\n"
  "    }\n"
  "  }\n"
  "  // reserve space for delay connection vector sizes on serialization buffer\n"
  "  *d_offset += 2;\n"
  "\n"
  "  // reserve space for connection delay data on serialization buffer\n"
  "  if (vv_delay_times && vv_delay_weights) {\n"
  "    *x_offset += vector_capacity(vv_delay_times) + vector_capacity(vv_delay_weights);\n"
  "  }\n"
  "}\n"
  "\n"
  "static void bbcore_read(double* x, int* d, int* x_offset, int* d_offset, _threadargsproto_) {\n"
  "  assert(!_p_delay_times && !_p_delay_weights);\n"
  "\n"
  "  // first get delay vector sizes\n"
  "  int* d_i = d + *d_offset;\n"
  "  int delay_times_sz = d_i[0];\n"
  "  int delay_weights_sz = d_i[1];\n"
  "  *d_offset += 2;\n"
  "\n"
  "  if ((delay_times_sz > 0) && (delay_weights_sz > 0)) {\n"
  "    double* x_i = x + *x_offset;\n"
  "\n"
  "    // allocate vectors\n"
  "    _p_delay_times = vector_new1(delay_times_sz);\n"
  "    _p_delay_weights = vector_new1(delay_weights_sz);\n"
  "\n"
  "    double* delay_times_el = vector_vec(_p_delay_times);\n"
  "    double* delay_weights_el = vector_vec(_p_delay_weights);\n"
  "\n"
  "    // copy data\n"
  "    int x_idx;\n"
  "    int vec_idx = 0;\n"
  "    for(x_idx = 0; x_idx < delay_times_sz + delay_weights_sz; x_idx += 2) {\n"
  "      delay_times_el[vec_idx] = x_i[x_idx];\n"
  "      delay_weights_el[vec_idx++] = x_i[x_idx+1];\n"
  "    }\n"
  "    *x_offset += delay_times_sz + delay_weights_sz;\n"
  "  }\n"
  "}\n"
  "ENDVERBATIM\n"
  ;
#endif
