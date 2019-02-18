COMMENT
/**
 * @file syn2reader.mod
 * @brief A Reader for Synapse files, inc Nrn and SYN2
 * @author F. Pereira
 * @date 2018-06
 * @remark Copyright (C) 2018 EPFL - Blue Brain Project
 * All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

COMMENT
Read Synapse file sources using synapse-tool
ENDCOMMENT

NEURON {
    ARTIFICIAL_CELL SynapseReader
    THREADSAFE
    BBCOREPOINTER ptr
}

PARAMETER {
}

ASSIGNED {
    ptr
    verboseLevel
}

INITIAL {
}

NET_RECEIVE(w) {
}

VERBATIM

#if defined(DISABLE_HDF5) || defined(CORENEURON_BUILD)
  #warning "Disabling Synapse Reader since HDF5 is disabled"
  #define DISABLE_SYNTOOL 1
#endif

// If SYN2 becomes default, we can just drop this
#ifndef ENABLE_SYNTOOL
#define DISABLE_SYNTOOL 1
#endif

// Super guard to avoid building mod
#ifdef DISABLE_SYNTOOL
#warning "SynapseReader Disabled"
#include <signal.h>

#else
#warning "SynapseReader Enabled"

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <syn2/c_reader.h>

#define CONN_SYNAPSES 0
#define CONN_GAPJUNCTIONS 1


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
    uint64_t tgid;
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
//   1 delay                      [1]  | N/A
//   2 morpho_section_id_post     [2]  | morpho_section_id_post
//   3 morpho_segment_id_post     [3]  | morpho_section_id_post
//   4 morpho_offset_segment_post [4]  | morpho_section_id_post
//   5 morpho_section_id_pre           | morpho_section_id_pre (unused)
//   6 morpho_segment_id_pre           | morpho_section_id_pre (unused)
//   7 morpho_offset_segment_pre       | morpho_section_id_pre (unused)
//   8 conductance                [5]  | conductance (optional)
//   9 u_syn                      [6]  | N/A
//  10 depression_time            [7]  | junction_id_pre
//  11 facilitation_time          [8]  | junction_id_post
//  12 decay_time                 [9]  | N/A
//  13 syn_type_id                [10] | N/A
//  14 morpho_type_id_pre              | N/A
//  15 morpho_branch_order_dend        | N/A
//  16 morpho_branch_order_axon        | N/A
//  17 n_rrp_vesicles (optional)  [11] | N/A
//  18 morpho_section_type_pos         | N/A

// C99 Use #define for constants
#define ND_FIELD_COUNT 12
#define ND_GJ_PREGID_I 0
#define ND_GJ_CONDUCTANCE_I 5

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

// The 6 mandatory fields for GapJunctions read by neurodamus
#define _BASE_GJ_FIELDS "connected_neurons_pre, \
                         morpho_section_id_post, \
                         morpho_segment_id_post, \
                         morpho_offset_segment_post, \
                         junction_id_pre, \
                         junction_id_post"

static const char* SYN_FIELDS_NO_RRP = BASE_SYN_FIELDS;
static const char* SYN_FIELDS = BASE_SYN_FIELDS ", " NRRP_FIELD;
static const char* GJ_FIELDS_NO_CONDUCTANCE = _BASE_GJ_FIELDS;
static const char* GJ_FIELDS = _BASE_GJ_FIELDS ", conductance" ;

// relative position of the 7 GJ fields into the 12-field neurodamus structure
// Conductance is fetched last since its optional
// Why the structure is not packed? Any special meaning for pos 1 and 6?
static const int ND_GJ_POSITIONS[] = {ND_GJ_PREGID_I, 2, 3, 4, 7, 8, ND_GJ_CONDUCTANCE_I};


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
    state_ptr->tgid = tgid;
    // "tb.fields" might be NULL if there is no data. Ok as long length is zero.
    state_ptr->fields = tb->fields;
    state_ptr->length = tb->length;
    state_ptr->n_fields = tb->n_fields;
    return tb->length;
}


/// Loads data from synapse file into internal state
static int _load_data(uint64_t tgid, int conn_type, const char* fields, ReaderState* state_ptr) {
    if (state_ptr->file == -1)  {
        fprintf(stderr, "[SynReader] Error: File not initialized.");
        raise(SIGUSR2);
    }

    // Already loaded?
    if (tgid == state_ptr->tgid && conn_type == state_ptr->conn_type) {
        return state_ptr->length;
    }

    const Syn2Selection sel = syn_select_post(tgid);
    const Syn2Table tb = syn_get_property_table(state_ptr->file, fields, sel);
    // tb.fields == NULL in case there are no cells (selection). If missing fields then exception

    state_ptr->conn_type = conn_type;
    return _store_result(tgid, &tb, state_ptr);
}

#endif  // SYNTOOL


//////////////////////////////////////////////////////////////////////
/// NMOD Methods
//////////////////////////////////////////////////////////////////////
ENDVERBATIM

CONSTRUCTOR { : string filepath
VERBATIM
#ifndef DISABLE_SYNTOOL
    ReaderState rs = STATE_RESET;
    if( !ifarg(1) ) {
        getStatePtr() = NULL;
        return;
    }

    if (!hoc_is_str_arg(1)) {
        fprintf(stderr, "[SynReader] Error: SynapseReader filename must be a string");
        raise(SIGUSR2);
    }

    if (ifarg(2)) {
        verboseLevel = *getarg(2);
    }

    // normal case - open a file and be ready to load data as needed
    rs.file = syn_open(gargstr(1));

    ReaderState* state_ptr = (ReaderState*) malloc(sizeof(ReaderState));
    *state_ptr = rs;
    // use macro to get the pointer, write new address
    getStatePtr() = state_ptr;

#endif
ENDVERBATIM
}



DESTRUCTOR {
VERBATIM
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
ENDVERBATIM
}



FUNCTION modEnabled() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return 1;
#else
    return 0;
#endif
ENDVERBATIM
}



FUNCTION countProperties(){ : string cellname
VERBATIM
#ifndef DISABLE_SYNTOOL
    const _Strings names_ds = _getFieldNames(getStatePtr());
    return names_ds.length;
#endif
ENDVERBATIM
}



FUNCTION countSynapses() { : string cellname
VERBATIM {
#ifndef DISABLE_SYNTOOL
    return syn_get_number_synapses(getStatePtr()->file);
#endif
}
ENDVERBATIM
}



FUNCTION hasNrrpField() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return _syn_has_field(NRRP_FIELD, getStatePtr());
#else
    return -1;
#endif
ENDVERBATIM
}

FUNCTION hasConductance() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return _syn_has_field("conductance", getStatePtr());
#else
    return -1;
#endif
ENDVERBATIM
}



COMMENT
/**
 * Loads synapse data from file into memory, all common fields required by neurodamus
 *
 * @param post_gid. The post gid to filter
 * @param string (optional) fields to load. Default: the 12 fields defined above
 * @return number of synapses read. -1 if error
 */
ENDCOMMENT
FUNCTION loadSynapses() { : double tgid, string fields
VERBATIM
#ifndef DISABLE_SYNTOOL
    uint64_t tgid = (uint64_t) *getarg(1) - 1;  // 0 based
    ReaderState* state_ptr = getStatePtr();
    const char* fields = ifarg(2)? gargstr(2) :
        (_syn_has_field(NRRP_FIELD, state_ptr)? SYN_FIELDS : SYN_FIELDS_NO_RRP);
    return _load_data(tgid, CONN_SYNAPSES, fields, state_ptr);
#else
    fprintf(stderr, "[SynReader] Error: Neurodamus compiled without SYNTOOL\n");
    raise(SIGUSR1);
#endif
ENDVERBATIM
}



COMMENT
/// Load Gap-Junctions with Synapsetool
ENDCOMMENT
FUNCTION loadGapJunctions() { : double tgid, string fields
VERBATIM
#ifndef DISABLE_SYNTOOL
    uint64_t tgid = (uint64_t) *getarg(1) - 1;
    //fields = _syn_has_field("conductance", state_ptr)? GJ_FIELDS : GJ_FIELDS_NO_CONDUCTANCE;
    return _load_data(tgid, CONN_GAPJUNCTIONS, GJ_FIELDS, getStatePtr());
#else
    fprintf(stderr, "[SynReader] Error: Neurodamus compiled without SYNTOOL\n");
    raise(SIGUSR1);
#endif
ENDVERBATIM
}



COMMENT
/**
 * Retrieve the value for an attribute of the active dataset.
 * Expected to contain only one value of double type
 *
 * @param synapse_i The index of the synapse to retrieve
 * @param vector The vector to hold the result data
 */
ENDCOMMENT
FUNCTION getSynapse() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    if (!ifarg(1) || !ifarg(2)) {
        fprintf(stderr, "[SynReader] Error: Function requires two arguments: "
                        "1. synapse index (row) to retrieve; 2. Destination Vector");
        raise(SIGUSR2);
    }

    ReaderState* state_ptr = getStatePtr();

    if (_syn_is_empty(state_ptr)) {
        fprintf(stderr, "[SynReader] Error: No synapse data. Please load synapses first.\n");
        raise(SIGUSR2);
    }

    int i, dst_i;
    unsigned int row = *getarg(1);
    void* xd = vector_arg(2);

    const int loaded_conn_type = state_ptr->conn_type;
    const int n_fields = state_ptr->n_fields;
    const Syn2Field* fields = state_ptr->fields;

    // resize if too small
    if (vector_capacity(xd) < ND_FIELD_COUNT) {
        vector_resize(xd, ND_FIELD_COUNT);
    }
    // Get pointer, only after eventual resize
    double * out_buf = vector_vec(xd);

    // init to -1 (due to holes in gjs)
    for(i=0; i<ND_FIELD_COUNT; i++) {
        out_buf[i] = -1;
    }

    for (i=0; i<n_fields; i++) {
        dst_i = (loaded_conn_type == CONN_GAPJUNCTIONS)? ND_GJ_POSITIONS[i] : i;
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

    // pre-gid (field 0) must be incremented by 1 for neurodamus compat
    out_buf[ND_GJ_PREGID_I] += 1;

    return 0;
#endif
ENDVERBATIM
}


VERBATIM

/** not executed in coreneuron and hence empty stubs sufficient */

static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}

static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
ENDVERBATIM
