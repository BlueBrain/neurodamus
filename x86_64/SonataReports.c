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
 
#define nrn_init _nrn_init__SonataReport
#define _nrn_initial _nrn_initial__SonataReport
#define nrn_cur _nrn_cur__SonataReport
#define _nrn_current _nrn_current__SonataReport
#define nrn_jacob _nrn_jacob__SonataReport
#define nrn_state _nrn_state__SonataReport
#define _net_receive _net_receive__SonataReport 
 
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
#define tstart _p[1]
#define tstop _p[2]
#define v _p[3]
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
 static double _hoc_AddVar();
 static double _hoc_AddNode();
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
 "AddVar", _hoc_AddVar,
 "AddNode", _hoc_AddNode,
 0, 0
};
#define AddVar AddVar_SonataReport
#define AddNode AddNode_SonataReport
 extern double AddVar( _threadargsproto_ );
 extern double AddNode( _threadargsproto_ );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt", "ms",
 "tstart", "ms",
 "tstop", "ms",
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
"SonataReport",
 "Dt",
 "tstart",
 "tstop",
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
 	tstart = 0;
 	tstop = 0;
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
 static void bbcore_write(double*, int*, int*, int*, _threadargsproto_);
 extern void hoc_reg_bbcore_write(int, void(*)(double*, int*, int*, int*, _threadargsproto_));
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _SonataReports_reg() {
	int _vectorized = 1;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 1,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
   hoc_reg_bbcore_write(_mechtype, bbcore_write);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 4, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 SonataReport /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SonataReports.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
 
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include <stdint.h>
#include <bbp/sonata/reports.h>

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
    char neuronName_[256];
    char rptName_[512];
} Data;

#endif
#endif
 
double AddNode ( _threadargsproto_ ) {
   double _lAddNode;
 
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = *tempdata;
    if(ifarg(1))
    {
        char population_name[256] = "All";
        unsigned long population_offset = 0;
        if (ifarg(2)) {
            sprintf(population_name,"%s", gargstr(2));
        }
        if (ifarg(3)) {
            population_offset = (unsigned long) *getarg(3);
        }
        unsigned long node_id = (unsigned long) *getarg(1);
        sonata_add_node(data->rptName_, population_name, population_offset, node_id);
    }
#endif
#endif
}
 
return _lAddNode;
 }
 
static double _hoc_AddNode(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  AddNode ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double AddVar ( _threadargsproto_ ) {
   double _lAddVar;
 
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = *tempdata;
    if(ifarg(1))
    {
        int element_id = (int)*getarg(2);
        int node_id = (int) *getarg(3);
        double* voltage = hoc_pgetarg(1);
        char population_name[256] = "All";
        if (ifarg(4)) {
            sprintf(population_name,"%s", gargstr(4));
        }
        sonata_add_element(data->rptName_, population_name, node_id, element_id, voltage);
    }
#endif
#endif
}
 
return _lAddVar;
 }
 
static double _hoc_AddVar(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  AddVar ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
/** not executed in coreneuron and hence need empty stubs */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }
 
static void _constructor(Prop* _prop) {
	double* _p; Datum* _ppvar; Datum* _thread;
	_thread = (Datum*)0;
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = 0;
    data = (Data*)hoc_Emalloc(sizeof(Data));
    hoc_malchk();
    if(ifarg(2) && hoc_is_str_arg(2) &&
        ifarg(3) && hoc_is_str_arg(3) &&
        ifarg(4) && ifarg(5) && ifarg(6) &&
        ifarg(7) && hoc_is_str_arg(7)
    )
    {
        sprintf(data->rptName_,"%s/%s",gargstr(3),gargstr(2));
        tstart = *getarg(4);
        tstop = *getarg(5);
        Dt = *getarg(6);

        sonata_create_report(data->rptName_, tstart, tstop, Dt, gargstr(7), gargstr(8));

        *tempdata = data; //makes to data available to other procedures through ptr
    }
    else
    {
        int i = 1;
        while(ifarg(i))
        {
            if(i==1)
                printf("There is an error creating report\n");
            printf("It has arg %d: ", i);
            if(hoc_is_str_arg(i))
                printf("%s\n",gargstr(i));
            else
                printf("%d\n",(int)*getarg(i));
            i++;
        }

    }
#else
        static warning_shown = 0;
        if (ifarg(2) && hoc_is_str_arg(2))
        {
            if (warning_shown == 0)
            {
                printf("WARNING: BinReports Constructor(): Trying to create and write report %s while the NEURODAMUS_DISABLE_REPORTINGLIB is set to ON, ignoring... \n", gargstr(2));
                warning_shown++;
            }
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SonataReports.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "Modified mod file\n"
  "\n"
  "Pointer is an object with Name of the cell, and the report\n"
  "\n"
  "How to use it:\n"
  "Create the object with this information:\n"
  "\n"
  "receive: location,reportname,cellname,path,tstart,tend,dt,sizemapping,kind,sizeatributesmapping\n"
  "one object per cell to report.\n"
  "\n"
  "\n"
  "AddVar(pointer to the variable (as in the older), mapping information)  so much mapping information as in siz\n"
  "\n"
  "\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "        THREADSAFE\n"
  "        POINT_PROCESS SonataReport\n"
  "        BBCOREPOINTER ptr : an object with two strings\n"
  "        RANGE Dt\n"
  "	RANGE tstart\n"
  "	RANGE tstop\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "	Dt = .1 (ms)\n"
  "	tstart = 0 (ms)\n"
  "	tstop  = 0 (ms)\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "	ptr\n"
  "}\n"
  "\n"
  "\n"
  "INITIAL {\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "#include <stdint.h>\n"
  "#include <bbp/sonata/reports.h>\n"
  "\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "\n"
  "typedef struct {\n"
  "    char neuronName_[256];\n"
  "    char rptName_[512];\n"
  "} Data;\n"
  "\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "\n"
  "COMMENT\n"
  "receive: location,reportname,path,tstart,tend,dt,kind\n"
  "ENDCOMMENT\n"
  "CONSTRUCTOR {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    Data** tempdata = (Data**)(&(_p_ptr));\n"
  "    Data* data = 0;\n"
  "    data = (Data*)hoc_Emalloc(sizeof(Data));\n"
  "    hoc_malchk();\n"
  "    if(ifarg(2) && hoc_is_str_arg(2) &&\n"
  "        ifarg(3) && hoc_is_str_arg(3) &&\n"
  "        ifarg(4) && ifarg(5) && ifarg(6) &&\n"
  "        ifarg(7) && hoc_is_str_arg(7)\n"
  "    )\n"
  "    {\n"
  "        sprintf(data->rptName_,\"%s/%s\",gargstr(3),gargstr(2));\n"
  "        tstart = *getarg(4);\n"
  "        tstop = *getarg(5);\n"
  "        Dt = *getarg(6);\n"
  "\n"
  "        sonata_create_report(data->rptName_, tstart, tstop, Dt, gargstr(7), gargstr(8));\n"
  "\n"
  "        *tempdata = data; //makes to data available to other procedures through ptr\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        int i = 1;\n"
  "        while(ifarg(i))\n"
  "        {\n"
  "            if(i==1)\n"
  "                printf(\"There is an error creating report\\n\");\n"
  "            printf(\"It has arg %d: \", i);\n"
  "            if(hoc_is_str_arg(i))\n"
  "                printf(\"%s\\n\",gargstr(i));\n"
  "            else\n"
  "                printf(\"%d\\n\",(int)*getarg(i));\n"
  "            i++;\n"
  "        }\n"
  "\n"
  "    }\n"
  "#else\n"
  "        static warning_shown = 0;\n"
  "        if (ifarg(2) && hoc_is_str_arg(2))\n"
  "        {\n"
  "            if (warning_shown == 0)\n"
  "            {\n"
  "                printf(\"WARNING: BinReports Constructor(): Trying to create and write report %s while the NEURODAMUS_DISABLE_REPORTINGLIB is set to ON, ignoring... \\n\", gargstr(2));\n"
  "                warning_shown++;\n"
  "            }\n"
  "        }\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION AddNode() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    Data** tempdata = (Data**)(&(_p_ptr));\n"
  "    Data* data = *tempdata;\n"
  "    if(ifarg(1))\n"
  "    {\n"
  "        char population_name[256] = \"All\";\n"
  "        unsigned long population_offset = 0;\n"
  "        if (ifarg(2)) {\n"
  "            sprintf(population_name,\"%s\", gargstr(2));\n"
  "        }\n"
  "        if (ifarg(3)) {\n"
  "            population_offset = (unsigned long) *getarg(3);\n"
  "        }\n"
  "        unsigned long node_id = (unsigned long) *getarg(1);\n"
  "        sonata_add_node(data->rptName_, population_name, population_offset, node_id);\n"
  "    }\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "COMMENT\n"
  "/*\n"
  "	AddVariable  with the next data\n"
  "		variable  A pointer to the value of the variable\n"
  "		information about mapping\n"
  "*/\n"
  "ENDCOMMENT\n"
  "FUNCTION AddVar() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "    Data** tempdata = (Data**)(&(_p_ptr));\n"
  "    Data* data = *tempdata;\n"
  "    if(ifarg(1))\n"
  "    {\n"
  "        int element_id = (int)*getarg(2);\n"
  "        int node_id = (int) *getarg(3);\n"
  "        double* voltage = hoc_pgetarg(1);\n"
  "        char population_name[256] = \"All\";\n"
  "        if (ifarg(4)) {\n"
  "            sprintf(population_name,\"%s\", gargstr(4));\n"
  "        }\n"
  "        sonata_add_element(data->rptName_, population_name, node_id, element_id, voltage);\n"
  "    }\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "/** not executed in coreneuron and hence need empty stubs */\n"
  "static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }\n"
  "static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }\n"
  "ENDVERBATIM\n"
  ;
#endif
