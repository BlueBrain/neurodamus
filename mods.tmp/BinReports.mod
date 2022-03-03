COMMENT
/**
 * Modified mod file
 *
 * Pointer is an object with Name of the cell, and the report
 *
 * How to use it:
 * Create the object with this information:
 *
 * receive: location,reportname,cellname,path,tstart,tend,dt,sizemapping,kind,sizeatributesmapping,iscParam
 * one object per cell to report.
 *
 *
 * AddVar(pointer to the variable (as in the older), mapping information)  so much mapping information as in siz
 */
ENDCOMMENT

NEURON {
        THREADSAFE
        POINT_PROCESS BinReport
        BBCOREPOINTER ptr : an object with two strings
        RANGE Dt
	RANGE tstart
	RANGE tstop
        RANGE ISC
}

PARAMETER {
	Dt = .1 (ms)
	tstart = 0 (ms)
	tstop  = 0 (ms)
        ISC = 0 (ms)
}

ASSIGNED {
	ptr
}


INITIAL {
VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
        if ((int)ISC)
            isc_init_connection();
        else
            records_finish_and_share();
#endif
#endif
ENDVERBATIM
}

VERBATIM
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
#include "reportinglib/Records.h"
#include "reportinglib/isc/iscAPI.h"

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
//extern double jimsRubbish;

typedef struct {
	char neuronName_[256];
	char rptName_[512];
}Data;

#endif
#endif

ENDVERBATIM

COMMENT

receive: location,reportname,cellname,path,gid,vgid,tstart,tend,dt,sizemapping,kind,sizeatributesmapping,iscParam
ENDCOMMENT
CONSTRUCTOR {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	Data** tempdata = (Data**)(&(_p_ptr));//???
	Data* data = 0;
	data = (Data*)hoc_Emalloc(sizeof(Data));
	hoc_malchk();
	if(ifarg(2) && hoc_is_str_arg(2) &&
			ifarg(3) && hoc_is_str_arg(3) &&
			ifarg(4) && hoc_is_str_arg(4) &&
			ifarg(5) && ifarg(6) &&
			ifarg(7) && ifarg(8) && ifarg(9) &&
			ifarg(10) &&
			ifarg(11) && hoc_is_str_arg(11) &&
			ifarg(12) &&
			ifarg(13) && hoc_is_str_arg(13)
	)
	{

		sprintf(data->neuronName_,"%s",gargstr(3));
		sprintf(data->rptName_,"%s/%s",gargstr(4),gargstr(2));
		//printf("%s\n",data->neuronName_);
		//printf("%s\n",data->rptName_);
		unsigned long gid,vgid;
		gid = (unsigned long) *getarg(5);
		vgid = (unsigned long) *getarg(6);
		//printf("Gid %d , Vgid %d\n",gid, vgid);

		tstart = *getarg(7);

		tstop = *getarg(8);

		Dt = *getarg(9);

		//printf("nRpsps received %f, nRpsps recorded %f \n",*getarg(14),reportingSteps);
		//printf("tstart %f , tend %f , dt %f\n",_tstart,_tend,_dt);
		int sizemapping,extramapping;
		sizemapping = (int)*getarg(10);
		extramapping = (int)*getarg(12);
		//printf("sizeMapping %d , extramapping %d\n",sizemapping, extramapping);
		//printf("Hasta aqui\n"); //up to here

		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);

                if (ifarg(14) && hoc_is_str_arg(14))
                {
                    ISC = 1.;
		    isc_add_report(data->rptName_, numberCell, gid, vgid, tstart, tstop, Dt, gargstr(13), gargstr(14));
                }
                else
                {
                    ISC = 0.;
                    records_add_report(data->rptName_,numberCell,gid, vgid, tstart,tstop , Dt,sizemapping,gargstr(11),extramapping,gargstr(13));
                }

		//printf("_________________ %s Creating\n",data->rptName_);

		*tempdata = data; //makes to data available to other procedures through ptr
	}
	else
	{
		//printf("There is an error creating report\n");
		int i = 1;
		while(ifarg(i))
		{
			if(i==1) printf("There is an error creating report\n");
			printf("It has arg %d: ", i);
			if(hoc_is_str_arg(i))
				printf("%s\n", gargstr(i));
			else
				printf("%.0lf\n", *getarg(i));
			i++;
		}

	}
#else
        static warning_shown = 0;
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


COMMENT
/*
	AddVariable  with the next data
		variable  A pointer to the value of the variable
		informacion about mapping
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
		int *ardata =NULL;
		int size = 1;
		ardata = (int *)hoc_Emalloc(sizeof(int)*size);
		hoc_malchk();
		//printf("Mapping info variable Size=%d\n",size);
		ardata[0]=(int) *getarg(2);
		//printf("records_add_var_with_mapping(data->rptName_=%s, data->neuronName_=%s,hoc_pgetarg(1)=%f,size=%d);",data->rptName_,data->neuronName_,hoc_pgetarg(1),size);
		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);

                if ((int)ISC)
                    isc_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), ardata);
                else
                    records_add_var_with_mapping(data->rptName_, numberCell, hoc_pgetarg(1), size, ardata);
	}
#endif
#endif
}
ENDVERBATIM
}

COMMENT
/*
	For extra mapping on graphics, , number of soma, axon, basal, etc
	this is need to share with the others to
*/
ENDCOMMENT
FUNCTION ExtraMapping() {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
	Data** tempdata = (Data**)(&(_p_ptr));
	Data* data = *tempdata;
	int *ardata =NULL;
	int i=1;
	while(ifarg(i))
	{
		i++;
	}
	int size = i-1;
	//printf("Adding extra mapping. Size=%d\n",size);
	if(size>0)
	{
		ardata = (int *)hoc_Emalloc(sizeof(int)*size);
		hoc_malchk();
		for(i=0;i<size;i++)
		{
			ardata[i]=(int) *getarg(i+1);
			//printf("Adding %d in position %d\n",ardata[i],i);
		}
		int numberCell;
		sscanf(data->neuronName_,"a%d",&numberCell);
		records_extra_mapping(data->rptName_, numberCell,size,ardata);
	}
#endif
#endif
}
ENDVERBATIM
}


PROCEDURE TimeStatistics() {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef DISABLE_REPORTINGLIB
         if ((int)ISC == 0)
  	     records_time_data();
#endif
#endif
}
ENDVERBATIM
}


VERBATIM
/** not executed in coreneuron and hence need empty stubs */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
ENDVERBATIM
