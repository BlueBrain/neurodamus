NEURON {
        THREADSAFE
        ARTIFICIAL_CELL BinReportHelper
        RANGE initialStep, activeStep
}

VERBATIM

#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include "reportinglib/Records.h"
#include "reportinglib/isc/iscAPI.h"
#ifndef DISABLE_MPI
#include <mpi.h>
#endif

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
extern double* nrn_recalc_ptr(double*);
extern void nrn_register_recalc_ptr_callback(void (*f)(void));

extern Object** hoc_objgetarg();
extern void* bbss_buffer_counts( int*, int**, int**, int* );
extern void bbss_save_global( void*, char*, int );
extern void bbss_restore_global( void*, char*, int );
extern void bbss_save( void*, int, char*, int );
extern void bbss_restore( void*, int, int, char*, int );
extern void bbss_save_done( void* );
extern void bbss_restore_done( void* );

extern int nrnmpi_myid;

void refreshPointers() { //callback function to update data locations before runtime
	records_refresh_pointers(nrn_recalc_ptr); //tell bin report library to update its pointers using nrn_recalc_ptr function
        isc_refresh_pointers(nrn_recalc_ptr);
}
#endif

//int len=0, *gids=0, *sizes=0, global_size=0, pieceCount=0;
void *bbss_ref = NULL;

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
    records_rec(activeStep);
    isc_send_data(activeStep);

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
    if( !ifarg(1) ) return;
    Dt = *getarg(1);

    records_set_atomic_step(Dt);
    isc_set_sim_dt(Dt);

    int register_recalc_ptr = 1;
    if( ifarg(2) ) register_recalc_ptr = (int)*getarg(2);
    if( register_recalc_ptr ) {
        nrn_register_recalc_ptr_callback( refreshPointers );
    }
#endif
#endif
}
ENDVERBATIM
}


COMMENT
/**
 * Resume the event delivery loop for NEURON restore. Call from Hoc only (there's param)
 *
 * @param t The initial time
 */
ENDCOMMENT
PROCEDURE restartEvent() {
VERBATIM
#ifndef CORENEURON_BUILD
    const double etime = *getarg(1);
    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
#endif
ENDVERBATIM
}


PROCEDURE make_comm() {
VERBATIM
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	records_setup_communicator();
#endif
#endif
}
ENDVERBATIM
}


PROCEDURE disable_auto_flush() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    records_set_auto_flush(0);
#endif
#endif
ENDVERBATIM
}


PROCEDURE set_steps_to_buffer() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int nsteps = (int) *getarg(1);
    records_set_steps_to_buffer( nsteps );
#endif
#endif
ENDVERBATIM
}

PROCEDURE set_max_buffer_size_hint() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int buf_size = (int) *getarg(1);
    records_set_max_buffer_size_hint(buf_size);
#endif
#endif
ENDVERBATIM
}

PROCEDURE flush() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
        // Note: flush uses actual time (t) whereas recData uses timestep.  Should try to only use one or the other in the future
	records_flush( t );
#endif
#endif
ENDVERBATIM
}



:Populate buffers from NEURON for savestate
: @param SaveState object
PROCEDURE pre_savestate() {
VERBATIM
{
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    int len, *gids, *sizes, global_size;
    char* gbuffer;
    char* saveFile = gargstr(1);

    //get sizes
    bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );

    //pass arrays to bin report library for header creation
    gbuffer = records_saveinit( saveFile, len, gids, sizes, global_size );

    //have neuron fill in global data for rank 0
    if( global_size ) {
        bbss_save_global( bbss_ref, gbuffer, global_size );
        records_saveglobal();
    }

    //for each gid, get the buffer from the bin report lib and give to NEURON layer
    int gidIndex=0;
    for( gidIndex=0; gidIndex<len; gidIndex++ ) {
        char *buffer = records_savebuffer( gids[gidIndex] );
        bbss_save( bbss_ref, gids[gidIndex], buffer, sizes[gidIndex] );
    }

    if(len) {
        free(gids);
        free(sizes);
    }

#endif
#endif
}
ENDVERBATIM
}

:Call ReportingLib for saving SaveState data using MPI I/O
PROCEDURE savestate() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB

    if(nrnmpi_myid == 0) {
        printf(" Call to ReportingLib for MPI I/O\n");
    }

    //all buffers populated, have lib execute final MPI-IO operations
    records_savestate();

    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it
    bbss_save_done( bbss_ref );
#endif
#endif
ENDVERBATIM
}


: only restore global data for the purposes of getting the post retore time
PROCEDURE restoretime() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    void *bbss_ref = NULL;
    int len=0, *gids, *sizes, global_size, pieceCount;
    char* gbuffer = NULL;
    char* saveFile = gargstr(1);

    //get sizes - actually care about gid info for restore
    if( len == 0 ) {
        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );
    }

    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save
    gbuffer = records_restoreinit( saveFile, &global_size );
    bbss_restore_global( bbss_ref, gbuffer, global_size );

    if(len) {
        free(gids);
        free(sizes);
    }
#endif
#endif
ENDVERBATIM
    initialStep = t/Dt
}



: @param SaveState object
PROCEDURE restorestate() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
{
    void *bbss_ref = NULL;
    int len=0, *gids, *sizes, global_size, pieceCount;
    char* gbuffer = NULL;
    char *saveFile = gargstr(1);

    //get sizes - actually care about gid info for restore
    if( len == 0 ) {
        bbss_ref = bbss_buffer_counts( &len, &gids, &sizes, &global_size );
    }

    // initialize counts, offsets, and get global data - all cpus must load global data unlike with save
    gbuffer = records_restoreinit( saveFile, &global_size );
    bbss_restore_global( bbss_ref, gbuffer, global_size );

    int nbytes = 0, gidIndex=0;
    //for each gid, get the buffer from the bin report lib and give to NEURON layer
    for( gidIndex=0; gidIndex<len; gidIndex++ ) {
        if( gids[gidIndex] != 0 ) {
            gbuffer = records_restore( gids[gidIndex], &pieceCount, &nbytes );
            //printf( "restore %d with %d pieces in %d bytes\n", gids[gidIndex], pieceCount, nbytes );
            bbss_restore( bbss_ref, gids[gidIndex], pieceCount, gbuffer, nbytes );
        }
    }

    //clean up -> I need to free some space.  If they were alloced using 'new', then need report lib to do it
    bbss_restore_done( bbss_ref );

    if(len) {
        free(gids);
        free(sizes);
    }
}
#endif
#endif
ENDVERBATIM

    activeStep = t/Dt
}

FUNCTION redirect() {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    FILE *fout;
    char fname[128];

    int mpi_size=1, mpi_rank=0;

#ifndef DISABLE_MPI
    // get MPI info
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);
#endif

    sprintf( fname, "NodeFiles/%d.%dnode.out", mpi_rank, mpi_size );
    fout = freopen( fname, "w", stdout );
    if( !fout ) {
        fprintf( stderr, "failed to redirect.  Terminating\n" );
        exit(0);
    }

    sprintf( fname, "NodeFiles/%d.%dnode.err", mpi_rank, mpi_size );
    fout = freopen( fname, "w", stderr );
    setbuf( fout, NULL );
#endif
#endif
}
ENDVERBATIM
}


PROCEDURE clear() {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
        records_clear();
#endif
#endif
ENDVERBATIM
}

