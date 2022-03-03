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
 
#define nrn_init _nrn_init_
#define _nrn_initial _nrn_initial_
#define nrn_cur _nrn_cur_
#define _nrn_current _nrn_current_
#define nrn_jacob _nrn_jacob_
#define nrn_state _nrn_state_
#define _net_receive _net_receive_ 
#define util_right util_right_ 
 
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
 /* external NEURON variables */
 /* declaration of user functions */
 static void _hoc_checkDirectory(void);
 static void _hoc_util_strhash(void);
 static void _hoc_util_right(void);
 static void _hoc_util_scanstr(void);
 static int _mechtype;
extern void _nrn_cacheloop_reg(int, int);
extern void hoc_register_prop_size(int, int, int);
extern void hoc_register_limits(int, HocParmLimits*);
extern void hoc_register_units(int, HocParmUnits*);
extern void nrn_promote(Prop*, int, int);
extern Memb_func* memb_func;
 extern void _nrn_setdata_reg(int, void(*)(Prop*));
 static void _setdata(Prop* _prop) {
 _p = _prop->param; _ppvar = _prop->dparam;
 }
 static void _hoc_setdata() {
 Prop *_prop, *hoc_getdata_range(int);
 _prop = hoc_getdata_range(_mechtype);
   _setdata(_prop);
 hoc_retpushx(1.);
}
 /* connect user functions to hoc names */
 static VoidFunc hoc_intfunc[] = {
 "setdata_utility", _hoc_setdata,
 "checkDirectory", _hoc_checkDirectory,
 "util_strhash", _hoc_util_strhash,
 "util_right", _hoc_util_right,
 "util_scanstr", _hoc_util_scanstr,
 0, 0
};
 extern double checkDirectory( );
 extern double util_strhash( );
 extern double util_scanstr( );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
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
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"utility",
 0,
 0,
 0,
 0};
 
extern Prop* need_memb(Symbol*);

static void nrn_alloc(Prop* _prop) {
	Prop *prop_ion;
	double *_p; Datum *_ppvar;
 	_p = nrn_prop_data_alloc(_mechtype, 0, _prop);
 	/*initialize range parameters*/
 	_prop->param = _p;
 	_prop->param_size = 0;
 
}
 static void _initlists();
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _utility_reg() {
	int _vectorized = 0;
  _initlists();
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 utility /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/utility.mod\n");
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int util_right();
 
/*VERBATIM*/

#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

extern char* gargstr();
extern char** hoc_pgargstr();
extern void hoc_assign_str();
extern double chkarg();

 
double util_scanstr (  ) {
   double _lutil_scanstr;
 
/*VERBATIM*/
{
	int ibegin, iend, i, flag;
	char *instr, **outstr, *cp, cend;
	instr = gargstr(1);
	ibegin = (int)chkarg(2, 0., 1e9);
	outstr = hoc_pgargstr(3);

	flag = 0;
	for (cp = instr+ibegin; *cp; ++cp, ++ibegin) {
		if (*cp != ' ' && *cp != '\n' && *cp != '\t') {
			flag = 1;
			break;
		}
	}
	if (flag == 0) {
		return -1.;
	}

	for (iend=ibegin; *cp; ++cp, ++iend) {
		if (*cp == ' ' || *cp == '\n' || *cp == '\t') {
			break;
		}
	}

	cend = instr[iend];
	instr[iend] = '\0';
	hoc_assign_str(outstr, instr + ibegin);
	instr[iend] = cend;
	return (double)iend;
}
 
return _lutil_scanstr;
 }
 
static void _hoc_util_scanstr(void) {
  double _r;
   _r =  util_scanstr (  );
 hoc_retpushx(_r);
}
 
static int  util_right (  ) {
   
/*VERBATIM*/
{
	int icp, i, flag;
	char* instr, **outstr;
	instr = gargstr(1);
	icp = (int)chkarg(2, 0., 1e9);
	outstr = hoc_pgargstr(3);

	hoc_assign_str(outstr, instr+icp);
}
  return 0; }
 
static void _hoc_util_right(void) {
  double _r;
   _r = 1.;
 util_right (  );
 hoc_retpushx(_r);
}
 
double util_strhash (  ) {
   double _lutil_strhash;
 
/*VERBATIM*/
{
	int i, j, k, h, n;
	char* s;
	s = gargstr(1);
	n = (int)chkarg(2, 1., 1e9);
	j = strlen(s);
	h = 0;
	for (i = 1; i < 5 && j >= i; ++i) {
		h *= 10;
		h += s[j - i];
	}

	return (double)(h%n);
}
 
return _lutil_strhash;
 }
 
static void _hoc_util_strhash(void) {
  double _r;
   _r =  util_strhash (  );
 hoc_retpushx(_r);
}
 
/*VERBATIM*/
/* creatory directory recursively, simlar to mkdir -p command */
int mkdir_p(const char* path) {
    const int path_len = strlen(path);
    if (path_len == 0) {
        printf("Warning: Empty path for creating directory");
        return -1;
    }

    char* dirpath = (char*) calloc(sizeof(char), path_len+1);
    strcpy(dirpath, path);
    errno = 0;

    char* p;
    /* iterate from outer upto inner dir */
    for (p = dirpath + 1; *p; p++) {
        if (*p == '/') {
            /* temporarily truncate to sub-dir */
            *p = '\0';
            if (mkdir(dirpath, S_IRWXU|S_IRGRP|S_IXGRP) != 0) {
                if (errno != EEXIST)
                    return -1;
            }
            *p = '/';
        }
    }

    if (mkdir(dirpath, S_IRWXU|S_IRGRP|S_IXGRP) != 0) {
        if (errno != EEXIST) {
            return -1;
        }
    }

    free(dirpath);
    return 0;
}
 
double checkDirectory (  ) {
   double _lcheckDirectory;
 
/*VERBATIM*/
    char* dirName = gargstr(1);
    struct stat st;
    if ( stat(dirName, &st) == 0) {
        if( !S_ISDIR(st.st_mode) ) {
            fprintf( stderr, "%s does not name a directory.\n", dirName );
            return -1;
        }
        return 0;
    }
    else if( errno == ENOENT ) {
        fprintf( stdout, "Directory %s does not exist.  Creating...\n", dirName );
        int res = mkdir_p(dirName);
        if( res < 0 ) {
            fprintf( stderr, "Failed to create directory %s.\n", dirName );
            return -1;
        }
        return 0;
    }
 
return _lcheckDirectory;
 }
 
static void _hoc_checkDirectory(void) {
  double _r;
   _r =  checkDirectory (  );
 hoc_retpushx(_r);
}

static void initmodel() {
  int _i; double _save;_ninits++;
{

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
