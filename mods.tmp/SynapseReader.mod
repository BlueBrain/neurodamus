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
ENDVERBATIM

CONSTRUCTOR { : string filepath
VERBATIM
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


FUNCTION countProperties(){
VERBATIM
#ifndef DISABLE_SYNTOOL
    const _Strings names_ds = _getFieldNames(getStatePtr());
    return names_ds.length;
#endif
ENDVERBATIM
}


FUNCTION hasProperty(){
    :param 1: (string) The name of the property to check existence
VERBATIM
#ifndef DISABLE_SYNTOOL
    return _syn_has_field(gargstr(1), getStatePtr());
#endif
ENDVERBATIM
}


FUNCTION countSynapses() {
VERBATIM {
#ifndef DISABLE_SYNTOOL
    return syn_get_number_synapses(getStatePtr()->file);
#endif
}
ENDVERBATIM
}


FUNCTION selectPopulation() {
    :param 1: (string) The name of the population to open
VERBATIM
#ifndef DISABLE_SYNTOOL
    return syn_select_population(getStatePtr()->file, gargstr(1));
#endif
ENDVERBATIM
}


FUNCTION hasNrrpField() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return HAS_NRRP();
#else
    return -1;
#endif
ENDVERBATIM
}


FUNCTION isV2() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return IS_V2();
#else
    return -1;
#endif
ENDVERBATIM
}


COMMENT
/** Loads synapse data from file into memory, all common fields required by neurodamus
 *
 * @param post_gid. The post gid to filter
 * @param string (optional) fields to load. Default: the ND_FIELD_COUNT fields defined above
 * @return number of synapses read. -1 if error
 */
ENDCOMMENT
FUNCTION loadSynapses() { : double tgid, string fields
VERBATIM
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
ENDVERBATIM
}



COMMENT
/// Load Gap-Junctions with Synapsetool
ENDCOMMENT
FUNCTION loadGapJunctions() { : double tgid, string fields
VERBATIM
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
ENDVERBATIM
}



COMMENT
/** Load a custom set of fields from the synapse file.
 *
 * @param 1: (double) The gid to query by, normally target gid
 * @param 2: (string) Fields
 * @param 3: (optional, bool) Query by source gid instead of target
 */
ENDCOMMENT
FUNCTION loadSynapseCustom() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    const uint64_t gid = (uint64_t) *getarg(1) - 1;  // 0 based
    const char* const fields = gargstr(2);
    const int pre_gid_instead = (ifarg(3) && *getarg(3));
    // If first field is a GID then activate ADD1
    int fieldset = CONN_CUSTOM
        + ((strncmp(fields, "connected_neurons_", 18) == 0)? CONN_FIELD0_ADD1 : 0);
    return _load_data(gid, pre_gid_instead, fieldset, fields, getStatePtr());
#endif
ENDVERBATIM
}



COMMENT
/** Retrieve one synape data (row) from the loaded dataset
 *
 * @param 1 The index of the synapse to retrieve
 * @param 2 The vector to hold the result data
 * @param 3 Fill mode, dont resize the vector (Default: false)
 */
ENDCOMMENT
FUNCTION getSynapse() {
VERBATIM
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
ENDVERBATIM
}


COMMENT
/** Retrieve the data of a property/field (column) from the loaded dataset
 *
 * @param 1 The field index to retrieve. In case of Synapses it's the field number (up to
 *  14). In case of loadSynapseCustom, the index of one requested field.
 * @param 2 The vector to hold the result data
 */
ENDCOMMENT
FUNCTION getPropertyData() {
VERBATIM
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
ENDVERBATIM
}


VERBATIM
/** not executed in coreneuron and hence empty stubs sufficient */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
ENDVERBATIM
