COMMENT
If the local variable step method is used then the only variables that should
be added are variables of the cell in which this FileRecord
has been instantiated.
ENDCOMMENT

NEURON {
        POINT_PROCESS HDF5Reader
        POINTER ptr
}

PARAMETER {
}

ASSIGNED {
        ptr
}

INITIAL {
	closeFile()
}

NET_RECEIVE(w) {
}

VERBATIM

#include "/bglscratch/bbp/build/libraries/hdf5/include/hdf5.h"
//#include "mpi.h"

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
	/* hdf5 version */
	hid_t file_;
	float * datamatrix_;
	char name_group[256];
	hsize_t rowsize_;
	hsize_t columnsize_;
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

#define dp double*

ENDVERBATIM

CONSTRUCTOR { : double - loc of point process ??? ,string filename
VERBATIM {
	char nameoffile[512];
	if(ifarg(2) && hoc_is_str_arg(2)) {
		//printf("Trying to open\n");
		INFOCAST;
        	Info* info = 0;
		strncpy(nameoffile, gargstr(2),256);
		info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk(); 
		//int mpi_size, mpi_rank;
		//MPI_Info mpi_info  = MPI_INFO_NULL;
		//MPI_Comm comm  = MPI_COMM_WORLD;

		/*
		* Initialize MPI
		*/
		//MPI_Comm_size(comm, &mpi_size);
		//MPI_Comm_rank(comm, &mpi_rank);  

		/* 
		* Set up file access property list with parallel I/O access
		*/
		//hid_t	plist_id;        /* property list identifier( access template) */
		//plist_id = H5Pcreate(H5P_FILE_ACCESS);
		//H5Pset_fapl_mpio(plist_id, comm, mpi_info);

		
		//info->file_ = H5Fopen(nameoffile,H5F_ACC_RDONLY,plist_id);
		info->file_ = H5Fopen(nameoffile,H5F_ACC_RDONLY,H5P_DEFAULT);
		info->datamatrix_=NULL;
		info->name_group[0]='\0';
		if(info->file_>=0)
		{
			//printf("Correctly open %s\n",nameoffile);
		}
		else
		{
			info->file_ = -1;
			printf("ERROR: It's not possible to open: %s\n",nameoffile);
		}
		*ip = info;
	}

}
ENDVERBATIM
}

DESTRUCTOR {
VERBATIM { 
	INFOCAST; Info* info = *ip; 
	if(info->file_>=0)
	{
		//printf("Trying to close\n");
		H5Fclose(info->file_);
		//printf("Close\n");
		info->file_ = -1;
	}
	if(info->datamatrix_ != NULL)
	{
		free(info->datamatrix_);
		info->datamatrix_ = NULL;
	}
}
ENDVERBATIM
}

FUNCTION loadData() {
VERBATIM { 
	INFOCAST; 
	Info* info = *ip;
	if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))
	{
		char name[256];
		strncpy(name,gargstr(1),256);
		if(strncmp(info->name_group,name,256))
		{
			hsize_t dims[2],offset[2];
			offset[0] = 0 ; offset [1] = 0;
			hid_t dataset_id, dataspace;
			dataset_id = H5Dopen(info->file_, name);
			if(dataset_id < 0)
			{
				printf("Error accessing to: %s, on file %s\n",info->name_group,info->file_);
				return 0;
			}
			strncpy(info->name_group,name,256);
			dataspace = H5Dget_space(dataset_id);
			int dimensions = H5Sget_simple_extent_ndims(dataspace);
			//printf("Dimensions:%d\n",dimensions);
			H5Sget_simple_extent_dims(dataspace,dims,NULL);
			//printf("Accessing to %s , nrow:%lu,ncolumns:%lu\n",info->name_group,(unsigned long)dims[0],(unsigned long)dims[1]);
			info->rowsize_ = dims[0];
			info->columnsize_ = dims[1];
			if(info->datamatrix_ != NULL)
			{
				//printf("Freeeing memory \n ");
				free(info->datamatrix_);
			}
			info->datamatrix_ = (float *) malloc(sizeof(float) *(info->rowsize_*info->columnsize_)); 
			//info->datamatrix_ = (float *) hoc_Emalloc(sizeof(float) *(info->rowsize_*info->columnsize_)); hoc_malchk();
			// Last line fails, corrupt memory of argument 1 and  probably more
			H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL);
			hid_t dataspacetogetdata=H5Screate_simple(2,dims,NULL);
			H5Dread(dataset_id,H5T_NATIVE_FLOAT,dataspacetogetdata,H5S_ALL,H5P_DEFAULT,info->datamatrix_);
			H5Sclose(dataspace);
			H5Sclose(dataspacetogetdata);
			H5Dclose(dataset_id);
			//printf("Working , accessed %s , on argstr1 %s\n",info->name_group,gargstr(1));
			return 0;
		}
			return 0;
	}
			return 0;

}
ENDVERBATIM
}

FUNCTION numberofrows() { : string cellname
VERBATIM { 
	INFOCAST; 
	Info* info = *ip;
	//printf("(Inside number of rows)Number of rows %s\n",gargstr(1));
	if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))
	{
		char name[256];
		strncpy(name,gargstr(1),256);
		if(strncmp(info->name_group,name,256) == 0)
		{
			//printf("Returning :%d\n",(int)info->rowsize_);
			int res = (int) info->rowsize_;
			//printf("Res :%d\n",res);
			return res;  
		}
		//printf("Numberofrows Error on the name of last loaded data: trying to access:%s loaded:%s\n",name,info->name_group);
		return 0;
	}
	else
	{
		return 0;
	}
}
ENDVERBATIM
}

FUNCTION getData() {
VERBATIM { 
	INFOCAST; 
	Info* info = *ip;
	if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && ifarg(3))
	{
		char name[256];
		strncpy(name,gargstr(1),256);
		if(strncmp(info->name_group,name,256) == 0)
		{
			hsize_t row,column;
			row = (hsize_t) *getarg(2);
			column = (hsize_t) *getarg(3);
			if(row<0 || row >=info->rowsize_ || column < 0 || column>=info->columnsize_)
			{
				printf("ERROR: trying to access to a row and column erroneus on %s, size: %d,%d accessing to %d,%d\n ",name,info->rowsize_,info->columnsize_,row,column);
				return 0;
			}
			float res = info->datamatrix_[row*info->columnsize_ + column];
			return res;
		}
		printf("(Getting data)Error on the name of last loaded data: access:%s loaded:%s\n",name,info->name_group);
		return 0;
	}
	else
	{
		//printf("ERROR:Error on number of rows of \n");
		return 0;
	}
}
ENDVERBATIM
}

FUNCTION closeFile() {
VERBATIM { 
	INFOCAST; 
	Info* info = *ip;
	if(info->file_ >=0)
	{
		//printf("Trying to close\n");
		H5Fclose(info->file_);
		//printf("Close\n");
		info->file_ = -1;
	}
	if(info->datamatrix_ != NULL)
	{
		free(info->datamatrix_);
		info->datamatrix_ = NULL;
		}
}
ENDVERBATIM
}
