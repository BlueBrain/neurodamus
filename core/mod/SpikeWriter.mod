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

#include <mpi.h>

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
            if(nrnmpi_myid == 0) {
                printf(" Error : No spike file path provided, can't write spikes! \n");
                return 1;
            }
        }

        // rank 0 write extra string at the begining as "/scatter"
        unsigned num_entries = nrnmpi_myid == 0 ? (num_spikes + 1) : num_spikes;

        // each spike record in the file is max 48 chars
        const int spike_record_length = 48;

        // amount of data for recording spikes
        unsigned num_bytes = (sizeof(char) * num_entries * spike_record_length);

        char *spike_data = (char *) malloc(num_bytes);

        if(spike_data == NULL) {
            printf("Error : Memory allocation failed for spike buffer I/O!\n");
            return 1;
        }

        strcpy(spike_data, "");

        if(nrnmpi_myid == 0) {
            strcat(spike_data, "/scatter\n");
        }

        // populate buffer with all entries
        int i;
        for(i = 0; i < num_spikes; i++) {
            char str[48];
            snprintf(str, 48, "%.3f\t%d\n", time[i], (int)gid[i]);
            strcat(spike_data, str);
        }

        // calculate offset into global file. note that we don't write
        // num_bytes but only "populated" characters
        unsigned long num_chars = strlen(spike_data);

        unsigned long offset = 0;
        MPI_Exscan(&num_chars, &offset, 1, MPI_UNSIGNED_LONG, MPI_SUM, MPI_COMM_WORLD);

        // write to file using parallel mpi i/o
        MPI_File fh;
        MPI_Status status;

        MPI_File_open(MPI_COMM_WORLD, filePath, MPI_MODE_CREATE | MPI_MODE_WRONLY, MPI_INFO_NULL, &fh);
        MPI_File_write_at_all(fh, offset, spike_data, num_chars, MPI_BYTE, &status);

        MPI_File_close(&fh);

    ENDVERBATIM
}

