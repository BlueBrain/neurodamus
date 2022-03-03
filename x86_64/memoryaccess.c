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
 
#define nrn_init _nrn_init__MemoryAccess
#define _nrn_initial _nrn_initial__MemoryAccess
#define nrn_cur _nrn_cur__MemoryAccess
#define _nrn_current _nrn_current__MemoryAccess
#define nrn_jacob _nrn_jacob__MemoryAccess
#define nrn_state _nrn_state__MemoryAccess
#define _net_receive _net_receive__MemoryAccess 
#define addvar addvar__MemoryAccess 
#define close close__MemoryAccess 
#define nothing nothing__MemoryAccess 
#define prdata prdata__MemoryAccess 
#define reveal reveal__MemoryAccess 
 
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
 static double _hoc_aopen();
 static double _hoc_addvar();
 static double _hoc_close();
 static double _hoc_nothing();
 static double _hoc_prstr();
 static double _hoc_prdata();
 static double _hoc_reveal();
 static double _hoc_wopen();
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
 "aopen", _hoc_aopen,
 "addvar", _hoc_addvar,
 "close", _hoc_close,
 "nothing", _hoc_nothing,
 "prstr", _hoc_prstr,
 "prdata", _hoc_prdata,
 "reveal", _hoc_reveal,
 "wopen", _hoc_wopen,
 0, 0
};
#define aopen aopen_MemoryAccess
#define prstr prstr_MemoryAccess
#define wopen wopen_MemoryAccess
 extern double aopen( _threadargsproto_ );
 extern double prstr( _threadargsproto_ );
 extern double wopen( _threadargsproto_ );
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
 static void _destructor(Prop*);
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"MemoryAccess",
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
 	_p = nrn_prop_data_alloc(_mechtype, 1, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 1;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 static void bbcore_write(double*, int*, int*, int*, _threadargsproto_);
 extern void hoc_reg_bbcore_write(int, void(*)(double*, int*, int*, int*, _threadargsproto_));
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _memoryaccess_reg() {
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
  hoc_register_prop_size(_mechtype, 1, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 MemoryAccess /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/memoryaccess.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int addvar(_threadargsproto_);
static int close(_threadargsproto_);
static int nothing(_threadargsproto_);
static int prdata(_threadargsproto_);
static int reveal(_threadargsproto_);
 
/*VERBATIM*/

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
    // do I need a file ptr?  I don't want to write anything out
	//FILE* file_;
    
    /**
     * Pointer to array of pointers referenceing neuron varables (such as voltage or conductances)
     */
	double** ptrs_; /* list of pointers to hoc variables */
    
    /**
     * In the event that each line needs some padding up front (e.g. for a tag), this stores
     * the offset into line where actual data can start to be written
     */
	//int n_; /* line_ to line_+n contains a constant tag */
    
    /**
     * The number of pointers stored in the vector
     */
	int np_;
    
    /**
     * Vector capacity
     */
	int psize_;
    
    //char* line_; /* for construction of a line to be printed */
    /**
     * space available for writing the data to a string for final output
     */
	//int linesize_;
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

 
static int  reveal ( _threadargsproto_ ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
    char *helper1 = gargstr(1);
    char *helper2 = gargstr(2);
    
    //fprintf( stderr, "received %s and %s\n", helper1, helper2 );
    //fprintf( stderr, "What are you? %d\n", info->np_ );
    
    double**** access = NULL;

    //I want to parse this character string into a hex address.  How do I control whether I get
    // a 64 vs a 32 bit value? can I just put it directly into my variable?
    
    //fprintf(stderr, "extract the address\n" );
    sscanf( helper1, "%x", &access );
    
    //if I were to print access now, it should contain the address of neurodamus's object
    //if I were to dereference access now, it should contain zero
    //fprintf( stderr, "maintained address? %x\n", (int) access );
    //fprintf( stderr, "is it NULL? %x\n", (int) *access );
    
    //now, derefernce access and make it point to the array reference (not the array itself,
    // since that will potentially be reallocated as more variables are added)
    
    //fprintf( stderr, "dereference and assign address\n" );
    *access = &(info->ptrs_);
    
    int **access2;
    sscanf( helper2, "%x", &access2 );
    *access2 = &(info->np_);
    
    //fill in value to check it
    //*(*access2) = 5;
    //fprintf(stderr, "I filled in %d %d %d\n", *access2, info->np_, *(*access2) );
}
  return 0; }
 
static double _hoc_reveal(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 reveal ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  nothing ( _threadargsproto_ ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
	//++info->np_;
    fprintf( stderr, "incremented to %d\n", info->np_ );
	/* allow 20 chars per double */
}
  return 0; }
 
static double _hoc_nothing(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 nothing ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  addvar ( _threadargsproto_ ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
	if (info->np_ >= info->psize_) {
		info->psize_ *= 2;
		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();
	}
	info->ptrs_[info->np_] = hoc_pgetarg(1);
    //fprintf( stderr, "stored %d into %d (value = %lf)\n", info->ptrs_[info->np_], info->ptrs_, *info->ptrs_[info->np_] );
	++info->np_;
    //fprintf( stderr, "incremented to %d\n", info->np_ );
	/* allow 20 chars per double */
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
 
static int  prdata ( _threadargsproto_ ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
}
  return 0; }
 
static double _hoc_prdata(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 prdata ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double prstr ( _threadargsproto_ ) {
   double _lprstr;
 
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
}
 
return _lprstr;
 }
 
static double _hoc_prstr(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  prstr ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double wopen ( _threadargsproto_ ) {
   double _lwopen;
 
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
}
 
return _lwopen;
 }
 
static double _hoc_wopen(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  wopen ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double aopen ( _threadargsproto_ ) {
   double _laopen;
 
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
}
 
return _laopen;
 }
 
static double _hoc_aopen(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  aopen ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  close ( _threadargsproto_ ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
}
  return 0; }
 
static double _hoc_close(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 close ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
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
	INFOCAST;
	Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
	//info->file_ = (FILE*)0;
	info->psize_ = 10;
	info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();
	//info->linesize_ = 200;
	//info->line_ = (char*)hoc_Ecalloc(info->linesize_, sizeof(char)); hoc_malchk();
	info->np_ = 0;
	//info->n_ = 0;
	*ip = info;
	
    //fprintf( stderr, "The truth now - %x %d\n", (int) &(info->np_), info->np_ );
    //check for argument containing memory address, set to reference the array
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
	INFOCAST; Info* info = *ip;
	free(info);
}
 }
 
}
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/memoryaccess.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "This object is designed to accept a pointer from a caller and use that to instantiate an array\n"
  "for the storage of neuron addresses.  For example, if I want access to synapse parameters,\n"
  "I would pass in a pointer (triple pointer?) and after an initial array is allocated, the passed in\n"
  "pointer would be set to refer to the mem block.  Then bglib would pass in the memory addresses that\n"
  "need to be inserted into that array.\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "  THREADSAFE\n"
  "	POINT_PROCESS MemoryAccess\n"
  "	BBCOREPOINTER ptr\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "	ptr\n"
  "}\n"
  "\n"
  "VERBATIM\n"
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
  "    // do I need a file ptr?  I don't want to write anything out\n"
  "	//FILE* file_;\n"
  "    \n"
  "    /**\n"
  "     * Pointer to array of pointers referenceing neuron varables (such as voltage or conductances)\n"
  "     */\n"
  "	double** ptrs_; /* list of pointers to hoc variables */\n"
  "    \n"
  "    /**\n"
  "     * In the event that each line needs some padding up front (e.g. for a tag), this stores\n"
  "     * the offset into line where actual data can start to be written\n"
  "     */\n"
  "	//int n_; /* line_ to line_+n contains a constant tag */\n"
  "    \n"
  "    /**\n"
  "     * The number of pointers stored in the vector\n"
  "     */\n"
  "	int np_;\n"
  "    \n"
  "    /**\n"
  "     * Vector capacity\n"
  "     */\n"
  "	int psize_;\n"
  "    \n"
  "    //char* line_; /* for construction of a line to be printed */\n"
  "    /**\n"
  "     * space available for writing the data to a string for final output\n"
  "     */\n"
  "	//int linesize_;\n"
  "} Info;\n"
  "\n"
  "#define INFOCAST Info** ip = (Info**)(&(_p_ptr))\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "CONSTRUCTOR {\n"
  "VERBATIM {\n"
  "	INFOCAST;\n"
  "	Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "	//info->file_ = (FILE*)0;\n"
  "	info->psize_ = 10;\n"
  "	info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();\n"
  "	//info->linesize_ = 200;\n"
  "	//info->line_ = (char*)hoc_Ecalloc(info->linesize_, sizeof(char)); hoc_malchk();\n"
  "	info->np_ = 0;\n"
  "	//info->n_ = 0;\n"
  "	*ip = info;\n"
  "	\n"
  "    //fprintf( stderr, \"The truth now - %x %d\\n\", (int) &(info->np_), info->np_ );\n"
  "    //check for argument containing memory address, set to reference the array\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM {\n"
  "	INFOCAST; Info* info = *ip;\n"
  "	free(info);\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE reveal() { : char* string char* string2\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "    char *helper1 = gargstr(1);\n"
  "    char *helper2 = gargstr(2);\n"
  "    \n"
  "    //fprintf( stderr, \"received %s and %s\\n\", helper1, helper2 );\n"
  "    //fprintf( stderr, \"What are you? %d\\n\", info->np_ );\n"
  "    \n"
  "    double**** access = NULL;\n"
  "\n"
  "    //I want to parse this character string into a hex address.  How do I control whether I get\n"
  "    // a 64 vs a 32 bit value? can I just put it directly into my variable?\n"
  "    \n"
  "    //fprintf(stderr, \"extract the address\\n\" );\n"
  "    sscanf( helper1, \"%x\", &access );\n"
  "    \n"
  "    //if I were to print access now, it should contain the address of neurodamus's object\n"
  "    //if I were to dereference access now, it should contain zero\n"
  "    //fprintf( stderr, \"maintained address? %x\\n\", (int) access );\n"
  "    //fprintf( stderr, \"is it NULL? %x\\n\", (int) *access );\n"
  "    \n"
  "    //now, derefernce access and make it point to the array reference (not the array itself,\n"
  "    // since that will potentially be reallocated as more variables are added)\n"
  "    \n"
  "    //fprintf( stderr, \"dereference and assign address\\n\" );\n"
  "    *access = &(info->ptrs_);\n"
  "    \n"
  "    int **access2;\n"
  "    sscanf( helper2, \"%x\", &access2 );\n"
  "    *access2 = &(info->np_);\n"
  "    \n"
  "    //fill in value to check it\n"
  "    //*(*access2) = 5;\n"
  "    //fprintf(stderr, \"I filled in %d %d %d\\n\", *access2, info->np_, *(*access2) );\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE nothing() { : double* pd\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "	//++info->np_;\n"
  "    fprintf( stderr, \"incremented to %d\\n\", info->np_ );\n"
  "	/* allow 20 chars per double */\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE addvar() { : double* pd\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "	if (info->np_ >= info->psize_) {\n"
  "		info->psize_ *= 2;\n"
  "		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();\n"
  "	}\n"
  "	info->ptrs_[info->np_] = hoc_pgetarg(1);\n"
  "    //fprintf( stderr, \"stored %d into %d (value = %lf)\\n\", info->ptrs_[info->np_], info->ptrs_, *info->ptrs_[info->np_] );\n"
  "	++info->np_;\n"
  "    //fprintf( stderr, \"incremented to %d\\n\", info->np_ );\n"
  "	/* allow 20 chars per double */\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE prdata() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION prstr() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION wopen() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION aopen() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE close() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "\n"
  "static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "ENDVERBATIM\n"
  "\n"
  ;
#endif
