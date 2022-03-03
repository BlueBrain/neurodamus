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
 
#define nrn_init _nrn_init__CoreConfig
#define _nrn_initial _nrn_initial__CoreConfig
#define nrn_cur _nrn_cur__CoreConfig
#define _nrn_current _nrn_current__CoreConfig
#define nrn_jacob _nrn_jacob__CoreConfig
#define nrn_state _nrn_state__CoreConfig
#define _net_receive _net_receive__CoreConfig 
#define psolve_core psolve_core__CoreConfig 
#define write_spike_population write_spike_population__CoreConfig 
#define write_population_count write_population_count__CoreConfig 
#define write_report_count write_report_count__CoreConfig 
#define write_sim_config write_sim_config__CoreConfig 
#define write_report_config write_report_config__CoreConfig 
 
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
#define _tsav _p[1]
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
 static double _hoc_psolve_core();
 static double _hoc_write_spike_population();
 static double _hoc_write_population_count();
 static double _hoc_write_report_count();
 static double _hoc_write_sim_config();
 static double _hoc_write_report_config();
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
 "psolve_core", _hoc_psolve_core,
 "write_spike_population", _hoc_write_spike_population,
 "write_population_count", _hoc_write_population_count,
 "write_report_count", _hoc_write_report_count,
 "write_sim_config", _hoc_write_sim_config,
 "write_report_config", _hoc_write_report_config,
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
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"CoreConfig",
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
 	_p = nrn_prop_data_alloc(_mechtype, 2, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 2;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 2, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _CoreConfig_reg() {
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
  hoc_register_prop_size(_mechtype, 2, 2);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
 add_nrn_artcell(_mechtype, 0);
 add_nrn_has_net_event(_mechtype);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 CoreConfig /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/CoreConfig.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int psolve_core(_threadargsproto_);
static int write_spike_population(_threadargsproto_);
static int write_population_count(_threadargsproto_);
static int write_report_count(_threadargsproto_);
static int write_sim_config(_threadargsproto_);
static int write_report_config(_threadargsproto_);
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t; {
   if ( 0.0 ) {
     net_event ( _pnt, t ) ;
     }
   } }
 
/*VERBATIM*/
#include <stdio.h>
#include <stdlib.h>
#include <alloca.h>
#include <string.h>
#include <limits.h>

#if defined(ENABLE_CORENEURON)
#include <coreneuron/engine.h>

#if defined(CORENEURON_VERSION) && (CORENEURON_VERSION >= 18)
# define CORENRN_CLI11 1
# define CORENRN_ARG_FMT "%s="
#else
# define CORENRN_CLI11 0
# define CORENRN_ARG_FMT "--%s "
#endif

#else   // not ENABLE_CORENEURON

#define CORENRN_CLI11 1
#define CORENRN_ARG_FMT "%s="

#endif  // defined(ENABLE_CORENEURON)

extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();
extern int nrnmpi_myid;
extern int hoc_is_str_arg(int iarg);
extern double* hoc_val_pointer(const char*);
extern double celsius;

// name of config files
#define CONFIG_FILENAME_TOTAL_LEN_MAX 32  // Include margin for extra / and \0
static const char* const SIM_CONFIG_FILE = "sim.conf";
static const char* const REPORT_CONFIG_FILE = "report.conf";
static const int DEFAULT_CELL_PERMUTE = 0;
static char* outputdir = NULL;



// helper function to open file and error checking
FILE* open_file(const char *filename, const char *mode) {
    FILE *fp = fopen(filename, mode);
    if(!fp) {
        printf("Error while opening file %s\n", filename);
        abort();
    }
    return fp;
}


/// Builds an absolute path from a relative path
/// doesnt require intermediate dirs to exist
static char* abspath(const char* pth, char* dstmem) {
    if(!pth || !strlen(pth)) { return NULL; }
    if(pth[0] == '/') {  // already absolute
        strcpy(dstmem, pth);
    } else {
        if (!realpath(".", dstmem)) { fprintf(stderr, "Error in abspath. Buffer?\n"); abort(); }
        if(strcmp(pth, ".") != 0) {
            sprintf(dstmem + strlen(dstmem), "/%s", pth);
        }
    }
    return dstmem;
}


 
static int  write_report_config ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    // gids to be reported is double vector
    double *gid_vec = vector_vec(vector_arg(11));
    int num_gids = vector_capacity(vector_arg(11));

    // Default buffer size
    int buffer_size = 8;
    if (ifarg(12) && !hoc_is_str_arg(12)) {
        buffer_size = (int)*getarg(12); 
    }

    // Default population name
    char population_name[256] = "All";
    if (ifarg(13)) {
        sprintf(population_name,"%s", hoc_gargstr(13));
    }

    // Default population offset
    int population_offset = 0;
    if (ifarg(14) && !hoc_is_str_arg(14)) {
        population_offset = (int)*getarg(14);
    }

    // copy doible gids to int array
    int *gids = (int*) calloc(num_gids, sizeof(int));
    int i;
    for(i = 0; i < num_gids; i++) {
        gids[i] = (int)gid_vec[i];
    }

    printf("Adding report %s for CoreNEURON with %d gids\n", hoc_gargstr(1), num_gids);
    char* reportConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(reportConf, "%s/%s", outputdir, REPORT_CONFIG_FILE);

    // write report information
    FILE *fp = open_file(reportConf, "a");
    fprintf(fp, "%s %s %s %s %s %s %d %lf %lf %lf %d %d %s %d\n",
            hoc_gargstr(1),
            hoc_gargstr(2),
            hoc_gargstr(3),
            hoc_gargstr(4),
            hoc_gargstr(5),
            hoc_gargstr(6),
            (int)*getarg(7),
            *getarg(8),
            *getarg(9),
            *getarg(10),
            num_gids,
            buffer_size,
            population_name,
            population_offset);
    fwrite(gids, sizeof(int), num_gids, fp);
    fprintf(fp, "%s", "\n");
    fclose(fp);
#endif
  return 0; }
 
static double _hoc_write_report_config(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_report_config ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_sim_config ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char tmpmem[PATH_MAX];
    snprintf(tmpmem, PATH_MAX, "%s/%s", outputdir, SIM_CONFIG_FILE);
    printf("Writing sim config file: %s\n", tmpmem);

    FILE *fp = open_file(tmpmem, "w");
    fprintf(fp, CORENRN_ARG_FMT"'%s'\n", "outpath", abspath(hoc_gargstr(1), tmpmem));
    fprintf(fp, CORENRN_ARG_FMT"'%s'\n", "datpath", abspath(hoc_gargstr(2), tmpmem));
    fprintf(fp, CORENRN_ARG_FMT"%lf\n",  "tstop", *getarg(3));
    fprintf(fp, CORENRN_ARG_FMT"%lf\n",  "dt", *getarg(4));
    fprintf(fp, CORENRN_ARG_FMT"%lf\n",  "forwardskip", *getarg(5));
    fprintf(fp, CORENRN_ARG_FMT"%d\n",   "prcellgid", (int)*getarg(6));
    fprintf(fp, CORENRN_ARG_FMT"%lf\n",  "celsius", celsius);
    fprintf(fp, CORENRN_ARG_FMT"%lf\n",  "voltage", *hoc_val_pointer("v_init"));
    fprintf(fp, CORENRN_ARG_FMT"'%s/%s'\n", "report-conf",  outputdir, REPORT_CONFIG_FILE);
    fprintf(fp, CORENRN_ARG_FMT"%d\n", "cell-permute", DEFAULT_CELL_PERMUTE);
    if (ifarg(7) && strlen(hoc_gargstr(7))) {  // if spike replay specified
        fprintf(fp, CORENRN_ARG_FMT"'%s'\n", "pattern", abspath(hoc_gargstr(7), tmpmem));
    }
    if (ifarg(8)) {  // if seed specified
        fprintf(fp, CORENRN_ARG_FMT"%d\n", "seed", (int)*getarg(8));
    }
# if CORENRN_CLI11
    fprintf(fp, "mpi=true\n");
# else
    fprintf(fp, "-mpi\n");
# endif

    fclose(fp);
#endif
  return 0; }
 
static double _hoc_write_sim_config(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_sim_config ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_report_count ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(filename, "%s/%s", outputdir, REPORT_CONFIG_FILE);
    FILE *fp = open_file(filename, "w");
    fprintf(fp, "%d\n", (int)*getarg(1));
    fclose(fp);
#endif
  return 0; }
 
static double _hoc_write_report_count(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_report_count ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_population_count ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(filename, "%s/%s", outputdir, REPORT_CONFIG_FILE);
    FILE *fp = open_file(filename, "a");
    fprintf(fp, "%d\n", (int)*getarg(1));
    fclose(fp);
#endif
  return 0; }
 
static double _hoc_write_population_count(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_population_count ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  write_spike_population ( _threadargsproto_ ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(filename, "%s/%s", outputdir, REPORT_CONFIG_FILE);
    FILE *fp = open_file(filename, "a");
    fprintf(fp, "%s", hoc_gargstr(1));
    if (ifarg(2)) {
        fprintf(fp, " %d", (int)*getarg(2));
    }
    fprintf(fp, "\n");
    fclose(fp);
#endif
  return 0; }
 
static double _hoc_write_spike_population(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 write_spike_population ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  psolve_core ( _threadargsproto_ ) {
   
/*VERBATIM*/
#if defined(ENABLE_CORENEURON)
    char* simConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(simConf, "%s/%s", outputdir, SIM_CONFIG_FILE);
# if CORENRN_CLI11
    char *argv[] = {"", "--read-config", simConf, "--skip-mpi-finalize", "--mpi", NULL, NULL, NULL, NULL};
# else
    char *argv[] = {"", "--read-config", simConf, "--skip-mpi-finalize", "-mpi", NULL, NULL, NULL, NULL};
# endif
    int argc = 5;
    int argIndex=1;
    while( ifarg(argIndex) ) {
        argv[argc++] = strdup( hoc_gargstr(argIndex++) );
    }
    solve_core(argc, argv);
#else
    if(nrnmpi_myid == 0) {
        fprintf(stderr, "%s", "ERROR : CoreNEURON library not linked with NEURODAMUS!\n");
    }
#endif
  return 0; }
 
static double _hoc_psolve_core(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 psolve_core ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
    if(ifarg(1)) {
        if(outputdir) free(outputdir);
        outputdir = realpath(hoc_gargstr(1), NULL);  // Always created before
    } // else: do nothing. Avoid that random instantiations
      // (e.g. from BBSaveState) overwrite the static outputdir
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/CoreConfig.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file CoreConfig.mod\n"
  " * @brief Interface to write simulation configuration for CoreNEURON\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    THREADSAFE\n"
  "    ARTIFICIAL_CELL CoreConfig\n"
  "}\n"
  "\n"
  "NET_RECEIVE (w) {\n"
  "    : net_event is required for neuron code generation and hence false if block\n"
  "    if (0) {\n"
  "        net_event(t)\n"
  "    }\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#include <stdio.h>\n"
  "#include <stdlib.h>\n"
  "#include <alloca.h>\n"
  "#include <string.h>\n"
  "#include <limits.h>\n"
  "\n"
  "#if defined(ENABLE_CORENEURON)\n"
  "#include <coreneuron/engine.h>\n"
  "\n"
  "#if defined(CORENEURON_VERSION) && (CORENEURON_VERSION >= 18)\n"
  "# define CORENRN_CLI11 1\n"
  "# define CORENRN_ARG_FMT \"%s=\"\n"
  "#else\n"
  "# define CORENRN_CLI11 0\n"
  "# define CORENRN_ARG_FMT \"--%s \"\n"
  "#endif\n"
  "\n"
  "#else   // not ENABLE_CORENEURON\n"
  "\n"
  "#define CORENRN_CLI11 1\n"
  "#define CORENRN_ARG_FMT \"%s=\"\n"
  "\n"
  "#endif  // defined(ENABLE_CORENEURON)\n"
  "\n"
  "extern double* vector_vec();\n"
  "extern int vector_capacity();\n"
  "extern void* vector_arg();\n"
  "extern int nrnmpi_myid;\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern double* hoc_val_pointer(const char*);\n"
  "extern double celsius;\n"
  "\n"
  "// name of config files\n"
  "#define CONFIG_FILENAME_TOTAL_LEN_MAX 32  // Include margin for extra / and \\0\n"
  "static const char* const SIM_CONFIG_FILE = \"sim.conf\";\n"
  "static const char* const REPORT_CONFIG_FILE = \"report.conf\";\n"
  "static const int DEFAULT_CELL_PERMUTE = 0;\n"
  "static char* outputdir = NULL;\n"
  "\n"
  "\n"
  "\n"
  "// helper function to open file and error checking\n"
  "FILE* open_file(const char *filename, const char *mode) {\n"
  "    FILE *fp = fopen(filename, mode);\n"
  "    if(!fp) {\n"
  "        printf(\"Error while opening file %s\\n\", filename);\n"
  "        abort();\n"
  "    }\n"
  "    return fp;\n"
  "}\n"
  "\n"
  "\n"
  "/// Builds an absolute path from a relative path\n"
  "/// doesnt require intermediate dirs to exist\n"
  "static char* abspath(const char* pth, char* dstmem) {\n"
  "    if(!pth || !strlen(pth)) { return NULL; }\n"
  "    if(pth[0] == '/') {  // already absolute\n"
  "        strcpy(dstmem, pth);\n"
  "    } else {\n"
  "        if (!realpath(\".\", dstmem)) { fprintf(stderr, \"Error in abspath. Buffer?\\n\"); abort(); }\n"
  "        if(strcmp(pth, \".\") != 0) {\n"
  "            sprintf(dstmem + strlen(dstmem), \"/%s\", pth);\n"
  "        }\n"
  "    }\n"
  "    return dstmem;\n"
  "}\n"
  "\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "://///////////////////////////////////////////////////////////\n"
  ":// Model functions\n"
  "://///////////////////////////////////////////////////////////\n"
  "\n"
  "CONSTRUCTOR  { : string outputdir\n"
  "VERBATIM\n"
  "    if(ifarg(1)) {\n"
  "        if(outputdir) free(outputdir);\n"
  "        outputdir = realpath(hoc_gargstr(1), NULL);  // Always created before\n"
  "    } // else: do nothing. Avoid that random instantiations\n"
  "      // (e.g. from BBSaveState) overwrite the static outputdir\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  ": write report defined in BlueConfig\n"
  "PROCEDURE write_report_config() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    if(nrnmpi_myid > 0) {\n"
  "        return 0;\n"
  "    }\n"
  "    // gids to be reported is double vector\n"
  "    double *gid_vec = vector_vec(vector_arg(11));\n"
  "    int num_gids = vector_capacity(vector_arg(11));\n"
  "\n"
  "    // Default buffer size\n"
  "    int buffer_size = 8;\n"
  "    if (ifarg(12) && !hoc_is_str_arg(12)) {\n"
  "        buffer_size = (int)*getarg(12); \n"
  "    }\n"
  "\n"
  "    // Default population name\n"
  "    char population_name[256] = \"All\";\n"
  "    if (ifarg(13)) {\n"
  "        sprintf(population_name,\"%s\", hoc_gargstr(13));\n"
  "    }\n"
  "\n"
  "    // Default population offset\n"
  "    int population_offset = 0;\n"
  "    if (ifarg(14) && !hoc_is_str_arg(14)) {\n"
  "        population_offset = (int)*getarg(14);\n"
  "    }\n"
  "\n"
  "    // copy doible gids to int array\n"
  "    int *gids = (int*) calloc(num_gids, sizeof(int));\n"
  "    int i;\n"
  "    for(i = 0; i < num_gids; i++) {\n"
  "        gids[i] = (int)gid_vec[i];\n"
  "    }\n"
  "\n"
  "    printf(\"Adding report %s for CoreNEURON with %d gids\\n\", hoc_gargstr(1), num_gids);\n"
  "    char* reportConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);\n"
  "    sprintf(reportConf, \"%s/%s\", outputdir, REPORT_CONFIG_FILE);\n"
  "\n"
  "    // write report information\n"
  "    FILE *fp = open_file(reportConf, \"a\");\n"
  "    fprintf(fp, \"%s %s %s %s %s %s %d %lf %lf %lf %d %d %s %d\\n\",\n"
  "            hoc_gargstr(1),\n"
  "            hoc_gargstr(2),\n"
  "            hoc_gargstr(3),\n"
  "            hoc_gargstr(4),\n"
  "            hoc_gargstr(5),\n"
  "            hoc_gargstr(6),\n"
  "            (int)*getarg(7),\n"
  "            *getarg(8),\n"
  "            *getarg(9),\n"
  "            *getarg(10),\n"
  "            num_gids,\n"
  "            buffer_size,\n"
  "            population_name,\n"
  "            population_offset);\n"
  "    fwrite(gids, sizeof(int), num_gids, fp);\n"
  "    fprintf(fp, \"%s\", \"\\n\");\n"
  "    fclose(fp);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  ": Write basic sim settings from Run block of BlueConfig\n"
  "PROCEDURE write_sim_config() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    if(nrnmpi_myid > 0) {\n"
  "        return 0;\n"
  "    }\n"
  "    char tmpmem[PATH_MAX];\n"
  "    snprintf(tmpmem, PATH_MAX, \"%s/%s\", outputdir, SIM_CONFIG_FILE);\n"
  "    printf(\"Writing sim config file: %s\\n\", tmpmem);\n"
  "\n"
  "    FILE *fp = open_file(tmpmem, \"w\");\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"'%s'\\n\", \"outpath\", abspath(hoc_gargstr(1), tmpmem));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"'%s'\\n\", \"datpath\", abspath(hoc_gargstr(2), tmpmem));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%lf\\n\",  \"tstop\", *getarg(3));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%lf\\n\",  \"dt\", *getarg(4));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%lf\\n\",  \"forwardskip\", *getarg(5));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%d\\n\",   \"prcellgid\", (int)*getarg(6));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%lf\\n\",  \"celsius\", celsius);\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%lf\\n\",  \"voltage\", *hoc_val_pointer(\"v_init\"));\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"'%s/%s'\\n\", \"report-conf\",  outputdir, REPORT_CONFIG_FILE);\n"
  "    fprintf(fp, CORENRN_ARG_FMT\"%d\\n\", \"cell-permute\", DEFAULT_CELL_PERMUTE);\n"
  "    if (ifarg(7) && strlen(hoc_gargstr(7))) {  // if spike replay specified\n"
  "        fprintf(fp, CORENRN_ARG_FMT\"'%s'\\n\", \"pattern\", abspath(hoc_gargstr(7), tmpmem));\n"
  "    }\n"
  "    if (ifarg(8)) {  // if seed specified\n"
  "        fprintf(fp, CORENRN_ARG_FMT\"%d\\n\", \"seed\", (int)*getarg(8));\n"
  "    }\n"
  "# if CORENRN_CLI11\n"
  "    fprintf(fp, \"mpi=true\\n\");\n"
  "# else\n"
  "    fprintf(fp, \"-mpi\\n\");\n"
  "# endif\n"
  "\n"
  "    fclose(fp);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  ": Write report count as first line\n"
  "PROCEDURE write_report_count() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    if(nrnmpi_myid > 0) {\n"
  "        return 0;\n"
  "    }\n"
  "    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);\n"
  "    sprintf(filename, \"%s/%s\", outputdir, REPORT_CONFIG_FILE);\n"
  "    FILE *fp = open_file(filename, \"w\");\n"
  "    fprintf(fp, \"%d\\n\", (int)*getarg(1));\n"
  "    fclose(fp);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ": Write population count as first line\n"
  "PROCEDURE write_population_count() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    if(nrnmpi_myid > 0) {\n"
  "        return 0;\n"
  "    }\n"
  "    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);\n"
  "    sprintf(filename, \"%s/%s\", outputdir, REPORT_CONFIG_FILE);\n"
  "    FILE *fp = open_file(filename, \"a\");\n"
  "    fprintf(fp, \"%d\\n\", (int)*getarg(1));\n"
  "    fclose(fp);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ": Write spike population name and gid offset\n"
  "PROCEDURE write_spike_population() {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "    if(nrnmpi_myid > 0) {\n"
  "        return 0;\n"
  "    }\n"
  "    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);\n"
  "    sprintf(filename, \"%s/%s\", outputdir, REPORT_CONFIG_FILE);\n"
  "    FILE *fp = open_file(filename, \"a\");\n"
  "    fprintf(fp, \"%s\", hoc_gargstr(1));\n"
  "    if (ifarg(2)) {\n"
  "        fprintf(fp, \" %d\", (int)*getarg(2));\n"
  "    }\n"
  "    fprintf(fp, \"\\n\");\n"
  "    fclose(fp);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE psolve_core() {\n"
  "VERBATIM\n"
  "#if defined(ENABLE_CORENEURON)\n"
  "    char* simConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);\n"
  "    sprintf(simConf, \"%s/%s\", outputdir, SIM_CONFIG_FILE);\n"
  "# if CORENRN_CLI11\n"
  "    char *argv[] = {\"\", \"--read-config\", simConf, \"--skip-mpi-finalize\", \"--mpi\", NULL, NULL, NULL, NULL};\n"
  "# else\n"
  "    char *argv[] = {\"\", \"--read-config\", simConf, \"--skip-mpi-finalize\", \"-mpi\", NULL, NULL, NULL, NULL};\n"
  "# endif\n"
  "    int argc = 5;\n"
  "    int argIndex=1;\n"
  "    while( ifarg(argIndex) ) {\n"
  "        argv[argc++] = strdup( hoc_gargstr(argIndex++) );\n"
  "    }\n"
  "    solve_core(argc, argv);\n"
  "#else\n"
  "    if(nrnmpi_myid == 0) {\n"
  "        fprintf(stderr, \"%s\", \"ERROR : CoreNEURON library not linked with NEURODAMUS!\\n\");\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  ;
#endif
