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
#include <alloca.h>
#include <string.h>
#include <limits.h>

#if defined(ENABLE_CORENEURON)
#include <coreneuron/engine.h>
#endif

extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();
extern int nrnmpi_myid;

// name of config files
#define CONFIG_FILENAME_TOTAL_LEN_MAX 32  // Include margin for extra / and \0
static const char* const SIM_CONFIG_FILE = "sim.conf";
static const char* const REPORT_CONFIG_FILE = "report.conf";
static const int DEFAULT_CELL_PERMUTE = 0;
static char* outputdir = NULL;



// helper function to open file and error checking
FILE* open_file(const char *filename, const char *mode) {
    FILE *fp = fopen(filename, mode);
    if(!fp) {
        printf("Error while opening file %s\n", filename);
        abort();
    }
    return fp;
}


/// Builds an absolute path from a relative path
/// doesnt require intermediate dirs to exist
static char* abspath(const char* pth, char* dstmem) {
    if(!pth || !strlen(pth)) { return NULL; }
    if(pth[0] == '/') {  // already absolute
        strcpy(dstmem, pth);
    } else {
        if (!realpath(".", dstmem)) { fprintf(stderr, "Error in abspath. Buffer?\n"); abort(); }
        if(strcmp(pth, ".") != 0) {
            sprintf(dstmem + strlen(dstmem), "/%s", pth);
        }
    }
    return dstmem;
}


ENDVERBATIM


://///////////////////////////////////////////////////////////
:// Model functions
://///////////////////////////////////////////////////////////

CONSTRUCTOR  { : string outputdir
VERBATIM
    if(ifarg(1)) {
        if(outputdir) free(outputdir);
        outputdir = realpath(hoc_gargstr(1), NULL);  // Always created before
    } // else: do nothing. Avoid that random instantiations
      // (e.g. from BBSaveState) overwrite the static outputdir
ENDVERBATIM
}


: write report defined in BlueConfig
PROCEDURE write_report_config() {
VERBATIM
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
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
    char* reportConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(reportConf, "%s/%s", outputdir, REPORT_CONFIG_FILE);

    // write report information
    FILE *fp = open_file(reportConf, "a");
    fprintf(fp, "%s %s %s %s %s %s %d %lf %lf %lf %d 8\n",
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
#endif
ENDVERBATIM
}


: Write basic sim settings from Run block of BlueConfig
PROCEDURE write_sim_config() {
VERBATIM
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char tmpmem[PATH_MAX];
    snprintf(tmpmem, PATH_MAX, "%s/%s", outputdir, SIM_CONFIG_FILE);
    printf("Writing sim config file: %s\n", tmpmem);

    FILE *fp = open_file(tmpmem, "w");
    fprintf(fp, "outpath='%s'\n", abspath(hoc_gargstr(1), tmpmem));
    fprintf(fp, "datpath='%s'\n", abspath(hoc_gargstr(2), tmpmem));
    fprintf(fp, "tstop=%lf\n", *getarg(3));
    fprintf(fp, "dt=%lf\n", *getarg(4));
    fprintf(fp, "forwardskip=%lf\n", *getarg(5));
    fprintf(fp, "prcellgid=%d\n", (int)*getarg(6));
    fprintf(fp, "report-conf='%s/%s'\n",  outputdir, REPORT_CONFIG_FILE);
    fprintf(fp, "cell-permute=%d\n", DEFAULT_CELL_PERMUTE);
    if (ifarg(7) && strlen(hoc_gargstr(7))) {  // if spike replay specified
        fprintf(fp, "pattern='%s'\n", abspath(hoc_gargstr(7), tmpmem));
    }
    fprintf(fp, "mpi=true\n");
    fclose(fp);
#endif
ENDVERBATIM
}


: Write report count as first line
PROCEDURE write_report_count() {  : int reportcount
VERBATIM
#ifndef CORENEURON_BUILD
    if(nrnmpi_myid > 0) {
        return 0;
    }
    char* filename = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(filename, "%s/%s", outputdir, REPORT_CONFIG_FILE);
    FILE *fp = open_file(filename, "w");
    fprintf(fp, "%d\n", (int)*getarg(1));
    fclose(fp);
#endif
ENDVERBATIM
}


PROCEDURE psolve_core() {
VERBATIM
#if defined(ENABLE_CORENEURON)
    char* simConf = alloca(strlen(outputdir) + CONFIG_FILENAME_TOTAL_LEN_MAX);
    sprintf(simConf, "%s/%s", outputdir, SIM_CONFIG_FILE);

    char *argv[] = {"", "--read-config", simConf, "--skip-mpi-finalize", "--mpi", NULL, NULL, NULL, NULL};
    int argc = 5;
    int argIndex=1;
    while( ifarg(argIndex) ) {
        argv[argc++] = strdup( hoc_gargstr(argIndex++) );
    }
    solve_core(argc, argv);
#else
    if(nrnmpi_myid == 0) {
        fprintf(stderr, "%s", "ERROR : CoreNEURON library not linked with NEURODAMUS!\n");
    }
#endif
ENDVERBATIM
}
