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
 
#define nrn_init _nrn_init__VecStim
#define _nrn_initial _nrn_initial__VecStim
#define nrn_cur _nrn_cur__VecStim
#define _nrn_current _nrn_current__VecStim
#define nrn_jacob _nrn_jacob__VecStim
#define nrn_state _nrn_state__VecStim
#define _net_receive _net_receive__VecStim 
#define play play__VecStim 
#define restartEvent restartEvent__VecStim 
 
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
#define ping _p[0]
#define index _p[1]
#define etime _p[2]
#define space _p[3]
#define v _p[4]
#define _tsav _p[5]
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
 static double _hoc_element();
 static double _hoc_play();
 static double _hoc_restartEvent();
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
 "element", _hoc_element,
 "play", _hoc_play,
 "restartEvent", _hoc_restartEvent,
 0, 0
};
#define element element_VecStim
 extern double element( _threadargsproto_ );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "ping", "ms",
 "etime", "ms",
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
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"VecStim",
 "ping",
 0,
 "index",
 "etime",
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
 	_p = nrn_prop_data_alloc(_mechtype, 6, _prop);
 	/*initialize range parameters*/
 	ping = 1;
  }
 	_prop->param = _p;
 	_prop->param_size = 6;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 
}
 static void _initlists();
 
#define _tqitem &(_ppvar[2]._pvoid)
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _VecStim_reg() {
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
  hoc_register_prop_size(_mechtype, 6, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "netsend");
 add_nrn_artcell(_mechtype, 2);
 add_nrn_has_net_event(_mechtype);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 VecStim /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/VecStim.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int play(_threadargsproto_);
static int restartEvent(_threadargsproto_);
 
/*VERBATIM*/
#ifdef STIM_DEBUG
# define debug_printf(...) printf(__VA_ARGS__)
#else
# define debug_printf(...)
#endif
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   if ( _lflag  == 1.0 ) {
     
/*VERBATIM*/
        debug_printf("[VecStim] net_event(): index=%d, etime=%g, t=%g\n", (int)index - 1, etime, t);
 net_event ( _pnt, t ) ;
     if ( element ( _threadargs_ ) > 0.0 ) {
       if ( etime < t ) {
         printf ( "[VecStim] WARNING: spike time (%g ms) before current time (%g ms)\n" , etime , t ) ;
         }
       else {
         artcell_net_send ( _tqitem, _args, _pnt, t +  etime - t , 1.0 ) ;
         }
       }
     }
   else if ( _lflag  == 2.0 ) {
     if ( index  == - 2.0 ) {
       printf ( "[VecStim] Detected new time vector.\n" ) ;
       restartEvent ( _threadargs_ ) ;
       }
     artcell_net_send ( _tqitem, _args, _pnt, t +  ping , 2.0 ) ;
     }
   } }
 
static int  restartEvent ( _threadargsproto_ ) {
   index = 0.0 ;
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    while (element(_threadargs_) && etime < t) {}  // Ignore past events
    if (index > 0) {
        // Invoke low-level artcell_net_send, since generic NMODL net_send is only
        // available in INITIAL and NET_RECEIVE blocks. It takes an ABSOLUTE time instead
        debug_printf("[VecStim] restartEvent(delay=%g): index=%d, etime=%g, t=%g\n", delay, (int)index - 1, etime, t);
        artcell_net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
    }
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
 
/*VERBATIM*/
extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();
 
double element ( _threadargsproto_ ) {
   double _lelement;
 
/*VERBATIM*/
    const int i = (int)index;
    void* const vv = *((void**)(&space));
    int size; double* px;
    if (i < 0 || vv == NULL)
        return 0;

    size = vector_capacity(vv);
    px = vector_vec(vv);
    if (i < size) {
        etime = px[i];
        index += 1.;
        debug_printf("[VecStim] element(): index=%d, etime=%g, t=%g\n", (int)index - 1, etime, t);
        return index;
    }
    index = -1;
    return 0;
 
return _lelement;
 }
 
static double _hoc_element(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  element ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  play ( _threadargsproto_ ) {
   
/*VERBATIM*/
    #ifndef CORENEURON_BUILD
    void** vv;
    vv = (void**)(&space);
    *vv = NULL;
    if (ifarg(1)) {
        *vv = vector_arg(1);
    }
    index = -2;
    #endif
  return 0; }
 
static double _hoc_play(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 play ( _p, _ppvar, _thread, _nt );
 return(_r);
}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
 {
   
/*VERBATIM*/
 #ifndef CORENEURON_BUILD
 // This Mechanism is not useful for CoreNeuron, since it has its own implementation
 // Therefore we should avoid even compiling it together, but for backwards compat keep guards
 index = 0.0 ;
   if ( element ( _threadargs_ ) ) {
     artcell_net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  etime - t , 1.0 ) ;
     }
   if ( ping > 0.0 ) {
     artcell_net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  ping , 2.0 ) ;
     }
   
/*VERBATIM*/
 #endif
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/VecStim.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file VecStim.mod\n"
  " * @brief\n"
  " * @author king\n"
  " * @date 2011-03-16\n"
  " * @remark Copyright \n"
  "\n"
  " BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "\n"
  ": Vector stream of events\n"
  "NEURON {\n"
  "    THREADSAFE\n"
  "    ARTIFICIAL_CELL VecStim\n"
  "    RANGE ping, index, etime\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "    ping = 1 (ms)\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "    index  : The index(+1) of the last retrieved element. See element()\n"
  "    etime (ms)\n"
  "    space\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "#ifdef STIM_DEBUG\n"
  "# define debug_printf(...) printf(__VA_ARGS__)\n"
  "#else\n"
  "# define debug_printf(...)\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "INITIAL {\n"
  "VERBATIM\n"
  " #ifndef CORENEURON_BUILD\n"
  " // This Mechanism is not useful for CoreNeuron, since it has its own implementation\n"
  " // Therefore we should avoid even compiling it together, but for backwards compat keep guards\n"
  "ENDVERBATIM\n"
  "    index = 0\n"
  "    if(element()) {\n"
  "        net_send(etime - t, 1)\n"
  "    }\n"
  "    if (ping > 0) {\n"
  "        net_send(ping, 2)\n"
  "    }\n"
  "VERBATIM\n"
  " #endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "NET_RECEIVE (w) {\n"
  "    if (flag == 1) {  : deliver event\n"
  "    VERBATIM\n"
  "        debug_printf(\"[VecStim] net_event(): index=%d, etime=%g, t=%g\\n\", (int)index - 1, etime, t);\n"
  "    ENDVERBATIM\n"
  "        net_event(t)\n"
  "\n"
  "        : schedule next event\n"
  "        if (element() > 0) {\n"
  "            if (etime < t) {\n"
  "                printf(\"[VecStim] WARNING: spike time (%g ms) before current time (%g ms)\\n\",etime,t)\n"
  "            } else {\n"
  "                net_send(etime - t, 1)\n"
  "            }\n"
  "        }\n"
  "    } else if (flag == 2) { : ping - reset index to 0\n"
  "        :printf(\"flag=2, etime=%g, t=%g, ping=%g, index=%g\\n\",etime,t,ping,index)\n"
  "        if (index == -2) { : play() has been called\n"
  "            printf(\"[VecStim] Detected new time vector.\\n\")\n"
  "            restartEvent()\n"
  "        }\n"
  "        net_send(ping, 2)\n"
  "    }\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * Resume the event delivery loop for NEURON restore.\n"
  " */\n"
  "ENDCOMMENT\n"
  "PROCEDURE restartEvent() {\n"
  "    index = 0\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    while (element(_threadargs_) && etime < t) {}  // Ignore past events\n"
  "    if (index > 0) {\n"
  "        // Invoke low-level artcell_net_send, since generic NMODL net_send is only\n"
  "        // available in INITIAL and NET_RECEIVE blocks. It takes an ABSOLUTE time instead\n"
  "        debug_printf(\"[VecStim] restartEvent(delay=%g): index=%d, etime=%g, t=%g\\n\", delay, (int)index - 1, etime, t);\n"
  "        artcell_net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "extern double* vector_vec();\n"
  "extern int vector_capacity();\n"
  "extern void* vector_arg();\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * \\brief Retrieves an element (spike time) from the source vector, store in etime.\n"
  " *\n"
  " * \\return The index+1 of the element (=~ true). Otherwise 0 (not initialized or end)\n"
  " *\n"
  " * NOTE: For back-compat index is incremented *after* the element is retrieved, making\n"
  " *   it like a base-1 indexing scheme, or representing the next elements index.\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION element() {\n"
  "VERBATIM\n"
  "    const int i = (int)index;\n"
  "    void* const vv = *((void**)(&space));\n"
  "    int size; double* px;\n"
  "    if (i < 0 || vv == NULL)\n"
  "        return 0;\n"
  "\n"
  "    size = vector_capacity(vv);\n"
  "    px = vector_vec(vv);\n"
  "    if (i < size) {\n"
  "        etime = px[i];\n"
  "        index += 1.;\n"
  "        debug_printf(\"[VecStim] element(): index=%d, etime=%g, t=%g\\n\", (int)index - 1, etime, t);\n"
  "        return index;\n"
  "    }\n"
  "    index = -1;\n"
  "    return 0;\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE play() {\n"
  "VERBATIM\n"
  "    #ifndef CORENEURON_BUILD\n"
  "    void** vv;\n"
  "    vv = (void**)(&space);\n"
  "    *vv = NULL;\n"
  "    if (ifarg(1)) {\n"
  "        *vv = vector_arg(1);\n"
  "    }\n"
  "    index = -2;\n"
  "    #endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ;
#endif
