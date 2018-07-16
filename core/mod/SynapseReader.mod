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
}

PARAMETER {
}

ASSIGNED {
    state_
    verboseLevel
}

INITIAL {
}

NET_RECEIVE(w) {
}

VERBATIM

#ifdef DISABLE_HDF5
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
#else
#warning "SynapseReader Enabled"

#include <stdio.h>
#include <string.h>
#include <syn2/c_reader.h>


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
extern void vector_resize(void* v, int n);
extern void* vector_arg(int);


typedef struct {
    syn2_vec_str data;
    int length;
} Strings_;


/// Hold Reader state, such as file handle and info about latest dataset loaded
typedef struct {
    s2id_t file;
    Strings_ fieldNames;
    // dataset dependent
    uint32_t tgid;
    const Syn2Field* fields;
    size_t length;
    int n_fields;
} ReaderState;

static const ReaderState STATE_RESET = {-1, {NULL, 0}, 0, NULL, 0, -1};

// Use state var as a pointer
#define state_ptr (*((ReaderState**)(&state_)))


// The NRN Synapse fields according to SYN2 transitional spec
// ----------------------------------------------------------
//   - connected_neurons_post
//   0 connected_neurons_pre
//   1 delay
//   2 morpho_section_id_post
//   3 morpho_segment_id_post
//   4 morpho_offset_segment_post
//   5 morpho_section_id_pre
//   6 morpho_segment_id_pre
//   7 morpho_offset_segment_pre
//   8 conductance
//   9 u_syn
//  10 depression_time
//  11 facilitation_time
//  12 decay_time
//  13 syn_type_id
//  14 morpho_type_id_pre
//  15 morpho_branch_order_dend  # N/A
//  16 morpho_branch_order_axon  # Irrelevant
//  17 n_rrp_vesicles
//  18 morpho_section_type_pos   # N/A

// The 12 synapse fields read by neurodamus
#define BASE_FIELDS "connected_neurons_pre, \
                     delay, \
                     morpho_section_id_post, \
                     morpho_segment_id_post, \
                     morpho_offset_segment_post, \
                     conductance, \
                     u_syn, depression_time, facilitation_time, \
                     decay_time, \
                     syn_type_id"

static const char* ALL_FIELDS_NO_RRP = BASE_FIELDS;
static const char* ALL_FIELDS = BASE_FIELDS ", n_rrp_vesicles";

static int syn_is_empty() {
    return state_ptr->fields == NULL;
}


static Strings_ getFieldNames() {
    if (state_ptr->fieldNames.data == NULL) {
        const Syn2Dataset names_ds = syn_list_property_names(state_ptr->file);
        state_ptr->fieldNames.data = as_str_array(names_ds.data);
        state_ptr->fieldNames.length = names_ds.length;
    }
    return state_ptr->fieldNames;
}


static int syn_hasNrrp()  {
    const Strings_ names_ds = getFieldNames();
    syn2_vec_str names = names_ds.data;

    int i;
    for (i=0; i < names_ds.length; i++) {
        if (strcmp(names[i], "n_rrp_vesicles") == 0)
            return 1;
    }
    return 0;
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
    
    if (!hoc_is_str_arg(1)) {
        fprintf(stderr, "[SynReader] Error: SynapseReader filename must be a string");
        return;
    }
    
    if (ifarg(2)) {
        verboseLevel = *getarg(2);
    }
    
    // normal case - open a file and be ready to load data as needed
    rs.file = syn_open(gargstr(1));
    
    state_ptr = (ReaderState*) malloc(sizeof(ReaderState));
    *state_ptr = rs;
    
#endif
ENDVERBATIM
}



DESTRUCTOR {
VERBATIM
#ifndef DISABLE_SYNTOOL
    syn_close(state_ptr->file);
    free(state_ptr);
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
    const Strings_ names_ds = getFieldNames();
    return names_ds.length;
#endif
ENDVERBATIM
}



FUNCTION countSynapses() { : string cellname
VERBATIM {
#ifndef DISABLE_SYNTOOL
    return syn_get_number_synapses(state_ptr->file);
#endif
}
ENDVERBATIM
}



FUNCTION hasNrrpField() {
VERBATIM
#ifndef DISABLE_SYNTOOL
    return syn_hasNrrp();
#else
    fprintf(stderr, "[SynReader] Warning: SynapseTool not Enabled")
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
    if (state_ptr->file == -1)  {
        fprintf(stderr, "[SynReader] Error: File not initialized.");
        return -1;
    }

    uint32_t tgid = (uint32_t) *getarg(1);

    if (tgid == state_ptr->tgid) {  // Already loaded?
        return state_ptr->length;
    }

    const char* fields = ifarg(2)? gargstr(2) : (syn_hasNrrp()? ALL_FIELDS : ALL_FIELDS_NO_RRP);
    const Syn2Selection sel = syn_select_post(tgid);

    const Syn2Table tb = syn_get_property_table(state_ptr->file, fields, sel);

    // "tb.fields" might be NULL if there is no data. Ok as long length is zero.
    // Keep results in the state obj
    state_ptr->tgid = tgid;
    state_ptr->fields = tb.fields;
    state_ptr->length = tb.length;
    state_ptr->n_fields = tb.n_fields;
    return tb.length;

#else
    fprintf(stderr, "[SynReader] Error: Neurodamus compiled without SYNTOOL\n");
    return -1;
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
        return -1;
    }

    if(syn_is_empty()) {
        fprintf(stderr, "[SynReader] Error: No synapse data. Please load synapses first.\n");
        return -1;
    }

    unsigned int row = *getarg(1);
    void* xd = vector_arg(2);
    const int n_fields = state_ptr->n_fields;

    if (vector_capacity(xd) != n_fields) {
        vector_resize(xd, n_fields);
    }

    double * out_buf = vector_vec(xd);

    const Syn2Field* fields = state_ptr->fields;

    int i;
    for (i=0; i<n_fields; i++) {
        switch(fields[i].datatype) {
        case SYN2_UINT:
            out_buf[i] = (double) as_uint_array(fields[i].data)[row];
            break;
        case SYN2_INT:
            out_buf[i] = (double) as_int_array(fields[i].data)[row];
            break;
        case SYN2_FLOAT:
            out_buf[i] = (double) as_float_array(fields[i].data)[row];
            break;
        case SYN2_DOUBLE:
            out_buf[i] = (double) as_double_array(fields[i].data)[row];
            break;
        }
    }

    return 0;
#endif
ENDVERBATIM
}
