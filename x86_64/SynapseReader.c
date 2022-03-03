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
 
#define nrn_init _nrn_init__SynapseReader
#define _nrn_initial _nrn_initial__SynapseReader
#define nrn_cur _nrn_cur__SynapseReader
#define _nrn_current _nrn_current__SynapseReader
#define nrn_jacob _nrn_jacob__SynapseReader
#define nrn_state _nrn_state__SynapseReader
#define _net_receive _net_receive__SynapseReader 
 
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
#define verboseLevel _p[0]
#define v _p[1]
#define _tsav _p[2]
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
 static double _hoc_countSynapses();
 static double _hoc_countProperties();
 static double _hoc_getPropertyData();
 static double _hoc_getSynapse();
 static double _hoc_hasNrrpField();
 static double _hoc_hasProperty();
 static double _hoc_isV2();
 static double _hoc_loadSynapseCustom();
 static double _hoc_loadGapJunctions();
 static double _hoc_loadSynapses();
 static double _hoc_modEnabled();
 static double _hoc_selectPopulation();
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
 "countSynapses", _hoc_countSynapses,
 "countProperties", _hoc_countProperties,
 "getPropertyData", _hoc_getPropertyData,
 "getSynapse", _hoc_getSynapse,
 "hasNrrpField", _hoc_hasNrrpField,
 "hasProperty", _hoc_hasProperty,
 "isV2", _hoc_isV2,
 "loadSynapseCustom", _hoc_loadSynapseCustom,
 "loadGapJunctions", _hoc_loadGapJunctions,
 "loadSynapses", _hoc_loadSynapses,
 "modEnabled", _hoc_modEnabled,
 "selectPopulation", _hoc_selectPopulation,
 0, 0
};
#define countSynapses countSynapses_SynapseReader
#define countProperties countProperties_SynapseReader
#define getPropertyData getPropertyData_SynapseReader
#define getSynapse getSynapse_SynapseReader
#define hasNrrpField hasNrrpField_SynapseReader
#define hasProperty hasProperty_SynapseReader
#define isV2 isV2_SynapseReader
#define loadSynapseCustom loadSynapseCustom_SynapseReader
#define loadGapJunctions loadGapJunctions_SynapseReader
#define loadSynapses loadSynapses_SynapseReader
#define modEnabled modEnabled_SynapseReader
#define selectPopulation selectPopulation_SynapseReader
 extern double countSynapses( _threadargsproto_ );
 extern double countProperties( _threadargsproto_ );
 extern double getPropertyData( _threadargsproto_ );
 extern double getSynapse( _threadargsproto_ );
 extern double hasNrrpField( _threadargsproto_ );
 extern double hasProperty( _threadargsproto_ );
 extern double isV2( _threadargsproto_ );
 extern double loadSynapseCustom( _threadargsproto_ );
 extern double loadGapJunctions( _threadargsproto_ );
 extern double loadSynapses( _threadargsproto_ );
 extern double modEnabled( _threadargsproto_ );
 extern double selectPopulation( _threadargsproto_ );
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
"SynapseReader",
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
 	_p = nrn_prop_data_alloc(_mechtype, 3, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 3;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 static void _net_receive(Point_process*, double*, double);
 static void bbcore_write(double*, int*, int*, int*, _threadargsproto_);
 extern void hoc_reg_bbcore_write(int, void(*)(double*, int*, int*, int*, _threadargsproto_));
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _SynapseReader_reg() {
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
  hoc_register_prop_size(_mechtype, 3, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "bbcorepointer");
 add_nrn_artcell(_mechtype, 0);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 SynapseReader /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SynapseReader.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{  double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _thread = (Datum*)0; _nt = (_NrnThread*)_pnt->_vnt;   _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t; {
   } }
 
/*VERBATIM*/

#if defined(DISABLE_HDF5) || defined(CORENEURON_BUILD)
  #pragma message("Disabling Synapse Reader since HDF5 is disabled")
  #define DISABLE_SYNTOOL 1
#endif

// If SYN2 becomes default, we can just drop this
#ifndef ENABLE_SYNTOOL
#define DISABLE_SYNTOOL 1
#endif

// Super guard to avoid building mod
#ifdef DISABLE_SYNTOOL
#pragma message("SynapseReader Disabled")
#include <signal.h>

#else  // SynReader Enabled

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <syn2/c_reader.h>

// Internal Enumeration
#define CONN_SYNAPSES_V1 0
#define CONN_GAPJUNCTIONS_V1 1
#define CONN_SYNAPSES_V2 2
#define CONN_GAPJUNCTIONS_V2 3
#define CONN_SYNAPSES_V3 4
#define CONN_CUSTOM 100
// Due to the inability of accessing the state from non-hoc functions, we pass flags in the fieldset
#define CONN_REQUIRE_NRRP (1<<16)
#define CONN_FIELD0_ADD1 (1<<17)


/// NEURON utility functions we want to use
extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
extern double* vector_vec(void* vv);
extern int vector_capacity(void* vv);
extern void* vector_arg(int);


typedef struct {
    syn2_vec_str data;
    int length;
} _Strings;


/// Hold Reader state, such as file handle and info about latest dataset loaded
typedef struct {
    s2id_t file;
    _Strings fieldNames;
    // dataset dependent
    uint64_t gid;  // query gid
    const Syn2Field* fields;
    size_t length;
    int n_fields;
    int conn_type;
} ReaderState;

static const ReaderState STATE_RESET = {-1, {NULL, 0}, UINT64_MAX, NULL, 0, -1};

// state_ptr shortcut. Only usable from within FUNCTIONS
#define getStatePtr() (*((ReaderState**)(&(_p_ptr))))


// The NRN Synapse fields according to SYN2 transitional spec
// ---------------------------------------------------------------------
// | Synapse field name     [ND index] |  Gap-J fields name
// ---------------------------------------------------------------------
//   - connected_neurons_post          | connected_neurons_post (not loaded)
//   0 connected_neurons_pre      [0]  | connected_neurons_pre
//   1 delay                      [1]  | (N/A)
//   2 morpho_section_id_post     [2]  | morpho_section_id_post
//   3 morpho_segment_id_post     [3]  | morpho_section_id_post
//   4 morpho_offset_segment_post [4]  | morpho_section_id_post
//   5 morpho_section_id_pre           | morpho_section_id_pre (unused)
//   6 morpho_segment_id_pre           | morpho_section_id_pre (unused)
//   7 morpho_offset_segment_pre       | morpho_section_id_pre (unused)
//   8 conductance                [5]  | conductance (required)
//   9 u_syn                      [6]  | (N/A)
//  10 depression_time            [7]  | junction_id_pre
//  11 facilitation_time          [8]  | junction_id_post
//  12 decay_time                 [9]  | N/A
//  13 syn_type_id                [10] | N/A
//  14 morpho_type_id_pre              | N/A
//  15 morpho_branch_order_dend        | N/A
//  16 morpho_branch_order_axon        | N/A
//  17 n_rrp_vesicles (optional)  [11] | N/A
//  18 morpho_section_type_pos         | N/A


// The SYN2 v2 spec fields
// : This spec deprecates compat with NRN
// ---------------------------------------------------------------------
// | Synapse field name     [ND index] |  Gap-J fields name
// ---------------------------------------------------------------------
//  connected_neurons_post            | connected_neurons_post (not loaded)
//  connected_neurons_pre        [0]  | connected_neurons_pre
//  delay                        [1]  | (N/A)
//  morpho_section_id_post       [2]  | morpho_section_id_post
//  (N/A)                        [3]  | (N/A)
//  morpho_section_fraction_post [4]  | morpho_section_fraction_post
//  conductance                  [5]  | conductance (required)
//  u_syn                        [6]  | (N/A)
//  depression_time              [7]  | junction_id_pre
//  facilitation_time            [8]  | junction_id_post
//  decay_time                   [9]  | (N/A)
//  syn_type_id                  [10] | (N/A)
//  n_rrp_vesicles  (required)   [11] | (N/A)


// NEUROGLIAL Field Spec  (for reference only)
// -----------------------------------
// | Synapse field name     [ND index]
// -----------------------------------
//  source_node_id     [query field]
//  target_node_id               [0]  !! NOTE: target
//  synapse_id                   [1]
//  morpho_section_id_pre        [2]
//  morpho_segment_id_pre        [3]
//  morpho_offset_segment_pre    [4]


// C99 Use #define for constants
#define ND_FIELD_COUNT 14
#define ND_PREGID_FIELD_I 0

// The 11 mandatory fields read by neurodamus
#define BASE_SYN_FIELDS "connected_neurons_pre, \
                         delay, \
                         morpho_section_id_post, \
                         morpho_segment_id_post, \
                         morpho_offset_segment_post, \
                         conductance, \
                         u_syn, depression_time, facilitation_time, \
                         decay_time, \
                         syn_type_id"

#define NRRP_FIELD "n_rrp_vesicles"
#define POST_FRACTION_FIELD "morpho_section_fraction_post"
#define UHILL_FIELD "u_hill_coefficient"
#define CONDUCTSF_FIELD "conductance_scale_factor"

// The 6 mandatory fields for GapJunctions read by neurodamus
#define GJ_FIELDS "connected_neurons_pre, \
                   morpho_section_id_post, \
                   morpho_segment_id_post, \
                   morpho_offset_segment_post, \
                   conductance, \
                   junction_id_pre, \
                   junction_id_post"

// V2 spec must not attempt to load morpho_section_id_pre
#define SYN_V2_FIELDS "connected_neurons_pre, \
                       delay, \
                       morpho_section_id_post, \
                       morpho_section_fraction_post, \
                       conductance, \
                       u_syn, \
                       depression_time, \
                       facilitation_time, \
                       decay_time, \
                       syn_type_id, \
                       n_rrp_vesicles"

#define GJ_V2_FIELDS "connected_neurons_pre, \
                      morpho_section_id_post, \
                      morpho_section_fraction_post, \
                      conductance, \
                      junction_id_pre, \
                      junction_id_post"


// Internal functions can't call getStatePtr()
#define HAS_NRRP() (_syn_has_field(NRRP_FIELD, getStatePtr()))
#define IS_V2() (_syn_has_field(POST_FRACTION_FIELD, getStatePtr()))
#define IS_V3() (IS_V2() && _syn_has_field(UHILL_FIELD, getStatePtr()) \
                         && _syn_has_field(CONDUCTSF_FIELD, getStatePtr()))

static const char* SYN_FIELDS_NO_RRP = BASE_SYN_FIELDS;
static const char* SYN_FIELDS = BASE_SYN_FIELDS ", " NRRP_FIELD;
static const char* SYN_V3_FIELDS = SYN_V2_FIELDS ", " UHILL_FIELD ", " CONDUCTSF_FIELD;

// relative position of the 7 GJ fields into the ND_FIELD_COUNT-field neurodamus structure
// Conductance is fetched last since its optional
// Why the structure is not packed? Any special meaning for pos 1 and 6?
static const int ND_GJ_POSITIONS[] = {ND_PREGID_FIELD_I, 2, 3, 4, 5, 7, 8};
// V2 relative positions
static const int ND_SYNv2_POSITIONS[] = {0, 1, 2, 4, 5, 6, 7, 8, 9, 10 ,11};
static const int ND_GJv2_POSITIONS[]  = {0, 2, 4, 5, 7, 8};
static const int ND_SYNv3_POSITIONS[] = {0, 1, 2, 4, 5, 6, 7, 8, 9, 10 ,11, 12, 13};


#define CONN_TYPE_POSITIONS(conn_type) \
    (conn_type == CONN_GAPJUNCTIONS_V1)? ND_GJ_POSITIONS \
        : (conn_type == CONN_SYNAPSES_V2)? ND_SYNv2_POSITIONS \
        : (conn_type == CONN_GAPJUNCTIONS_V2)? ND_GJv2_POSITIONS \
        : (conn_type == CONN_SYNAPSES_V3)? ND_SYNv3_POSITIONS \
        : NULL


/**
 * INTERNAL FUNCTIONS
 * ------------------
 *
 * These functions are pure-c, not available from the hoc interface,
 * As so the only way to access state_ptr is to receive it by argument
 */

static int _syn_is_empty(ReaderState* state_ptr) {
    return state_ptr->fields == NULL;
}


static _Strings _getFieldNames(ReaderState* state_ptr) {
    if (state_ptr->fieldNames.data == NULL) {
        const Syn2Dataset names_ds = syn_list_property_names(state_ptr->file);
        state_ptr->fieldNames.data = as_str_array(names_ds.data);
        state_ptr->fieldNames.length = names_ds.length;
    }
    return state_ptr->fieldNames;
}


static int _syn_has_field(const char* field_name, ReaderState* state_ptr) {
    const _Strings names_ds = _getFieldNames(state_ptr);
    syn2_vec_str names = names_ds.data;

    int i;
    for (i=0; i < names_ds.length; i++) {
        if (strcmp(names[i], field_name) == 0)
            return 1;
    }
    return 0;
}


/// Store table results to internal state object
static int _store_result(uint64_t tgid, const Syn2Table *tb, ReaderState* state_ptr)  {
    state_ptr->gid = tgid;
    // "tb.fields" might be NULL if there is no data. Ok as long length is zero.
    state_ptr->fields = tb->fields;
    state_ptr->length = tb->length;
    state_ptr->n_fields = tb->n_fields;
    return tb->length;
}


#define COPY_SYN2_VECTOR(type, src, dst, length) \
    for (i=0; i < length; ++i) \
        dst[i] = as_##type##_array(src)[i]; \

static const double* to_double_vec(const Syn2Field *field, size_t n_rows, double* output) {
    int i;
    switch(field->datatype) {
    case SYN2_UINT:
        COPY_SYN2_VECTOR(uint, field->data, output, n_rows);
        break;
    case SYN2_INT:
        COPY_SYN2_VECTOR(int, field->data, output, n_rows);
        break;
    case SYN2_FLOAT:
        COPY_SYN2_VECTOR(float, field->data, output, n_rows);
        break;
    case SYN2_DOUBLE:
        memcpy(output, field->data, n_rows * sizeof(double));
        break;
    }
    return output;
}


/**
 * Loads data from synapse file into internal state.
 *
 * @param tgid: The gid of the post cell to load connectivity
 * @param pre_gid_instead: use given gid to filter by source gid instead
 * @param conn_type: The type of connectivity/fielset to load
 * @param fields: custom string of fields in case FIELDSET_CUSTOM specified
 */
static int _load_data(uint64_t tgid,
                      int pre_gid_instead,
                      int conn_type,
                      const char* fields,
                      ReaderState* state_ptr) {
    if (state_ptr->file == -1)  {
        fprintf(stderr, "[SynReader] Error: File not initialized.\n");
        raise(SIGUSR2);
    }

    const int base_conn_type = conn_type & 0xffff;
    switch(base_conn_type) {
        case CONN_SYNAPSES_V1:
            fields = (conn_type & CONN_REQUIRE_NRRP)? SYN_FIELDS : SYN_FIELDS_NO_RRP;
            break;
        case CONN_SYNAPSES_V2:
            fields = SYN_V2_FIELDS;
            break;
        case CONN_GAPJUNCTIONS_V1:
            fields = GJ_FIELDS;
            break;
        case CONN_GAPJUNCTIONS_V2:
            fields = GJ_V2_FIELDS;
            break;
        case CONN_SYNAPSES_V3:
            fields = SYN_V3_FIELDS;
            break;
        default:
            if (fields == NULL) {
                fprintf(stderr, "[SynReader] Error: FIELDSET_CUSTOM requested but no fields provided.\n");
                raise(SIGUSR2);
            }
    }

    // Already loaded?
    if (tgid == state_ptr->gid && conn_type == state_ptr->conn_type) {
        // Not knowing prev names, check at least the number of fields is same
        char* fields_str = (char*) fields;
        int n_fields_requested = 1;
        while ((fields_str=strchr(fields_str+1, ',')) != NULL) {
            n_fields_requested++;
        }
        if (state_ptr->n_fields == n_fields_requested) {
            return state_ptr->length;
        }
    }

    // NeuroGlial is probably the only case we query by source gid (of the Glia)
    const Syn2Selection sel = pre_gid_instead ? syn_select_pre(tgid)
                                              : syn_select_post(tgid);

    const Syn2Table tb = syn_get_property_table(state_ptr->file, fields, sel);

    state_ptr->conn_type = conn_type;
    return _store_result(tgid, &tb, state_ptr);
}

#endif  // SYNTOOL


//////////////////////////////////////////////////////////////////////
/// NMOD Methods
//////////////////////////////////////////////////////////////////////
 
double modEnabled ( _threadargsproto_ ) {
   double _lmodEnabled;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    return 1;
#else
    return 0;
#endif
 
return _lmodEnabled;
 }
 
static double _hoc_modEnabled(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  modEnabled ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double countProperties ( _threadargsproto_ ) {
   double _lcountProperties;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    const _Strings names_ds = _getFieldNames(getStatePtr());
    return names_ds.length;
#endif
 
return _lcountProperties;
 }
 
static double _hoc_countProperties(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  countProperties ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double hasProperty ( _threadargsproto_ ) {
   double _lhasProperty;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    return _syn_has_field(gargstr(1), getStatePtr());
#endif
 
return _lhasProperty;
 }
 
static double _hoc_hasProperty(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  hasProperty ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double countSynapses ( _threadargsproto_ ) {
   double _lcountSynapses;
 
/*VERBATIM*/
{
#ifndef DISABLE_SYNTOOL
    return syn_get_number_synapses(getStatePtr()->file);
#endif
}
 
return _lcountSynapses;
 }
 
static double _hoc_countSynapses(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  countSynapses ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double selectPopulation ( _threadargsproto_ ) {
   double _lselectPopulation;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    return syn_select_population(getStatePtr()->file, gargstr(1));
#endif
 
return _lselectPopulation;
 }
 
static double _hoc_selectPopulation(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  selectPopulation ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double hasNrrpField ( _threadargsproto_ ) {
   double _lhasNrrpField;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    return HAS_NRRP();
#else
    return -1;
#endif
 
return _lhasNrrpField;
 }
 
static double _hoc_hasNrrpField(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  hasNrrpField ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double isV2 ( _threadargsproto_ ) {
   double _lisV2;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    return IS_V2();
#else
    return -1;
#endif
 
return _lisV2;
 }
 
static double _hoc_isV2(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  isV2 ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double loadSynapses ( _threadargsproto_ ) {
   double _lloadSynapses;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    uint64_t tgid = (uint64_t) *getarg(1) - 1;  // 0 based
    const char* fields = ifarg(2)? gargstr(2): NULL;
    int fieldset = (fields != NULL)? CONN_CUSTOM
                   : IS_V3()? CONN_SYNAPSES_V3
                   : IS_V2()? CONN_SYNAPSES_V2
                   : CONN_SYNAPSES_V1 + (HAS_NRRP()? CONN_REQUIRE_NRRP : 0);
    return _load_data(tgid, 0, fieldset | CONN_FIELD0_ADD1, fields, getStatePtr());
#else
    fprintf(stderr, "[SynReader] Error: Neurodamus compiled without SYNTOOL\n");
    raise(SIGUSR1);
#endif
 
return _lloadSynapses;
 }
 
static double _hoc_loadSynapses(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  loadSynapses ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double loadGapJunctions ( _threadargsproto_ ) {
   double _lloadGapJunctions;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    uint64_t tgid = (uint64_t) *getarg(1) - 1;  // 0 based
    const char* fields = ifarg(2)? gargstr(2): NULL;
    int fieldset = (fields != NULL)? CONN_CUSTOM
                   : IS_V2()? CONN_GAPJUNCTIONS_V2 : CONN_GAPJUNCTIONS_V1;
    return _load_data(tgid, 0, fieldset | CONN_FIELD0_ADD1, fields, getStatePtr());
#else
    fprintf(stderr, "[SynReader] Error: Neurodamus compiled without SYNTOOL\n");
    raise(SIGUSR1);
#endif
 
return _lloadGapJunctions;
 }
 
static double _hoc_loadGapJunctions(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  loadGapJunctions ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double loadSynapseCustom ( _threadargsproto_ ) {
   double _lloadSynapseCustom;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    const uint64_t gid = (uint64_t) *getarg(1) - 1;  // 0 based
    const char* const fields = gargstr(2);
    const int pre_gid_instead = (ifarg(3) && *getarg(3));
    // If first field is a GID then activate ADD1
    int fieldset = CONN_CUSTOM
        + ((strncmp(fields, "connected_neurons_", 18) == 0)? CONN_FIELD0_ADD1 : 0);
    return _load_data(gid, pre_gid_instead, fieldset, fields, getStatePtr());
#endif
 
return _lloadSynapseCustom;
 }
 
static double _hoc_loadSynapseCustom(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  loadSynapseCustom ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double getSynapse ( _threadargsproto_ ) {
   double _lgetSynapse;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    if (!ifarg(1) || !ifarg(2)) {
        fprintf(stderr, "[SynReader] Error: Function requires two arguments: "
                        "1. synapse index (row) to retrieve; 2. Destination Vector\n");
        raise(SIGUSR2);
    }

    ReaderState* const state_ptr = getStatePtr();

    if (_syn_is_empty(state_ptr)) {
        fprintf(stderr, "[SynReader] Error: No synapse data. Please load synapses first.\n");
        raise(SIGUSR2);
    }

    int i, dst_i;
    const unsigned int row = *getarg(1);
    void* const xd = vector_arg(2);
    const int fill_mode = ifarg(3)? (int)*getarg(3): 0;


    const int loaded_conn_type = state_ptr->conn_type & 0xffff;
    const int n_fields = state_ptr->n_fields;
    const Syn2Field* const fields = state_ptr->fields;
    const int target_vec_size = (loaded_conn_type == CONN_CUSTOM)? n_fields
                                                                 : ND_FIELD_COUNT;
    if (! fill_mode || vector_capacity(xd) < target_vec_size) {
        vector_resize(xd, target_vec_size);   // shrink keeps buffer
    }
    double * const out_buf = vector_vec(xd);  // Get pointer after eventual resize

    // init to -1 (due to holes in gjs)
    for(i=0; i < target_vec_size; i++) {
        out_buf[i] = -1;
    }

    // Except for Synapses v1 and Custom, we have to translate fields position
    const int * const field_pos = CONN_TYPE_POSITIONS(loaded_conn_type);

    for (i=0; i<n_fields; i++) {
        dst_i = (field_pos != NULL)? field_pos[i] : i;
        switch(fields[i].datatype) {
        case SYN2_UINT:
            out_buf[dst_i] = (double) as_uint_array(fields[i].data)[row];
            break;
        case SYN2_INT:
            out_buf[dst_i] = (double) as_int_array(fields[i].data)[row];
            break;
        case SYN2_FLOAT:
            out_buf[dst_i] = (double) as_float_array(fields[i].data)[row];
            break;
        case SYN2_DOUBLE:
            out_buf[dst_i] = (double) as_double_array(fields[i].data)[row];
            break;
        }
    }

    // pre/post-gid (field 0) must be incremented by 1 for neurodamus compat
    if(state_ptr->conn_type & CONN_FIELD0_ADD1) {
        out_buf[0] += 1;
    }

    return 0;
#endif
 
return _lgetSynapse;
 }
 
static double _hoc_getSynapse(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  getSynapse ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
double getPropertyData ( _threadargsproto_ ) {
   double _lgetPropertyData;
 
/*VERBATIM*/
#ifndef DISABLE_SYNTOOL
    if (!ifarg(1) || !ifarg(2)) {
        fprintf(stderr, "[SynReader] Error: Function requires two arguments: "
                        "1. property index (column) to retrieve; 2. Destination Vector\n");
        raise(SIGUSR2);
    }

    ReaderState* const state_ptr = getStatePtr();
    const int loaded_conn_type = state_ptr->conn_type & 0xffff;
    const unsigned int column = *getarg(1);
    void* const xd = vector_arg(2);

    const int * const field_pos = CONN_TYPE_POSITIONS(loaded_conn_type);
    const int field_i = (field_pos != NULL)? field_pos[column] : column;
    const Syn2Field field = state_ptr->fields[field_i];

    vector_resize(xd, state_ptr->length);  // shinking is almost no-op
    double * const vec_buffer = vector_vec(xd);
    to_double_vec(&field, state_ptr->length, vec_buffer);

    // In case field 0 asked "add1" (for gids) then apply it
    if (column == 0 && (state_ptr->conn_type & CONN_FIELD0_ADD1)) {
        int i;
        for (i=0; i < state_ptr->length; i++) {
            vec_buffer[i]++;
        }
    }

#endif
 
return _lgetPropertyData;
 }
 
static double _hoc_getPropertyData(void* _vptr) {
 double _r;
   double* _p; Datum* _ppvar; Datum* _thread; _NrnThread* _nt;
   _p = ((Point_process*)_vptr)->_prop->param;
  _ppvar = ((Point_process*)_vptr)->_prop->dparam;
  _thread = _extcall_thread;
  _nt = (_NrnThread*)((Point_process*)_vptr)->_vnt;
 _r =  getPropertyData ( _p, _ppvar, _thread, _nt );
 return(_r);
}
 
/*VERBATIM*/
/** not executed in coreneuron and hence empty stubs sufficient */
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
#ifndef DISABLE_SYNTOOL
    ReaderState rs = STATE_RESET;
    if (!ifarg(1)) {
        getStatePtr() = NULL;
        return;
    }

    if (!hoc_is_str_arg(1)) {
        fprintf(stderr, "[SynReader] Error: SynapseReader filename must be a string\n");
        raise(SIGUSR2);
    }

    if (ifarg(2)) {
        verboseLevel = *getarg(2);
        syn_set_verbose(verboseLevel);
    }

    // normal case - open a file and be ready to load data as needed
    rs.file = syn_open(gargstr(1));

    ReaderState* state_ptr = (ReaderState*) malloc(sizeof(ReaderState));
    *state_ptr = rs;
    // use macro to get the pointer, write new address
    getStatePtr() = state_ptr;

#endif
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
#ifndef DISABLE_SYNTOOL
    // state_ptr shall never be NULL since we attemp to follow RAII. The only exceptions are
    //  - for Save-State, when Neuron recreates the mechs without params
    //  - In SynReaders.hoc to know whether Synapsetool is available
    ReaderState* state_ptr = getStatePtr();
    if (state_ptr) {
        syn_close(state_ptr->file);
        free(state_ptr);
    }
#endif
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
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/SynapseReader.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file syn2reader.mod\n"
  " * @brief A Reader for Synapse files, inc Nrn and SYN2\n"
  " * @author F. Pereira\n"
  " * @date 2018-06\n"
  " * @remark Copyright (C) 2018 EPFL - Blue Brain Project\n"
  " * All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "COMMENT\n"
  "Read Synapse file sources using synapse-tool\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    ARTIFICIAL_CELL SynapseReader\n"
  "    THREADSAFE\n"
  "    BBCOREPOINTER ptr\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "    ptr\n"
  "    verboseLevel\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "}\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "\n"
  "#if defined(DISABLE_HDF5) || defined(CORENEURON_BUILD)\n"
  "  #pragma message(\"Disabling Synapse Reader since HDF5 is disabled\")\n"
  "  #define DISABLE_SYNTOOL 1\n"
  "#endif\n"
  "\n"
  "// If SYN2 becomes default, we can just drop this\n"
  "#ifndef ENABLE_SYNTOOL\n"
  "#define DISABLE_SYNTOOL 1\n"
  "#endif\n"
  "\n"
  "// Super guard to avoid building mod\n"
  "#ifdef DISABLE_SYNTOOL\n"
  "#pragma message(\"SynapseReader Disabled\")\n"
  "#include <signal.h>\n"
  "\n"
  "#else  // SynReader Enabled\n"
  "\n"
  "#include <stdint.h>\n"
  "#include <stdio.h>\n"
  "#include <string.h>\n"
  "#include <signal.h>\n"
  "#include <syn2/c_reader.h>\n"
  "\n"
  "// Internal Enumeration\n"
  "#define CONN_SYNAPSES_V1 0\n"
  "#define CONN_GAPJUNCTIONS_V1 1\n"
  "#define CONN_SYNAPSES_V2 2\n"
  "#define CONN_GAPJUNCTIONS_V2 3\n"
  "#define CONN_SYNAPSES_V3 4\n"
  "#define CONN_CUSTOM 100\n"
  "// Due to the inability of accessing the state from non-hoc functions, we pass flags in the fieldset\n"
  "#define CONN_REQUIRE_NRRP (1<<16)\n"
  "#define CONN_FIELD0_ADD1 (1<<17)\n"
  "\n"
  "\n"
  "/// NEURON utility functions we want to use\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int nrnmpi_numprocs;\n"
  "extern int nrnmpi_myid;\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "extern double* vector_vec(void* vv);\n"
  "extern int vector_capacity(void* vv);\n"
  "extern void* vector_arg(int);\n"
  "\n"
  "\n"
  "typedef struct {\n"
  "    syn2_vec_str data;\n"
  "    int length;\n"
  "} _Strings;\n"
  "\n"
  "\n"
  "/// Hold Reader state, such as file handle and info about latest dataset loaded\n"
  "typedef struct {\n"
  "    s2id_t file;\n"
  "    _Strings fieldNames;\n"
  "    // dataset dependent\n"
  "    uint64_t gid;  // query gid\n"
  "    const Syn2Field* fields;\n"
  "    size_t length;\n"
  "    int n_fields;\n"
  "    int conn_type;\n"
  "} ReaderState;\n"
  "\n"
  "static const ReaderState STATE_RESET = {-1, {NULL, 0}, UINT64_MAX, NULL, 0, -1};\n"
  "\n"
  "// state_ptr shortcut. Only usable from within FUNCTIONS\n"
  "#define getStatePtr() (*((ReaderState**)(&(_p_ptr))))\n"
  "\n"
  "\n"
  "// The NRN Synapse fields according to SYN2 transitional spec\n"
  "// ---------------------------------------------------------------------\n"
  "// | Synapse field name     [ND index] |  Gap-J fields name\n"
  "// ---------------------------------------------------------------------\n"
  "//   - connected_neurons_post          | connected_neurons_post (not loaded)\n"
  "//   0 connected_neurons_pre      [0]  | connected_neurons_pre\n"
  "//   1 delay                      [1]  | (N/A)\n"
  "//   2 morpho_section_id_post     [2]  | morpho_section_id_post\n"
  "//   3 morpho_segment_id_post     [3]  | morpho_section_id_post\n"
  "//   4 morpho_offset_segment_post [4]  | morpho_section_id_post\n"
  "//   5 morpho_section_id_pre           | morpho_section_id_pre (unused)\n"
  "//   6 morpho_segment_id_pre           | morpho_section_id_pre (unused)\n"
  "//   7 morpho_offset_segment_pre       | morpho_section_id_pre (unused)\n"
  "//   8 conductance                [5]  | conductance (required)\n"
  "//   9 u_syn                      [6]  | (N/A)\n"
  "//  10 depression_time            [7]  | junction_id_pre\n"
  "//  11 facilitation_time          [8]  | junction_id_post\n"
  "//  12 decay_time                 [9]  | N/A\n"
  "//  13 syn_type_id                [10] | N/A\n"
  "//  14 morpho_type_id_pre              | N/A\n"
  "//  15 morpho_branch_order_dend        | N/A\n"
  "//  16 morpho_branch_order_axon        | N/A\n"
  "//  17 n_rrp_vesicles (optional)  [11] | N/A\n"
  "//  18 morpho_section_type_pos         | N/A\n"
  "\n"
  "\n"
  "// The SYN2 v2 spec fields\n"
  "// : This spec deprecates compat with NRN\n"
  "// ---------------------------------------------------------------------\n"
  "// | Synapse field name     [ND index] |  Gap-J fields name\n"
  "// ---------------------------------------------------------------------\n"
  "//  connected_neurons_post            | connected_neurons_post (not loaded)\n"
  "//  connected_neurons_pre        [0]  | connected_neurons_pre\n"
  "//  delay                        [1]  | (N/A)\n"
  "//  morpho_section_id_post       [2]  | morpho_section_id_post\n"
  "//  (N/A)                        [3]  | (N/A)\n"
  "//  morpho_section_fraction_post [4]  | morpho_section_fraction_post\n"
  "//  conductance                  [5]  | conductance (required)\n"
  "//  u_syn                        [6]  | (N/A)\n"
  "//  depression_time              [7]  | junction_id_pre\n"
  "//  facilitation_time            [8]  | junction_id_post\n"
  "//  decay_time                   [9]  | (N/A)\n"
  "//  syn_type_id                  [10] | (N/A)\n"
  "//  n_rrp_vesicles  (required)   [11] | (N/A)\n"
  "\n"
  "\n"
  "// NEUROGLIAL Field Spec  (for reference only)\n"
  "// -----------------------------------\n"
  "// | Synapse field name     [ND index]\n"
  "// -----------------------------------\n"
  "//  source_node_id     [query field]\n"
  "//  target_node_id               [0]  !! NOTE: target\n"
  "//  synapse_id                   [1]\n"
  "//  morpho_section_id_pre        [2]\n"
  "//  morpho_segment_id_pre        [3]\n"
  "//  morpho_offset_segment_pre    [4]\n"
  "\n"
  "\n"
  "// C99 Use #define for constants\n"
  "#define ND_FIELD_COUNT 14\n"
  "#define ND_PREGID_FIELD_I 0\n"
  "\n"
  "// The 11 mandatory fields read by neurodamus\n"
  "#define BASE_SYN_FIELDS \"connected_neurons_pre, \\\n"
  "                         delay, \\\n"
  "                         morpho_section_id_post, \\\n"
  "                         morpho_segment_id_post, \\\n"
  "                         morpho_offset_segment_post, \\\n"
  "                         conductance, \\\n"
  "                         u_syn, depression_time, facilitation_time, \\\n"
  "                         decay_time, \\\n"
  "                         syn_type_id\"\n"
  "\n"
  "#define NRRP_FIELD \"n_rrp_vesicles\"\n"
  "#define POST_FRACTION_FIELD \"morpho_section_fraction_post\"\n"
  "#define UHILL_FIELD \"u_hill_coefficient\"\n"
  "#define CONDUCTSF_FIELD \"conductance_scale_factor\"\n"
  "\n"
  "// The 6 mandatory fields for GapJunctions read by neurodamus\n"
  "#define GJ_FIELDS \"connected_neurons_pre, \\\n"
  "                   morpho_section_id_post, \\\n"
  "                   morpho_segment_id_post, \\\n"
  "                   morpho_offset_segment_post, \\\n"
  "                   conductance, \\\n"
  "                   junction_id_pre, \\\n"
  "                   junction_id_post\"\n"
  "\n"
  "// V2 spec must not attempt to load morpho_section_id_pre\n"
  "#define SYN_V2_FIELDS \"connected_neurons_pre, \\\n"
  "                       delay, \\\n"
  "                       morpho_section_id_post, \\\n"
  "                       morpho_section_fraction_post, \\\n"
  "                       conductance, \\\n"
  "                       u_syn, \\\n"
  "                       depression_time, \\\n"
  "                       facilitation_time, \\\n"
  "                       decay_time, \\\n"
  "                       syn_type_id, \\\n"
  "                       n_rrp_vesicles\"\n"
  "\n"
  "#define GJ_V2_FIELDS \"connected_neurons_pre, \\\n"
  "                      morpho_section_id_post, \\\n"
  "                      morpho_section_fraction_post, \\\n"
  "                      conductance, \\\n"
  "                      junction_id_pre, \\\n"
  "                      junction_id_post\"\n"
  "\n"
  "\n"
  "// Internal functions can't call getStatePtr()\n"
  "#define HAS_NRRP() (_syn_has_field(NRRP_FIELD, getStatePtr()))\n"
  "#define IS_V2() (_syn_has_field(POST_FRACTION_FIELD, getStatePtr()))\n"
  "#define IS_V3() (IS_V2() && _syn_has_field(UHILL_FIELD, getStatePtr()) \\\n"
  "                         && _syn_has_field(CONDUCTSF_FIELD, getStatePtr()))\n"
  "\n"
  "static const char* SYN_FIELDS_NO_RRP = BASE_SYN_FIELDS;\n"
  "static const char* SYN_FIELDS = BASE_SYN_FIELDS \", \" NRRP_FIELD;\n"
  "static const char* SYN_V3_FIELDS = SYN_V2_FIELDS \", \" UHILL_FIELD \", \" CONDUCTSF_FIELD;\n"
  "\n"
  "// relative position of the 7 GJ fields into the ND_FIELD_COUNT-field neurodamus structure\n"
  "// Conductance is fetched last since its optional\n"
  "// Why the structure is not packed? Any special meaning for pos 1 and 6?\n"
  "static const int ND_GJ_POSITIONS[] = {ND_PREGID_FIELD_I, 2, 3, 4, 5, 7, 8};\n"
  "// V2 relative positions\n"
  "static const int ND_SYNv2_POSITIONS[] = {0, 1, 2, 4, 5, 6, 7, 8, 9, 10 ,11};\n"
  "static const int ND_GJv2_POSITIONS[]  = {0, 2, 4, 5, 7, 8};\n"
  "static const int ND_SYNv3_POSITIONS[] = {0, 1, 2, 4, 5, 6, 7, 8, 9, 10 ,11, 12, 13};\n"
  "\n"
  "\n"
  "#define CONN_TYPE_POSITIONS(conn_type) \\\n"
  "    (conn_type == CONN_GAPJUNCTIONS_V1)? ND_GJ_POSITIONS \\\n"
  "        : (conn_type == CONN_SYNAPSES_V2)? ND_SYNv2_POSITIONS \\\n"
  "        : (conn_type == CONN_GAPJUNCTIONS_V2)? ND_GJv2_POSITIONS \\\n"
  "        : (conn_type == CONN_SYNAPSES_V3)? ND_SYNv3_POSITIONS \\\n"
  "        : NULL\n"
  "\n"
  "\n"
  "/**\n"
  " * INTERNAL FUNCTIONS\n"
  " * ------------------\n"
  " *\n"
  " * These functions are pure-c, not available from the hoc interface,\n"
  " * As so the only way to access state_ptr is to receive it by argument\n"
  " */\n"
  "\n"
  "static int _syn_is_empty(ReaderState* state_ptr) {\n"
  "    return state_ptr->fields == NULL;\n"
  "}\n"
  "\n"
  "\n"
  "static _Strings _getFieldNames(ReaderState* state_ptr) {\n"
  "    if (state_ptr->fieldNames.data == NULL) {\n"
  "        const Syn2Dataset names_ds = syn_list_property_names(state_ptr->file);\n"
  "        state_ptr->fieldNames.data = as_str_array(names_ds.data);\n"
  "        state_ptr->fieldNames.length = names_ds.length;\n"
  "    }\n"
  "    return state_ptr->fieldNames;\n"
  "}\n"
  "\n"
  "\n"
  "static int _syn_has_field(const char* field_name, ReaderState* state_ptr) {\n"
  "    const _Strings names_ds = _getFieldNames(state_ptr);\n"
  "    syn2_vec_str names = names_ds.data;\n"
  "\n"
  "    int i;\n"
  "    for (i=0; i < names_ds.length; i++) {\n"
  "        if (strcmp(names[i], field_name) == 0)\n"
  "            return 1;\n"
  "    }\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "/// Store table results to internal state object\n"
  "static int _store_result(uint64_t tgid, const Syn2Table *tb, ReaderState* state_ptr)  {\n"
  "    state_ptr->gid = tgid;\n"
  "    // \"tb.fields\" might be NULL if there is no data. Ok as long length is zero.\n"
  "    state_ptr->fields = tb->fields;\n"
  "    state_ptr->length = tb->length;\n"
  "    state_ptr->n_fields = tb->n_fields;\n"
  "    return tb->length;\n"
  "}\n"
  "\n"
  "\n"
  "#define COPY_SYN2_VECTOR(type, src, dst, length) \\\n"
  "    for (i=0; i < length; ++i) \\\n"
  "        dst[i] = as_##type##_array(src)[i]; \\\n"
  "\n"
  "static const double* to_double_vec(const Syn2Field *field, size_t n_rows, double* output) {\n"
  "    int i;\n"
  "    switch(field->datatype) {\n"
  "    case SYN2_UINT:\n"
  "        COPY_SYN2_VECTOR(uint, field->data, output, n_rows);\n"
  "        break;\n"
  "    case SYN2_INT:\n"
  "        COPY_SYN2_VECTOR(int, field->data, output, n_rows);\n"
  "        break;\n"
  "    case SYN2_FLOAT:\n"
  "        COPY_SYN2_VECTOR(float, field->data, output, n_rows);\n"
  "        break;\n"
  "    case SYN2_DOUBLE:\n"
  "        memcpy(output, field->data, n_rows * sizeof(double));\n"
  "        break;\n"
  "    }\n"
  "    return output;\n"
  "}\n"
  "\n"
  "\n"
  "/**\n"
  " * Loads data from synapse file into internal state.\n"
  " *\n"
  " * @param tgid: The gid of the post cell to load connectivity\n"
  " * @param pre_gid_instead: use given gid to filter by source gid instead\n"
  " * @param conn_type: The type of connectivity/fielset to load\n"
  " * @param fields: custom string of fields in case FIELDSET_CUSTOM specified\n"
  " */\n"
  "static int _load_data(uint64_t tgid,\n"
  "                      int pre_gid_instead,\n"
  "                      int conn_type,\n"
  "                      const char* fields,\n"
  "                      ReaderState* state_ptr) {\n"
  "    if (state_ptr->file == -1)  {\n"
  "        fprintf(stderr, \"[SynReader] Error: File not initialized.\\n\");\n"
  "        raise(SIGUSR2);\n"
  "    }\n"
  "\n"
  "    const int base_conn_type = conn_type & 0xffff;\n"
  "    switch(base_conn_type) {\n"
  "        case CONN_SYNAPSES_V1:\n"
  "            fields = (conn_type & CONN_REQUIRE_NRRP)? SYN_FIELDS : SYN_FIELDS_NO_RRP;\n"
  "            break;\n"
  "        case CONN_SYNAPSES_V2:\n"
  "            fields = SYN_V2_FIELDS;\n"
  "            break;\n"
  "        case CONN_GAPJUNCTIONS_V1:\n"
  "            fields = GJ_FIELDS;\n"
  "            break;\n"
  "        case CONN_GAPJUNCTIONS_V2:\n"
  "            fields = GJ_V2_FIELDS;\n"
  "            break;\n"
  "        case CONN_SYNAPSES_V3:\n"
  "            fields = SYN_V3_FIELDS;\n"
  "            break;\n"
  "        default:\n"
  "            if (fields == NULL) {\n"
  "                fprintf(stderr, \"[SynReader] Error: FIELDSET_CUSTOM requested but no fields provided.\\n\");\n"
  "                raise(SIGUSR2);\n"
  "            }\n"
  "    }\n"
  "\n"
  "    // Already loaded?\n"
  "    if (tgid == state_ptr->gid && conn_type == state_ptr->conn_type) {\n"
  "        // Not knowing prev names, check at least the number of fields is same\n"
  "        char* fields_str = (char*) fields;\n"
  "        int n_fields_requested = 1;\n"
  "        while ((fields_str=strchr(fields_str+1, ',')) != NULL) {\n"
  "            n_fields_requested++;\n"
  "        }\n"
  "        if (state_ptr->n_fields == n_fields_requested) {\n"
  "            return state_ptr->length;\n"
  "        }\n"
  "    }\n"
  "\n"
  "    // NeuroGlial is probably the only case we query by source gid (of the Glia)\n"
  "    const Syn2Selection sel = pre_gid_instead ? syn_select_pre(tgid)\n"
  "                                              : syn_select_post(tgid);\n"
  "\n"
  "    const Syn2Table tb = syn_get_property_table(state_ptr->file, fields, sel);\n"
  "\n"
  "    state_ptr->conn_type = conn_type;\n"
  "    return _store_result(tgid, &tb, state_ptr);\n"
  "}\n"
  "\n"
  "#endif  // SYNTOOL\n"
  "\n"
  "\n"
  "//////////////////////////////////////////////////////////////////////\n"
  "/// NMOD Methods\n"
  "//////////////////////////////////////////////////////////////////////\n"
  "ENDVERBATIM\n"
  "\n"
  "CONSTRUCTOR { : string filepath\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    ReaderState rs = STATE_RESET;\n"
  "    if (!ifarg(1)) {\n"
  "        getStatePtr() = NULL;\n"
  "        return;\n"
  "    }\n"
  "\n"
  "    if (!hoc_is_str_arg(1)) {\n"
  "        fprintf(stderr, \"[SynReader] Error: SynapseReader filename must be a string\\n\");\n"
  "        raise(SIGUSR2);\n"
  "    }\n"
  "\n"
  "    if (ifarg(2)) {\n"
  "        verboseLevel = *getarg(2);\n"
  "        syn_set_verbose(verboseLevel);\n"
  "    }\n"
  "\n"
  "    // normal case - open a file and be ready to load data as needed\n"
  "    rs.file = syn_open(gargstr(1));\n"
  "\n"
  "    ReaderState* state_ptr = (ReaderState*) malloc(sizeof(ReaderState));\n"
  "    *state_ptr = rs;\n"
  "    // use macro to get the pointer, write new address\n"
  "    getStatePtr() = state_ptr;\n"
  "\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    // state_ptr shall never be NULL since we attemp to follow RAII. The only exceptions are\n"
  "    //  - for Save-State, when Neuron recreates the mechs without params\n"
  "    //  - In SynReaders.hoc to know whether Synapsetool is available\n"
  "    ReaderState* state_ptr = getStatePtr();\n"
  "    if (state_ptr) {\n"
  "        syn_close(state_ptr->file);\n"
  "        free(state_ptr);\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION modEnabled() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return 1;\n"
  "#else\n"
  "    return 0;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION countProperties(){\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    const _Strings names_ds = _getFieldNames(getStatePtr());\n"
  "    return names_ds.length;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION hasProperty(){\n"
  "    :param 1: (string) The name of the property to check existence\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return _syn_has_field(gargstr(1), getStatePtr());\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION countSynapses() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return syn_get_number_synapses(getStatePtr()->file);\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION selectPopulation() {\n"
  "    :param 1: (string) The name of the population to open\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return syn_select_population(getStatePtr()->file, gargstr(1));\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION hasNrrpField() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return HAS_NRRP();\n"
  "#else\n"
  "    return -1;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION isV2() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    return IS_V2();\n"
  "#else\n"
  "    return -1;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/** Loads synapse data from file into memory, all common fields required by neurodamus\n"
  " *\n"
  " * @param post_gid. The post gid to filter\n"
  " * @param string (optional) fields to load. Default: the ND_FIELD_COUNT fields defined above\n"
  " * @return number of synapses read. -1 if error\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION loadSynapses() { : double tgid, string fields\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    uint64_t tgid = (uint64_t) *getarg(1) - 1;  // 0 based\n"
  "    const char* fields = ifarg(2)? gargstr(2): NULL;\n"
  "    int fieldset = (fields != NULL)? CONN_CUSTOM\n"
  "                   : IS_V3()? CONN_SYNAPSES_V3\n"
  "                   : IS_V2()? CONN_SYNAPSES_V2\n"
  "                   : CONN_SYNAPSES_V1 + (HAS_NRRP()? CONN_REQUIRE_NRRP : 0);\n"
  "    return _load_data(tgid, 0, fieldset | CONN_FIELD0_ADD1, fields, getStatePtr());\n"
  "#else\n"
  "    fprintf(stderr, \"[SynReader] Error: Neurodamus compiled without SYNTOOL\\n\");\n"
  "    raise(SIGUSR1);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/// Load Gap-Junctions with Synapsetool\n"
  "ENDCOMMENT\n"
  "FUNCTION loadGapJunctions() { : double tgid, string fields\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    uint64_t tgid = (uint64_t) *getarg(1) - 1;  // 0 based\n"
  "    const char* fields = ifarg(2)? gargstr(2): NULL;\n"
  "    int fieldset = (fields != NULL)? CONN_CUSTOM\n"
  "                   : IS_V2()? CONN_GAPJUNCTIONS_V2 : CONN_GAPJUNCTIONS_V1;\n"
  "    return _load_data(tgid, 0, fieldset | CONN_FIELD0_ADD1, fields, getStatePtr());\n"
  "#else\n"
  "    fprintf(stderr, \"[SynReader] Error: Neurodamus compiled without SYNTOOL\\n\");\n"
  "    raise(SIGUSR1);\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/** Load a custom set of fields from the synapse file.\n"
  " *\n"
  " * @param 1: (double) The gid to query by, normally target gid\n"
  " * @param 2: (string) Fields\n"
  " * @param 3: (optional, bool) Query by source gid instead of target\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION loadSynapseCustom() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    const uint64_t gid = (uint64_t) *getarg(1) - 1;  // 0 based\n"
  "    const char* const fields = gargstr(2);\n"
  "    const int pre_gid_instead = (ifarg(3) && *getarg(3));\n"
  "    // If first field is a GID then activate ADD1\n"
  "    int fieldset = CONN_CUSTOM\n"
  "        + ((strncmp(fields, \"connected_neurons_\", 18) == 0)? CONN_FIELD0_ADD1 : 0);\n"
  "    return _load_data(gid, pre_gid_instead, fieldset, fields, getStatePtr());\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/** Retrieve one synape data (row) from the loaded dataset\n"
  " *\n"
  " * @param 1 The index of the synapse to retrieve\n"
  " * @param 2 The vector to hold the result data\n"
  " * @param 3 Fill mode, dont resize the vector (Default: false)\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION getSynapse() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    if (!ifarg(1) || !ifarg(2)) {\n"
  "        fprintf(stderr, \"[SynReader] Error: Function requires two arguments: \"\n"
  "                        \"1. synapse index (row) to retrieve; 2. Destination Vector\\n\");\n"
  "        raise(SIGUSR2);\n"
  "    }\n"
  "\n"
  "    ReaderState* const state_ptr = getStatePtr();\n"
  "\n"
  "    if (_syn_is_empty(state_ptr)) {\n"
  "        fprintf(stderr, \"[SynReader] Error: No synapse data. Please load synapses first.\\n\");\n"
  "        raise(SIGUSR2);\n"
  "    }\n"
  "\n"
  "    int i, dst_i;\n"
  "    const unsigned int row = *getarg(1);\n"
  "    void* const xd = vector_arg(2);\n"
  "    const int fill_mode = ifarg(3)? (int)*getarg(3): 0;\n"
  "\n"
  "\n"
  "    const int loaded_conn_type = state_ptr->conn_type & 0xffff;\n"
  "    const int n_fields = state_ptr->n_fields;\n"
  "    const Syn2Field* const fields = state_ptr->fields;\n"
  "    const int target_vec_size = (loaded_conn_type == CONN_CUSTOM)? n_fields\n"
  "                                                                 : ND_FIELD_COUNT;\n"
  "    if (! fill_mode || vector_capacity(xd) < target_vec_size) {\n"
  "        vector_resize(xd, target_vec_size);   // shrink keeps buffer\n"
  "    }\n"
  "    double * const out_buf = vector_vec(xd);  // Get pointer after eventual resize\n"
  "\n"
  "    // init to -1 (due to holes in gjs)\n"
  "    for(i=0; i < target_vec_size; i++) {\n"
  "        out_buf[i] = -1;\n"
  "    }\n"
  "\n"
  "    // Except for Synapses v1 and Custom, we have to translate fields position\n"
  "    const int * const field_pos = CONN_TYPE_POSITIONS(loaded_conn_type);\n"
  "\n"
  "    for (i=0; i<n_fields; i++) {\n"
  "        dst_i = (field_pos != NULL)? field_pos[i] : i;\n"
  "        switch(fields[i].datatype) {\n"
  "        case SYN2_UINT:\n"
  "            out_buf[dst_i] = (double) as_uint_array(fields[i].data)[row];\n"
  "            break;\n"
  "        case SYN2_INT:\n"
  "            out_buf[dst_i] = (double) as_int_array(fields[i].data)[row];\n"
  "            break;\n"
  "        case SYN2_FLOAT:\n"
  "            out_buf[dst_i] = (double) as_float_array(fields[i].data)[row];\n"
  "            break;\n"
  "        case SYN2_DOUBLE:\n"
  "            out_buf[dst_i] = (double) as_double_array(fields[i].data)[row];\n"
  "            break;\n"
  "        }\n"
  "    }\n"
  "\n"
  "    // pre/post-gid (field 0) must be incremented by 1 for neurodamus compat\n"
  "    if(state_ptr->conn_type & CONN_FIELD0_ADD1) {\n"
  "        out_buf[0] += 1;\n"
  "    }\n"
  "\n"
  "    return 0;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/** Retrieve the data of a property/field (column) from the loaded dataset\n"
  " *\n"
  " * @param 1 The field index to retrieve. In case of Synapses it's the field number (up to\n"
  " *  14). In case of loadSynapseCustom, the index of one requested field.\n"
  " * @param 2 The vector to hold the result data\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION getPropertyData() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_SYNTOOL\n"
  "    if (!ifarg(1) || !ifarg(2)) {\n"
  "        fprintf(stderr, \"[SynReader] Error: Function requires two arguments: \"\n"
  "                        \"1. property index (column) to retrieve; 2. Destination Vector\\n\");\n"
  "        raise(SIGUSR2);\n"
  "    }\n"
  "\n"
  "    ReaderState* const state_ptr = getStatePtr();\n"
  "    const int loaded_conn_type = state_ptr->conn_type & 0xffff;\n"
  "    const unsigned int column = *getarg(1);\n"
  "    void* const xd = vector_arg(2);\n"
  "\n"
  "    const int * const field_pos = CONN_TYPE_POSITIONS(loaded_conn_type);\n"
  "    const int field_i = (field_pos != NULL)? field_pos[column] : column;\n"
  "    const Syn2Field field = state_ptr->fields[field_i];\n"
  "\n"
  "    vector_resize(xd, state_ptr->length);  // shinking is almost no-op\n"
  "    double * const vec_buffer = vector_vec(xd);\n"
  "    to_double_vec(&field, state_ptr->length, vec_buffer);\n"
  "\n"
  "    // In case field 0 asked \"add1\" (for gids) then apply it\n"
  "    if (column == 0 && (state_ptr->conn_type & CONN_FIELD0_ADD1)) {\n"
  "        int i;\n"
  "        for (i=0; i < state_ptr->length; i++) {\n"
  "            vec_buffer[i]++;\n"
  "        }\n"
  "    }\n"
  "\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "VERBATIM\n"
  "/** not executed in coreneuron and hence empty stubs sufficient */\n"
  "static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {\n"
  "}\n"
  "ENDVERBATIM\n"
  ;
#endif
