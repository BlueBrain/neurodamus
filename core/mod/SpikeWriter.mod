COMMENT
/**
 * @file SpikeWriter.mod
 * @brief Interface to write spikes in parallel using MPI-IO
 */
ENDCOMMENT

NEURON {
    ARTIFICIAL_CELL SpikeWriter
}

VERBATIM
#include <stdlib.h>

#ifndef DISABLE_MPI
#include <mpi.h>
#endif

extern double* vector_vec();
extern int vector_capacity();
extern void* vector_arg();

extern int nrnmpi_myid;

ENDVERBATIM

: write_spikes to file in parallel
PROCEDURE write() {

    VERBATIM

        double *time = NULL, *gid = NULL;
        int num_spikes = 0;
        char *filePath = NULL;

        // first vector is time of spikes
        if (ifarg(1)) {
            void *v = vector_arg(1);
            time = vector_vec(v);
            num_spikes = vector_capacity(v);
        }

        // second vector is associated gids
        if (ifarg(2)) {
            void *v = vector_arg(2);
            gid = vector_vec(v);
        }

        // third argument is file path
        if(ifarg(3)) {
            filePath = hoc_gargstr(3);
        } else  {
#ifndef DISABLE_MPI
            if(nrnmpi_myid == 0) {
                fprintf(stderr, " Error : No spike file path provided, can't write spikes! \n");
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
#else
            fprintf(stderr, " Error : No spike file path provided, can't write spikes! \n");
            exit(-1);
#endif
        }

        // rank 0 write extra string at the begining as "/scatter"
        unsigned num_entries = nrnmpi_myid == 0 ? (num_spikes + 1) : num_spikes;

        // each spike record in the file is max 48 chars
        const int spike_record_length = 48;

        // amount of data for recording spikes +  zero termination
        unsigned num_bytes = (sizeof(char) * num_entries * spike_record_length) + 1;

        char *spike_data = (char *) malloc(num_bytes);

        if(spike_data == NULL) {
            fprintf(stderr, "Error : Memory allocation failed for spike buffer I/O!\n");
#ifndef DISABLE_MPI
            MPI_Abort(MPI_COMM_WORLD, 1);
#else
            exit(-1);
#endif
        }

        strcpy(spike_data, "");

        if(nrnmpi_myid == 0) {
            strcat(spike_data, "/scatter\n");
        }

        // populate buffer with all entries
        int i;
        for(i = 0; i < num_spikes; i++) {
            char str[spike_record_length];
            int nstr = snprintf(str, spike_record_length, "%.3f\t%d\n", time[i], (int)gid[i]);
            if (nstr >= spike_record_length) {
                fprintf(stderr, "Error : Record written is larger than spike record buffer\n");
                free(spike_data);
#ifndef DISABLE_MPI
                MPI_Abort(MPI_COMM_WORLD, 1);
#else
                exit(-1);
#endif
            }
            strcat(spike_data, str);
        }

        // calculate offset into global file. note that we don't write
        // num_bytes but only "populated" characters
        unsigned long num_chars = strlen(spike_data);

#ifndef DISABLE_MPI
        unsigned long offset = 0;

        MPI_Exscan(&num_chars, &offset, 1, MPI_UNSIGNED_LONG, MPI_SUM, MPI_COMM_WORLD);

        if (nrnmpi_myid == 0) {
            offset = 0;
        }

        // write to file using parallel mpi i/o Remove it first in case it exists.
        // Must delete because MPI_File_open does not have a Truncate mode
        MPI_File fh;
        MPI_Status status;
        MPI_File_delete(filePath, MPI_INFO_NULL);
        MPI_File_open(MPI_COMM_WORLD, filePath, MPI_MODE_CREATE | MPI_MODE_WRONLY, MPI_INFO_NULL, &fh);
        MPI_File_write_at_all(fh, offset, spike_data, num_chars, MPI_BYTE, &status);

        MPI_File_close(&fh);
#else
        FILE *spike_file = fopen(filePath, "w");
        fprintf(spike_file, spike_data);
        fclose(spike_file);
#endif

        free(spike_data);

    ENDVERBATIM
}

