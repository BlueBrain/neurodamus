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
 
#define nrn_init _nrn_init__MemUsage
#define _nrn_initial _nrn_initial__MemUsage
#define nrn_cur _nrn_cur__MemUsage
#define _nrn_current _nrn_current__MemUsage
#define nrn_jacob _nrn_jacob__MemUsage
#define nrn_state _nrn_state__MemUsage
#define _net_receive _net_receive__MemUsage 
#define print_node_mem_usage print_node_mem_usage__MemUsage 
#define print_mem_usage print_mem_usage__MemUsage 
 
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
 static double _hoc_print_node_mem_usage();
 static double _hoc_print_mem_usage();
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
 "print_node_mem_usage", _hoc_print_node_mem_usage,
 "print_mem_usage", _hoc_print_mem_usage,
 0, 0
};
 /* declare global and static user variables */
#define avgUsageMB avgUsageMB_MemUsage
 double avgUsageMB = 0;
#define maxUsageMB maxUsageMB_MemUsage
 double maxUsageMB = 0;
#define minUsageMB minUsageMB_MemUsage
 double minUsageMB = 0;
#define rank rank_MemUsage
 double rank = 0;
#define size size_MemUsage
 double size = 0;
#define stdevUsageMB stdevUsageMB_MemUsage
 double stdevUsageMB = 0;
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 0,0
};
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 "minUsageMB_MemUsage", &minUsageMB_MemUsage,
 "maxUsageMB_MemUsage", &maxUsageMB_MemUsage,
 "avgUsageMB_MemUsage", &avgUsageMB_MemUsage,
 "stdevUsageMB_MemUsage", &stdevUsageMB_MemUsage,
 "rank_MemUsage", &rank_MemUsage,
 "size_MemUsage", &size_MemUsage,
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
"MemUsage",
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
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _MemUsage_reg() {
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
 	ivoc_help("help ?1 MemUsage /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/MemUsage.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int print_node_mem_usage(_threadargsproto_);
static int print_mem_usage(_threadargsproto_);
 
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#include <unistd.h>
#ifndef DISABLE_MPI
#include <mpi.h>
#endif
#endif
int nrn_mallinfo(int);
 
static int  print_mem_usage ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
/**
 * Gather memory usage statistics for all nodes in the network, printing to the console
 *
 * Use by default the VmRSS of /proc/self/statm to report the memory usage of Neurodamus
 * VmRSS: Resident set size.  Note that the value here is the sum of RssAnon, RssFile, and RssShmem.
 * RssAnon: Size of resident anonymous memory.  (since Linux 4.5).
 * RssFile: Size of resident file mappings.  (since Linux 4.5).
 * RssShmem: Size of resident shared memory (includes System V shared memory, mappings from tmpfs(5),
 * and shared anonymous mappings).  (since Linux 4.5)
 * Based on VmRSS we calculate all the memory of the Neurodamus process which resides on the main memory.
 * The size might not be decreasing because of the page not being released by the system even after a
 * deallocation of memory.
 * This is the same way that memory is reported in CoreNEURON.
 * In case /proc/self/statm cannot be opened, fall back to the old memory reporting with mallinfo.
 * argument 6 to nrn_mallinfo includes memory mapped files (m.hblkhd + m.arena)
 * argument 1 to nrn_mallinfo returns uordblks which is "total size of memory occupied by chunks handed out by malloc"
 */
    FILE *file;
    file = fopen("/proc/self/statm", "r");
    double usageMB;
    if (file != NULL) {
        unsigned long long int data_size;
        fscanf(file, "%llu %llu", &data_size, &data_size);
        fclose(file);
        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);
    } else {
        usageMB = (double) nrn_mallinfo(1) / (double) (1024*1024);
    }
#ifndef DISABLE_MPI
    MPI_Reduce( &usageMB, &minUsageMB, 1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD );
    MPI_Reduce( &usageMB, &maxUsageMB, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD );
    MPI_Reduce( &usageMB, &avgUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );

    avgUsageMB /= size;

    MPI_Bcast( &avgUsageMB, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD );

    double diffSquared = (usageMB-avgUsageMB)*(usageMB-avgUsageMB);
    MPI_Reduce( &diffSquared, &stdevUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );
    stdevUsageMB = sqrt( stdevUsageMB/size);

    if( rank == 0 ) {
        printf( "\e[90m[DEBUG] Memusage [MB]: Max=%.2lf, Min=%.2lf, Mean(Stdev)=%.2lf(%.2lf)\e[39m\n",\
                maxUsageMB, minUsageMB, avgUsageMB, stdevUsageMB );
    }
#else
    printf( "\e[90m[DEBUG] Memusage [MB]: %.2lf \e[39m\n", usageMB );
#endif

#endif
  return 0; }
 
static double _hoc_print_mem_usage(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 print_mem_usage ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  print_node_mem_usage ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    FILE *file;
    file = fopen("/proc/self/statm", "r");
    double usageMB;
    if (file != NULL) {
        unsigned long long int data_size;
        fscanf(file, "%llu %llu", &data_size, &data_size);
        fclose(file);
        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);
    } else {
        usageMB = (double) nrn_mallinfo(6) / (double) (1024*1024);
    }
    printf( "\e[90m[DEBUG] Node: %.0lf Memusage [MB]: %.2lf \e[39m\n", rank, usageMB );
#endif
  return 0; }
 
static double _hoc_print_node_mem_usage(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 print_node_mem_usage ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
    int i_rank=0, i_size=1;
#ifndef DISABLE_MPI
    MPI_Comm_size(MPI_COMM_WORLD, &i_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &i_rank);
#endif
    rank = i_rank;
    size = i_size;
 }
 
}
}

static void initmodel(double* _p, Datum* _ppvar, Datum* _thread, _NrnThread* _nt) {
  int _i; double _save;{
 {
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/MemUsage.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file MemUsage.mod\n"
  " * @brief\n"
  " * @author king\n"
  " * @date 2011-02-04\n"
  " * @remark Copyright \n"
  "\n"
  " BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    THREADSAFE\n"
  "    ARTIFICIAL_CELL MemUsage\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#include <unistd.h>\n"
  "#ifndef DISABLE_MPI\n"
  "#include <mpi.h>\n"
  "#endif\n"
  "#endif\n"
  "int nrn_mallinfo(int);\n"
  "ENDVERBATIM\n"
  "\n"
  "PARAMETER {\n"
  "    minUsageMB = 0\n"
  "    maxUsageMB = 0\n"
  "    avgUsageMB = 0\n"
  "    stdevUsageMB = 0\n"
  "    rank = 0\n"
  "    size = 0\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "}\n"
  "\n"
  "CONSTRUCTOR  {\n"
  "VERBATIM\n"
  "    int i_rank=0, i_size=1;\n"
  "#ifndef DISABLE_MPI\n"
  "    MPI_Comm_size(MPI_COMM_WORLD, &i_size);\n"
  "    MPI_Comm_rank(MPI_COMM_WORLD, &i_rank);\n"
  "#endif\n"
  "    rank = i_rank;\n"
  "    size = i_size;\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE print_mem_usage() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "/**\n"
  " * Gather memory usage statistics for all nodes in the network, printing to the console\n"
  " *\n"
  " * Use by default the VmRSS of /proc/self/statm to report the memory usage of Neurodamus\n"
  " * VmRSS: Resident set size.  Note that the value here is the sum of RssAnon, RssFile, and RssShmem.\n"
  " * RssAnon: Size of resident anonymous memory.  (since Linux 4.5).\n"
  " * RssFile: Size of resident file mappings.  (since Linux 4.5).\n"
  " * RssShmem: Size of resident shared memory (includes System V shared memory, mappings from tmpfs(5),\n"
  " * and shared anonymous mappings).  (since Linux 4.5)\n"
  " * Based on VmRSS we calculate all the memory of the Neurodamus process which resides on the main memory.\n"
  " * The size might not be decreasing because of the page not being released by the system even after a\n"
  " * deallocation of memory.\n"
  " * This is the same way that memory is reported in CoreNEURON.\n"
  " * In case /proc/self/statm cannot be opened, fall back to the old memory reporting with mallinfo.\n"
  " * argument 6 to nrn_mallinfo includes memory mapped files (m.hblkhd + m.arena)\n"
  " * argument 1 to nrn_mallinfo returns uordblks which is \"total size of memory occupied by chunks handed out by malloc\"\n"
  " */\n"
  "    FILE *file;\n"
  "    file = fopen(\"/proc/self/statm\", \"r\");\n"
  "    double usageMB;\n"
  "    if (file != NULL) {\n"
  "        unsigned long long int data_size;\n"
  "        fscanf(file, \"%llu %llu\", &data_size, &data_size);\n"
  "        fclose(file);\n"
  "        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);\n"
  "    } else {\n"
  "        usageMB = (double) nrn_mallinfo(1) / (double) (1024*1024);\n"
  "    }\n"
  "#ifndef DISABLE_MPI\n"
  "    MPI_Reduce( &usageMB, &minUsageMB, 1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD );\n"
  "    MPI_Reduce( &usageMB, &maxUsageMB, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD );\n"
  "    MPI_Reduce( &usageMB, &avgUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );\n"
  "\n"
  "    avgUsageMB /= size;\n"
  "\n"
  "    MPI_Bcast( &avgUsageMB, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD );\n"
  "\n"
  "    double diffSquared = (usageMB-avgUsageMB)*(usageMB-avgUsageMB);\n"
  "    MPI_Reduce( &diffSquared, &stdevUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );\n"
  "    stdevUsageMB = sqrt( stdevUsageMB/size);\n"
  "\n"
  "    if( rank == 0 ) {\n"
  "        printf( \"\\e[90m[DEBUG] Memusage [MB]: Max=%.2lf, Min=%.2lf, Mean(Stdev)=%.2lf(%.2lf)\\e[39m\\n\",\\\n"
  "                maxUsageMB, minUsageMB, avgUsageMB, stdevUsageMB );\n"
  "    }\n"
  "#else\n"
  "    printf( \"\\e[90m[DEBUG] Memusage [MB]: %.2lf \\e[39m\\n\", usageMB );\n"
  "#endif\n"
  "\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE print_node_mem_usage() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    FILE *file;\n"
  "    file = fopen(\"/proc/self/statm\", \"r\");\n"
  "    double usageMB;\n"
  "    if (file != NULL) {\n"
  "        unsigned long long int data_size;\n"
  "        fscanf(file, \"%llu %llu\", &data_size, &data_size);\n"
  "        fclose(file);\n"
  "        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);\n"
  "    } else {\n"
  "        usageMB = (double) nrn_mallinfo(6) / (double) (1024*1024);\n"
  "    }\n"
  "    printf( \"\\e[90m[DEBUG] Node: %.0lf Memusage [MB]: %.2lf \\e[39m\\n\", rank, usageMB );\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  ;
#endif
