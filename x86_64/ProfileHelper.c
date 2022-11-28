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
 
#define nrn_init _nrn_init__ProfileHelper
#define _nrn_initial _nrn_initial__ProfileHelper
#define nrn_cur _nrn_cur__ProfileHelper
#define _nrn_current _nrn_current__ProfileHelper
#define nrn_jacob _nrn_jacob__ProfileHelper
#define nrn_state _nrn_state__ProfileHelper
#define _net_receive _net_receive__ProfileHelper 
#define pause_profiling pause_profiling__ProfileHelper 
#define resume_profiling resume_profiling__ProfileHelper 
 
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
#define v _p[0]
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
 static double _hoc_pause_profiling();
 static double _hoc_resume_profiling();
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
 "pause_profiling", _hoc_pause_profiling,
 "resume_profiling", _hoc_resume_profiling,
 0, 0
};
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
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
"ProfileHelper",
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
 	_p = nrn_prop_data_alloc(_mechtype, 1, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 1;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 2, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 
}
 static void _initlists();
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _ProfileHelper_reg() {
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
  hoc_register_prop_size(_mechtype, 1, 2);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
 add_nrn_artcell(_mechtype, 0);
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 ProfileHelper /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ProfileHelper.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int pause_profiling(_threadargsproto_);
static int resume_profiling(_threadargsproto_);
 
/*VERBATIM*/

// tau profiling api
#if defined(ENABLE_TAU_PROFILER)
#include <TAU.h>

// score-p profiling api
#elif defined(ENABLE_SCOREP_PROFILER)
#include <scorep/SCOREP_User.h>

// hpctoolkit profiling api
#elif defined(ENABLE_HPCTOOLKIT_PROFILER)
#include <hpctoolkit.h>

#endif


static void print_message(const char *message) {
    #ifndef CORENEURON_BUILD
    extern int nrnmpi_myid;
    if(nrnmpi_myid == 0) {
        printf("%s", message);
    }
    #endif
}

 
static int  resume_profiling ( _threadargsproto_ ) {
   
/*VERBATIM*/

        #if defined(ENABLE_TAU_PROFILER)
            TAU_ENABLE_INSTRUMENTATION();
            print_message("Resume TAU Profiling\n");
        #elif defined(ENABLE_SCOREP_PROFILER)
            SCOREP_RECORDING_ON()
            print_message("Resume Score-P Profiling\n");
        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)
            hpctoolkit_sampling_start();
            print_message("Resume HPCToolkit Profiling\n");
        #endif

  return 0; }
 
static double _hoc_resume_profiling(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 resume_profiling ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  pause_profiling ( _threadargsproto_ ) {
   
/*VERBATIM*/

        #if defined(ENABLE_TAU_PROFILER)
            TAU_DISABLE_INSTRUMENTATION();
            print_message("Pause TAU Profiling\n");
        #elif defined(ENABLE_SCOREP_PROFILER)
            SCOREP_RECORDING_OFF()
            print_message("Pause Score-P Profiling\n");
        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)
            hpctoolkit_sampling_stop();
            print_message("Pause HPCToolkit Profiling\n");
        #endif

  return 0; }
 
static double _hoc_pause_profiling(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 pause_profiling ( _p, _ppvar, _thread, _nt );
 return(_r);
}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{

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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ProfileHelper.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file ProfileHelper.mod\n"
  " * @brief Provide an interface to resume/pause profiling from different profiling tools\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    THREADSAFE\n"
  "    ARTIFICIAL_CELL ProfileHelper\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "// tau profiling api\n"
  "#if defined(ENABLE_TAU_PROFILER)\n"
  "#include <TAU.h>\n"
  "\n"
  "// score-p profiling api\n"
  "#elif defined(ENABLE_SCOREP_PROFILER)\n"
  "#include <scorep/SCOREP_User.h>\n"
  "\n"
  "// hpctoolkit profiling api\n"
  "#elif defined(ENABLE_HPCTOOLKIT_PROFILER)\n"
  "#include <hpctoolkit.h>\n"
  "\n"
  "#endif\n"
  "\n"
  "\n"
  "static void print_message(const char *message) {\n"
  "    #ifndef CORENEURON_BUILD\n"
  "    extern int nrnmpi_myid;\n"
  "    if(nrnmpi_myid == 0) {\n"
  "        printf(\"%s\", message);\n"
  "    }\n"
  "    #endif\n"
  "}\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  ": Start/Resume profiling\n"
  "PROCEDURE resume_profiling() {\n"
  "\n"
  "    VERBATIM\n"
  "\n"
  "        #if defined(ENABLE_TAU_PROFILER)\n"
  "            TAU_ENABLE_INSTRUMENTATION();\n"
  "            print_message(\"Resume TAU Profiling\\n\");\n"
  "        #elif defined(ENABLE_SCOREP_PROFILER)\n"
  "            SCOREP_RECORDING_ON()\n"
  "            print_message(\"Resume Score-P Profiling\\n\");\n"
  "        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)\n"
  "            hpctoolkit_sampling_start();\n"
  "            print_message(\"Resume HPCToolkit Profiling\\n\");\n"
  "        #endif\n"
  "\n"
  "    ENDVERBATIM\n"
  "\n"
  "}\n"
  "\n"
  ": Pause profiling\n"
  "PROCEDURE pause_profiling() {\n"
  "\n"
  "    VERBATIM\n"
  "\n"
  "        #if defined(ENABLE_TAU_PROFILER)\n"
  "            TAU_DISABLE_INSTRUMENTATION();\n"
  "            print_message(\"Pause TAU Profiling\\n\");\n"
  "        #elif defined(ENABLE_SCOREP_PROFILER)\n"
  "            SCOREP_RECORDING_OFF()\n"
  "            print_message(\"Pause Score-P Profiling\\n\");\n"
  "        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)\n"
  "            hpctoolkit_sampling_stop();\n"
  "            print_message(\"Pause HPCToolkit Profiling\\n\");\n"
  "        #endif\n"
  "\n"
  "    ENDVERBATIM\n"
  "\n"
  "}\n"
  ;
#endif