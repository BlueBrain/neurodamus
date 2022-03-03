/* Created by Language version: 7.7.0 */
/* NOT VECTORIZED */
#define NRN_VECTORIZED 0
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
 
#define nrn_init _nrn_init__ASCIIRecord
#define _nrn_initial _nrn_initial__ASCIIRecord
#define nrn_cur _nrn_cur__ASCIIRecord
#define _nrn_current _nrn_current__ASCIIRecord
#define nrn_jacob _nrn_jacob__ASCIIRecord
#define nrn_state _nrn_state__ASCIIRecord
#define _net_receive _net_receive__ASCIIRecord 
#define addmapping addmapping__ASCIIRecord 
#define addvar addvar__ASCIIRecord 
#define consolidateTiming consolidateTiming__ASCIIRecord 
#define restartEvent restartEvent__ASCIIRecord 
#define recdata recdata__ASCIIRecord 
#define writeMeta writeMeta__ASCIIRecord 
 
#define _threadargscomma_ /**/
#define _threadargsprotocomma_ /**/
#define _threadargs_ /**/
#define _threadargsproto_ /**/
 	/*SUPPRESS 761*/
	/*SUPPRESS 762*/
	/*SUPPRESS 763*/
	/*SUPPRESS 765*/
	 extern double *getarg();
 static double *_p; static Datum *_ppvar;
 
#define t nrn_threads->_t
#define dt nrn_threads->_dt
#define rank _p[0]
#define Dt _p[1]
#define tstart _p[2]
#define tstop _p[3]
#define rpts _p[4]
#define _tsav _p[5]
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
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_addmapping();
 static double _hoc_addvar();
 static double _hoc_consolidateTiming();
 static double _hoc_newMapping();
 static double _hoc_newReport();
 static double _hoc_restartEvent();
 static double _hoc_recdata();
 static double _hoc_writeMeta();
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
 _p = _prop->param; _ppvar = _prop->dparam;
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
 "addmapping", _hoc_addmapping,
 "addvar", _hoc_addvar,
 "consolidateTiming", _hoc_consolidateTiming,
 "newMapping", _hoc_newMapping,
 "newReport", _hoc_newReport,
 "restartEvent", _hoc_restartEvent,
 "recdata", _hoc_recdata,
 "writeMeta", _hoc_writeMeta,
 0, 0
};
#define newMapping newMapping_ASCIIRecord
#define newReport newReport_ASCIIRecord
 extern double newMapping( );
 extern double newReport( );
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
 static double v = 0;
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
"ASCIIRecord",
 "rank",
 "Dt",
 "tstart",
 "tstop",
 "rpts",
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
 	_p = nrn_prop_data_alloc(_mechtype, 6, _prop);
 	/*initialize range parameters*/
 	rank = 0;
 	Dt = 0.1;
 	tstart = 0;
 	tstop = 0;
 	rpts = 0;
  }
 	_prop->param = _p;
 	_prop->param_size = 6;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 4, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 
#define _tqitem &(_ppvar[3]._pvoid)
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _ASCIIrecord_reg() {
	int _vectorized = 0;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 0,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 	register_destructor(_destructor);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 6, 4);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "pointer");
  hoc_register_dparam_semantics(_mechtype, 3, "netsend");
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 ASCIIRecord /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ASCIIrecord.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int addmapping();
static int addvar();
static int consolidateTiming();
static int restartEvent();
static int recdata();
static int writeMeta();
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{    _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t;   if (_lflag == 1. ) {*(_tqitem) = 0;}
 {
   recdata ( _threadargs_ ) ;
   if ( t < tstop ) {
     net_send ( _tqitem, _args, _pnt, t +  Dt , 1.0 ) ;
     }
   } }
 
/*VERBATIM*/

#include <math.h>

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
    void* nextReport_;
    int handle_;
    char neuronName_[256];
    char rptName_[256];
    char path_[512];
    char fn_[256];
    int tstep_;
    int tsteps_;
    double tstart_;
    double tstop_;
    double Dt_;
    double** ptrs_; /* list of pointers to hoc variables */
    float* buf_; 
    float* map_; 
    int np_;
    int nm_;
    int tp_; /* temporary indicator of passed variable pointers */
    int mp_; /* temporary indicator of passed variable pointers */

    /* for ASCII version */
    char* line_;    /* this buffers the values of one timestep*/
    FILE* ascfile_; /* file pointer to ascii file*/
} Info;


#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

#define dp double*

extern void nrn_register_recalc_ptr_callback(void (*f)());
extern Point_process* ob2pntproc(Object*);
extern double* nrn_recalc_ptr(double*);

static void recalc_ptr_callback() {
	Symbol* sym;
	hoc_List* instances;
	hoc_Item* q;
	/*printf("ASCIIrecord.mod recalc_ptr_callback\n");*/
	/* hoc has a list of the ASCIIRecord instances */
	sym = hoc_lookup("ASCIIRecord");
	instances = sym->u.template->olist;
	ITERATE(q, instances) {
		Info* InfoPtr;
		int i;
		Point_process* pnt;
		Object* o = OBJ(q);
		/*printf("callback for %s\n", hoc_object_name(o));*/
		pnt = ob2pntproc(o);
		_ppvar = pnt->_prop->dparam;
		INFOCAST;
		for (InfoPtr = *ip; InfoPtr != 0; InfoPtr = (Info*) InfoPtr->nextReport_)
			for (i=0; i < InfoPtr->np_; ++i)
				InfoPtr->ptrs_[i]= nrn_recalc_ptr(InfoPtr->ptrs_[i]);

	}
}

 
static int  restartEvent (  ) {
   
/*VERBATIM*/
#ifndef CORENEURON_BUILD
    const double etime = *getarg(1);
    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
#endif
  return 0; }
 
static double _hoc_restartEvent(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 restartEvent (  );
 return(_r);
}
 
double newReport (  ) {
   double _lnewReport;
 
/*VERBATIM*/
{
        INFOCAST;
	Info* iPtr;
	Info* info;
	for (iPtr = *ip; iPtr->nextReport_ != 0; iPtr = (Info*) iPtr->nextReport_) {}
	int newRpt = 0;
	int trial = 0;
	int fileOpen = 0;
	char fn[1024];

	if (iPtr->handle_ == -1) {
		if (hoc_is_str_arg(1)) sprintf(iPtr->neuronName_, "%s", gargstr(1));
		else sprintf(iPtr->neuronName_, "neuron");

		if (hoc_is_str_arg(2)) sprintf(iPtr->rptName_, "%s", gargstr(2));
		else sprintf(iPtr->rptName_, "report");

		sprintf(fn, "%s/%s.%s", iPtr->path_, iPtr->fn_, iPtr->rptName_);
		iPtr->ascfile_ = fopen(fn, "wb");
		fileOpen = iPtr->ascfile_ ? 1 : 0;
		while ((!fileOpen) && (trial < 20)) {
			iPtr->ascfile_ = fopen(fn, "wb");
			fileOpen = iPtr->ascfile_ ? 1 : 0;
			trial += 1;
		}
		iPtr->handle_ = 0;

	}
	// there already is a report --> need to create a new info struct
	else {
		newRpt = 1;
//        	Info* info = 0;
		info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
		info->handle_ = -1;
		info->nextReport_ = 0;
		info->neuronName_[0]= 0;
		info->rptName_[0]= 0;
//		info->neuron_ = 0;
		info->tstart_ = 0;
		info->tstop_ = 0;
		info->Dt_ = 0;
//		info->rpt_ = 0;
	        info->ptrs_ = 0;
	        info->np_ = 0;
	        info->nm_ = 0;
		info->tp_ = 0;
		info->mp_ = 0;
		info->tstep_ = 0;
		info->tsteps_ = 0;
		info->line_ = 0;
		info->map_ = 0;

		if (hoc_is_str_arg(1)) sprintf(info->neuronName_, "%s", gargstr(1));
		else sprintf(info->neuronName_, "neuron");

		if (hoc_is_str_arg(2)) sprintf(info->rptName_, "%s", gargstr(2));
		else sprintf(info->rptName_, "report");

		sprintf(info->fn_, "%s", (*ip)->fn_);
		sprintf(info->path_, "%s", (*ip)->path_);

		sprintf(fn, "%s/%s.%s", info->path_, info->fn_, info->rptName_);
		info->ascfile_ = fopen(fn, "wb");
		fileOpen = info->ascfile_ ? 1 : 0;
		while ((!fileOpen) && (trial < 20)) {
			info->ascfile_ = fopen(fn, "wb");
			fileOpen = info->ascfile_ ? 1 : 0;
			trial += 1;
		}
		iPtr=info;

	}
	if (!fileOpen) {
		fprintf(stderr, "[ASCIIrecord] Rank %.0lf: Error! couldn't open file %s!\n",
				rank, fn);
		return 0;
	}

	char tmp[256];
	char unitStr[5];

	if (ifarg(3)) {
		iPtr->np_   = (int) *getarg(3);
	        iPtr->ptrs_ = (double**)hoc_Ecalloc(iPtr->np_, sizeof(double*)); hoc_malchk();
	        iPtr->buf_  = (float*)hoc_Ecalloc(iPtr->np_, sizeof(float)); hoc_malchk();
	}

	if (ifarg(4) && ifarg(5) && ifarg(6)) {
		iPtr->tstart_   = *getarg(4);
		iPtr->tstop_    = *getarg(5);
		iPtr->Dt_       = *getarg(6);
//		printf("tstart = %g\n", info->tstart_);
//		printf("tstop = %g\n", info->tstop_);
//		printf("Dt = %g\n", info->Dt_);
		iPtr->tsteps_   = (int) (((iPtr->tstop_-iPtr->tstart_)/iPtr->Dt_)+.5);
//		printf("steps = %d\n", info->tsteps_);
		iPtr->tsteps_ += 1;
//		printf("steps = %d\n", info->tsteps_);
	}

	if (hoc_is_str_arg(7)) {
		sprintf(unitStr, "%s", gargstr(7));
	} else {
		sprintf(unitStr, "xx");
	}

	tstart = iPtr->tstart_;
	tstop  = iPtr->tstop_;
	Dt = iPtr->Dt_;

	/* initset can only be called once in case of ASCII reporting */

	if ((iPtr->ascfile_) && (iPtr->line_==0)) {
		sprintf(tmp, "# neuron = %s\n", iPtr->neuronName_); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# report = %s\n", iPtr->rptName_); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# tstart = %g\n", iPtr->tstart_); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# tstop  = %g\n", iPtr->tstop_); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# Dt     = %g\n", iPtr->Dt_); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# tunit  = ms\n"); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# dunit  = %s\n", unitStr); fputs(tmp, iPtr->ascfile_);
		sprintf(tmp, "# rank   = %.0lf\n", rank); fputs(tmp, iPtr->ascfile_);

		// allow 20 chars per double value.
		iPtr->line_ = (char*)hoc_Ecalloc(iPtr->np_*20, sizeof(char)); hoc_malchk();
	}

//	if (!newRpt) *ip = info;
	if (newRpt == 1) {
		Info* tPtr; int hd = 1;
		for (tPtr = *ip; tPtr->nextReport_ != 0; tPtr = (Info*) tPtr->nextReport_, hd++) {}
		tPtr->nextReport_ = iPtr;
		iPtr->handle_ = hd;
	}
	rpts += 1;

	return iPtr->handle_;
}
 
return _lnewReport;
 }
 
static double _hoc_newReport(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  newReport (  );
 return(_r);
}
 
double newMapping (  ) {
   double _lnewMapping;
 
/*VERBATIM*/
{ 
//printf("newMapping\n");
	INFOCAST; Info* iPtr = 0; Info* info = 0;
	char tmp[256];
	if (ifarg(1)) {
		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
		if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
		else info=iPtr;
	}

	if (hoc_is_str_arg(2)) {
		if (strncmp(gargstr(2), "point", 5) == 0) {
		        info->map_  = (float*)hoc_Ecalloc(info->np_*3, sizeof(float)); hoc_malchk();
			info->nm_ = 3*info->np_;
		}
		else if (strncmp(gargstr(2), "compartment", 11) == 0) {
		        info->map_  = (float*)hoc_Ecalloc(info->np_, sizeof(float)); hoc_malchk();
			info->nm_ = info->np_;
		}	
	}

	if (info->ascfile_) {        

		if (strncmp(gargstr(2), "point", 5) == 0) {
		}
		else if (strncmp(gargstr(2), "compartment", 11) == 0) {
			int sec, soma, axon, basal, apic;
			sec = soma = axon = basal = apic = 0;

			if (ifarg(3)) {
				sec = (int) *getarg(3);
			}
			if (ifarg(4)) {
				soma = (int) *getarg(4);
			}
			if (ifarg(5)) {
				axon = (int) *getarg(5);
			}
			if (ifarg(6)) {
				basal = (int) *getarg(6);
			}
			if (ifarg(7)) {
				apic = (int) *getarg(7);
			}

			sprintf(tmp, "#\n"); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# type      = compartment\n"); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# totalSecs = %d\n", sec); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# somaSecs  = %d\n", soma); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# axonSecs  = %d\n", axon); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# basalSecs = %d\n", basal); fputs(tmp, info->ascfile_);
			sprintf(tmp, "# apicSecs  = %d\n", apic); fputs(tmp, info->ascfile_);

		}
	}
	
}
 
return _lnewMapping;
 }
 
static double _hoc_newMapping(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  newMapping (  );
 return(_r);
}
 
static int  addvar (  ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = 0; Info* iPtr = 0;
//printf("addVar\n");
	if (ifarg(1)) {
		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
		if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
		else info=iPtr;
	}

        if (info->tp_ < info->np_) {
	        info->ptrs_[info->tp_] = hoc_pgetarg(2);
//		if (ifarg(3)) {
//			info->map_[info->tp_] = (float) *getarg(3);
//		}
        	++(info->tp_);
        }
}
  return 0; }
 
static double _hoc_addvar(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 addvar (  );
 return(_r);
}
 
static int  addmapping (  ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = 0; Info* iPtr = 0;
//printf("addMapping\n");
	if (ifarg(1)) {
		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
		if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
		else info=iPtr;
	}

//	printf("getarg(2) = %g\n", *getarg(2));
        if (info->mp_ < info->np_) {
		if (ifarg(2)) {
			info->map_[info->mp_] = (float) *getarg(2);
//			printf("info->map = %g\n", info->map_[info->mp_]);
		}
		if (ifarg(3)) {
			info->map_[info->mp_+info->np_] = (float) *getarg(3);
		}
		if (ifarg(4)) {
			info->map_[info->mp_+info->np_*2] = (float) *getarg(4);
		}
        	++info->mp_;
        }
}
  return 0; }
 
static double _hoc_addmapping(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 addmapping (  );
 return(_r);
}
 
static int  recdata (  ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
		if ((t >= info->tstart_) && (t <= info->tstop_)) {
			if (info->ascfile_) {
				int i, n;
				n = 0;
				for (i=0; i < info->tp_; i++) {
					n += sprintf(info->line_ + n, " %g", *info->ptrs_[i]);
				}
				
				sprintf(info->line_ + n, "\n");
					fputs(info->line_, info->ascfile_);
        		}
        	}
		++info->tstep_;		
        }	
}
  return 0; }
 
static double _hoc_recdata(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 recdata (  );
 return(_r);
}
 
static int  writeMeta (  ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
//printf("writeMeta()\n");
	char tmp[256];
	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
	        if (info->map_) {
			if (info->ascfile_) {
				int i = 0;
				sprintf(tmp, "# mapping  = "); fputs(tmp, info->ascfile_);
				for (i = 0; i< info->np_; i++) {
					sprintf(tmp, "%g ", info->map_[i]);	
					fputs(tmp, info->ascfile_);
				}
				sprintf(tmp, "\n"); fputs(tmp, info->ascfile_);
			}
	        }
	}
}
  return 0; }
 
static double _hoc_writeMeta(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 writeMeta (  );
 return(_r);
}
 
static int  consolidateTiming (  ) {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip;
//printf("consolidateTiming()\n");
        double tmin = tstart; // values of last report!
        double tmax = tstop; // values of last report!
	double myeps=1e-10;
	double commonDt = Dt;
//printf("tmin=%g\n", tmin);
//printf("tmax=%g\n", tmax);
//printf("Dt=%g\n", Dt);
	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
		if (info->tstart_ < tmin) tmin = info->tstart_;
		if (info->tstop_ > tmax) tmax = info->tstop_;
                if (info->Dt_ != Dt) {
                	if (rank == 0) printf("[ASCIIrecord] Warning: Dt is not the same throughout reports! Setting Dt to %g\n", Dt);
                	info->Dt_ = Dt;
                }
        }
//printf("tmin=%g\n", tmin);
//printf("tmax=%g\n", tmax);
//printf("Dt=%g\n", Dt);

	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
		int steps2start = (int)((info->tstart_-tmin)/Dt+.5);
		double dsteps2start = (info->tstart_-tmin)/Dt;
		if (fabs(dsteps2start - (double)(steps2start)) > myeps) {
			info->tstart_ = tmin + steps2start*Dt;
                	if (rank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting start time to %g\n", info->tstart_);
		}
		int steps2stop = (int)((info->tstop_-tmin)/Dt+.5);
		double dsteps2stop = (info->tstop_-tmin)/Dt;
		if (fabs(dsteps2stop - (double)(steps2stop)) > myeps) {
			info->tstop_ = tmin + steps2stop*Dt;
                	if (rank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting stop time to %g\n", info->tstop_);
		}
        }

	tstart = tmin;
	tstop = tmax;

//printf("tstart_=%g\n", info->tstart_);
//printf("tstop_=%g\n", info->tstop_);
//printf("Dt=%g\n", Dt);

/*
	phase* firstphase = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();
	firstphase->time = 0;
	firstphase->step = 0;
	firstphase->next = 0;
	int interval = 0;
	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
		phase* p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();
		if (interval == 0) {
			p->time = info->tstart;
			p->step = info->Dt;
			firstphase->next = p;
			p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();
			p->time = info->tstop;
			p->step = 0;
			p->next = 0;
			firstphase->next->next = p;
		} else {
			phase* pptr; phase* npptr = 0;
			for(pptr = firstphase; (pptr->next != 0) && (info->tstart < pptr->next->time); pptr = pptr->next) {}
			
			// the intervals are disjoint and interval is the last
			if (pptr->next == 0)) {
				p->time = info->tstart;
				p->step = info->Dt;
				pptr->next = p;
				p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();
				p->time = info->tstop;
				p->step = 0;
				p->next = 0;
				pptr->next->next = p;
			} else {
                                npptr = pptr->next;
				p->time = info->tstart;
				// choose smallest timestep - need to check for consitstency 
                                if (info->Dt < pptr->step) p->step = info->Dt;
				else p->step = pptr->step;
				p->next = npptr;
				pptr = p;
                                p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();

				double Dt_back = 0;
				// check whether intermediate intervals have correct time step 
				for (; (pptr->next != 0) && (info->tstop < pptr->next->time); pptr = pptr->next) {
					Dt_back = pptr->step;
                                	if (info->Dt < pptr->step) pptr->step = info->Dt;
				}
                                // interval ends is at end 
                                if (pptr->next == 0) {
                                         p->time = info->tstop;
                                         p->step = 0;
                                         p->next = 0;
                                         pptr->next = p;
                                } else {
					p->time = info->tstop;
					p->step = Dt_back;
					p->next = pptr->next;
					pptr->next = p
				}
 
			}
		}
		interval++;
	}
	
 	delete[] timesteps;
	delete[] times;
*/
}
  return 0; }
 
static double _hoc_consolidateTiming(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 consolidateTiming (  );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
	static int first = 1;
	if (first) {
		first = 0;
		nrn_register_recalc_ptr_callback(recalc_ptr_callback);
	}
        if (ifarg(2)) {
                rank = (int) *getarg(2);
        }

	if (ifarg(4) && (hoc_is_str_arg(3)) && (hoc_is_str_arg(4))) {
		INFOCAST;
        	Info* info = 0;

		info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk(); 
		info->nextReport_ = 0;
		info->neuronName_[0]= 0;
		info->rptName_[0]= 0;
		info->handle_ = -1;
//		info->neuron_ = 0;
		info->tstart_ = 0;
		info->tstop_ = 0;
		info->Dt_ = 0;
//		info->rpt_ = 0;
		info->ptrs_ = 0;
		info->np_ = 0;
		info->nm_ = 0;
		info->tp_ = 0;
		info->mp_ = 0;
		info->tstep_ = 0;
		info->tsteps_ = 0;
		info->line_ = 0;
		info->map_ = 0;
		
		*ip = info;
		sprintf((*ip)->path_, "%s", gargstr(3));
		sprintf((*ip)->fn_, "%s", gargstr(4));
	}

}
 }
 
}
}
 
static void _destructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{ INFOCAST; Info* info = *ip; 
	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
		if (info->ascfile_) {
			fflush(info->ascfile_);
			fclose(info->ascfile_);
			info->ascfile_ = (FILE*)0;
		}
	}
}
 }
 
}
}

static void initmodel() {
  int _i; double _save;_ninits++;
{
 {
   writeMeta ( _threadargs_ ) ;
   consolidateTiming ( _threadargs_ ) ;
   net_send ( _tqitem, (double*)0, _ppvar[1]._pvoid, t +  tstart , 1.0 ) ;
   }

}
}

static void nrn_init(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
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
 initmodel();
}}

static double _nrn_current(double _v){double _current=0.;v=_v;{
} return _current;
}

static void nrn_state(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v = 0.0; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
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

static void _initlists() {
 int _i; static int _first = 1;
  if (!_first) return;
_first = 0;
}

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/ASCIIrecord.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "If the local variable step method is used then the only variables that should\n"
  "be added are variables of the cell in which this FileRecord\n"
  "has been instantiated.\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    POINT_PROCESS ASCIIRecord\n"
  "    POINTER ptr\n"
  "    RANGE rank : rank of processor\n"
  "    RANGE Dt\n"
  "	RANGE tstart\n"
  "	RANGE tstop\n"
  "	RANGE rpts\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "    rank = 0\n"
  "	Dt = .1 (ms)\n"
  "	tstart = 0 (ms)\n"
  "	tstop  = 0 (ms)\n"
  "	rpts = 0\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "    ptr\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "	writeMeta()\n"
  "    consolidateTiming()\n"
  "    net_send(tstart, 1)\n"
  "}\n"
  "\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "    recdata()\n"
  "    if (t<tstop) {\n"
  "        net_send(Dt, 1)\n"
  "    }\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#include <math.h>\n"
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
  "    void* nextReport_;\n"
  "    int handle_;\n"
  "    char neuronName_[256];\n"
  "    char rptName_[256];\n"
  "    char path_[512];\n"
  "    char fn_[256];\n"
  "    int tstep_;\n"
  "    int tsteps_;\n"
  "    double tstart_;\n"
  "    double tstop_;\n"
  "    double Dt_;\n"
  "    double** ptrs_; /* list of pointers to hoc variables */\n"
  "    float* buf_; \n"
  "    float* map_; \n"
  "    int np_;\n"
  "    int nm_;\n"
  "    int tp_; /* temporary indicator of passed variable pointers */\n"
  "    int mp_; /* temporary indicator of passed variable pointers */\n"
  "\n"
  "    /* for ASCII version */\n"
  "    char* line_;    /* this buffers the values of one timestep*/\n"
  "    FILE* ascfile_; /* file pointer to ascii file*/\n"
  "} Info;\n"
  "\n"
  "\n"
  "#define INFOCAST Info** ip = (Info**)(&(_p_ptr))\n"
  "\n"
  "#define dp double*\n"
  "\n"
  "extern void nrn_register_recalc_ptr_callback(void (*f)());\n"
  "extern Point_process* ob2pntproc(Object*);\n"
  "extern double* nrn_recalc_ptr(double*);\n"
  "\n"
  "static void recalc_ptr_callback() {\n"
  "	Symbol* sym;\n"
  "	hoc_List* instances;\n"
  "	hoc_Item* q;\n"
  "	/*printf(\"ASCIIrecord.mod recalc_ptr_callback\\n\");*/\n"
  "	/* hoc has a list of the ASCIIRecord instances */\n"
  "	sym = hoc_lookup(\"ASCIIRecord\");\n"
  "	instances = sym->u.template->olist;\n"
  "	ITERATE(q, instances) {\n"
  "		Info* InfoPtr;\n"
  "		int i;\n"
  "		Point_process* pnt;\n"
  "		Object* o = OBJ(q);\n"
  "		/*printf(\"callback for %s\\n\", hoc_object_name(o));*/\n"
  "		pnt = ob2pntproc(o);\n"
  "		_ppvar = pnt->_prop->dparam;\n"
  "		INFOCAST;\n"
  "		for (InfoPtr = *ip; InfoPtr != 0; InfoPtr = (Info*) InfoPtr->nextReport_)\n"
  "			for (i=0; i < InfoPtr->np_; ++i)\n"
  "				InfoPtr->ptrs_[i]= nrn_recalc_ptr(InfoPtr->ptrs_[i]);\n"
  "\n"
  "	}\n"
  "}\n"
  "\n"
  "ENDVERBATIM\n"
  "\n"
  "CONSTRUCTOR { : double - loc of point process, int rank, string path, string filename\n"
  "VERBATIM {\n"
  "	static int first = 1;\n"
  "	if (first) {\n"
  "		first = 0;\n"
  "		nrn_register_recalc_ptr_callback(recalc_ptr_callback);\n"
  "	}\n"
  "        if (ifarg(2)) {\n"
  "                rank = (int) *getarg(2);\n"
  "        }\n"
  "\n"
  "	if (ifarg(4) && (hoc_is_str_arg(3)) && (hoc_is_str_arg(4))) {\n"
  "		INFOCAST;\n"
  "        	Info* info = 0;\n"
  "\n"
  "		info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk(); \n"
  "		info->nextReport_ = 0;\n"
  "		info->neuronName_[0]= 0;\n"
  "		info->rptName_[0]= 0;\n"
  "		info->handle_ = -1;\n"
  "//		info->neuron_ = 0;\n"
  "		info->tstart_ = 0;\n"
  "		info->tstop_ = 0;\n"
  "		info->Dt_ = 0;\n"
  "//		info->rpt_ = 0;\n"
  "		info->ptrs_ = 0;\n"
  "		info->np_ = 0;\n"
  "		info->nm_ = 0;\n"
  "		info->tp_ = 0;\n"
  "		info->mp_ = 0;\n"
  "		info->tstep_ = 0;\n"
  "		info->tsteps_ = 0;\n"
  "		info->line_ = 0;\n"
  "		info->map_ = 0;\n"
  "		\n"
  "		*ip = info;\n"
  "		sprintf((*ip)->path_, \"%s\", gargstr(3));\n"
  "		sprintf((*ip)->fn_, \"%s\", gargstr(4));\n"
  "	}\n"
  "\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM { INFOCAST; Info* info = *ip; \n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "		if (info->ascfile_) {\n"
  "			fflush(info->ascfile_);\n"
  "			fclose(info->ascfile_);\n"
  "			info->ascfile_ = (FILE*)0;\n"
  "		}\n"
  "	}\n"
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
  "FUNCTION newReport() { : string neuronname, string setname, double vars, double tstart, double tstop, double dt, string unit\n"
  "VERBATIM {\n"
  "        INFOCAST;\n"
  "	Info* iPtr;\n"
  "	Info* info;\n"
  "	for (iPtr = *ip; iPtr->nextReport_ != 0; iPtr = (Info*) iPtr->nextReport_) {}\n"
  "	int newRpt = 0;\n"
  "	int trial = 0;\n"
  "	int fileOpen = 0;\n"
  "	char fn[1024];\n"
  "\n"
  "	if (iPtr->handle_ == -1) {\n"
  "		if (hoc_is_str_arg(1)) sprintf(iPtr->neuronName_, \"%s\", gargstr(1));\n"
  "		else sprintf(iPtr->neuronName_, \"neuron\");\n"
  "\n"
  "		if (hoc_is_str_arg(2)) sprintf(iPtr->rptName_, \"%s\", gargstr(2));\n"
  "		else sprintf(iPtr->rptName_, \"report\");\n"
  "\n"
  "		sprintf(fn, \"%s/%s.%s\", iPtr->path_, iPtr->fn_, iPtr->rptName_);\n"
  "		iPtr->ascfile_ = fopen(fn, \"wb\");\n"
  "		fileOpen = iPtr->ascfile_ ? 1 : 0;\n"
  "		while ((!fileOpen) && (trial < 20)) {\n"
  "			iPtr->ascfile_ = fopen(fn, \"wb\");\n"
  "			fileOpen = iPtr->ascfile_ ? 1 : 0;\n"
  "			trial += 1;\n"
  "		}\n"
  "		iPtr->handle_ = 0;\n"
  "\n"
  "	}\n"
  "	// there already is a report --> need to create a new info struct\n"
  "	else {\n"
  "		newRpt = 1;\n"
  "//        	Info* info = 0;\n"
  "		info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "		info->handle_ = -1;\n"
  "		info->nextReport_ = 0;\n"
  "		info->neuronName_[0]= 0;\n"
  "		info->rptName_[0]= 0;\n"
  "//		info->neuron_ = 0;\n"
  "		info->tstart_ = 0;\n"
  "		info->tstop_ = 0;\n"
  "		info->Dt_ = 0;\n"
  "//		info->rpt_ = 0;\n"
  "	        info->ptrs_ = 0;\n"
  "	        info->np_ = 0;\n"
  "	        info->nm_ = 0;\n"
  "		info->tp_ = 0;\n"
  "		info->mp_ = 0;\n"
  "		info->tstep_ = 0;\n"
  "		info->tsteps_ = 0;\n"
  "		info->line_ = 0;\n"
  "		info->map_ = 0;\n"
  "\n"
  "		if (hoc_is_str_arg(1)) sprintf(info->neuronName_, \"%s\", gargstr(1));\n"
  "		else sprintf(info->neuronName_, \"neuron\");\n"
  "\n"
  "		if (hoc_is_str_arg(2)) sprintf(info->rptName_, \"%s\", gargstr(2));\n"
  "		else sprintf(info->rptName_, \"report\");\n"
  "\n"
  "		sprintf(info->fn_, \"%s\", (*ip)->fn_);\n"
  "		sprintf(info->path_, \"%s\", (*ip)->path_);\n"
  "\n"
  "		sprintf(fn, \"%s/%s.%s\", info->path_, info->fn_, info->rptName_);\n"
  "		info->ascfile_ = fopen(fn, \"wb\");\n"
  "		fileOpen = info->ascfile_ ? 1 : 0;\n"
  "		while ((!fileOpen) && (trial < 20)) {\n"
  "			info->ascfile_ = fopen(fn, \"wb\");\n"
  "			fileOpen = info->ascfile_ ? 1 : 0;\n"
  "			trial += 1;\n"
  "		}\n"
  "		iPtr=info;\n"
  "\n"
  "	}\n"
  "	if (!fileOpen) {\n"
  "		fprintf(stderr, \"[ASCIIrecord] Rank %.0lf: Error! couldn't open file %s!\\n\",\n"
  "				rank, fn);\n"
  "		return 0;\n"
  "	}\n"
  "\n"
  "	char tmp[256];\n"
  "	char unitStr[5];\n"
  "\n"
  "	if (ifarg(3)) {\n"
  "		iPtr->np_   = (int) *getarg(3);\n"
  "	        iPtr->ptrs_ = (double**)hoc_Ecalloc(iPtr->np_, sizeof(double*)); hoc_malchk();\n"
  "	        iPtr->buf_  = (float*)hoc_Ecalloc(iPtr->np_, sizeof(float)); hoc_malchk();\n"
  "	}\n"
  "\n"
  "	if (ifarg(4) && ifarg(5) && ifarg(6)) {\n"
  "		iPtr->tstart_   = *getarg(4);\n"
  "		iPtr->tstop_    = *getarg(5);\n"
  "		iPtr->Dt_       = *getarg(6);\n"
  "//		printf(\"tstart = %g\\n\", info->tstart_);\n"
  "//		printf(\"tstop = %g\\n\", info->tstop_);\n"
  "//		printf(\"Dt = %g\\n\", info->Dt_);\n"
  "		iPtr->tsteps_   = (int) (((iPtr->tstop_-iPtr->tstart_)/iPtr->Dt_)+.5);\n"
  "//		printf(\"steps = %d\\n\", info->tsteps_);\n"
  "		iPtr->tsteps_ += 1;\n"
  "//		printf(\"steps = %d\\n\", info->tsteps_);\n"
  "	}\n"
  "\n"
  "	if (hoc_is_str_arg(7)) {\n"
  "		sprintf(unitStr, \"%s\", gargstr(7));\n"
  "	} else {\n"
  "		sprintf(unitStr, \"xx\");\n"
  "	}\n"
  "\n"
  "	tstart = iPtr->tstart_;\n"
  "	tstop  = iPtr->tstop_;\n"
  "	Dt = iPtr->Dt_;\n"
  "\n"
  "	/* initset can only be called once in case of ASCII reporting */\n"
  "\n"
  "	if ((iPtr->ascfile_) && (iPtr->line_==0)) {\n"
  "		sprintf(tmp, \"# neuron = %s\\n\", iPtr->neuronName_); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# report = %s\\n\", iPtr->rptName_); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# tstart = %g\\n\", iPtr->tstart_); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# tstop  = %g\\n\", iPtr->tstop_); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# Dt     = %g\\n\", iPtr->Dt_); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# tunit  = ms\\n\"); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# dunit  = %s\\n\", unitStr); fputs(tmp, iPtr->ascfile_);\n"
  "		sprintf(tmp, \"# rank   = %.0lf\\n\", rank); fputs(tmp, iPtr->ascfile_);\n"
  "\n"
  "		// allow 20 chars per double value.\n"
  "		iPtr->line_ = (char*)hoc_Ecalloc(iPtr->np_*20, sizeof(char)); hoc_malchk();\n"
  "	}\n"
  "\n"
  "//	if (!newRpt) *ip = info;\n"
  "	if (newRpt == 1) {\n"
  "		Info* tPtr; int hd = 1;\n"
  "		for (tPtr = *ip; tPtr->nextReport_ != 0; tPtr = (Info*) tPtr->nextReport_, hd++) {}\n"
  "		tPtr->nextReport_ = iPtr;\n"
  "		iPtr->handle_ = hd;\n"
  "	}\n"
  "	rpts += 1;\n"
  "\n"
  "	return iPtr->handle_;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION newMapping() { : double rptHd, string mapping\n"
  "VERBATIM { \n"
  "//printf(\"newMapping\\n\");\n"
  "	INFOCAST; Info* iPtr = 0; Info* info = 0;\n"
  "	char tmp[256];\n"
  "	if (ifarg(1)) {\n"
  "		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "		if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "		else info=iPtr;\n"
  "	}\n"
  "\n"
  "	if (hoc_is_str_arg(2)) {\n"
  "		if (strncmp(gargstr(2), \"point\", 5) == 0) {\n"
  "		        info->map_  = (float*)hoc_Ecalloc(info->np_*3, sizeof(float)); hoc_malchk();\n"
  "			info->nm_ = 3*info->np_;\n"
  "		}\n"
  "		else if (strncmp(gargstr(2), \"compartment\", 11) == 0) {\n"
  "		        info->map_  = (float*)hoc_Ecalloc(info->np_, sizeof(float)); hoc_malchk();\n"
  "			info->nm_ = info->np_;\n"
  "		}	\n"
  "	}\n"
  "\n"
  "	if (info->ascfile_) {        \n"
  "\n"
  "		if (strncmp(gargstr(2), \"point\", 5) == 0) {\n"
  "		}\n"
  "		else if (strncmp(gargstr(2), \"compartment\", 11) == 0) {\n"
  "			int sec, soma, axon, basal, apic;\n"
  "			sec = soma = axon = basal = apic = 0;\n"
  "\n"
  "			if (ifarg(3)) {\n"
  "				sec = (int) *getarg(3);\n"
  "			}\n"
  "			if (ifarg(4)) {\n"
  "				soma = (int) *getarg(4);\n"
  "			}\n"
  "			if (ifarg(5)) {\n"
  "				axon = (int) *getarg(5);\n"
  "			}\n"
  "			if (ifarg(6)) {\n"
  "				basal = (int) *getarg(6);\n"
  "			}\n"
  "			if (ifarg(7)) {\n"
  "				apic = (int) *getarg(7);\n"
  "			}\n"
  "\n"
  "			sprintf(tmp, \"#\\n\"); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# type      = compartment\\n\"); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# totalSecs = %d\\n\", sec); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# somaSecs  = %d\\n\", soma); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# axonSecs  = %d\\n\", axon); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# basalSecs = %d\\n\", basal); fputs(tmp, info->ascfile_);\n"
  "			sprintf(tmp, \"# apicSecs  = %d\\n\", apic); fputs(tmp, info->ascfile_);\n"
  "\n"
  "		}\n"
  "	}\n"
  "	\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "PROCEDURE addvar() { : int rptHD, double* pd\n"
  "VERBATIM { INFOCAST; Info* info = 0; Info* iPtr = 0;\n"
  "//printf(\"addVar\\n\");\n"
  "	if (ifarg(1)) {\n"
  "		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "		if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "		else info=iPtr;\n"
  "	}\n"
  "\n"
  "        if (info->tp_ < info->np_) {\n"
  "	        info->ptrs_[info->tp_] = hoc_pgetarg(2);\n"
  "//		if (ifarg(3)) {\n"
  "//			info->map_[info->tp_] = (float) *getarg(3);\n"
  "//		}\n"
  "        	++(info->tp_);\n"
  "        }\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE addmapping() { : int rptHD, double var1, double var2, double var3\n"
  "VERBATIM { INFOCAST; Info* info = 0; Info* iPtr = 0;\n"
  "//printf(\"addMapping\\n\");\n"
  "	if (ifarg(1)) {\n"
  "		for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}\n"
  "		if (iPtr == 0) printf(\"ERROR: given handle does not correspond to report!\\n\");\n"
  "		else info=iPtr;\n"
  "	}\n"
  "\n"
  "//	printf(\"getarg(2) = %g\\n\", *getarg(2));\n"
  "        if (info->mp_ < info->np_) {\n"
  "		if (ifarg(2)) {\n"
  "			info->map_[info->mp_] = (float) *getarg(2);\n"
  "//			printf(\"info->map = %g\\n\", info->map_[info->mp_]);\n"
  "		}\n"
  "		if (ifarg(3)) {\n"
  "			info->map_[info->mp_+info->np_] = (float) *getarg(3);\n"
  "		}\n"
  "		if (ifarg(4)) {\n"
  "			info->map_[info->mp_+info->np_*2] = (float) *getarg(4);\n"
  "		}\n"
  "        	++info->mp_;\n"
  "        }\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE recdata() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "		if ((t >= info->tstart_) && (t <= info->tstop_)) {\n"
  "			if (info->ascfile_) {\n"
  "				int i, n;\n"
  "				n = 0;\n"
  "				for (i=0; i < info->tp_; i++) {\n"
  "					n += sprintf(info->line_ + n, \" %g\", *info->ptrs_[i]);\n"
  "				}\n"
  "				\n"
  "				sprintf(info->line_ + n, \"\\n\");\n"
  "					fputs(info->line_, info->ascfile_);\n"
  "        		}\n"
  "        	}\n"
  "		++info->tstep_;		\n"
  "        }	\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "PROCEDURE writeMeta() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "//printf(\"writeMeta()\\n\");\n"
  "	char tmp[256];\n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "	        if (info->map_) {\n"
  "			if (info->ascfile_) {\n"
  "				int i = 0;\n"
  "				sprintf(tmp, \"# mapping  = \"); fputs(tmp, info->ascfile_);\n"
  "				for (i = 0; i< info->np_; i++) {\n"
  "					sprintf(tmp, \"%g \", info->map_[i]);	\n"
  "					fputs(tmp, info->ascfile_);\n"
  "				}\n"
  "				sprintf(tmp, \"\\n\"); fputs(tmp, info->ascfile_);\n"
  "			}\n"
  "	        }\n"
  "	}\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  ": currently, consolidateTiming() has a simple logic:\n"
  ": 1. go through all reports and get minimum start time and maximum stop time\n"
  ": 2. check whether all reports have same Dt\n"
  ": 3. check whether the start and stop times are consistent with common Dt\n"
  "PROCEDURE consolidateTiming() {\n"
  "VERBATIM { INFOCAST; Info* info = *ip;\n"
  "//printf(\"consolidateTiming()\\n\");\n"
  "        double tmin = tstart; // values of last report!\n"
  "        double tmax = tstop; // values of last report!\n"
  "	double myeps=1e-10;\n"
  "	double commonDt = Dt;\n"
  "//printf(\"tmin=%g\\n\", tmin);\n"
  "//printf(\"tmax=%g\\n\", tmax);\n"
  "//printf(\"Dt=%g\\n\", Dt);\n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "		if (info->tstart_ < tmin) tmin = info->tstart_;\n"
  "		if (info->tstop_ > tmax) tmax = info->tstop_;\n"
  "                if (info->Dt_ != Dt) {\n"
  "                	if (rank == 0) printf(\"[ASCIIrecord] Warning: Dt is not the same throughout reports! Setting Dt to %g\\n\", Dt);\n"
  "                	info->Dt_ = Dt;\n"
  "                }\n"
  "        }\n"
  "//printf(\"tmin=%g\\n\", tmin);\n"
  "//printf(\"tmax=%g\\n\", tmax);\n"
  "//printf(\"Dt=%g\\n\", Dt);\n"
  "\n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "		int steps2start = (int)((info->tstart_-tmin)/Dt+.5);\n"
  "		double dsteps2start = (info->tstart_-tmin)/Dt;\n"
  "		if (fabs(dsteps2start - (double)(steps2start)) > myeps) {\n"
  "			info->tstart_ = tmin + steps2start*Dt;\n"
  "                	if (rank == 0) printf(\"[ASCIIrecord] Warning: Adjusting reporting start time to %g\\n\", info->tstart_);\n"
  "		}\n"
  "		int steps2stop = (int)((info->tstop_-tmin)/Dt+.5);\n"
  "		double dsteps2stop = (info->tstop_-tmin)/Dt;\n"
  "		if (fabs(dsteps2stop - (double)(steps2stop)) > myeps) {\n"
  "			info->tstop_ = tmin + steps2stop*Dt;\n"
  "                	if (rank == 0) printf(\"[ASCIIrecord] Warning: Adjusting reporting stop time to %g\\n\", info->tstop_);\n"
  "		}\n"
  "        }\n"
  "\n"
  "	tstart = tmin;\n"
  "	tstop = tmax;\n"
  "\n"
  "//printf(\"tstart_=%g\\n\", info->tstart_);\n"
  "//printf(\"tstop_=%g\\n\", info->tstop_);\n"
  "//printf(\"Dt=%g\\n\", Dt);\n"
  "\n"
  "/*\n"
  "	phase* firstphase = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();\n"
  "	firstphase->time = 0;\n"
  "	firstphase->step = 0;\n"
  "	firstphase->next = 0;\n"
  "	int interval = 0;\n"
  "	for (info = *ip; info != 0; info = (Info*) info->nextReport_) {\n"
  "		phase* p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();\n"
  "		if (interval == 0) {\n"
  "			p->time = info->tstart;\n"
  "			p->step = info->Dt;\n"
  "			firstphase->next = p;\n"
  "			p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();\n"
  "			p->time = info->tstop;\n"
  "			p->step = 0;\n"
  "			p->next = 0;\n"
  "			firstphase->next->next = p;\n"
  "		} else {\n"
  "			phase* pptr; phase* npptr = 0;\n"
  "			for(pptr = firstphase; (pptr->next != 0) && (info->tstart < pptr->next->time); pptr = pptr->next) {}\n"
  "			\n"
  "			// the intervals are disjoint and interval is the last\n"
  "			if (pptr->next == 0)) {\n"
  "				p->time = info->tstart;\n"
  "				p->step = info->Dt;\n"
  "				pptr->next = p;\n"
  "				p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();\n"
  "				p->time = info->tstop;\n"
  "				p->step = 0;\n"
  "				p->next = 0;\n"
  "				pptr->next->next = p;\n"
  "			} else {\n"
  "                                npptr = pptr->next;\n"
  "				p->time = info->tstart;\n"
  "				// choose smallest timestep - need to check for consitstency \n"
  "                                if (info->Dt < pptr->step) p->step = info->Dt;\n"
  "				else p->step = pptr->step;\n"
  "				p->next = npptr;\n"
  "				pptr = p;\n"
  "                                p = (phase*)hoc_Emalloc(sizeof(phase)); hoc_malchk();\n"
  "\n"
  "				double Dt_back = 0;\n"
  "				// check whether intermediate intervals have correct time step \n"
  "				for (; (pptr->next != 0) && (info->tstop < pptr->next->time); pptr = pptr->next) {\n"
  "					Dt_back = pptr->step;\n"
  "                                	if (info->Dt < pptr->step) pptr->step = info->Dt;\n"
  "				}\n"
  "                                // interval ends is at end \n"
  "                                if (pptr->next == 0) {\n"
  "                                         p->time = info->tstop;\n"
  "                                         p->step = 0;\n"
  "                                         p->next = 0;\n"
  "                                         pptr->next = p;\n"
  "                                } else {\n"
  "					p->time = info->tstop;\n"
  "					p->step = Dt_back;\n"
  "					p->next = pptr->next;\n"
  "					pptr->next = p\n"
  "				}\n"
  " \n"
  "			}\n"
  "		}\n"
  "		interval++;\n"
  "	}\n"
  "	\n"
  " 	delete[] timesteps;\n"
  "	delete[] times;\n"
  "*/\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  ;
#endif
