COMMENT
/**
 * @file HDF5reader.mod
 * @brief 
 * @author king
 * @date 2009-10-23
 * @remark Copyright © BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.
 */
ENDCOMMENT

COMMENT
This is intended to serve two purposes.  One as a general purpose reader for HDF5 files with a basic set of
accessor functions.  In addition, it will have special handling for our synapse 
data files such that they can be handled
more efficiently in a  massively parallel manner.
ENDCOMMENT

NEURON {
        ARTIFICIAL_CELL HDF5Reader
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

#define H5_USE_16_API 1
//#include "/opt/hdf5/include/hdf5.h"  //-linsrv
//#include "/bgscratch/bbptmp/build/libraries/hdf5/include/hdf5.h"  //-blugene
#include "/users/delalond/Dev/bglib1.5/dep-install/include/hdf5.h" // Cray XT5
#include "mpi.h"
#include <stdlib.h>

/// NEURON utility functions we want to use
extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);
extern double* vector_vec(void* vv);
extern int vector_capacity(void* vv);
extern void* vector_arg(int);
extern void* vector_resize();

/**
 * Hold persistenet HDF5 data such as file handle and info about latest dataset loaded
 */
struct Info {
    
    /// data members for general HDF5 usage
    hid_t file_;
    float * datamatrix_;
    char name_group[256];
    hsize_t rowsize_;
    hsize_t columnsize_;
    
    /// For coordinated synapse loading (may not be needed for smaller circuits) 
    int gid_;
    int dataCount;
    int dataIndex;
    float** dataCollection;
    int *rowCollection;
    int *colCollection;
    int *gidCollection;
};

typedef struct Info Info;

///Utility macro to make the NEURON pointer accessible for reading and writing (seems like we have more levels of indirection than necessary - JGK)
#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

#define dp double*

/**
 * Utility function to ensure that all members of an Info struct are initialized.
 */
void initInfo( Info *info )
{
    info->file_ = -1;
    info->datamatrix_ = NULL;
    info->name_group[0] = '\0';
    info->rowsize_ = 0;
    info->columnsize_ = 0;
    info->gid_ = 0;
    info->dataCount = 0;
    info->dataIndex = 0;
    info->dataCollection = NULL;
    info->rowCollection = NULL;
    info->colCollection = NULL;
    info->gidCollection = NULL;
}

/**
 * Callback function for H5Giterate - this will load data for a dataset into memory.  It will be
 * kept in a buffer until explicitly freed.  This will be after all exchanges have completed.
 */
herr_t loadShareData( hid_t loc_id, const char *name, void *opdata )
{
    INFOCAST;
    Info* info = *ip;
    assert( info->file_ >= 0 );
    
    //fprintf( stderr, "open dataset %s\n", name );
    
    //make sure we are using a dataset that corresponds to a gid
    info->gid_ = atoi( name+1 );
    char rebuild[128];
    sprintf( rebuild, "a%d", info->gid_ );
    if( strcmp( rebuild, name ) != 0 ) {
        //non-synapse dataset, but not an error (could just be the version info)
        //fprintf( stderr, "ignore non-gid dataset\n" );
        return 0;
    }
    
    hsize_t dims[2] = {0,0}, offset[2] = {0,0};
    hid_t dataset_id, dataspace;
    dataset_id = H5Dopen(info->file_, name);
    if(dataset_id < 0)
    {
        printf("Error accessing to dataset %s in synapse file\n", name);
        return -1;
    }
    
    dataspace = H5Dget_space( dataset_id );
    int dimensions = H5Sget_simple_extent_ndims(dataspace);
    
    H5Sget_simple_extent_dims( dataspace, dims, NULL );
    info->rowsize_ = (unsigned long) dims[0];
    if( dimensions > 1 )
        info->columnsize_ = dims[1];
    else
        info->columnsize_ = 1;        
    
    info->datamatrix_ = (float *) malloc( sizeof(float) * (info->rowsize_*info->columnsize_) ); 
    H5Sselect_hyperslab( dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL );
    hid_t dataspacetogetdata = H5Screate_simple(dimensions,dims,NULL);
    H5Dread( dataset_id, H5T_NATIVE_FLOAT, dataspacetogetdata, H5S_ALL, H5P_DEFAULT, info->datamatrix_ );
    H5Sclose( dataspace );
    H5Sclose( dataspacetogetdata );
    H5Dclose( dataset_id );
    
    return 1;
}

/**
 * Open an HDF5 file for reading.  In the case of synapse data, the data may be loaded immediately to improve read performance.
 * Some or all of the synapse data will be loaded with the intent to exchange that data across nodes in order to ship required
 * synapse data to the appropriate cpu.
 * 
 * @param filename File to open
 * @param nNodesPerFile 0: open file, but don't load data; 1: open file and read entire contents; N: read protion of file
 * @param startRank used to help calculate data range to load when file subportion is loaded
 * @param myRank used to help calculate data range to load when file subportion is loaded
 */
int openFile( Info* info, const char *filename, int nRanksPerFile, int startRank, int myRank )
{
    if( info->file_ != -1 ) {
        H5Fclose(info->file_);
    }
    
    //fprintf( stderr, "arg check: %s %d %d %d\n", filename, nRanksPerFile, startRank, myRank );

    info->file_ = H5Fopen( filename, H5F_ACC_RDONLY, H5P_DEFAULT );
    info->name_group[0]='\0';
    if( info->file_ < 0 ) {
        info->file_ = -1;
        printf( "ERROR: Failed to open synapse file: %s\n", filename );
        return -1;
    }
    
    //fprintf( stderr, "file opened\n" );
    
    if( nRanksPerFile == 0 ) {
        //fprintf( stderr, "normal case - return now\n" );
        // don't need to load data yet, return now
        return 0;
    }
    
    int nDatasetsToImport=0, startIndex=0;
    hsize_t nObjects;
    H5Gget_num_objs( info->file_, &nObjects );
    
    // get some stats on how big the file is    
    fprintf( stderr, "nObjects %d\n", (int) nObjects );
    
    if( nRanksPerFile == 1 ) {
        nDatasetsToImport = (int) nObjects;
    }    
    else {
        // need to determine which indices to read
        nDatasetsToImport = (int) nObjects / nRanksPerFile;
        if( nObjects%nRanksPerFile != 0 )
            nDatasetsToImport++;
        
        startIndex = (myRank-startRank)*nDatasetsToImport;
        if( startIndex + nDatasetsToImport > (int) nObjects ) {
            nDatasetsToImport = (int) nObjects - startIndex;
            if( nDatasetsToImport <= 0 ) {
                //fprintf( stderr, "No need to import any data on rank %d since all %d are claimed\n", myRank, (int) nObjects );
                return 0;
            }
        }        
    }
    
    info->dataCount += nDatasetsToImport;
    info->dataCollection = (float**) realloc ( info->dataCollection, sizeof(float*)*info->dataCount );
    info->rowCollection = (int*) realloc ( info->rowCollection, sizeof(int)*info->dataCount );
    info->colCollection = (int*) realloc ( info->colCollection, sizeof(int)*info->dataCount );
    info->gidCollection = (int*) realloc ( info->gidCollection, sizeof(int)*info->dataCount );
    
    //fprintf( stderr, "load datasets %d through %d (max %d)\n", startIndex, startIndex+nDatasetsToImport, (int) nObjects );
    
    int i, verify=startIndex, result;
    for( i=startIndex; i<startIndex+nDatasetsToImport && i<nObjects; i++ ) {
        assert( verify == i );
        result = H5Giterate( info->file_, "/", &verify, loadShareData, NULL );
        if( result != 1 )
            continue;
            
        info->dataCollection[info->dataIndex] = info->datamatrix_;
        info->rowCollection[info->dataIndex] = (int) info->rowsize_;
        info->colCollection[info->dataIndex] = (int) info->columnsize_;
        info->gidCollection[info->dataIndex] = info->gid_;
        info->dataIndex++;
    }
    
    info->datamatrix_ = NULL;
    info->rowsize_ = 0;
    info->columnsize_ = 0;
    info->gid_ = 0;
        
    return 0;
}

ENDVERBATIM

CONSTRUCTOR { : double - loc of point process ??? ,string filename
VERBATIM {
    char nameoffile[512];
    int nFiles = 1;
    
    //redirect();
    
    if( ifarg(2) ) {
        nFiles = *getarg(2);
    }
    
    //fprintf( stderr, "continue? %d %d %d\n", nFiles, ifarg(1), hoc_is_str_arg(1) );
    
    if(ifarg(1) && hoc_is_str_arg(1)) {
        INFOCAST;
        Info* info = 0;
        
        strncpy(nameoffile, gargstr(1),256);
        info = (Info*) hoc_Emalloc(sizeof(Info)); hoc_malchk();
        initInfo( info );
        *ip = info;
        
        //fprintf( stderr, "%s\n", nameoffile );
        
        if( nFiles == 1 ) {
            // normal case - open a file and be ready to load data as needed
            openFile( info, nameoffile, 0, 0, 0 );
        }
        else
        {
            // testing - can we read from a single nrn.h5.X file, take a subset of the datasets and then be ready to communicate
            //  the available local data to the other cpus in the network
            
            int mpi_size, mpi_rank;
            MPI_Comm_size( MPI_COMM_WORLD, &mpi_size );
            MPI_Comm_rank( MPI_COMM_WORLD, &mpi_rank );
            
            //fprintf( stderr, "%d vs %d\n", mpi_size, nFiles );
            
            // need to determine if I open multiple files per cpu or multiple cpus share a file
            if( mpi_size > nFiles ) { // multiple cpus per file
                int nRanksPerFile = (int) mpi_size / nFiles;
                if( mpi_size % nFiles != 0 )
                    nRanksPerFile++;
                    
                //fprintf( stderr, "nRanksPerFile %d = %d/%d\n", nRanksPerFile, mpi_size, nFiles );
                
                if( nRanksPerFile * nFiles > mpi_size ) { // no files left for this rank
                    info->file_ = -1;
                    return 0;
                }
                
                int fileIndex = (int) mpi_rank / nRanksPerFile;  //this should be truncated
                int startRank = fileIndex * nRanksPerFile;
                
                sprintf( nameoffile, "%s.%d", gargstr(1), fileIndex );
                //fprintf( stderr, "I should open file %s\n", nameoffile );
                
                openFile( info, nameoffile, nRanksPerFile, startRank, mpi_rank );
                
            } else {
                // one or more files per cpu - any file opened should load all the data.
                int nFilesPerRank = nFiles / mpi_size;
                //fprintf( stderr, "nFilesPerRank %d = %d/%d\n", nFilesPerRank, nFiles, mpi_size );
                
                if( nFiles % mpi_size != 0 ) {
                    nFilesPerRank++;
                }
                int startFile = mpi_rank * nFilesPerRank;
                if( startFile+nFilesPerRank > nFiles ) {
                    nFilesPerRank = nFiles-startFile;
                    if( nFilesPerRank <= 0 ) {
                        info->file_ = -1;
                        return 0;
                    }
                }
                
                int fileIndex=0;
                for( fileIndex=0; fileIndex<nFilesPerRank; fileIndex++ ) {
                    sprintf( nameoffile, "%s.%d", gargstr(1), startFile+fileIndex );
                    openFile( info, nameoffile, 1, 0, 0 );
                }
            }
        }
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

FUNCTION redirect() {
VERBATIM {
    FILE *fout;
    char fname[128];
    
    int mpi_size, mpi_rank;
    //fprintf( stderr, "rank %d\n", getpid() );
    //sleep(20);

    
    // get MPI info
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);  
    
    if( mpi_rank != 0 ) {    
        sprintf( fname, "NodeFiles/%d.%dnode.out", mpi_rank, mpi_size );
        fout = freopen( fname, "w", stdout );
        if( !fout ) {
            fprintf( stderr, "failed to redirect.  Terminating\n" );
            exit(0);
        }
        
        sprintf( fname, "NodeFiles/%d.%dnode.err", mpi_rank, mpi_size );
        fout = freopen( fname, "w", stderr );
        setbuf( fout, NULL );
    }
}
ENDVERBATIM
}

FUNCTION checkVersion() {
VERBATIM {
    INFOCAST; 
    Info* info = *ip;
    int mpi_size, mpi_rank;

    // get MPI info
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);  
    
    int versionNumber = 0;
    
    //check version for synapse file; must be version 1 -> only have processor 0 do this to avoid output overload on errors
    if( mpi_rank == 0 )
    {
        hid_t dataset_id = H5Dopen( info->file_, "version" );
        if( dataset_id < 0 ) //no version info - must be version 0
        {
            fprintf( stderr, "Error. Incompatible synapse version file (given version 0 file, require version 1).\n" );
            fprintf( stderr, "Terminating" );
            MPI_Abort( MPI_COMM_WORLD, 27 );
        }
        
        H5Aread( H5Aopen_name( dataset_id, "attr" ), H5T_NATIVE_INT, &versionNumber );
        if( versionNumber != 1 )
        {
            fprintf( stderr, "Error. Incompatible synapse version file (given version %d file, require version 1).\n", versionNumber );
            fprintf( stderr, "Terminating" );
            MPI_Abort( MPI_COMM_WORLD, 28 );
        }
        
        H5Dclose(dataset_id);
    }
    return 0;
}
ENDVERBATIM
}

FUNCTION loadData() {
VERBATIM { 
    INFOCAST; 
    Info* info = *ip;
    
    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))
    {
        //fprintf( stderr, "loadData old style\n" );
        char name[256];
        strncpy(name,gargstr(1),256);
        if(strncmp(info->name_group,name,256))
        {
            hsize_t dims[2] = {0,0},offset[2] = {0,0};
            offset[0] = 0 ; offset [1] = 0;
            hid_t dataset_id, dataspace;
            dataset_id = H5Dopen(info->file_, name);
            if(dataset_id < 0)
            {
                printf("Error accessing to dataset %s in synapse file\n", name);
                return -1;
            }
            strncpy(info->name_group,name,256);
            dataspace = H5Dget_space(dataset_id);
            int dimensions = H5Sget_simple_extent_ndims(dataspace);
            //printf("Dimensions:%d\n",dimensions);
            H5Sget_simple_extent_dims(dataspace,dims,NULL);
            //printf("Accessing to %s , nrow:%lu,ncolumns:%lu\n",info->name_group,(unsigned long)dims[0],(unsigned long)dims[1]);
            info->rowsize_ = (unsigned long)dims[0];
            if( dimensions > 1 )
                info->columnsize_ = dims[1];
            else
                info->columnsize_ = 1;
            //printf("\n Size of data is row= [%d], Col = [%lu]\n", dims[0], (unsigned long)dims[1]);
            if(info->datamatrix_ != NULL)
            {
                //printf("Freeeing memory \n ");
                free(info->datamatrix_);
            }
            info->datamatrix_ = (float *) malloc(sizeof(float) *(info->rowsize_*info->columnsize_)); 
            //info->datamatrix_ = (float *) hoc_Emalloc(sizeof(float) *(info->rowsize_*info->columnsize_)); hoc_malchk();
            // Last line fails, corrupt memory of argument 1 and  probably more
            H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL);
            hid_t dataspacetogetdata=H5Screate_simple(dimensions,dims,NULL);
            H5Dread(dataset_id,H5T_NATIVE_FLOAT,dataspacetogetdata,H5S_ALL,H5P_DEFAULT,info->datamatrix_);
            H5Sclose(dataspace);
            H5Sclose(dataspacetogetdata);
            H5Dclose(dataset_id);
            //printf("Working , accessed %s , on argstr1 %s\n",info->name_group,gargstr(1));
            return 0;
        }
        return 0;
    } else if( ifarg(1) ) {
        int gid = *getarg(1);
        int gidIndex=0;
        
        for( gidIndex=0; gidIndex<info->dataCount; gidIndex++ ) {
            if( info->gidCollection[gidIndex] == gid ) {
                info->datamatrix_ = info->dataCollection[gidIndex];
                info->rowsize_ = info->rowCollection[gidIndex];
                info->columnsize_ = info->colCollection[gidIndex];
                
                sprintf( info->name_group, "a%d", gid );
                return 0;
            }
        }
        
        //if we reach here, did not find data
        fprintf( stderr, "Error: failed to find data for gid %d\n", gid );
    }
    
    return 0;
}
ENDVERBATIM
}

FUNCTION getNoOfColumns(){ : string cellname
VERBATIM { 
    INFOCAST;
    Info* info = *ip;
    //printf("(Inside number of Col)Number of Col %s\n",gargstr(1));
    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))
    {
        char name[256];
        strncpy(name,gargstr(1),256);
        if(strncmp(info->name_group,name,256) == 0)
        {
            //printf("Returning :%d\n",(int)info->rowsize_);
            int res = (int) info->columnsize_;
            //printf("Res :%d\n",res);
            return res;
        }
        //printf("NumberofCol Error on the name of last loaded data: trying to access:%s loaded:%s\n",name,info->name_group);
        return 0;
    }
    else
    {
        return 0;
    }
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




FUNCTION getColumnDataRange() {
VERBATIM { 
    INFOCAST; 
    Info* info = *ip;
    void* pdVec = NULL;
    double* pd  = NULL;
    int i = 0;
    int nStart, nEnd, count;
    if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )
    {
        char name[256];
        strncpy(name,gargstr(1),256);
        if(strncmp(info->name_group,name,256) == 0)
        {
            hsize_t column;
            column  = (hsize_t) *getarg(2);
            if(column<0 || column >=info->columnsize_ )
            {
                printf("ERROR: trying to access to a column erroneus on %s, size: %d,%d accessing to column %d\n ",name,info->rowsize_,info->columnsize_,column);
                return 0;
            }
            pdVec = vector_arg(3);
            nStart = (int)*getarg(4);
            nEnd  = (int)*getarg(5);
            vector_resize(pdVec, nEnd-nStart+1);
            pd = vector_vec(pdVec);
            count =0;
            for( i=nStart; i<=nEnd; i++){
                pd[count] = info->datamatrix_[i*info->columnsize_ + column];
                count = count +1;
                //printf("\n Filling [%f]", pd[i]);
            }
            //float res = info->datamatrix_[row*info->columnsize_ + column];
            return 1;
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



COMMENT
/**
 * Load all the data from a single column of active dataset into a NEURON Vector object
 *
 * @param dataset name - used to confirm that the active dataset matches what is requested
 * @param column index
 * @param Vector object to fill - resized as needed to hold the available data
 */
ENDCOMMENT
FUNCTION getColumnData() {
VERBATIM { 
    INFOCAST; 
    Info* info = *ip;
    void* pdVec = NULL;
    double* pd  = NULL;
    int i = 0;
    if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )
    {
        char name[256];
        strncpy(name,gargstr(1),256);
        if(strncmp(info->name_group,name,256) == 0)
        {
            hsize_t column;
            column  = (hsize_t) *getarg(2);
            if(column<0 || column >=info->columnsize_ )
            {
                printf("ERROR: trying to access to a column erroneus on %s, size: %d,%d accessing to column %d\n ",name,info->rowsize_,info->columnsize_,column);
                return 0;
            }
            pdVec = vector_arg(3);
            vector_resize(pdVec, (int) info->rowsize_);
            pd = vector_vec(pdVec);
            for( i=0; i<info->rowsize_; i++){
                pd[i] = info->datamatrix_[i*info->columnsize_ + column];
                //printf("\n Filling [%f]", pd[i]);
            }
            //float res = info->datamatrix_[row*info->columnsize_ + column];
            return 1;
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



COMMENT
/**
 * Retrieve the value for an attribute of the active dataset.  Expected to contain only one value of double type
 * 
 * @param dataset name
 * @param attribute name
 */
ENDCOMMENT
FUNCTION getAttributeValue() {
VERBATIM
    INFOCAST; 
    Info* info = *ip;
    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && hoc_is_str_arg(2) )
    {
        hid_t dataset_id = H5Dopen( info->file_, gargstr(1) );
        if( dataset_id < 0 )
        {
            fprintf( stderr, "Error: no dataset with name %s available.\n", gargstr(1) );
            return 0;
        }
        
        double soughtValue;
        hid_t attr_id = H5Aopen_name( dataset_id, gargstr(2) );
        if( attr_id < 0 ) {
            fprintf( stderr, "Error: failed to open attribute %s\n", gargstr(2) );
            return 0;
        }
        H5Aread( attr_id, H5T_NATIVE_DOUBLE, &soughtValue );
        H5Dclose(dataset_id);
        
        return soughtValue;
    }
    
    return 0;
ENDVERBATIM
}


FUNCTION exchangeSynapses() {
VERBATIM
/**
 * @param gidvec hoc vector containing list of gids on local cpu
 */
if( ifarg(1) ) {
    INFOCAST; 
    Info* info = *ip;
    
    void* vv = vector_arg(1);
    int gidCount = vector_capacity(vv);
    double *gidList = vector_vec(vv);
    
    //fprintf( stderr, "will be getting data for %d gids, sharing %d\n", gidCount, info->dataIndex ); 
    
    int mpi_size, mpi_rank;
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);
        
    int *gidTransmissionCounts = (int*) malloc (sizeof(int)*mpi_size);
    
    if( info->dataIndex != info->dataCount ) {
        // expected since version datasets throw off dataCount
        //fprintf( stderr, "Warning - why shouldn't data index and data count be the same.  Over estimated the count?\n" );
    }
    MPI_Allgather( &info->dataIndex, 1, MPI_INT, gidTransmissionCounts, 1, MPI_INT, MPI_COMM_WORLD );
    
    float **keepData = (float**) malloc ( sizeof(float*)*gidCount );
    int *keepRows = (int*) malloc ( sizeof(int)*gidCount );
    int *keepCols = (int*) malloc ( sizeof(int)*gidCount );
    int *keepGids = (int*) malloc ( sizeof(int)*gidCount );
    float *activeData = NULL;
    int maxCount = 0;
    int maxDataBlock = 0;
    
    int nodeIndex=0, keepIndex=0;
    int *gatherRows=NULL, *gatherCols=NULL, *gatherGids=NULL;
int blab = 1000;
double kstart = MPI_Wtime();
    for( ; nodeIndex < mpi_size; nodeIndex++ ) {
        // don't bother with data exchange if no gids
        if( gidTransmissionCounts[nodeIndex] == 0 )
            continue;
        
double jstart = MPI_Wtime();
        if( maxCount < gidTransmissionCounts[nodeIndex] ) {
            maxCount = gidTransmissionCounts[nodeIndex];
            gatherRows = (int*) realloc ( gatherRows, sizeof(int)*3*maxCount );
        }
        gatherCols = &(gatherRows[gidTransmissionCounts[nodeIndex]]);
        gatherGids = &(gatherRows[gidTransmissionCounts[nodeIndex]*2]);

        if( nodeIndex == mpi_rank ) {
            memcpy( gatherRows, info->rowCollection, sizeof(int)*gidTransmissionCounts[nodeIndex] );
            memcpy( gatherCols, info->colCollection, sizeof(int)*gidTransmissionCounts[nodeIndex] );
            memcpy( gatherGids, info->gidCollection, sizeof(int)*gidTransmissionCounts[nodeIndex] );
        }
        
if( blab == 1000 && mpi_rank == 0 )
 fprintf( stderr, "expecting %d synapse elements from cpu %d %lf\n", gidTransmissionCounts[nodeIndex], nodeIndex, MPI_Wtime()-kstart );
if( blab == 1000 && mpi_rank == 0 )
 fprintf( stderr, "0 elapsed %lf s\n", MPI_Wtime()-jstart );
        MPI_Bcast( gatherRows, 3*gidTransmissionCounts[nodeIndex], MPI_INT, nodeIndex, MPI_COMM_WORLD );
if( blab == 1000 && mpi_rank == 0 )
 fprintf( stderr, "1 elapsed %lf s\n", MPI_Wtime()-jstart );
        
        int sendIndex=0, searchIndex=0;
        for( sendIndex=0; sendIndex<gidTransmissionCounts[nodeIndex]; sendIndex++ ) {
            if( nodeIndex == mpi_rank ) {
                if( activeData ) {
                    free(activeData);
                }
                //fprintf( stderr, "xmit gid %d (%d)\n", gatherGids[sendIndex], info->gidCollection[sendIndex] );
                activeData = info->dataCollection[sendIndex];
                maxDataBlock = sizeof(float)*gatherRows[sendIndex]*gatherCols[sendIndex];
            } else {
                if( maxDataBlock < sizeof(float)*gatherRows[sendIndex]*gatherCols[sendIndex] ) {
                    maxDataBlock = sizeof(float)*gatherRows[sendIndex]*gatherCols[sendIndex];
                    activeData = (float*) realloc ( activeData, maxDataBlock );
                }
                //fprintf( stderr, "recv gid %d from %d\n", gatherGids[sendIndex], nodeIndex );
                //activeData = (float*) malloc ( sizeof(float)*gatherRows[sendIndex]*gatherCols[sendIndex] );
            }
            
            MPI_Bcast( activeData, gatherRows[sendIndex]*gatherCols[sendIndex], MPI_FLOAT, nodeIndex, MPI_COMM_WORLD );
            
            // if we need this data, store the pointer.  Otherwise free the memory
            int found = 0;
            for( searchIndex=0; searchIndex<gidCount; searchIndex++ ) {
                if( gidList[searchIndex] == gatherGids[sendIndex] ) {
if( mpi_rank == 0 )
                    fprintf( stderr, "found gid %lf which I need (recv from node %d)\n", gidList[searchIndex], nodeIndex );
                    keepData[keepIndex] = activeData;
                    keepGids[keepIndex] = gatherGids[sendIndex];
                    keepRows[keepIndex] = gatherRows[sendIndex];
                    keepCols[keepIndex] = gatherCols[sendIndex];
                    keepIndex++;
                    found = 1;
                    activeData = NULL;
                    maxDataBlock = 0;
                }
            }
            
            //if( !found ) {
            //    free(activeData);
            //}
        }
if( blab == 1000 && mpi_rank == 0 )
 fprintf( stderr, "2 elapsed %lf s\n", MPI_Wtime()-jstart );

blab++;
if( blab > 1000 ) {
    blab-=1000;
}
    }

    free( gatherRows );
    if( activeData ) {
        free(activeData);
    }
    
    // TODO: stop leaking memory here
    info->dataCollection = keepData;
    info->rowCollection = keepRows;
    info->colCollection = keepCols;
    info->gidCollection = keepGids;
    info->dataCount = gidCount;
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
