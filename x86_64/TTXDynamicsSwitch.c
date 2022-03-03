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
 
#define nrn_init _nrn_init__TTXDynamicsSwitch
#define _nrn_initial _nrn_initial__TTXDynamicsSwitch
#define nrn_cur _nrn_cur__TTXDynamicsSwitch
#define _nrn_current _nrn_current__TTXDynamicsSwitch
#define nrn_jacob _nrn_jacob__TTXDynamicsSwitch
#define nrn_state _nrn_state__TTXDynamicsSwitch
#define _net_receive _net_receive__TTXDynamicsSwitch 
 
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
#define ttxo_level _p[0]
#define ttxo _p[1]
#define ttxi _p[2]
#define v _p[3]
#define _g _p[4]
#define _ion_ttxo	*_ppvar[0]._pval
#define _ion_ttxi	*_ppvar[1]._pval
#define _style_ttx	*((int*)_ppvar[2]._pvoid)
 
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

 extern void _nrn_setdata_reg(int, void(*)(Prop*));
 static void _setdata(Prop* _prop) {
 _extcall_prop = _prop;
 }
 static void _hoc_setdata() {
 Prop *_prop, *hoc_getdata_range(int);
 _prop = hoc_getdata_range(_mechtype);
   _setdata(_prop);
 hoc_retpushx(1.);
}
 /* connect user functions to hoc names */
 static VoidFunc hoc_intfunc[] = {
 "setdata_TTXDynamicsSwitch", _hoc_setdata,
 0, 0
};
 /* declare global and static user variables */
#define ttxi_sentinel ttxi_sentinel_TTXDynamicsSwitch
 double ttxi_sentinel = 0.015625;
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "ttxi_sentinel_TTXDynamicsSwitch", "mM",
 "ttxo_level_TTXDynamicsSwitch", "mM",
 0,0
};
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 "ttxi_sentinel_TTXDynamicsSwitch", &ttxi_sentinel_TTXDynamicsSwitch,
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
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"TTXDynamicsSwitch",
 "ttxo_level_TTXDynamicsSwitch",
 0,
 0,
 0,
 0};
 static Symbol* _ttx_sym;
 
extern Prop* need_memb(Symbol*);

static void nrn_alloc(Prop* _prop) {
	Prop *prop_ion;
	double *_p; Datum *_ppvar;
 	_p = nrn_prop_data_alloc(_mechtype, 5, _prop);
 	/*initialize range parameters*/
 	ttxo_level = 1e-12;
 	_prop->param = _p;
 	_prop->param_size = 5;
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 prop_ion = need_memb(_ttx_sym);
 nrn_check_conc_write(_prop, prop_ion, 0);
 nrn_check_conc_write(_prop, prop_ion, 1);
 nrn_promote(prop_ion, 3, 0);
 	_ppvar[0]._pval = &prop_ion->param[2]; /* ttxo */
 	_ppvar[1]._pval = &prop_ion->param[1]; /* ttxi */
 	_ppvar[2]._pvoid = (void*)(&(prop_ion->dparam[0]._i)); /* iontype for ttx */
 
}
 static void _initlists();
 static void _update_ion_pointer(Datum*);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _TTXDynamicsSwitch_reg() {
	int _vectorized = 1;
  _initlists();
 	ion_reg("ttx", 1.0);
 	_ttx_sym = hoc_lookup("ttx_ion");
 	register_mech(_mechanism, nrn_alloc,nrn_cur, nrn_jacob, nrn_state, nrn_init, hoc_nrnpointerindex, 1);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
     _nrn_thread_reg(_mechtype, 2, _update_ion_pointer);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 5, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "ttx_ion");
  hoc_register_dparam_semantics(_mechtype, 1, "ttx_ion");
  hoc_register_dparam_semantics(_mechtype, 2, "#ttx_ion");
 	nrn_writes_conc(_mechtype, 0);
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 TTXDynamicsSwitch /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/TTXDynamicsSwitch.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
 extern void nrn_update_ion_pointer(Symbol*, Datum*, int, int);
 static void _update_ion_pointer(Datum* _ppvar) {
   nrn_update_ion_pointer(_ttx_sym, _ppvar, 0, 2);
   nrn_update_ion_pointer(_ttx_sym, _ppvar, 1, 1);
 }

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
 {
   ttxo = ttxo_level ;
   ttxi = ttxi_sentinel ;
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
  ttxo = _ion_ttxo;
  ttxi = _ion_ttxi;
 initmodel(_p, _ppvar, _thread, _nt);
  _ion_ttxo = ttxo;
  _ion_ttxi = ttxi;
  nrn_wrote_conc(_ttx_sym, (&(_ion_ttxi)) - 1, _style_ttx);
}
}

static double _nrn_current(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt, double _v){double _current=0.;v=_v;{
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
  ttxo = _ion_ttxo;
  ttxi = _ion_ttxi;
 {
   ttxo = ttxo_level ;
   }
  _ion_ttxo = ttxo;
  _ion_ttxi = ttxi;
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/TTXDynamicsSwitch.mod";
static const char* nmodl_file_text = 
  ": Simple switching TTX dynamics\n"
  ": Outside TTX concentration level stays fixed at ttxo_level, which can be\n"
  ": set as a range variable\n"
  ": Implemented by Werner Van Geit @ BlueBrain Project, Jan 2015\n"
  "\n"
  "NEURON	{\n"
  "	SUFFIX TTXDynamicsSwitch\n"
  "	USEION ttx WRITE ttxo, ttxi VALENCE 1\n"
  "    RANGE ttxo_level\n"
  "}\n"
  "\n"
  "PARAMETER	{\n"
  "    : 1e-12 represent 'no TTX', using 0.0 could generate problems during the \n"
  "    : possible calculation of ettx \n"
  "    ttxo_level = 1e-12 (mM)\n"
  "\n"
  "    : Check at the end of the mod file for the reasoning behind this sentinel\n"
  "    : value\n"
  "    ttxi_sentinel = 0.015625 (mM) : 1.0/64.0\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "    ttxo (mM)\n"
  "    ttxi (mM)\n"
  "}\n"
  "\n"
  "BREAKPOINT	{\n"
  "    ttxo = ttxo_level\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "    ttxo = ttxo_level\n"
  "    ttxi = ttxi_sentinel\n"
  "}\n"
  "\n"
  ": WVG @ BBP, Jan 2015\n"
  ": The internal ttx concentration is a sentinel value, this value should\n"
  ": not be used for any calculation\n"
  ": The reason it is here is that Neuron's default value for a concentration\n"
  ": is 1.0. In case a sodium channel uses the TTX concentration to \n"
  ": enable/disable itself, it shouldn't use the default value. It should only\n"
  ": use the ttxo value when it has been initialised by this TTXDynamicsSwitch\n"
  ": mechanism.\n"
  ": (or any other value that manages the outside ttx concentration)\n"
  ": The channel should read the ttxi value, and check for this sentinel value\n"
  ": If it matches, it means this mechanism is control the ttxo concentration\n"
  ": otherwise ttxo should be ignored\n"
  ": Chose 1.0/64.0 as sentinel because it can be exactly represented in binary\n"
  ": floating-point representation\n"
  ;
#endif
