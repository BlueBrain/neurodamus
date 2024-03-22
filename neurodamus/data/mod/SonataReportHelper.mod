NEURON {
        THREADSAFE
        ARTIFICIAL_CELL SonataReportHelper
        RANGE initialStep, activeStep
}

VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include <stdint.h>
#include <bbp/sonata/reports.h>
#include <mpi.h>
#ifndef NRN_VERSION_GTEQ_8_2_0
    extern int ifarg(int iarg);
    extern double* getarg(int iarg);
    extern double* vector_vec();
    extern int vector_capacity();
    extern void* vector_arg(int);
    extern void nrn_register_recalc_ptr_callback(void (*f)(void));
    extern double* nrn_recalc_ptr(double*);
#endif
#ifndef NRN_MECHANISM_DATA_IS_SOA
    void sonataRefreshPointers() { //callback function to update data locations before runtime
        sonata_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function
    }
#endif
#endif
#endif
ENDVERBATIM

PARAMETER {
    Dt = .1 (ms)
    activeStep = 0
    initialStep = 0
}

INITIAL {
    activeStep = initialStep
    net_send(initialStep*Dt, 1)
}


NET_RECEIVE(w) {

VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_record_data(activeStep);
    activeStep++;
#endif
#endif
ENDVERBATIM
    net_send(Dt, 1)
}

CONSTRUCTOR  {
VERBATIM {
/**
* \param 1: Dt (double, optional). If not given no initializaton is performed
* \param 2: register_recalc_ptr (double, optional). By default will invoke
*    nrn_register_recalc_ptr_callback, which can be disabled by passing 0
*/
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    if( !ifarg(1) ) {
        return;
    }
    Dt = *getarg(1);
    sonata_set_atomic_step(Dt);
#ifndef NRN_MECHANISM_DATA_IS_SOA
    int register_recalc_ptr = 1;
    if( ifarg(2) ) {
        register_recalc_ptr = (int)*getarg(2);
    }
    if( register_recalc_ptr ) {
        nrn_register_recalc_ptr_callback( sonataRefreshPointers );
    }
#endif
#endif
#endif
}
ENDVERBATIM
}

PROCEDURE make_comm() {
VERBATIM
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_setup_communicators();
#endif
#endif
}
ENDVERBATIM
}

PROCEDURE prepare_datasets() {
VERBATIM
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_prepare_datasets();
#endif
#endif
}
ENDVERBATIM
}

PROCEDURE disable_auto_flush() {
}

PROCEDURE set_steps_to_buffer() {
}

PROCEDURE set_max_buffer_size_hint() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int buffer_size = (int) *getarg(1);
    sonata_set_max_buffer_size_hint(buffer_size);
#endif
#endif
ENDVERBATIM
}

PROCEDURE flush() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    // Note: flush uses actual time (t) whereas recData uses timestep.  Should try to only use one or the other in the future
    sonata_flush( t );
#endif
#endif
ENDVERBATIM
}

:Populate buffers from NEURON for savestate
: @param SaveState object
PROCEDURE pre_savestate() {
}

:Call ReportingLib for saving SaveState data using MPI I/O
PROCEDURE savestate() {
}

: only restore global data for the purposes of getting the post retore time
PROCEDURE restoretime() {
    initialStep = t/Dt
}

: @param SaveState object
PROCEDURE restorestate() {
    activeStep = t/Dt
}

FUNCTION redirect() {
}

PROCEDURE clear() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_clear();
#endif
#endif
ENDVERBATIM
}

PROCEDURE create_spikefile() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    char output_dir[256] = ".";
    // output dir
    if (ifarg(1)) {
        sprintf(output_dir,"%s", gargstr(1));
    }
    char file_name[256] = "out";
    // file name
    if (ifarg(2)) {
        sprintf(file_name,"%s", gargstr(2));
    }
    sonata_create_spikefile(output_dir, file_name);
#endif
#endif
ENDVERBATIM
}

PROCEDURE write_spike_populations() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_write_spike_populations();
#endif
#endif
ENDVERBATIM
}

PROCEDURE close_spikefile() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    sonata_close_spikefile();
#endif
#endif
ENDVERBATIM
}

PROCEDURE write_spikes() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    char output_dir[256] = ".";
    char population_name[256] = "All";
    char file_name[256] = "out";
    double *time = NULL, *gid = NULL;
    int num_spikes = 0;
    int num_gids = 0;
    IvocVect* v1;
    IvocVect* v2;

    // first vector is time of spikes
    if (ifarg(1)) {
        v1 = vector_arg(1);
        time = vector_vec(v1);
        num_spikes = vector_capacity(v1);
    }

    // second vector is associated gids
    if (ifarg(2)) {
        v2 = vector_arg(2);
        gid = vector_vec(v2);
        num_gids = vector_capacity(v2);
    }

    // output dir
    if (ifarg(3)) {
        sprintf(output_dir,"%s", gargstr(3));
    }

    if (ifarg(4)) {
        sprintf(population_name,"%s", gargstr(4));
    }

    int* int_gid = (int*)malloc(num_gids * sizeof(int));
    int i;
    for(i=0; i<num_spikes; ++i) {
        int_gid[i] = (int)gid[i];
    }
    sonata_create_spikefile(output_dir, file_name);
    sonata_add_spikes_population(population_name, 0, time, num_spikes, int_gid, num_gids);
    sonata_write_spike_populations();
    sonata_close_spikefile();
    free(int_gid);
#endif
#endif
ENDVERBATIM
}

PROCEDURE add_spikes_population() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    char population_name[256] = "All";
    int population_offset = 0;
    double *time = NULL, *gid = NULL;
    int num_spikes = 0;
    int num_gids = 0;
    IvocVect* v1;
    IvocVect* v2;

    // first vector is time of spikes
    if (ifarg(1)) {
        v1 = vector_arg(1);
        time = vector_vec(v1);
        num_spikes = vector_capacity(v1);
    }

    // second vector is associated gids
    if (ifarg(2)) {
        v2 = vector_arg(2);
        gid = vector_vec(v2);
        num_gids = vector_capacity(v2);
    }

    if (ifarg(3)) {
        sprintf(population_name,"%s", gargstr(3));
    }

    if (ifarg(4)) {
        population_offset = (int) *getarg(4);
    }

    int* int_gid = (int*)malloc(num_gids * sizeof(int));
    int i;
    for(i=0; i<num_spikes; ++i) {
        int_gid[i] = (int)gid[i];
    }
    sonata_add_spikes_population(population_name, population_offset, time, num_spikes, int_gid, num_gids);
    free(int_gid);
#endif
#endif
ENDVERBATIM
}
