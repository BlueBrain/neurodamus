COMMENT
/**
 * @file CoreConfig.mod
 * @brief Interface to write simulation configuration for CoreNEURON
 */
ENDCOMMENT

NEURON {
    THREADSAFE
    ARTIFICIAL_CELL CoreConfig
}

VERBATIM
#include <stdio.h>
#include <stdlib.h>
#if !NRNBBCORE && defined(ENABLE_CORENEURON)
#include <coreneuron/engine.h>
#endif

extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();
extern int nrnmpi_myid;

// name of config files
static char* SIM_CONFIG_FILE = "sim.conf";
static char* REPORT_CONFIG_FILE = "report.conf";
static const int DEFAULT_CELL_PERMUTE = 0;

#define MAX_FILE_PATH 4096

// helper function to open file and error checking
FILE* open_file(const char *filename, const char *mode) {
    FILE *fp = fopen(filename, mode);
    if(!fp) {
        printf("Error while writing simulation configuration in %s\n", REPORT_CONFIG_FILE);
        abort();
    }
    return fp;
}
ENDVERBATIM

: write report defined in BlueConfig
PROCEDURE write_report_config() {
    VERBATIM
    #if !NRNBBCORE
        if(nrnmpi_myid == 0) {
            // gids to be reported is double vector
            double *gid_vec = vector_vec(vector_arg(11));
            int num_gids = vector_capacity(vector_arg(11));

            // copy doible gids to int array
            int *gids = (int*) calloc(num_gids, sizeof(int));
            int i;
            for(i = 0; i < num_gids; i++) {
                gids[i] = (int)gid_vec[i];
            }

            printf("Adding report %s for CoreNEURON with %d gids\n", hoc_gargstr(1), num_gids);
            char filename[MAX_FILE_PATH];
            snprintf(filename, MAX_FILE_PATH, "%s/%s", hoc_gargstr(12), REPORT_CONFIG_FILE);

            // write report information
            FILE *fp = open_file(filename, "a");
            fprintf(fp, "%s %s %s %s %s %s %d %lf %lf %lf %d\n",
                    hoc_gargstr(1),
                    hoc_gargstr(2),
                    hoc_gargstr(3),
                    hoc_gargstr(4),
                    hoc_gargstr(5),
                    hoc_gargstr(6),
                    (int)*getarg(7),
                    *getarg(8),
                    *getarg(9),
                    *getarg(10),
                    num_gids);
            fwrite(gids, sizeof(int), num_gids, fp);
            fprintf(fp, "%s", "\n");
            fclose(fp);
        }
    #endif
    ENDVERBATIM
}

: Write basic sim settings from Run block of BlueConfig
PROCEDURE write_sim_config() {
VERBATIM
    #if !NRNBBCORE
    // should be done by rank 0 only
    if(nrnmpi_myid == 0) {
        char pattern_option[MAX_FILE_PATH] = "";

        // if spike replay specified
        if (strlen(hoc_gargstr(7))) {
            snprintf(pattern_option, MAX_FILE_PATH, "--pattern %s\n", hoc_gargstr(7));
        }

        FILE *fp = open_file(SIM_CONFIG_FILE, "w");
        fprintf(fp, "--outpath %s\n", hoc_gargstr(1));
        fprintf(fp, "--datpath %s\n", hoc_gargstr(2));
        fprintf(fp, "--tstop %lf\n", *getarg(3));
        fprintf(fp, "--dt %lf\n", *getarg(4));
        fprintf(fp, "--forwardskip %lf\n", *getarg(5));
        fprintf(fp, "--prcellgid %d\n", (int)*getarg(6));
        fprintf(fp, "--report-conf %s/%s\n", hoc_gargstr(8), REPORT_CONFIG_FILE);
        fprintf(fp, "--cell-permute %d\n", DEFAULT_CELL_PERMUTE);
        fprintf(fp, "%s", pattern_option);
        fprintf(fp, "-mpi\n");
        fclose(fp);
    }
    #endif
ENDVERBATIM
}

: Write report count as first line
PROCEDURE write_report_count() {
VERBATIM
    #if !NRNBBCORE
    // should be done by rank 0 only
    if(nrnmpi_myid == 0) {
        char filename[MAX_FILE_PATH];
        snprintf(filename, MAX_FILE_PATH, "%s/%s", hoc_gargstr(2), REPORT_CONFIG_FILE);
        FILE *fp = open_file(filename, "w");
        fprintf(fp, "%d\n", (int)*getarg(1));
        fclose(fp);
    }
    #endif
ENDVERBATIM
}

PROCEDURE psolve_core() {
    VERBATIM
        #if !NRNBBCORE && defined(ENABLE_CORENEURON)
            int argc = 5;
            char *argv[5] = {"", "--read-config", SIM_CONFIG_FILE, "--skip-mpi-finalize", "-mpi"};
            solve_core(argc, argv);
        #else
            if(nrnmpi_myid == 0) {
                fprintf(stderr, "%s", "ERROR : CoreNEURON library not linked!\n");
                abort();
            }
        #endif
    ENDVERBATIM
}
