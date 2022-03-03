COMMENT
/**
 * @file ProfileHelper.mod
 * @brief Provide an interface to resume/pause profiling from different profiling tools
 */
ENDCOMMENT

NEURON {
    THREADSAFE
    ARTIFICIAL_CELL ProfileHelper
}

VERBATIM

// tau profiling api
#if defined(ENABLE_TAU_PROFILER)
#include <TAU.h>

// score-p profiling api
#elif defined(ENABLE_SCOREP_PROFILER)
#include <scorep/SCOREP_User.h>

// hpctoolkit profiling api
#elif defined(ENABLE_HPCTOOLKIT_PROFILER)
#include <hpctoolkit.h>

#endif


static void print_message(const char *message) {
    #ifndef CORENEURON_BUILD
    extern int nrnmpi_myid;
    if(nrnmpi_myid == 0) {
        printf("%s", message);
    }
    #endif
}

ENDVERBATIM

: Start/Resume profiling
PROCEDURE resume_profiling() {

    VERBATIM

        #if defined(ENABLE_TAU_PROFILER)
            TAU_ENABLE_INSTRUMENTATION();
            print_message("Resume TAU Profiling\n");
        #elif defined(ENABLE_SCOREP_PROFILER)
            SCOREP_RECORDING_ON()
            print_message("Resume Score-P Profiling\n");
        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)
            hpctoolkit_sampling_start();
            print_message("Resume HPCToolkit Profiling\n");
        #endif

    ENDVERBATIM

}

: Pause profiling
PROCEDURE pause_profiling() {

    VERBATIM

        #if defined(ENABLE_TAU_PROFILER)
            TAU_DISABLE_INSTRUMENTATION();
            print_message("Pause TAU Profiling\n");
        #elif defined(ENABLE_SCOREP_PROFILER)
            SCOREP_RECORDING_OFF()
            print_message("Pause Score-P Profiling\n");
        #elif defined(ENABLE_HPCTOOLKIT_PROFILER)
            hpctoolkit_sampling_stop();
            print_message("Pause HPCToolkit Profiling\n");
        #endif

    ENDVERBATIM

}
