COMMENT
Modified mod file

Pointer is an object with Name of the cell, and the report

How to use it:
Create the object with this information:

receive: location,reportname,cellname,path,tstart,tend,dt,sizemapping,kind,sizeatributesmapping
one object per cell to report.


AddVar(pointer to the variable (as in the older), mapping information)  so much mapping information as in siz


ENDCOMMENT

NEURON {
        THREADSAFE
        POINT_PROCESS SonataReport
        BBCOREPOINTER ptr : an object with two strings
        RANGE Dt
	RANGE tstart
	RANGE tstop
}

PARAMETER {
	Dt = .1 (ms)
	tstart = 0 (ms)
	tstop  = 0 (ms)
}

ASSIGNED {
	ptr
}


INITIAL {
}

VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include <stdint.h>
#include <bbp/sonata/reports.h>
#ifndef NRN_VERSION_GTEQ_8_2_0
extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
#endif

typedef struct {
    char neuronName_[256];
    char rptName_[512];
} Data;

#endif
#endif
ENDVERBATIM

COMMENT
receive: location,reportname,path,tstart,tend,dt,kind
ENDCOMMENT
CONSTRUCTOR {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = 0;
    data = (Data*)hoc_Emalloc(sizeof(Data));
    hoc_malchk();
    if(ifarg(2) && hoc_is_str_arg(2) &&
        ifarg(3) && hoc_is_str_arg(3) &&
        ifarg(4) && ifarg(5) && ifarg(6) &&
        ifarg(7) && hoc_is_str_arg(7)
    )
    {
        sprintf(data->rptName_,"%s/%s",gargstr(3),gargstr(2));
        tstart = *getarg(4);
        tstop = *getarg(5);
        Dt = *getarg(6);

        sonata_create_report(data->rptName_, tstart, tstop, Dt, gargstr(7), gargstr(8));

        *tempdata = data; //makes to data available to other procedures through ptr
    }
    else
    {
        int i = 1;
        while(ifarg(i))
        {
            if(i==1)
                printf("There is an error creating report\n");
            printf("It has arg %d: ", i);
            if(hoc_is_str_arg(i))
                printf("%s\n",gargstr(i));
            else
                printf("%d\n",(int)*getarg(i));
            i++;
        }

    }
#else
        static int warning_shown = 0;
        if (ifarg(2) && hoc_is_str_arg(2))
        {
            if (warning_shown == 0)
            {
                printf("WARNING: BinReports Constructor(): Trying to create and write report %s while the NEURODAMUS_DISABLE_REPORTINGLIB is set to ON, ignoring... \n", gargstr(2));
                warning_shown++;
            }
        }
#endif
#endif
}
ENDVERBATIM
}

FUNCTION AddNode() {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = *tempdata;
    if(ifarg(1))
    {
        char population_name[256] = "All";
        unsigned long population_offset = 0;
        if (ifarg(2)) {
            sprintf(population_name,"%s", gargstr(2));
        }
        if (ifarg(3)) {
            population_offset = (unsigned long) *getarg(3);
        }
        unsigned long node_id = (unsigned long) *getarg(1);
        sonata_add_node(data->rptName_, population_name, population_offset, node_id);
    }
#endif
#endif
}
ENDVERBATIM
}

COMMENT
/*
	AddVariable  with the next data
		variable  A pointer to the value of the variable
		information about mapping
*/
ENDCOMMENT
FUNCTION AddVar() {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
    Data** tempdata = (Data**)(&(_p_ptr));
    Data* data = *tempdata;
    if(ifarg(1))
    {
        int element_id = (int)*getarg(2);
        int node_id = (int) *getarg(3);
        char population_name[256] = "All";
        if (ifarg(4)) {
            sprintf(population_name,"%s", gargstr(4));
        }
#ifdef NRN_MECHANISM_DATA_IS_SOA
        sonata_add_element_handle(data->rptName_, population_name, node_id, element_id, [x=hoc_hgetarg<double>(1)]() { return *x; });
#else
        sonata_add_element(data->rptName_, population_name, node_id, element_id, hoc_pgetarg(1));
#endif
    }
#endif
#endif
}
ENDVERBATIM
}

VERBATIM
/** not executed in coreneuron and hence need empty stubs */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) { }
ENDVERBATIM
