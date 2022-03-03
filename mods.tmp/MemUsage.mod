COMMENT
/**
 * @file MemUsage.mod
 * @brief
 * @author king
 * @date 2011-02-04
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

NEURON {
    THREADSAFE
    ARTIFICIAL_CELL MemUsage
}

VERBATIM
#ifndef CORENEURON_BUILD
#include <unistd.h>
#ifndef DISABLE_MPI
#include <mpi.h>
#endif
#endif
int nrn_mallinfo(int);
ENDVERBATIM

PARAMETER {
    minUsageMB = 0
    maxUsageMB = 0
    avgUsageMB = 0
    stdevUsageMB = 0
    rank = 0
    size = 0
}

INITIAL {
}

CONSTRUCTOR  {
VERBATIM
    int i_rank=0, i_size=1;
#ifndef DISABLE_MPI
    MPI_Comm_size(MPI_COMM_WORLD, &i_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &i_rank);
#endif
    rank = i_rank;
    size = i_size;
ENDVERBATIM
}

PROCEDURE print_mem_usage() {
VERBATIM
#ifndef CORENEURON_BUILD
/**
 * Gather memory usage statistics for all nodes in the network, printing to the console
 *
 * Use by default the VmRSS of /proc/self/statm to report the memory usage of Neurodamus
 * VmRSS: Resident set size.  Note that the value here is the sum of RssAnon, RssFile, and RssShmem.
 * RssAnon: Size of resident anonymous memory.  (since Linux 4.5).
 * RssFile: Size of resident file mappings.  (since Linux 4.5).
 * RssShmem: Size of resident shared memory (includes System V shared memory, mappings from tmpfs(5),
 * and shared anonymous mappings).  (since Linux 4.5)
 * Based on VmRSS we calculate all the memory of the Neurodamus process which resides on the main memory.
 * The size might not be decreasing because of the page not being released by the system even after a
 * deallocation of memory.
 * This is the same way that memory is reported in CoreNEURON.
 * In case /proc/self/statm cannot be opened, fall back to the old memory reporting with mallinfo.
 * argument 6 to nrn_mallinfo includes memory mapped files (m.hblkhd + m.arena)
 * argument 1 to nrn_mallinfo returns uordblks which is "total size of memory occupied by chunks handed out by malloc"
 */
    FILE *file;
    file = fopen("/proc/self/statm", "r");
    double usageMB;
    if (file != NULL) {
        unsigned long long int data_size;
        fscanf(file, "%llu %llu", &data_size, &data_size);
        fclose(file);
        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);
    } else {
        usageMB = (double) nrn_mallinfo(1) / (double) (1024*1024);
    }
#ifndef DISABLE_MPI
    MPI_Reduce( &usageMB, &minUsageMB, 1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD );
    MPI_Reduce( &usageMB, &maxUsageMB, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD );
    MPI_Reduce( &usageMB, &avgUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );

    avgUsageMB /= size;

    MPI_Bcast( &avgUsageMB, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD );

    double diffSquared = (usageMB-avgUsageMB)*(usageMB-avgUsageMB);
    MPI_Reduce( &diffSquared, &stdevUsageMB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD );
    stdevUsageMB = sqrt( stdevUsageMB/size);

    if( rank == 0 ) {
        printf( "\e[90m[DEBUG] Memusage [MB]: Max=%.2lf, Min=%.2lf, Mean(Stdev)=%.2lf(%.2lf)\e[39m\n",\
                maxUsageMB, minUsageMB, avgUsageMB, stdevUsageMB );
    }
#else
    printf( "\e[90m[DEBUG] Memusage [MB]: %.2lf \e[39m\n", usageMB );
#endif

#endif
ENDVERBATIM
}


PROCEDURE print_node_mem_usage() {
VERBATIM
#ifndef CORENEURON_BUILD
    FILE *file;
    file = fopen("/proc/self/statm", "r");
    double usageMB;
    if (file != NULL) {
        unsigned long long int data_size;
        fscanf(file, "%llu %llu", &data_size, &data_size);
        fclose(file);
        usageMB = (data_size * sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);
    } else {
        usageMB = (double) nrn_mallinfo(6) / (double) (1024*1024);
    }
    printf( "\e[90m[DEBUG] Node: %.0lf Memusage [MB]: %.2lf \e[39m\n", rank, usageMB );
#endif
ENDVERBATIM
}
