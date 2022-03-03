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
 
#define nrn_init _nrn_init__BinReport
#define _nrn_initial _nrn_initial__BinReport
#define nrn_cur _nrn_cur__BinReport
#define _nrn_current _nrn_current__BinReport
#define nrn_jacob _nrn_jacob__BinReport
#define nrn_state _nrn_state__BinReport
#define _net_receive _net_receive__BinReport 
#define TimeStatistics TimeStatistics__BinReport 
 
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
#define ISC _p[3]
#define v _p[4]
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
 static double _hoc_ExtraMapping();
 static double _hoc_TimeStatistics();
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
 "ExtraMapping", _hoc_ExtraMapping,
 "TimeStatistics", _hoc_TimeStatistics,
 0, 0
};
#define AddVar AddVar_BinReport
#define ExtraMapping ExtraMapping_BinReport
 extern double AddVar( _threadargsproto_ );
 extern double ExtraMapping( _threadargsproto_ );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 "Dt", "ms",
 "tstart", "ms",
 "tstop", "ms",
 "ISC", "ms",
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
"BinReport",
 "Dt",
 "tstart",
 "tstop",
 "ISC",
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
 	_p = nrn_prop_data_alloc(_mechtype, 5, _prop);
 	/*initialize range parameters*/
 	Dt = 0.1;
 	tstart = 0;
 	tstop = 0;
 	ISC = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 5;
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

 void _BinReports_reg() {
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
  hoc_register_prop_size(_mechtype, 5, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 BinReport /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/BinReports.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int TimeStatistics(_threadargsproto_);
 
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include "reportinglib/Records.h"
#include "reportinglib/isc/iscAPI.h"

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
//extern double jimsRubbish;

typedef struct {
	char neuronName_[256];
	char rptName_[512];
}Data;

#endif
#endif

 
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
		int *ardata =NULL;
		int size = 1;
		ardata = (int *)hoc_Emalloc(sizeof(int)*size);
		hoc_malchk();
		//printf("Mapping info variable Size=%d\n",size);
		ardata[0]=(int) *getarg(2);
		//printf("records_add_var_with_mapping(data->rptName_=%s, data->neuronName_=%s,hoc_pgetarg(1)=%f,size=%d);",data->rptName_,data->neuronName_,hoc_pgetarg(1),size);
		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);

                if ((int)ISC)
                    isc_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), ardata);
                else
                    records_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), size, ardata);
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
 
double ExtraMapping ( _threadargsproto_ ) {
   double _lExtraMapping;
 
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	Data** tempdata = (Data**)(&(_p_ptr));
	Data* data = *tempdata;
	int *ardata =NULL;
	int i=1;
	while(ifarg(i))
	{
		i++;
	}
	int size = i-1;
	//printf("Adding extra mapping. Size=%d\n",size);
	if(size>0)
	{
		ardata = (int *)hoc_Emalloc(sizeof(int)*size);
		hoc_malchk();
		for(i=0;i<size;i++)
		{
			ardata[i]=(int) *getarg(i+1);
			//printf("Adding %d in position %d\n",ardata[i],i);
		}
		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);
		records_extra_mapping(data->rptName_, numberCell,size,ardata);
	}
#endif
#endif
}
 
return _lExtraMapping;
 }
 
static double _hoc_ExtraMapping(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  ExtraMapping ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
static int  TimeStatistics ( _threadargsproto_ ) {
   
/*VERBATIM*/
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
         if ((int)ISC == 0)
  	     records_time_data();
#endif
#endif
}
  return 0; }
 
static double _hoc_TimeStatistics(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r = 1.;
 TimeStatistics ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
/** not executed in coreneuron and hence need empty stubs */
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
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	Data** tempdata = (Data**)(&(_p_ptr));//???
	Data* data = 0;
	data = (Data*)hoc_Emalloc(sizeof(Data));
	hoc_malchk();
	if(ifarg(2) && hoc_is_str_arg(2) &&
			ifarg(3) && hoc_is_str_arg(3) &&
			ifarg(4) && hoc_is_str_arg(4) &&
			ifarg(5) && ifarg(6) &&
			ifarg(7) && ifarg(8) && ifarg(9) &&
			ifarg(10) &&
			ifarg(11) && hoc_is_str_arg(11) &&
			ifarg(12) &&
			ifarg(13) && hoc_is_str_arg(13)
	)
	{

		sprintf(data->neuronName_,"%s",gargstr(3));
		sprintf(data->rptName_,"%s/%s",gargstr(4),gargstr(2));
		//printf("%s\n",data->neuronName_);
		//printf("%s\n",data->rptName_);
		unsigned long gid,vgid;
		gid = (unsigned long) *getarg(5);
		vgid = (unsigned long) *getarg(6);
		//printf("Gid %d , Vgid %d\n",gid, vgid);

		tstart = *getarg(7);

		tstop = *getarg(8);

		Dt = *getarg(9);

		//printf("nRpsps received %f, nRpsps recorded %f \n",*getarg(14),reportingSteps);
		//printf("tstart %f , tend %f , dt %f\n",_tstart,_tend,_dt);
		int sizemapping,extramapping;
		sizemapping = (int)*getarg(10);
		extramapping = (int)*getarg(12);
		//printf("sizeMapping %d , extramapping %d\n",sizemapping, extramapping);
		//printf("Hasta aqui\n"); //up to here

		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);

                if (ifarg(14) && hoc_is_str_arg(14))
                {
                    ISC = 1.;
		    isc_add_report(data->rptName_, numberCell, gid, vgid, tstart, tstop, Dt, gargstr(13), gargstr(14));
                }
                else
                {
                    ISC = 0.;
                    records_add_report(data->rptName_,numberCell,gid, vgid, tstart,tstop , Dt,sizemapping,gargstr(11),extramapping,gargstr(13));
                }

		//printf("_________________ %s Creating\n",data->rptName_);

		*tempdata = data; //makes to data available to other procedures through ptr
	}
	else
	{
		//printf("There is an error creating report\n");
		int i = 1;
		while(ifarg(i))
		{
			if(i==1) printf("There is an error creating report\n");
			printf("It has arg %d: ", i);
			if(hoc_is_str_arg(i))
				printf("%s\n", gargstr(i));
			else
				printf("%.0lf\n", *getarg(i));
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
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
        if ((int)ISC)
            isc_init_connection();
        else
            records_finish_and_share();
#endif
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/BinReports.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * Modified mod file\n"
  " *\n"
  " * Pointer is an object with Name of the cell, and the report\n"
  " *\n"
  " * How to use it:\n"
  " * Create the object with this information:\n"
  " *\n"
  " * receive: location,reportname,cellname,path,tstart,tend,dt,sizemapping,kind,sizeatributesmapping,iscParam\n"
  " * one object per cell to report.\n"
  " *\n"
  " *\n"
  " * AddVar(pointer to the variable (as in the older), mapping information)  so much mapping information as in siz\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "        THREADSAFE\n"
  "        POINT_PROCESS BinReport\n"
  "        BBCOREPOINTER ptr : an object with two strings\n"
  "        RANGE Dt\n"
  "	RANGE tstart\n"
  "	RANGE tstop\n"
  "        RANGE ISC\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "	Dt = .1 (ms)\n"
  "	tstart = 0 (ms)\n"
  "	tstop  = 0 (ms)\n"
  "        ISC = 0 (ms)\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "	ptr\n"
  "}\n"
  "\n"
  "\n"
  "INITIAL {\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "        if ((int)ISC)\n"
  "            isc_init_connection();\n"
  "        else\n"
  "            records_finish_and_share();\n"
  "#endif\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "#include \"reportinglib/Records.h\"\n"
  "#include \"reportinglib/isc/iscAPI.h\"\n"
  "\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "//extern double jimsRubbish;\n"
  "\n"
  "typedef struct {\n"
  "	char neuronName_[256];\n"
  "	char rptName_[512];\n"
  "}Data;\n"
  "\n"
  "#endif\n"
  "#endif\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "COMMENT\n"
  "\n"
  "receive: location,reportname,cellname,path,gid,vgid,tstart,tend,dt,sizemapping,kind,sizeatributesmapping,iscParam\n"
  "ENDCOMMENT\n"
  "CONSTRUCTOR {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "	Data** tempdata = (Data**)(&(_p_ptr));//???\n"
  "	Data* data = 0;\n"
  "	data = (Data*)hoc_Emalloc(sizeof(Data));\n"
  "	hoc_malchk();\n"
  "	if(ifarg(2) && hoc_is_str_arg(2) &&\n"
  "			ifarg(3) && hoc_is_str_arg(3) &&\n"
  "			ifarg(4) && hoc_is_str_arg(4) &&\n"
  "			ifarg(5) && ifarg(6) &&\n"
  "			ifarg(7) && ifarg(8) && ifarg(9) &&\n"
  "			ifarg(10) &&\n"
  "			ifarg(11) && hoc_is_str_arg(11) &&\n"
  "			ifarg(12) &&\n"
  "			ifarg(13) && hoc_is_str_arg(13)\n"
  "	)\n"
  "	{\n"
  "\n"
  "		sprintf(data->neuronName_,\"%s\",gargstr(3));\n"
  "		sprintf(data->rptName_,\"%s/%s\",gargstr(4),gargstr(2));\n"
  "		//printf(\"%s\\n\",data->neuronName_);\n"
  "		//printf(\"%s\\n\",data->rptName_);\n"
  "		unsigned long gid,vgid;\n"
  "		gid = (unsigned long) *getarg(5);\n"
  "		vgid = (unsigned long) *getarg(6);\n"
  "		//printf(\"Gid %d , Vgid %d\\n\",gid, vgid);\n"
  "\n"
  "		tstart = *getarg(7);\n"
  "\n"
  "		tstop = *getarg(8);\n"
  "\n"
  "		Dt = *getarg(9);\n"
  "\n"
  "		//printf(\"nRpsps received %f, nRpsps recorded %f \\n\",*getarg(14),reportingSteps);\n"
  "		//printf(\"tstart %f , tend %f , dt %f\\n\",_tstart,_tend,_dt);\n"
  "		int sizemapping,extramapping;\n"
  "		sizemapping = (int)*getarg(10);\n"
  "		extramapping = (int)*getarg(12);\n"
  "		//printf(\"sizeMapping %d , extramapping %d\\n\",sizemapping, extramapping);\n"
  "		//printf(\"Hasta aqui\\n\"); //up to here\n"
  "\n"
  "		int numberCell;\n"
  "		sscanf(data->neuronName_,\"a%d\",&numberCell);\n"
  "\n"
  "                if (ifarg(14) && hoc_is_str_arg(14))\n"
  "                {\n"
  "                    ISC = 1.;\n"
  "		    isc_add_report(data->rptName_, numberCell, gid, vgid, tstart, tstop, Dt, gargstr(13), gargstr(14));\n"
  "                }\n"
  "                else\n"
  "                {\n"
  "                    ISC = 0.;\n"
  "                    records_add_report(data->rptName_,numberCell,gid, vgid, tstart,tstop , Dt,sizemapping,gargstr(11),extramapping,gargstr(13));\n"
  "                }\n"
  "\n"
  "		//printf(\"_________________ %s Creating\\n\",data->rptName_);\n"
  "\n"
  "		*tempdata = data; //makes to data available to other procedures through ptr\n"
  "	}\n"
  "	else\n"
  "	{\n"
  "		//printf(\"There is an error creating report\\n\");\n"
  "		int i = 1;\n"
  "		while(ifarg(i))\n"
  "		{\n"
  "			if(i==1) printf(\"There is an error creating report\\n\");\n"
  "			printf(\"It has arg %d: \", i);\n"
  "			if(hoc_is_str_arg(i))\n"
  "				printf(\"%s\\n\", gargstr(i));\n"
  "			else\n"
  "				printf(\"%.0lf\\n\", *getarg(i));\n"
  "			i++;\n"
  "		}\n"
  "\n"
  "	}\n"
  "#else\n"
  "        static warning_shown = 0;\n"
  "        if (ifarg(2) && hoc_is_str_arg(2))\n"
  "        {\n"
  "          if (warning_shown == 0)\n"
  "          {\n"
  "            printf(\"WARNING: BinReports Constructor(): Trying to create and write report %s while the NEURODAMUS_DISABLE_REPORTINGLIB is set to ON, ignoring... \\n\", gargstr(2));\n"
  "            warning_shown++;\n"
  "          }\n"
  "        }\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/*\n"
  "	AddVariable  with the next data\n"
  "		variable  A pointer to the value of the variable\n"
  "		informacion about mapping\n"
  "*/\n"
  "ENDCOMMENT\n"
  "FUNCTION AddVar() {\n"
  "\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "	Data** tempdata = (Data**)(&(_p_ptr));\n"
  "	Data* data = *tempdata;\n"
  "	if(ifarg(1))\n"
  "	{\n"
  "		int *ardata =NULL;\n"
  "		int size = 1;\n"
  "		ardata = (int *)hoc_Emalloc(sizeof(int)*size);\n"
  "		hoc_malchk();\n"
  "		//printf(\"Mapping info variable Size=%d\\n\",size);\n"
  "		ardata[0]=(int) *getarg(2);\n"
  "		//printf(\"records_add_var_with_mapping(data->rptName_=%s, data->neuronName_=%s,hoc_pgetarg(1)=%f,size=%d);\",data->rptName_,data->neuronName_,hoc_pgetarg(1),size);\n"
  "		int numberCell;\n"
  "		sscanf(data->neuronName_,\"a%d\",&numberCell);\n"
  "\n"
  "                if ((int)ISC)\n"
  "                    isc_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), ardata);\n"
  "                else\n"
  "                    records_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), size, ardata);\n"
  "	}\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "COMMENT\n"
  "/*\n"
  "	For extra mapping on graphics, , number of soma, axon, basal, etc\n"
  "	this is need to share with the others to\n"
  "*/\n"
  "ENDCOMMENT\n"
  "FUNCTION ExtraMapping() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "	Data** tempdata = (Data**)(&(_p_ptr));\n"
  "	Data* data = *tempdata;\n"
  "	int *ardata =NULL;\n"
  "	int i=1;\n"
  "	while(ifarg(i))\n"
  "	{\n"
  "		i++;\n"
  "	}\n"
  "	int size = i-1;\n"
  "	//printf(\"Adding extra mapping. Size=%d\\n\",size);\n"
  "	if(size>0)\n"
  "	{\n"
  "		ardata = (int *)hoc_Emalloc(sizeof(int)*size);\n"
  "		hoc_malchk();\n"
  "		for(i=0;i<size;i++)\n"
  "		{\n"
  "			ardata[i]=(int) *getarg(i+1);\n"
  "			//printf(\"Adding %d in position %d\\n\",ardata[i],i);\n"
  "		}\n"
  "		int numberCell;\n"
  "		sscanf(data->neuronName_,\"a%d\",&numberCell);\n"
  "		records_extra_mapping(data->rptName_, numberCell,size,ardata);\n"
  "	}\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "PROCEDURE TimeStatistics() {\n"
  "VERBATIM {\n"
  "#ifndef CORENEURON_BUILD\n"
  "#ifndef DISABLE_REPORTINGLIB\n"
  "         if ((int)ISC == 0)\n"
  "  	     records_time_data();\n"
  "#endif\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "/** not executed in coreneuron and hence need empty stubs */\n"
  "static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "ENDVERBATIM\n"
  ;
#endif
