/* Created by Language version: 7.7.0 */
/* NOT VECTORIZED */
#define NRN_VECTORIZED 0
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "scoplib_ansi.h"
#undef PI
#define nil 0
#include "md1redef.h"
#include "section.h"
#include "nrniv_mf.h"
#include "md2redef.h"
 
#if METHOD3
extern int _method3;
#endif

#if !NRNGPU
#undef exp
#define exp hoc_Exp
extern double hoc_Exp(double);
#endif
 
#define nrn_init _nrn_init__HDF5Reader
#define _nrn_initial _nrn_initial__HDF5Reader
#define nrn_cur _nrn_cur__HDF5Reader
#define _nrn_current _nrn_current__HDF5Reader
#define nrn_jacob _nrn_jacob__HDF5Reader
#define nrn_state _nrn_state__HDF5Reader
#define _net_receive _net_receive__HDF5Reader 
#define getDataString getDataString__HDF5Reader 
#define getDimensions getDimensions__HDF5Reader 
 
#define _threadargscomma_ /**/
#define _threadargsprotocomma_ /**/
#define _threadargs_ /**/
#define _threadargsproto_ /**/
 	/*SUPPRESS 761*/
	/*SUPPRESS 762*/
	/*SUPPRESS 763*/
	/*SUPPRESS 765*/
	 extern double *getarg();
 static double *_p; static Datum *_ppvar;
 
#define t nrn_threads->_t
#define dt nrn_threads->_dt
#define _tsav _p[0]
#define _nd_area  *_ppvar[0]._pval
#define ptr	*_ppvar[2]._pval
#define _p_ptr	_ppvar[2]._pval
 
#if MAC
#if !defined(v)
#define v _mlhv
#endif
#if !defined(h)
#define h _mlhh
#endif
#endif
 
#if defined(__cplusplus)
extern "C" {
#endif
 static int hoc_nrnpointerindex =  2;
 /* external NEURON variables */
 /* declaration of user functions */
 static double _hoc_closeFile();
 static double _hoc_checkVersion();
 static double _hoc_exchangeSynapseLocations();
 static double _hoc_getAttributeValue();
 static double _hoc_getColumnData();
 static double _hoc_getColumnDataRange();
 static double _hoc_getDataString();
 static double _hoc_getDimensions();
 static double _hoc_getDataInt();
 static double _hoc_getData();
 static double _hoc_getNoOfColumns();
 static double _hoc_loadData();
 static double _hoc_numberofrows();
 static double _hoc_redirect();
 static int _mechtype;
extern void _nrn_cacheloop_reg(int, int);
extern void hoc_register_prop_size(int, int, int);
extern void hoc_register_limits(int, HocParmLimits*);
extern void hoc_register_units(int, HocParmUnits*);
extern void nrn_promote(Prop*, int, int);
extern Memb_func* memb_func;
 
#define NMODL_TEXT 1
#if NMODL_TEXT
static const char* nmodl_file_text;
static const char* nmodl_filename;
extern void hoc_reg_nmodl_text(int, const char*);
extern void hoc_reg_nmodl_filename(int, const char*);
#endif

 extern Prop* nrn_point_prop_;
 static int _pointtype;
 static void* _hoc_create_pnt(_ho) Object* _ho; { void* create_point_process();
 return create_point_process(_pointtype, _ho);
}
 static void _hoc_destroy_pnt();
 static double _hoc_loc_pnt(_vptr) void* _vptr; {double loc_point_process();
 return loc_point_process(_pointtype, _vptr);
}
 static double _hoc_has_loc(_vptr) void* _vptr; {double has_loc_point();
 return has_loc_point(_vptr);
}
 static double _hoc_get_loc_pnt(_vptr)void* _vptr; {
 double get_loc_point_process(); return (get_loc_point_process(_vptr));
}
 extern void _nrn_setdata_reg(int, void(*)(Prop*));
 static void _setdata(Prop* _prop) {
 _p = _prop->param; _ppvar = _prop->dparam;
 }
 static void _hoc_setdata(void* _vptr) { Prop* _prop;
 _prop = ((Point_process*)_vptr)->_prop;
   _setdata(_prop);
 }
 /* connect user functions to hoc names */
 static VoidFunc hoc_intfunc[] = {
 0,0
};
 static Member_func _member_func[] = {
 "loc", _hoc_loc_pnt,
 "has_loc", _hoc_has_loc,
 "get_loc", _hoc_get_loc_pnt,
 "closeFile", _hoc_closeFile,
 "checkVersion", _hoc_checkVersion,
 "exchangeSynapseLocations", _hoc_exchangeSynapseLocations,
 "getAttributeValue", _hoc_getAttributeValue,
 "getColumnData", _hoc_getColumnData,
 "getColumnDataRange", _hoc_getColumnDataRange,
 "getDataString", _hoc_getDataString,
 "getDimensions", _hoc_getDimensions,
 "getDataInt", _hoc_getDataInt,
 "getData", _hoc_getData,
 "getNoOfColumns", _hoc_getNoOfColumns,
 "loadData", _hoc_loadData,
 "numberofrows", _hoc_numberofrows,
 "redirect", _hoc_redirect,
 0, 0
};
#define closeFile closeFile_HDF5Reader
#define checkVersion checkVersion_HDF5Reader
#define exchangeSynapseLocations exchangeSynapseLocations_HDF5Reader
#define getAttributeValue getAttributeValue_HDF5Reader
#define getColumnData getColumnData_HDF5Reader
#define getColumnDataRange getColumnDataRange_HDF5Reader
#define getDataInt getDataInt_HDF5Reader
#define getData getData_HDF5Reader
#define getNoOfColumns getNoOfColumns_HDF5Reader
#define loadData loadData_HDF5Reader
#define numberofrows numberofrows_HDF5Reader
#define redirect redirect_HDF5Reader
 extern double closeFile( );
 extern double checkVersion( );
 extern double exchangeSynapseLocations( );
 extern double getAttributeValue( );
 extern double getColumnData( );
 extern double getColumnDataRange( );
 extern double getDataInt( );
 extern double getData( );
 extern double getNoOfColumns( );
 extern double loadData( );
 extern double numberofrows( );
 extern double redirect( );
 /* declare global and static user variables */
 /* some parameters have upper and lower limits */
 static HocParmLimits _hoc_parm_limits[] = {
 0,0,0
};
 static HocParmUnits _hoc_parm_units[] = {
 0,0
};
 static double v = 0;
 /* connect global user variables to hoc */
 static DoubScal hoc_scdoub[] = {
 0,0
};
 static DoubVec hoc_vdoub[] = {
 0,0,0
};
 static double _sav_indep;
 static void nrn_alloc(Prop*);
static void  nrn_init(_NrnThread*, _Memb_list*, int);
static void nrn_state(_NrnThread*, _Memb_list*, int);
 static void _hoc_destroy_pnt(_vptr) void* _vptr; {
   destroy_point_process(_vptr);
}
 static void _destructor(Prop*);
 static void _constructor(Prop*);
 /* connect range variables in _p that hoc is supposed to know about */
 static const char *_mechanism[] = {
 "7.7.0",
"HDF5Reader",
 0,
 0,
 0,
 "ptr",
 0};
 
extern Prop* need_memb(Symbol*);

static void nrn_alloc(Prop* _prop) {
	Prop *prop_ion;
	double *_p; Datum *_ppvar;
  if (nrn_point_prop_) {
	_prop->_alloc_seq = nrn_point_prop_->_alloc_seq;
	_p = nrn_point_prop_->param;
	_ppvar = nrn_point_prop_->dparam;
 }else{
 	_p = nrn_prop_data_alloc(_mechtype, 1, _prop);
 	/*initialize range parameters*/
  }
 	_prop->param = _p;
 	_prop->param_size = 1;
  if (!nrn_point_prop_) {
 	_ppvar = nrn_prop_datum_alloc(_mechtype, 3, _prop);
  }
 	_prop->dparam = _ppvar;
 	/*connect ionic variables to this model*/
 if (!nrn_point_prop_) {_constructor(_prop);}
 
}
 static void _initlists();
 static void _net_receive(Point_process*, double*, double);
 extern Symbol* hoc_lookup(const char*);
extern void _nrn_thread_reg(int, int, void(*)(Datum*));
extern void _nrn_thread_table_reg(int, void(*)(double*, Datum*, Datum*, _NrnThread*, int));
extern void hoc_register_tolerance(int, HocStateTolerance*, Symbol***);
extern void _cvode_abstol( Symbol**, double*, int);

 void _HDF5reader_reg() {
	int _vectorized = 0;
  _initlists();
 	_pointtype = point_register_mech(_mechanism,
	 nrn_alloc,(void*)0, (void*)0, (void*)0, nrn_init,
	 hoc_nrnpointerindex, 0,
	 _hoc_create_pnt, _hoc_destroy_pnt, _member_func);
 	register_destructor(_destructor);
 _mechtype = nrn_get_mechtype(_mechanism[1]);
     _nrn_setdata_reg(_mechtype, _setdata);
 #if NMODL_TEXT
  hoc_reg_nmodl_text(_mechtype, nmodl_file_text);
  hoc_reg_nmodl_filename(_mechtype, nmodl_filename);
#endif
  hoc_register_prop_size(_mechtype, 1, 3);
  hoc_register_dparam_semantics(_mechtype, 0, "area");
  hoc_register_dparam_semantics(_mechtype, 1, "pntproc");
  hoc_register_dparam_semantics(_mechtype, 2, "pointer");
 add_nrn_artcell(_mechtype, 0);
 pnt_receive[_mechtype] = _net_receive;
 pnt_receive_size[_mechtype] = 1;
 	hoc_register_var(hoc_scdoub, hoc_vdoub, hoc_intfunc);
 	ivoc_help("help ?1 HDF5Reader /gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/HDF5reader.mod\n");
 hoc_register_limits(_mechtype, _hoc_parm_limits);
 hoc_register_units(_mechtype, _hoc_parm_units);
 }
static int _reset;
static char *modelname = "";

static int error;
static int _ninits = 0;
static int _match_recurse=1;
static void _modl_cleanup(){ _match_recurse=1;}
static int getDataString();
static int getDimensions();
 
static void _net_receive (_pnt, _args, _lflag) Point_process* _pnt; double* _args; double _lflag; 
{    _p = _pnt->_prop->param; _ppvar = _pnt->_prop->dparam;
  if (_tsav > t){ extern char* hoc_object_name(); hoc_execerror(hoc_object_name(_pnt->ob), ":Event arrived out of order. Must call ParallelContext.set_maxstep AFTER assigning minimum NetCon.delay");}
 _tsav = t; {
   } }
 
/*VERBATIM*/
#ifndef DISABLE_HDF5

#undef ptr
#define H5_USE_16_API 1
#undef dt
#include "hdf5.h"
#define dt nrn_threads->_dt

#ifndef DISABLE_MPI
#include "mpi.h"
#endif

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

/**
 * During synapse loading initialization, the h5 files with synapse data are catalogged
 * such that each cpu looks at a subset of what's available and gets ready to report to
 * other cpus where to find postsynaptic cells
 */
struct SynapseCatalog
{
    /// The base filename for synapse data.  The fileID is applied as a suffix (%s.%d)
    char* rootName;

    /// If possible, we should use the merge script generated by circuit building to find the gid->file id mapping
    FILE *directFile;

    /// When working with multiple files, track the id of the active file open
    int fileID;

    /// The number of files this cpu has catalogged
    int nFiles;

    /// The IDs for the files this cpu has catalogged
    int *fileIDs;

    /// For each file, the number of gids catalogged
    int *availablegidCount;

    /// For each file, an array of the gids catalogged
    int **availablegids;

    /// The index of the gid being handled in the catalog
    int gidIndex;
};

typedef struct SynapseCatalog SynapseCatalog;

/**
 * After loading, the cpus will exchange requests for info about which files contain synapse
 * data for their local gids.  This is used to store the received info provided those gids receive
 */
struct ConfirmedCells
{
    /// The number of files and gids that are confirmed as loadable for this cpu
    int count;

    /// The gids that can be loaded by this cpu
    int *gids;

    /// The files to be opened for this cpu's gids
    int *fileIDs;
};

typedef struct ConfirmedCells ConfirmedCells;

#define NONE 0
#define FLOAT_MATRIX 1
#define LONG_VECTOR 2

/**
 * Hold persistent HDF5 data such as file handle and info about latest dataset loaded
 */
struct Info {

    /// data members for general HDF5 usage
    hid_t file_;
    float * datamatrix_;
    long long *datavector_;
    char name_group[256];
    hsize_t rowsize_;
    hsize_t columnsize_;
    hid_t acc_tpl1;
    int mode;

    /// Sometimes we want to silence certain warnings
    int verboseLevel;

    /// Used to catalog contents of some h5 files tracked by this cpu
    SynapseCatalog synapseCatalog;

    /// Receive info on which files contain data for gids local to this cpu
    ConfirmedCells confirmedCells;
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
    // These fields are used when data is being accessed from a dataset
    info->file_ = -1;
    info->datamatrix_ = NULL;
    info->datavector_ = NULL;
    info->mode = NONE;
    info->name_group[0] = '\0';
    info->rowsize_ = 0;
    info->columnsize_ = 0;
    info->acc_tpl1 = -1;
    info->verboseLevel = 0;
    // These fields are used exclusively for catalogging which h5 files contain which postsynaptic gids
    info->synapseCatalog.rootName = NULL;
    info->synapseCatalog.directFile = NULL;
    info->synapseCatalog.fileID = -1;
    info->synapseCatalog.fileIDs = NULL;
    info->synapseCatalog.nFiles = 0;
    info->synapseCatalog.availablegidCount = NULL;
    info->synapseCatalog.availablegids = NULL;
    info->synapseCatalog.gidIndex = 0;
    info->confirmedCells.count = 0;
    info->confirmedCells.gids = NULL;
    info->confirmedCells.fileIDs = NULL;
}



/**
 * Use to sort gids for look up during call of readDirectMapping func
 */
int gidcompare( const void *a, const void *b ) {
    return ( *(double*)a - *(double*)b );
}



/**
 * Use to confirm a gid is present on local cpu to help readDirectMapping func.  use binary search on sorted gidList
 */
int gidexists( double searchgid, int ngids, double *gidList ) {
    int first = 0;
    int last = ngids-1;
    int middle = (first+last)/2;

    while( first <= last ) {
        if( gidList[middle] < searchgid ) {
            first = middle + 1;
        } else if( gidList[middle] == searchgid ) {
            return 1;
        } else {
            last = middle - 1;
        }

        middle = (first+last)/2;
    }

    return 0;
}


/**
 * Use Circuit Builder output script to know which files hold this cpu's gid synapse data.  Should be
 * short term solution until better loading method is available.
 */
void readDirectMapping( Info *info, int ngids, double *gidList ) {

    // gidList might already be sorted, but I don't want to make that assumption.  I also shouldn't alter it, so make a copy
    double *tmpList = (double*) malloc( ngids * sizeof(double) );
    memcpy( tmpList, gidList, ngids*sizeof(double) );
    qsort( tmpList, ngids, sizeof(double), gidcompare );

    // prepare confirmed info
    info->confirmedCells.count = ngids;
    info->confirmedCells.gids = (int*) malloc(ngids*sizeof(int));
    info->confirmedCells.fileIDs = (int*) malloc(ngids*sizeof(int));

    // read file data
    FILE *fin = info->synapseCatalog.directFile;
    info->synapseCatalog.directFile = NULL;

    // read line by line.  care about lines with given substrings
    // e.g. $CMD -i $H5.7950 -o $H5 -s /a216759 -d /a216759 -f $F

    char line[1024];
    char *res = fgets( line, 1024, fin );
    int gid = -1;
    int gidIndex = 0;
    while( res != NULL ) {
        if( strncmp( line, "$CMD", 4 ) == 0 ) {
            char *gidloc = strstr( line, "/a" );
            if( gidloc != NULL ) {
                gid = atoi(&gidloc[2]);
            }
            if( gidexists( (double) gid, ngids, tmpList ) ) {
                int fileID = atoi(&line[12]);
                info->confirmedCells.gids[gidIndex] = gid;
                info->confirmedCells.fileIDs[gidIndex] = fileID;
                gidIndex++;
            }
        }

        res = fgets( line, 1024, fin );
    }

    fclose( fin );
    free(tmpList);
}



/**
 * Callback function for H5Giterate - if the dataset opened corresponds to a gid, it is catalogged so the
 * local cpu can inform other cpus the whereabouts of that gid
 *
 * @param loc_id hdf5 handle to the open file
 * @param name name of the dataset to be accessed during this iteration step
 * @param opdata not used since we have global Info object
 */
herr_t loadShareData( hid_t loc_id, const char *name, void *opdata )
{
    INFOCAST;
    Info* info = *ip;
    assert( info->file_ >= 0 );

    //fprintf( stderr, "open dataset %s\n", name );

    //make sure we are using a dataset that corresponds to a gid
    int gid = atoi( name+1 );
    char rebuild[32];
    snprintf( rebuild, 32, "a%d", gid );
    if( strcmp( rebuild, name ) != 0 ) {
        //non-synapse dataset, but not an error (could just be the version info)
        //fprintf( stderr, "ignore non-gid dataset\n" );
        return 0;
    }

    // we have confirmed that this dataset corresponds to a gid.  The active file should make it part of its data
    int fileIndex = info->synapseCatalog.nFiles-1;
    info->synapseCatalog.availablegids[ fileIndex ][ info->synapseCatalog.gidIndex++ ] = gid;

    return 1;
}



/**
 * Open an HDF5 file for reading.  In the event of synapse data, the datasets of the file may be iterated in order to
 * build a catalog of available gids and their file locations.
 *
 * @param info Structure that manages hdf5 info
 * @param filename File to open
 * @param fileID Integer to identify this file (attached as suffix to filename)
 * @param nNodesPerFile 0: open file, but don't load data; 1: open file for catalogging; N: read portion of file for catalogging
 * @param startRank used to help calculate data range to load when file subportion is loaded
 * @param myRank used to help calculate data range to load when file subportion is loaded
 */
int openFile( Info* info, const char *filename, int fileID, int nRanksPerFile, int startRank, int myRank )
{
    if( info->file_ != -1 ) {
        H5Fclose(info->file_);
    }

    char nameoffile[512];
    //fprintf( stderr, "arg check: %s %d %d %d\n", filename, nRanksPerFile, startRank, myRank );
    if( fileID != -1 ) {
        snprintf( nameoffile, 512, "%s.%d", filename, fileID );
    } else {
        strncpy( nameoffile, filename, 512 );
    }

    info->name_group[0]='\0';

    hid_t file_driver = (info->acc_tpl1 != -1)? info->acc_tpl1 : H5P_DEFAULT;

    // Opens the file with the alternate handler
    info->file_ = H5Fopen( nameoffile, H5F_ACC_RDONLY, file_driver);
    int result = (info->file_ < 0);
    int failed = result;

#ifndef DISABLE_MPI
    if( info->acc_tpl1 != -1 ) {
        MPI_Allreduce( &result, &failed, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD );

        if( failed ) {
            int canreport = (result<0)?nrnmpi_myid:nrnmpi_numprocs, willreport = 0;
            MPI_Allreduce( &canreport, &willreport, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD );

            if( willreport == nrnmpi_myid ) {
                fprintf(stderr, "%d ERROR: %d ranks failed collective open of synapse file: %s\n", nrnmpi_myid, failed, nameoffile );
            }
            info->file_ = -1;
            H5Eprint(stderr);
            return -1;
        }
    } else  // to the serial-version if
#endif
    if( failed ) {
        info->file_ = -1;
        fprintf(stderr, "ERROR: Failed to open synapse file: %s\n", nameoffile );
        H5Eprint(stderr);
        return -1;
    }

    if( nRanksPerFile == 0 ) {
        // don't need to load data yet, so we return
        return 0;
    }

    // will catalog synapse data
    info->synapseCatalog.fileID = fileID;

    int nDatasetsToImport=0, startIndex=0;
    hsize_t nObjects;
    H5Gget_num_objs( info->file_, &nObjects );

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

    int nFiles = ++info->synapseCatalog.nFiles;
    info->synapseCatalog.fileIDs = (int*) realloc ( info->synapseCatalog.fileIDs, sizeof(int)*nFiles );
    info->synapseCatalog.fileIDs[nFiles-1] = fileID;
    info->synapseCatalog.availablegidCount = (int*) realloc ( info->synapseCatalog.availablegidCount, sizeof(int)*nFiles );
    info->synapseCatalog.availablegids = (int**) realloc ( info->synapseCatalog.availablegids, sizeof(int*)*nFiles );

    info->synapseCatalog.availablegidCount[nFiles-1] = nDatasetsToImport;
    info->synapseCatalog.availablegids[nFiles-1] = (int*) calloc ( nDatasetsToImport, sizeof(int) );
    info->synapseCatalog.gidIndex=0;

    //fprintf( stderr, "load datasets %d through %d (max %d)\n", startIndex, startIndex+nDatasetsToImport, (int) nObjects );

    int i, verify=startIndex;
    for( i=startIndex; i<startIndex+nDatasetsToImport && i<nObjects; i++ ) {
        assert( verify == i );
        result = H5Giterate( info->file_, "/", &verify, loadShareData, NULL );
        if( result != 1 )
            continue;
    }

    return 0;
}



/**
 * Load a dataset so that the dimensions are available, but don't retrieve any data
 *
 * @param info Structure that manages hdf5 info, its datamatrix_ variable is populated with hdf5 data on success
 * @param name The name of the dataset to access
 * @return 0 on success, < 0 on error
 */
int loadDimensions( Info *info, char* name )
{
    int isCurrentlyLoaded = strncmp( info->name_group, name, 256 ) == 0;
    if( isCurrentlyLoaded )
        return 0;

    hsize_t dims[2] = {0}, offset[2] = {0};
    hid_t dataset_id, dataspace;

    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)
    {
        fprintf(stderr, "Error accessing to dataset %s in synapse file\n", name);
        return -1;
    }
    dataset_id = H5Dopen(info->file_, name);

    strncpy(info->name_group, name, 256);

    dataspace = H5Dget_space(dataset_id);

    int dimensions = H5Sget_simple_extent_ndims(dataspace);
    H5Sget_simple_extent_dims(dataspace,dims,NULL);
    info->rowsize_ = (unsigned long)dims[0];
    if( dimensions > 1 )
        info->columnsize_ = dims[1];
    else
        info->columnsize_ = 1;

    H5Sclose(dataspace);
    H5Dclose(dataset_id);

    return 0;
}



/**
 * Given the name of a dataset, load it from the current hdf5 file into the matrix pointer
 *
 * @param info Structure that manages hdf5 info, its datamatrix_ variable is populated with hdf5 data on success
 * @param name The name of the dataset to access and load in the hdf5 file
 */
int loadDataMatrix( Info *info, char* name )
{
    int isCurrentlyLoaded = strncmp( info->name_group, name, 256 ) == 0;
    if( isCurrentlyLoaded )
        return 0;

    hsize_t dims[2] = {0}, offset[2] = {0};
    hid_t dataset_id, dataspace;

    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0) {
        return -1;
    }
    dataset_id = H5Dopen(info->file_, name);

    strncpy(info->name_group, name, 256);

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



/**
 * Given the name of a dataset with id values, load it from the current hdf5 file into the matrix pointer
 *
 * @param info Structure that manages hdf5 info, its datavector_ variable is populated with hdf5 data on success
 * @param name The name of the dataset to access and load in the hdf5 file
 */
int loadDataVector( Info *info, char* name )
{
    hsize_t dims[2] = {0}, offset[2] = {0};
    hid_t dataset_id, dataspace;

    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)
    {
        fprintf(stderr, "Error accessing to dataset %s in synapse file\n", name);
        return -1;
    }
    dataset_id = H5Dopen(info->file_, name);
    dataspace = H5Dget_space(dataset_id);

    strncpy(info->name_group, name, 256);

    int dimensions = H5Sget_simple_extent_ndims(dataspace);
    H5Sget_simple_extent_dims(dataspace,dims,NULL);
    info->rowsize_ = (unsigned long)dims[0];
    if( dimensions > 1 )
        info->columnsize_ = dims[1];
    else
        info->columnsize_ = 1;

    if(info->datavector_ != NULL) {
        free(info->datavector_);
    }
    info->datavector_ = (long long *) malloc(sizeof(long long)*(info->rowsize_*info->columnsize_));

    H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL);
    hid_t dataspacetogetdata=H5Screate_simple(dimensions,dims,NULL);
    H5Dread(dataset_id,H5T_NATIVE_ULONG,dataspacetogetdata,H5S_ALL,H5P_DEFAULT,info->datavector_);
    H5Sclose(dataspace);
    H5Sclose(dataspacetogetdata);
    H5Dclose(dataset_id);
    return 0;
}



/**
 * Load an individual value from a dataset
 *
 * @param info Shared data
 * @param name dataset to open and read from
 * @param row  data item to retrieve
 * @param dest int address where data is to be stored
 */
int loadDataInt( Info* info, char* name, hid_t row, int *dest )
{
    hsize_t dims[1] = {1}, offset[1] = {row}, offset_out[1] = {0}, count[1] = {1};
    hid_t dataset_id, dataspace, memspace, space; //, filetype;
    herr_t status;
    int ndims = 0;
    long long temp;

    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0) {
        fprintf(stderr, "Error accessing to dataset %s in h5 file\n", name);
        return -1;
    }

    dataset_id = H5Dopen(info->file_, name);
    dataspace = H5Dget_space(dataset_id);

    //filetype = H5Dget_type (dataset_id);
    space = H5Dget_space (dataset_id);
    ndims = H5Sget_simple_extent_dims (space, dims, NULL);

    status = H5Sselect_hyperslab( space, H5S_SELECT_SET, offset, NULL, count, NULL );

    // memory space to receive data and select hyperslab in that
    memspace = H5Screate_simple( 1, dims, NULL );
    status = H5Sselect_hyperslab( memspace, H5S_SELECT_SET, offset_out, NULL, count, NULL );

    status = H5Dread (dataset_id, H5T_NATIVE_ULONG, memspace, space, H5P_DEFAULT, &temp );

    *dest = temp;

    status = H5Sclose (space);
    status = H5Sclose(dataspace);
    status = H5Dclose(dataset_id);

    return 0;
}



/**
 * Given the name of a dataset that should contain variable length string data, load those strings
 */
int loadDataString( Info* info, char* name, hid_t row, char **hoc_dest )
{
    hsize_t dims[1] = {1}, offset[1] = {row}, offset_out[1] = {0}, count[1] = {1};
    hid_t dataset_id, dataspace, memspace, space, filetype, memtype;
    herr_t status;
    char** rdata;
    int ndims = 0;

    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)
    {
        fprintf(stderr, "Error accessing to dataset %s in h5 file\n", name);
        return -1;
    }
    dataset_id = H5Dopen(info->file_, name);
    dataspace = H5Dget_space(dataset_id);

    filetype = H5Dget_type (dataset_id);
    space = H5Dget_space (dataset_id);
    ndims = H5Sget_simple_extent_dims (space, dims, NULL);
    rdata = (char **) malloc (sizeof (char *));

    memtype = H5Tcopy (H5T_C_S1);
    status = H5Tset_size (memtype, H5T_VARIABLE);
    H5Tset_cset(memtype, H5T_CSET_UTF8);

    status = H5Sselect_hyperslab( space, H5S_SELECT_SET, offset, NULL, count, NULL );

    // memory space to receive data and select hyperslab in that
    memspace = H5Screate_simple( 1, dims, NULL );
    status = H5Sselect_hyperslab( memspace, H5S_SELECT_SET, offset_out, NULL, count, NULL );

    status = H5Dread (dataset_id, memtype, memspace, space, H5P_DEFAULT, rdata);

    hoc_assign_str( hoc_dest, rdata[0] );

    //fprintf( stderr, "free h5 mem\n" );  // TODO: determine why this causes a crash.  For now we leak memory
    //status = H5Dvlen_reclaim (memtype, space, H5P_DEFAULT, rdata );
    //fprintf( stderr, "free rdata\n" );
    free(rdata);

    status = H5Sclose (space);
    status = H5Sclose (dataspace);
    status = H5Tclose (filetype);
    status = H5Tclose (memtype);
    status = H5Dclose (dataset_id);

    return 0;
}

#endif  // DISABLE_HDF5
 
double redirect (  ) {
   double _lredirect;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
#ifndef DISABLE_MPI
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
#endif  // DISABLE_MPI
#endif  // DISABLE_HDF5
}
 
return _lredirect;
 }
 
static double _hoc_redirect(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  redirect (  );
 return(_r);
}
 
double checkVersion (  ) {
   double _lcheckVersion;
 
/*VERBATIM*/
{
    int versionNumber = 0;
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;
    int mpi_size=1, mpi_rank=0;

#ifndef DISABLE_MPI
    // get MPI info
    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);
#endif

    if( mpi_rank == 0 )
    {
        if( H5Lexists(info->file_, "info", H5P_DEFAULT) == 0) {
            versionNumber = 0;
        } else {
            hid_t dataset_id = H5Dopen( info->file_, "info" );
            hid_t attr_id = H5Aopen_name( dataset_id, "version" );
            H5Aread( attr_id, H5T_NATIVE_INT, &versionNumber );
            H5Aclose(attr_id);
            H5Dclose(dataset_id);
        }
    }

#ifndef DISABLE_MPI
    MPI_Bcast( &versionNumber, 1, MPI_INT, 0, MPI_COMM_WORLD );
#endif

#endif  // DISABLE_HDF5
    return versionNumber;
}
 
return _lcheckVersion;
 }
 
static double _hoc_checkVersion(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  checkVersion (  );
 return(_r);
}
 
double loadData (  ) {
   double _lloadData;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;

    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))
    {
        if( ifarg(2) ) {
            if( *getarg(2) == 1 ) { //load vector
                info->mode = LONG_VECTOR;
                return loadDataVector( info, gargstr(1) );
            }
        }

        info->mode = FLOAT_MATRIX;
        return loadDataMatrix( info, gargstr(1) );
    }
    else if( ifarg(1) )
    {
        int gid = *getarg(1);
        int gidIndex=0;

        for( gidIndex=0; gidIndex<info->confirmedCells.count; gidIndex++ ) {
            if( info->confirmedCells.gids[gidIndex] == gid ) {
                openFile( info, info->synapseCatalog.rootName, info->confirmedCells.fileIDs[gidIndex], 0, 0, 0 );

                char cellname[256];
                sprintf( cellname, "a%d", gid );

                info->mode = FLOAT_MATRIX;
                return loadDataMatrix( info, cellname );
            }
        }

        //if we reach here, did not find data
        if( info->verboseLevel > 0 )
            fprintf( stderr, "Warning: failed to find data for gid %d\n", gid );
    }

    return -1;
#endif  // DISABLE_HDF5
}
 
return _lloadData;
 }
 
static double _hoc_loadData(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  loadData (  );
 return(_r);
}
 
double getNoOfColumns (  ) {
   double _lgetNoOfColumns;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
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
#endif
}
 
return _lgetNoOfColumns;
 }
 
static double _hoc_getNoOfColumns(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getNoOfColumns (  );
 return(_r);
}
 
double numberofrows (  ) {
   double _lnumberofrows;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
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
        fprintf(stderr, "general error: bad file handle, missing arg?");
        return 0;
    }
#endif
}
 
return _lnumberofrows;
 }
 
static double _hoc_numberofrows(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  numberofrows (  );
 return(_r);
}
 
double getData (  ) {
   double _lgetData;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
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
                fprintf(stderr, "ERROR: trying to access to a row and column erroneus on %s, size: %lld,%lld accessing to %lld,%lld\n",
                        name, info->rowsize_, info->columnsize_, row, column);
                return 0;
            }

            if( info->mode == FLOAT_MATRIX ) {
                return info->datamatrix_[row*info->columnsize_ + column];
            } else if( info->mode == LONG_VECTOR ) {
                return (double) info->datavector_[row];
            } else {
                fprintf( stderr, "unexpected mode: %d\n", info->mode );
            }
        }
        fprintf(stderr, "(Getting data)Error on the name of last loaded data: access:%s loaded:%s\n",name,info->name_group);
        return 0;
    }
    else
    {
        fprintf( stderr, "ERROR:Error on number of rows of %s\n", gargstr(1) );
        return 0;
    }
#endif
}
 
return _lgetData;
 }
 
static double _hoc_getData(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getData (  );
 return(_r);
}
 
double getDataInt (  ) {
   double _lgetDataInt;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;
    int value = -1;

    _lgetDataInt = 0;
    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )
    {
        // Use HDF5 interface to get the requested string item from the dataset
        if( loadDataInt( info, gargstr(1), *getarg(2), &value ) == 0 ) {
            _lgetDataInt = value;
        }
    }
#endif
 
return _lgetDataInt;
 }
 
static double _hoc_getDataInt(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getDataInt (  );
 return(_r);
}
 
static int  getDimensions (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;

    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) ) {
        loadDimensions( info, gargstr(1) );
    }
#endif
  return 0; }
 
static double _hoc_getDimensions(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 getDimensions (  );
 return(_r);
}
 
static int  getDataString (  ) {
   
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;

    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && ifarg(3) )
    {
        // Use HDF5 interface to get the requested string item from the dataset
        loadDataString( info, gargstr(1), *getarg(2), hoc_pgargstr(3) );
    }
#endif
  return 0; }
 
static double _hoc_getDataString(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r = 1.;
 getDataString (  );
 return(_r);
}
 
double getColumnDataRange (  ) {
   double _lgetColumnDataRange;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
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
                fprintf(stderr, "ERROR: trying to access to a column erroneus on %s, size: %lld,%lld accessing to column %lld\n ",name,info->rowsize_,info->columnsize_,column);
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
        fprintf(stderr, "(Getting data)Error on the name of last loaded data: access:%s loaded:%s\n",name,info->name_group);
        return 0;
    }
    else
    {
        //printf("ERROR:Error on number of rows of \n");
        return 0;
    }
#endif
}
 
return _lgetColumnDataRange;
 }
 
static double _hoc_getColumnDataRange(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getColumnDataRange (  );
 return(_r);
}
 
double getColumnData (  ) {
   double _lgetColumnData;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
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
                fprintf(stderr, "ERROR: trying to access to a column erroneus on %s, size: %lld,%lld accessing to column %lld\n ",name,info->rowsize_,info->columnsize_,column);
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
        fprintf(stderr, "(Getting data)Error on the name of last loaded data: access:%s loaded:%s\n",name,info->name_group);
        return 0;
    }
    else
    {
        //printf("ERROR:Error on number of rows of \n");
        return 0;
    }
#endif
}
 
return _lgetColumnData;
 }
 
static double _hoc_getColumnData(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getColumnData (  );
 return(_r);
}
 
double getAttributeValue (  ) {
   double _lgetAttributeValue;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;
    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && hoc_is_str_arg(2) )
    {
        if( H5Lexists(info->file_, gargstr(1), H5P_DEFAULT) == 0)
        {
            fprintf( stderr, "Error: no dataset with name %s available.\n", gargstr(1) );
            return 0;
        }
        hid_t dataset_id = H5Dopen( info->file_, gargstr(1) );

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
#endif
 
return _lgetAttributeValue;
 }
 
static double _hoc_getAttributeValue(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  getAttributeValue (  );
 return(_r);
}
 
double closeFile (  ) {
   double _lcloseFile;
 
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* info = *ip;
    if(info->file_ >=0)
    {
        H5Fclose(info->file_);
        //printf("Close\n");
        info->file_ = -1;
    }
    if(info->datamatrix_ != NULL)
    {
        free(info->datamatrix_);
        info->datamatrix_ = NULL;
    }
#endif
}
 
return _lcloseFile;
 }
 
static double _hoc_closeFile(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  closeFile (  );
 return(_r);
}
 
double exchangeSynapseLocations (  ) {
   double _lexchangeSynapseLocations;
 
/*VERBATIM*/
#ifndef DISABLE_HDF5
#ifndef DISABLE_MPI
    INFOCAST;
    Info* info = *ip;

    void* vv = vector_arg(1);
    int gidCount = vector_capacity(vv);
    double *gidList = vector_vec(vv);

    if( info->synapseCatalog.directFile != NULL ) {
        // the file generated by circuit building with gid to file id exists, so use that to determine mapping instead
        readDirectMapping( info, gidCount, gidList );
        return 0;
    }

    int mpi_size, mpi_rank;

    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);
    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);

    // used to store the number of gids found per cpu
    int *foundCountsAcrossCPUs = (int*) malloc( sizeof(int)*mpi_size );
    int *foundDispls = (int*) malloc( sizeof(int)*mpi_size );

    int bufferSize;

    // have every cpu allocate a buffer capable of holding the data for the cpu with the most cells
    MPI_Allreduce( &gidCount, &bufferSize, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD );
    double* gidsRequested = (double*) malloc ( sizeof(double)*bufferSize );
    int* gidsFound = (int*) malloc( sizeof(int)*bufferSize );
    int* fileIDsFound = (int*) malloc( sizeof(int)*bufferSize );

    double *tempRequest;  //used to hold the gidsRequested buffer when this cpu is broadcasting its gidList

    // each cpu in turn will bcast its local gids.  It should then get back the file indices where the data can be found.
    int activeRank, requestCount;
    for( activeRank=0; activeRank<mpi_size; activeRank++ ) {
        if( activeRank == mpi_rank ) {
            requestCount = gidCount;
            tempRequest = gidsRequested;
            gidsRequested = gidList;
        }

        MPI_Bcast( &requestCount, 1, MPI_INT, activeRank, MPI_COMM_WORLD );
        MPI_Bcast( gidsRequested, requestCount, MPI_DOUBLE, activeRank, MPI_COMM_WORLD );

        // each cpu will check if the requested gids exist in its list
        int nFiles = 0;

        // TODO: linear searches at the moment.  Maybe a more efficient ln(n) search.  Although, I would prefer to implement that
        //  with access to STL or the like data structures.
        int fileIndex, gidIndex, requestIndex;
        for( fileIndex=0; fileIndex < info->synapseCatalog.nFiles; fileIndex++ ) {
            for( gidIndex=0; gidIndex < info->synapseCatalog.availablegidCount[fileIndex]; gidIndex++ ) {
                for( requestIndex=0; requestIndex < requestCount; requestIndex++ ) {
                    if( info->synapseCatalog.availablegids[fileIndex][gidIndex] == gidsRequested[requestIndex] ) {
                        gidsFound[nFiles] = gidsRequested[requestIndex];
                        fileIDsFound[nFiles++] = info->synapseCatalog.fileIDs[fileIndex];
                    }
                }
            }
        }

        MPI_Gather( &nFiles, 1, MPI_INT, foundCountsAcrossCPUs, 1, MPI_INT, activeRank, MPI_COMM_WORLD );

        if( activeRank == mpi_rank ) {
            info->confirmedCells.count = 0;

            int nodeIndex;
            for( nodeIndex=0; nodeIndex<mpi_size; nodeIndex++ ) {
                foundDispls[nodeIndex] = info->confirmedCells.count;
                info->confirmedCells.count += foundCountsAcrossCPUs[nodeIndex];
            }
            info->confirmedCells.gids = (int*) malloc ( sizeof(int)*info->confirmedCells.count );
            info->confirmedCells.fileIDs = (int*) malloc ( sizeof(int)*info->confirmedCells.count );
        }

        MPI_Gatherv( gidsFound, nFiles, MPI_INT, info->confirmedCells.gids, foundCountsAcrossCPUs, foundDispls, MPI_INT, activeRank, MPI_COMM_WORLD );
        MPI_Gatherv( fileIDsFound, nFiles, MPI_INT, info->confirmedCells.fileIDs, foundCountsAcrossCPUs, foundDispls, MPI_INT, activeRank, MPI_COMM_WORLD );

        // put back the original gid request buffer so as to not destroy this cpu's gidList
        if( activeRank == mpi_rank ) {
            gidsRequested = tempRequest;
        }

    }

    free(gidsRequested);
    free(gidsFound);
    free(fileIDsFound);
    free(foundCountsAcrossCPUs);
    free(foundDispls);
#endif  // DISABLE_MPI
#endif  // DISABLE_HDF5
 
return _lexchangeSynapseLocations;
 }
 
static double _hoc_exchangeSynapseLocations(void* _vptr) {
 double _r;
    _hoc_setdata(_vptr);
 _r =  exchangeSynapseLocations (  );
 return(_r);
}
 
static void _constructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
#ifdef DISABLE_HDF5
    // Neuron might init the mechanism. With args it's the user.
    if(ifarg(1)) {
        fprintf(stderr, "HDF5 support is not available\n");
        exit(-1);
    }
#else
    char nameoffile[512];
    int nFiles = 1;

    if( ifarg(2) ) {
        nFiles = *getarg(2);
    }

    if(ifarg(1) && hoc_is_str_arg(1)) {
        INFOCAST;
        Info* info = 0;

        strncpy(nameoffile, gargstr(1),512);
        info = (Info*) hoc_Emalloc(sizeof(Info)); hoc_malchk();
        initInfo( info );

        if( ifarg(3) ) {
            info->verboseLevel = *getarg(3);
        }

        *ip = info;

        if( nFiles == 1 ) {
            hid_t plist_id = 0;

            // if a second arg was explicitly given as 1, I assume that we are doing a parallel file access
            // saw deadlock while running on viz cluster and hence disabling parallel read
            if( ifarg(2) ) {
                if( nrnmpi_myid == 0 ) { fprintf( stderr, "using parallel hdf5 is disabled\n" ); }
                //info->acc_tpl1 = H5Pcreate(H5P_FILE_ACCESS);
                //H5Pset_fapl_mpio(info->acc_tpl1, MPI_COMM_WORLD, MPI_INFO_NULL);
            }

            // normal case - open a file and be ready to load data as needed
            openFile( info, nameoffile, -1, 0, 0, 0 );
        }
        else {
            // Each cpu is reponsible for a portion of the data
            info->synapseCatalog.rootName = strdup( nameoffile );

            int mpi_size=1, mpi_rank=0;
#ifndef DISABLE_MPI
            MPI_Comm_size( MPI_COMM_WORLD, &mpi_size );
            MPI_Comm_rank( MPI_COMM_WORLD, &mpi_rank );
#endif
            //fprintf( stderr, "%d vs %d\n", mpi_size, nFiles );
            // attempt to use the merge script to catalog files.  Only if it is not found should we then go to the
            // individual files and iterate the datasets
            int plength = strlen(nameoffile);
            char *nrnPath = (char*) malloc( plength + 128 );
            strncpy( nrnPath, nameoffile, plength+1 );
            char *term = strrchr( nrnPath, '/' ); *term = 0;

            // rem: recent circuit building has changed the name of the merge script.  Hopefully it will not change again.  But anyways
            // we might replace this whole mod file with a completely better method in the future.
            strcat( nrnPath, "/mergeAllH5.sh" );
            FILE *fin = fopen( nrnPath, "r" );
            if( !fin ) {
                // try the other name
                *term = 0;
                strcat( nrnPath, "/merge_nrn_positions.sh" );
                fin = fopen( nrnPath, "r" );
            }
            free(nrnPath);
            if( fin ) {
                info->synapseCatalog.directFile = fin;
                return;
            }

            // need to determine if I open multiple files per cpu or multiple cpus share a file
            if( mpi_size > nFiles ) { // multiple cpus per file
                int nRanksPerFile = (int) mpi_size / nFiles;
                if( mpi_size % nFiles != 0 )
                    nRanksPerFile++;

                //fprintf( stderr, "nRanksPerFile %d = %d/%d\n", nRanksPerFile, mpi_size, nFiles );

                if( nRanksPerFile * nFiles > mpi_size ) { // no files left for this rank
                    info->file_ = -1;
                    return;
                }

                int fileIndex = (int) mpi_rank / nRanksPerFile;  //this should be truncated
                int startRank = fileIndex * nRanksPerFile;

                //sprintf( nameoffile, "%s.%d", gargstr(1), fileIndex );
                //fprintf( stderr, "I should open file %s\n", nameoffile );

                openFile( info, nameoffile, fileIndex, nRanksPerFile, startRank, mpi_rank );

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
                        return;
                    }
                }

                int fileIndex=0;
                for( fileIndex=0; fileIndex<nFilesPerRank; fileIndex++ ) {
                    //sprintf( nameoffile, "%s.%d", gargstr(1), startFile+fileIndex );
                    openFile( info, nameoffile, startFile+fileIndex, 1, 0, 0 );
                }
            }
        }
    }
#endif  // DISABLE_HDF5
}
 }
 
}
}
 
static void _destructor(Prop* _prop) {
	_p = _prop->param; _ppvar = _prop->dparam;
{
 {
   
/*VERBATIM*/
{
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    if(info->file_>=0)
    {
        if( info->acc_tpl1 != -1 ) {
            if( nrnmpi_myid == 0 ) { fprintf( stderr, "terminating parallel h5 access\n" ); }
            H5Pclose(info->acc_tpl1);
        }
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
    if( info->datavector_ != NULL )
    {
        free( info->datavector_ );
        info->datavector_ = NULL;
    }
#endif
}
 }
 
}
}

static void initmodel() {
  int _i; double _save;_ninits++;
{
 {
   }

}
}

static void nrn_init(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 _tsav = -1e20;
 initmodel();
}}

static double _nrn_current(double _v){double _current=0.;v=_v;{
} return _current;
}

static void nrn_state(_NrnThread* _nt, _Memb_list* _ml, int _type){
Node *_nd; double _v = 0.0; int* _ni; int _iml, _cntml;
#if CACHEVEC
    _ni = _ml->_nodeindices;
#endif
_cntml = _ml->_nodecount;
for (_iml = 0; _iml < _cntml; ++_iml) {
 _p = _ml->_data[_iml]; _ppvar = _ml->_pdata[_iml];
 _nd = _ml->_nodelist[_iml];
 v=_v;
{
}}

}

static void terminal(){}

static void _initlists() {
 int _i; static int _first = 1;
  if (!_first) return;
_first = 0;
}

#if NMODL_TEXT
static const char* nmodl_filename = "/gpfs/bbp.cscs.ch/home/tharayil/generalized-neurodamus-py/neurodamus-py/mods.tmp/HDF5reader.mod";
static const char* nmodl_file_text = 
  "COMMENT\n"
  "/**\n"
  " * @file HDF5reader.mod\n"
  " * @brief\n"
  " * @author king\n"
  " * @date 2009-10-23\n"
  " * @remark Copyright \n"
  "\n"
  " BBP/EPFL 2005-2011; All rights reserved. Do not distribute without further notice.\n"
  " */\n"
  "ENDCOMMENT\n"
  "\n"
  "COMMENT\n"
  "This is intended to serve two purposes.  One as a general purpose reader for HDF5 files with a basic set of\n"
  "accessor functions.  In addition, it will have special handling for our synapse data files such that they can be handled\n"
  "more efficiently in a  massively parallel manner.  I feel inclined to spin this functionality out into a c++ class where\n"
  "I can access more advanced coding structures, especially STL.\n"
  "ENDCOMMENT\n"
  "\n"
  "NEURON {\n"
  "    ARTIFICIAL_CELL HDF5Reader\n"
  "    POINTER ptr\n"
  "}\n"
  "\n"
  "PARAMETER {\n"
  "}\n"
  "\n"
  "ASSIGNED {\n"
  "        ptr\n"
  "}\n"
  "\n"
  "INITIAL {\n"
  "    : 20.07.2018 - For multicycle Model Generation using GluSynapse, I stopped closing the file during stdinit.  Should revist this in the future\n"
  "    :closeFile()\n"
  "}\n"
  "\n"
  "NET_RECEIVE(w) {\n"
  "}\n"
  "\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "\n"
  "#undef ptr\n"
  "#define H5_USE_16_API 1\n"
  "#undef dt\n"
  "#include \"hdf5.h\"\n"
  "#define dt nrn_threads->_dt\n"
  "\n"
  "#ifndef DISABLE_MPI\n"
  "#include \"mpi.h\"\n"
  "#endif\n"
  "\n"
  "#include <stdlib.h>\n"
  "\n"
  "/// NEURON utility functions we want to use\n"
  "extern double* hoc_pgetarg(int iarg);\n"
  "extern double* getarg(int iarg);\n"
  "extern char* gargstr(int iarg);\n"
  "extern int hoc_is_str_arg(int iarg);\n"
  "extern int nrnmpi_numprocs;\n"
  "extern int nrnmpi_myid;\n"
  "extern int ifarg(int iarg);\n"
  "extern double chkarg(int iarg, double low, double high);\n"
  "extern double* vector_vec(void* vv);\n"
  "extern int vector_capacity(void* vv);\n"
  "extern void* vector_arg(int);\n"
  "\n"
  "/**\n"
  " * During synapse loading initialization, the h5 files with synapse data are catalogged\n"
  " * such that each cpu looks at a subset of what's available and gets ready to report to\n"
  " * other cpus where to find postsynaptic cells\n"
  " */\n"
  "struct SynapseCatalog\n"
  "{\n"
  "    /// The base filename for synapse data.  The fileID is applied as a suffix (%s.%d)\n"
  "    char* rootName;\n"
  "\n"
  "    /// If possible, we should use the merge script generated by circuit building to find the gid->file id mapping\n"
  "    FILE *directFile;\n"
  "\n"
  "    /// When working with multiple files, track the id of the active file open\n"
  "    int fileID;\n"
  "\n"
  "    /// The number of files this cpu has catalogged\n"
  "    int nFiles;\n"
  "\n"
  "    /// The IDs for the files this cpu has catalogged\n"
  "    int *fileIDs;\n"
  "\n"
  "    /// For each file, the number of gids catalogged\n"
  "    int *availablegidCount;\n"
  "\n"
  "    /// For each file, an array of the gids catalogged\n"
  "    int **availablegids;\n"
  "\n"
  "    /// The index of the gid being handled in the catalog\n"
  "    int gidIndex;\n"
  "};\n"
  "\n"
  "typedef struct SynapseCatalog SynapseCatalog;\n"
  "\n"
  "/**\n"
  " * After loading, the cpus will exchange requests for info about which files contain synapse\n"
  " * data for their local gids.  This is used to store the received info provided those gids receive\n"
  " */\n"
  "struct ConfirmedCells\n"
  "{\n"
  "    /// The number of files and gids that are confirmed as loadable for this cpu\n"
  "    int count;\n"
  "\n"
  "    /// The gids that can be loaded by this cpu\n"
  "    int *gids;\n"
  "\n"
  "    /// The files to be opened for this cpu's gids\n"
  "    int *fileIDs;\n"
  "};\n"
  "\n"
  "typedef struct ConfirmedCells ConfirmedCells;\n"
  "\n"
  "#define NONE 0\n"
  "#define FLOAT_MATRIX 1\n"
  "#define LONG_VECTOR 2\n"
  "\n"
  "/**\n"
  " * Hold persistent HDF5 data such as file handle and info about latest dataset loaded\n"
  " */\n"
  "struct Info {\n"
  "\n"
  "    /// data members for general HDF5 usage\n"
  "    hid_t file_;\n"
  "    float * datamatrix_;\n"
  "    long long *datavector_;\n"
  "    char name_group[256];\n"
  "    hsize_t rowsize_;\n"
  "    hsize_t columnsize_;\n"
  "    hid_t acc_tpl1;\n"
  "    int mode;\n"
  "\n"
  "    /// Sometimes we want to silence certain warnings\n"
  "    int verboseLevel;\n"
  "\n"
  "    /// Used to catalog contents of some h5 files tracked by this cpu\n"
  "    SynapseCatalog synapseCatalog;\n"
  "\n"
  "    /// Receive info on which files contain data for gids local to this cpu\n"
  "    ConfirmedCells confirmedCells;\n"
  "};\n"
  "\n"
  "typedef struct Info Info;\n"
  "\n"
  "///Utility macro to make the NEURON pointer accessible for reading and writing (seems like we have more levels of indirection than necessary - JGK)\n"
  "#define INFOCAST Info** ip = (Info**)(&(_p_ptr))\n"
  "\n"
  "#define dp double*\n"
  "\n"
  "/**\n"
  " * Utility function to ensure that all members of an Info struct are initialized.\n"
  " */\n"
  "void initInfo( Info *info )\n"
  "{\n"
  "    // These fields are used when data is being accessed from a dataset\n"
  "    info->file_ = -1;\n"
  "    info->datamatrix_ = NULL;\n"
  "    info->datavector_ = NULL;\n"
  "    info->mode = NONE;\n"
  "    info->name_group[0] = '\\0';\n"
  "    info->rowsize_ = 0;\n"
  "    info->columnsize_ = 0;\n"
  "    info->acc_tpl1 = -1;\n"
  "    info->verboseLevel = 0;\n"
  "    // These fields are used exclusively for catalogging which h5 files contain which postsynaptic gids\n"
  "    info->synapseCatalog.rootName = NULL;\n"
  "    info->synapseCatalog.directFile = NULL;\n"
  "    info->synapseCatalog.fileID = -1;\n"
  "    info->synapseCatalog.fileIDs = NULL;\n"
  "    info->synapseCatalog.nFiles = 0;\n"
  "    info->synapseCatalog.availablegidCount = NULL;\n"
  "    info->synapseCatalog.availablegids = NULL;\n"
  "    info->synapseCatalog.gidIndex = 0;\n"
  "    info->confirmedCells.count = 0;\n"
  "    info->confirmedCells.gids = NULL;\n"
  "    info->confirmedCells.fileIDs = NULL;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Use to sort gids for look up during call of readDirectMapping func\n"
  " */\n"
  "int gidcompare( const void *a, const void *b ) {\n"
  "    return ( *(double*)a - *(double*)b );\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Use to confirm a gid is present on local cpu to help readDirectMapping func.  use binary search on sorted gidList\n"
  " */\n"
  "int gidexists( double searchgid, int ngids, double *gidList ) {\n"
  "    int first = 0;\n"
  "    int last = ngids-1;\n"
  "    int middle = (first+last)/2;\n"
  "\n"
  "    while( first <= last ) {\n"
  "        if( gidList[middle] < searchgid ) {\n"
  "            first = middle + 1;\n"
  "        } else if( gidList[middle] == searchgid ) {\n"
  "            return 1;\n"
  "        } else {\n"
  "            last = middle - 1;\n"
  "        }\n"
  "\n"
  "        middle = (first+last)/2;\n"
  "    }\n"
  "\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "/**\n"
  " * Use Circuit Builder output script to know which files hold this cpu's gid synapse data.  Should be\n"
  " * short term solution until better loading method is available.\n"
  " */\n"
  "void readDirectMapping( Info *info, int ngids, double *gidList ) {\n"
  "\n"
  "    // gidList might already be sorted, but I don't want to make that assumption.  I also shouldn't alter it, so make a copy\n"
  "    double *tmpList = (double*) malloc( ngids * sizeof(double) );\n"
  "    memcpy( tmpList, gidList, ngids*sizeof(double) );\n"
  "    qsort( tmpList, ngids, sizeof(double), gidcompare );\n"
  "\n"
  "    // prepare confirmed info\n"
  "    info->confirmedCells.count = ngids;\n"
  "    info->confirmedCells.gids = (int*) malloc(ngids*sizeof(int));\n"
  "    info->confirmedCells.fileIDs = (int*) malloc(ngids*sizeof(int));\n"
  "\n"
  "    // read file data\n"
  "    FILE *fin = info->synapseCatalog.directFile;\n"
  "    info->synapseCatalog.directFile = NULL;\n"
  "\n"
  "    // read line by line.  care about lines with given substrings\n"
  "    // e.g. $CMD -i $H5.7950 -o $H5 -s /a216759 -d /a216759 -f $F\n"
  "\n"
  "    char line[1024];\n"
  "    char *res = fgets( line, 1024, fin );\n"
  "    int gid = -1;\n"
  "    int gidIndex = 0;\n"
  "    while( res != NULL ) {\n"
  "        if( strncmp( line, \"$CMD\", 4 ) == 0 ) {\n"
  "            char *gidloc = strstr( line, \"/a\" );\n"
  "            if( gidloc != NULL ) {\n"
  "                gid = atoi(&gidloc[2]);\n"
  "            }\n"
  "            if( gidexists( (double) gid, ngids, tmpList ) ) {\n"
  "                int fileID = atoi(&line[12]);\n"
  "                info->confirmedCells.gids[gidIndex] = gid;\n"
  "                info->confirmedCells.fileIDs[gidIndex] = fileID;\n"
  "                gidIndex++;\n"
  "            }\n"
  "        }\n"
  "\n"
  "        res = fgets( line, 1024, fin );\n"
  "    }\n"
  "\n"
  "    fclose( fin );\n"
  "    free(tmpList);\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Callback function for H5Giterate - if the dataset opened corresponds to a gid, it is catalogged so the\n"
  " * local cpu can inform other cpus the whereabouts of that gid\n"
  " *\n"
  " * @param loc_id hdf5 handle to the open file\n"
  " * @param name name of the dataset to be accessed during this iteration step\n"
  " * @param opdata not used since we have global Info object\n"
  " */\n"
  "herr_t loadShareData( hid_t loc_id, const char *name, void *opdata )\n"
  "{\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    assert( info->file_ >= 0 );\n"
  "\n"
  "    //fprintf( stderr, \"open dataset %s\\n\", name );\n"
  "\n"
  "    //make sure we are using a dataset that corresponds to a gid\n"
  "    int gid = atoi( name+1 );\n"
  "    char rebuild[32];\n"
  "    snprintf( rebuild, 32, \"a%d\", gid );\n"
  "    if( strcmp( rebuild, name ) != 0 ) {\n"
  "        //non-synapse dataset, but not an error (could just be the version info)\n"
  "        //fprintf( stderr, \"ignore non-gid dataset\\n\" );\n"
  "        return 0;\n"
  "    }\n"
  "\n"
  "    // we have confirmed that this dataset corresponds to a gid.  The active file should make it part of its data\n"
  "    int fileIndex = info->synapseCatalog.nFiles-1;\n"
  "    info->synapseCatalog.availablegids[ fileIndex ][ info->synapseCatalog.gidIndex++ ] = gid;\n"
  "\n"
  "    return 1;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Open an HDF5 file for reading.  In the event of synapse data, the datasets of the file may be iterated in order to\n"
  " * build a catalog of available gids and their file locations.\n"
  " *\n"
  " * @param info Structure that manages hdf5 info\n"
  " * @param filename File to open\n"
  " * @param fileID Integer to identify this file (attached as suffix to filename)\n"
  " * @param nNodesPerFile 0: open file, but don't load data; 1: open file for catalogging; N: read portion of file for catalogging\n"
  " * @param startRank used to help calculate data range to load when file subportion is loaded\n"
  " * @param myRank used to help calculate data range to load when file subportion is loaded\n"
  " */\n"
  "int openFile( Info* info, const char *filename, int fileID, int nRanksPerFile, int startRank, int myRank )\n"
  "{\n"
  "    if( info->file_ != -1 ) {\n"
  "        H5Fclose(info->file_);\n"
  "    }\n"
  "\n"
  "    char nameoffile[512];\n"
  "    //fprintf( stderr, \"arg check: %s %d %d %d\\n\", filename, nRanksPerFile, startRank, myRank );\n"
  "    if( fileID != -1 ) {\n"
  "        snprintf( nameoffile, 512, \"%s.%d\", filename, fileID );\n"
  "    } else {\n"
  "        strncpy( nameoffile, filename, 512 );\n"
  "    }\n"
  "\n"
  "    info->name_group[0]='\\0';\n"
  "\n"
  "    hid_t file_driver = (info->acc_tpl1 != -1)? info->acc_tpl1 : H5P_DEFAULT;\n"
  "\n"
  "    // Opens the file with the alternate handler\n"
  "    info->file_ = H5Fopen( nameoffile, H5F_ACC_RDONLY, file_driver);\n"
  "    int result = (info->file_ < 0);\n"
  "    int failed = result;\n"
  "\n"
  "#ifndef DISABLE_MPI\n"
  "    if( info->acc_tpl1 != -1 ) {\n"
  "        MPI_Allreduce( &result, &failed, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD );\n"
  "\n"
  "        if( failed ) {\n"
  "            int canreport = (result<0)?nrnmpi_myid:nrnmpi_numprocs, willreport = 0;\n"
  "            MPI_Allreduce( &canreport, &willreport, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD );\n"
  "\n"
  "            if( willreport == nrnmpi_myid ) {\n"
  "                fprintf(stderr, \"%d ERROR: %d ranks failed collective open of synapse file: %s\\n\", nrnmpi_myid, failed, nameoffile );\n"
  "            }\n"
  "            info->file_ = -1;\n"
  "            H5Eprint(stderr);\n"
  "            return -1;\n"
  "        }\n"
  "    } else  // to the serial-version if\n"
  "#endif\n"
  "    if( failed ) {\n"
  "        info->file_ = -1;\n"
  "        fprintf(stderr, \"ERROR: Failed to open synapse file: %s\\n\", nameoffile );\n"
  "        H5Eprint(stderr);\n"
  "        return -1;\n"
  "    }\n"
  "\n"
  "    if( nRanksPerFile == 0 ) {\n"
  "        // don't need to load data yet, so we return\n"
  "        return 0;\n"
  "    }\n"
  "\n"
  "    // will catalog synapse data\n"
  "    info->synapseCatalog.fileID = fileID;\n"
  "\n"
  "    int nDatasetsToImport=0, startIndex=0;\n"
  "    hsize_t nObjects;\n"
  "    H5Gget_num_objs( info->file_, &nObjects );\n"
  "\n"
  "    if( nRanksPerFile == 1 ) {\n"
  "        nDatasetsToImport = (int) nObjects;\n"
  "    }\n"
  "    else {\n"
  "        // need to determine which indices to read\n"
  "        nDatasetsToImport = (int) nObjects / nRanksPerFile;\n"
  "        if( nObjects%nRanksPerFile != 0 )\n"
  "            nDatasetsToImport++;\n"
  "\n"
  "        startIndex = (myRank-startRank)*nDatasetsToImport;\n"
  "        if( startIndex + nDatasetsToImport > (int) nObjects ) {\n"
  "            nDatasetsToImport = (int) nObjects - startIndex;\n"
  "            if( nDatasetsToImport <= 0 ) {\n"
  "                //fprintf( stderr, \"No need to import any data on rank %d since all %d are claimed\\n\", myRank, (int) nObjects );\n"
  "                return 0;\n"
  "            }\n"
  "        }\n"
  "    }\n"
  "\n"
  "    int nFiles = ++info->synapseCatalog.nFiles;\n"
  "    info->synapseCatalog.fileIDs = (int*) realloc ( info->synapseCatalog.fileIDs, sizeof(int)*nFiles );\n"
  "    info->synapseCatalog.fileIDs[nFiles-1] = fileID;\n"
  "    info->synapseCatalog.availablegidCount = (int*) realloc ( info->synapseCatalog.availablegidCount, sizeof(int)*nFiles );\n"
  "    info->synapseCatalog.availablegids = (int**) realloc ( info->synapseCatalog.availablegids, sizeof(int*)*nFiles );\n"
  "\n"
  "    info->synapseCatalog.availablegidCount[nFiles-1] = nDatasetsToImport;\n"
  "    info->synapseCatalog.availablegids[nFiles-1] = (int*) calloc ( nDatasetsToImport, sizeof(int) );\n"
  "    info->synapseCatalog.gidIndex=0;\n"
  "\n"
  "    //fprintf( stderr, \"load datasets %d through %d (max %d)\\n\", startIndex, startIndex+nDatasetsToImport, (int) nObjects );\n"
  "\n"
  "    int i, verify=startIndex;\n"
  "    for( i=startIndex; i<startIndex+nDatasetsToImport && i<nObjects; i++ ) {\n"
  "        assert( verify == i );\n"
  "        result = H5Giterate( info->file_, \"/\", &verify, loadShareData, NULL );\n"
  "        if( result != 1 )\n"
  "            continue;\n"
  "    }\n"
  "\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Load a dataset so that the dimensions are available, but don't retrieve any data\n"
  " *\n"
  " * @param info Structure that manages hdf5 info, its datamatrix_ variable is populated with hdf5 data on success\n"
  " * @param name The name of the dataset to access\n"
  " * @return 0 on success, < 0 on error\n"
  " */\n"
  "int loadDimensions( Info *info, char* name )\n"
  "{\n"
  "    int isCurrentlyLoaded = strncmp( info->name_group, name, 256 ) == 0;\n"
  "    if( isCurrentlyLoaded )\n"
  "        return 0;\n"
  "\n"
  "    hsize_t dims[2] = {0}, offset[2] = {0};\n"
  "    hid_t dataset_id, dataspace;\n"
  "\n"
  "    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)\n"
  "    {\n"
  "        fprintf(stderr, \"Error accessing to dataset %s in synapse file\\n\", name);\n"
  "        return -1;\n"
  "    }\n"
  "    dataset_id = H5Dopen(info->file_, name);\n"
  "\n"
  "    strncpy(info->name_group, name, 256);\n"
  "\n"
  "    dataspace = H5Dget_space(dataset_id);\n"
  "\n"
  "    int dimensions = H5Sget_simple_extent_ndims(dataspace);\n"
  "    H5Sget_simple_extent_dims(dataspace,dims,NULL);\n"
  "    info->rowsize_ = (unsigned long)dims[0];\n"
  "    if( dimensions > 1 )\n"
  "        info->columnsize_ = dims[1];\n"
  "    else\n"
  "        info->columnsize_ = 1;\n"
  "\n"
  "    H5Sclose(dataspace);\n"
  "    H5Dclose(dataset_id);\n"
  "\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Given the name of a dataset, load it from the current hdf5 file into the matrix pointer\n"
  " *\n"
  " * @param info Structure that manages hdf5 info, its datamatrix_ variable is populated with hdf5 data on success\n"
  " * @param name The name of the dataset to access and load in the hdf5 file\n"
  " */\n"
  "int loadDataMatrix( Info *info, char* name )\n"
  "{\n"
  "    int isCurrentlyLoaded = strncmp( info->name_group, name, 256 ) == 0;\n"
  "    if( isCurrentlyLoaded )\n"
  "        return 0;\n"
  "\n"
  "    hsize_t dims[2] = {0}, offset[2] = {0};\n"
  "    hid_t dataset_id, dataspace;\n"
  "\n"
  "    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0) {\n"
  "        return -1;\n"
  "    }\n"
  "    dataset_id = H5Dopen(info->file_, name);\n"
  "\n"
  "    strncpy(info->name_group, name, 256);\n"
  "\n"
  "    dataspace = H5Dget_space(dataset_id);\n"
  "\n"
  "    int dimensions = H5Sget_simple_extent_ndims(dataspace);\n"
  "    //printf(\"Dimensions:%d\\n\",dimensions);\n"
  "    H5Sget_simple_extent_dims(dataspace,dims,NULL);\n"
  "    //printf(\"Accessing to %s , nrow:%lu,ncolumns:%lu\\n\",info->name_group,(unsigned long)dims[0],(unsigned long)dims[1]);\n"
  "    info->rowsize_ = (unsigned long)dims[0];\n"
  "    if( dimensions > 1 )\n"
  "        info->columnsize_ = dims[1];\n"
  "    else\n"
  "        info->columnsize_ = 1;\n"
  "    //printf(\"\\n Size of data is row= [%d], Col = [%lu]\\n\", dims[0], (unsigned long)dims[1]);\n"
  "    if(info->datamatrix_ != NULL)\n"
  "    {\n"
  "        //printf(\"Freeeing memory \\n \");\n"
  "        free(info->datamatrix_);\n"
  "    }\n"
  "    info->datamatrix_ = (float *) malloc(sizeof(float) *(info->rowsize_*info->columnsize_));\n"
  "    //info->datamatrix_ = (float *) hoc_Emalloc(sizeof(float) *(info->rowsize_*info->columnsize_)); hoc_malchk();\n"
  "    // Last line fails, corrupt memory of argument 1 and  probably more\n"
  "    H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL);\n"
  "    hid_t dataspacetogetdata=H5Screate_simple(dimensions,dims,NULL);\n"
  "    H5Dread(dataset_id,H5T_NATIVE_FLOAT,dataspacetogetdata,H5S_ALL,H5P_DEFAULT,info->datamatrix_);\n"
  "    H5Sclose(dataspace);\n"
  "    H5Sclose(dataspacetogetdata);\n"
  "    H5Dclose(dataset_id);\n"
  "    //printf(\"Working , accessed %s , on argstr1 %s\\n\",info->name_group,gargstr(1));\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Given the name of a dataset with id values, load it from the current hdf5 file into the matrix pointer\n"
  " *\n"
  " * @param info Structure that manages hdf5 info, its datavector_ variable is populated with hdf5 data on success\n"
  " * @param name The name of the dataset to access and load in the hdf5 file\n"
  " */\n"
  "int loadDataVector( Info *info, char* name )\n"
  "{\n"
  "    hsize_t dims[2] = {0}, offset[2] = {0};\n"
  "    hid_t dataset_id, dataspace;\n"
  "\n"
  "    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)\n"
  "    {\n"
  "        fprintf(stderr, \"Error accessing to dataset %s in synapse file\\n\", name);\n"
  "        return -1;\n"
  "    }\n"
  "    dataset_id = H5Dopen(info->file_, name);\n"
  "    dataspace = H5Dget_space(dataset_id);\n"
  "\n"
  "    strncpy(info->name_group, name, 256);\n"
  "\n"
  "    int dimensions = H5Sget_simple_extent_ndims(dataspace);\n"
  "    H5Sget_simple_extent_dims(dataspace,dims,NULL);\n"
  "    info->rowsize_ = (unsigned long)dims[0];\n"
  "    if( dimensions > 1 )\n"
  "        info->columnsize_ = dims[1];\n"
  "    else\n"
  "        info->columnsize_ = 1;\n"
  "\n"
  "    if(info->datavector_ != NULL) {\n"
  "        free(info->datavector_);\n"
  "    }\n"
  "    info->datavector_ = (long long *) malloc(sizeof(long long)*(info->rowsize_*info->columnsize_));\n"
  "\n"
  "    H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, offset, NULL, dims, NULL);\n"
  "    hid_t dataspacetogetdata=H5Screate_simple(dimensions,dims,NULL);\n"
  "    H5Dread(dataset_id,H5T_NATIVE_ULONG,dataspacetogetdata,H5S_ALL,H5P_DEFAULT,info->datavector_);\n"
  "    H5Sclose(dataspace);\n"
  "    H5Sclose(dataspacetogetdata);\n"
  "    H5Dclose(dataset_id);\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Load an individual value from a dataset\n"
  " *\n"
  " * @param info Shared data\n"
  " * @param name dataset to open and read from\n"
  " * @param row  data item to retrieve\n"
  " * @param dest int address where data is to be stored\n"
  " */\n"
  "int loadDataInt( Info* info, char* name, hid_t row, int *dest )\n"
  "{\n"
  "    hsize_t dims[1] = {1}, offset[1] = {row}, offset_out[1] = {0}, count[1] = {1};\n"
  "    hid_t dataset_id, dataspace, memspace, space; //, filetype;\n"
  "    herr_t status;\n"
  "    int ndims = 0;\n"
  "    long long temp;\n"
  "\n"
  "    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0) {\n"
  "        fprintf(stderr, \"Error accessing to dataset %s in h5 file\\n\", name);\n"
  "        return -1;\n"
  "    }\n"
  "\n"
  "    dataset_id = H5Dopen(info->file_, name);\n"
  "    dataspace = H5Dget_space(dataset_id);\n"
  "\n"
  "    //filetype = H5Dget_type (dataset_id);\n"
  "    space = H5Dget_space (dataset_id);\n"
  "    ndims = H5Sget_simple_extent_dims (space, dims, NULL);\n"
  "\n"
  "    status = H5Sselect_hyperslab( space, H5S_SELECT_SET, offset, NULL, count, NULL );\n"
  "\n"
  "    // memory space to receive data and select hyperslab in that\n"
  "    memspace = H5Screate_simple( 1, dims, NULL );\n"
  "    status = H5Sselect_hyperslab( memspace, H5S_SELECT_SET, offset_out, NULL, count, NULL );\n"
  "\n"
  "    status = H5Dread (dataset_id, H5T_NATIVE_ULONG, memspace, space, H5P_DEFAULT, &temp );\n"
  "\n"
  "    *dest = temp;\n"
  "\n"
  "    status = H5Sclose (space);\n"
  "    status = H5Sclose(dataspace);\n"
  "    status = H5Dclose(dataset_id);\n"
  "\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "/**\n"
  " * Given the name of a dataset that should contain variable length string data, load those strings\n"
  " */\n"
  "int loadDataString( Info* info, char* name, hid_t row, char **hoc_dest )\n"
  "{\n"
  "    hsize_t dims[1] = {1}, offset[1] = {row}, offset_out[1] = {0}, count[1] = {1};\n"
  "    hid_t dataset_id, dataspace, memspace, space, filetype, memtype;\n"
  "    herr_t status;\n"
  "    char** rdata;\n"
  "    int ndims = 0;\n"
  "\n"
  "    if( H5Lexists(info->file_, name, H5P_DEFAULT) == 0)\n"
  "    {\n"
  "        fprintf(stderr, \"Error accessing to dataset %s in h5 file\\n\", name);\n"
  "        return -1;\n"
  "    }\n"
  "    dataset_id = H5Dopen(info->file_, name);\n"
  "    dataspace = H5Dget_space(dataset_id);\n"
  "\n"
  "    filetype = H5Dget_type (dataset_id);\n"
  "    space = H5Dget_space (dataset_id);\n"
  "    ndims = H5Sget_simple_extent_dims (space, dims, NULL);\n"
  "    rdata = (char **) malloc (sizeof (char *));\n"
  "\n"
  "    memtype = H5Tcopy (H5T_C_S1);\n"
  "    status = H5Tset_size (memtype, H5T_VARIABLE);\n"
  "    H5Tset_cset(memtype, H5T_CSET_UTF8);\n"
  "\n"
  "    status = H5Sselect_hyperslab( space, H5S_SELECT_SET, offset, NULL, count, NULL );\n"
  "\n"
  "    // memory space to receive data and select hyperslab in that\n"
  "    memspace = H5Screate_simple( 1, dims, NULL );\n"
  "    status = H5Sselect_hyperslab( memspace, H5S_SELECT_SET, offset_out, NULL, count, NULL );\n"
  "\n"
  "    status = H5Dread (dataset_id, memtype, memspace, space, H5P_DEFAULT, rdata);\n"
  "\n"
  "    hoc_assign_str( hoc_dest, rdata[0] );\n"
  "\n"
  "    //fprintf( stderr, \"free h5 mem\\n\" );  // TODO: determine why this causes a crash.  For now we leak memory\n"
  "    //status = H5Dvlen_reclaim (memtype, space, H5P_DEFAULT, rdata );\n"
  "    //fprintf( stderr, \"free rdata\\n\" );\n"
  "    free(rdata);\n"
  "\n"
  "    status = H5Sclose (space);\n"
  "    status = H5Sclose (dataspace);\n"
  "    status = H5Tclose (filetype);\n"
  "    status = H5Tclose (memtype);\n"
  "    status = H5Dclose (dataset_id);\n"
  "\n"
  "    return 0;\n"
  "}\n"
  "\n"
  "#endif  // DISABLE_HDF5\n"
  "ENDVERBATIM\n"
  "\n"
  "\n"
  "\n"
  "CONSTRUCTOR { : double - loc of point process ??? ,string filename\n"
  "VERBATIM {\n"
  "#ifdef DISABLE_HDF5\n"
  "    // Neuron might init the mechanism. With args it's the user.\n"
  "    if(ifarg(1)) {\n"
  "        fprintf(stderr, \"HDF5 support is not available\\n\");\n"
  "        exit(-1);\n"
  "    }\n"
  "#else\n"
  "    char nameoffile[512];\n"
  "    int nFiles = 1;\n"
  "\n"
  "    if( ifarg(2) ) {\n"
  "        nFiles = *getarg(2);\n"
  "    }\n"
  "\n"
  "    if(ifarg(1) && hoc_is_str_arg(1)) {\n"
  "        INFOCAST;\n"
  "        Info* info = 0;\n"
  "\n"
  "        strncpy(nameoffile, gargstr(1),512);\n"
  "        info = (Info*) hoc_Emalloc(sizeof(Info)); hoc_malchk();\n"
  "        initInfo( info );\n"
  "\n"
  "        if( ifarg(3) ) {\n"
  "            info->verboseLevel = *getarg(3);\n"
  "        }\n"
  "\n"
  "        *ip = info;\n"
  "\n"
  "        if( nFiles == 1 ) {\n"
  "            hid_t plist_id = 0;\n"
  "\n"
  "            // if a second arg was explicitly given as 1, I assume that we are doing a parallel file access\n"
  "            // saw deadlock while running on viz cluster and hence disabling parallel read\n"
  "            if( ifarg(2) ) {\n"
  "                if( nrnmpi_myid == 0 ) { fprintf( stderr, \"using parallel hdf5 is disabled\\n\" ); }\n"
  "                //info->acc_tpl1 = H5Pcreate(H5P_FILE_ACCESS);\n"
  "                //H5Pset_fapl_mpio(info->acc_tpl1, MPI_COMM_WORLD, MPI_INFO_NULL);\n"
  "            }\n"
  "\n"
  "            // normal case - open a file and be ready to load data as needed\n"
  "            openFile( info, nameoffile, -1, 0, 0, 0 );\n"
  "        }\n"
  "        else {\n"
  "            // Each cpu is reponsible for a portion of the data\n"
  "            info->synapseCatalog.rootName = strdup( nameoffile );\n"
  "\n"
  "            int mpi_size=1, mpi_rank=0;\n"
  "#ifndef DISABLE_MPI\n"
  "            MPI_Comm_size( MPI_COMM_WORLD, &mpi_size );\n"
  "            MPI_Comm_rank( MPI_COMM_WORLD, &mpi_rank );\n"
  "#endif\n"
  "            //fprintf( stderr, \"%d vs %d\\n\", mpi_size, nFiles );\n"
  "            // attempt to use the merge script to catalog files.  Only if it is not found should we then go to the\n"
  "            // individual files and iterate the datasets\n"
  "            int plength = strlen(nameoffile);\n"
  "            char *nrnPath = (char*) malloc( plength + 128 );\n"
  "            strncpy( nrnPath, nameoffile, plength+1 );\n"
  "            char *term = strrchr( nrnPath, '/' ); *term = 0;\n"
  "\n"
  "            // rem: recent circuit building has changed the name of the merge script.  Hopefully it will not change again.  But anyways\n"
  "            // we might replace this whole mod file with a completely better method in the future.\n"
  "            strcat( nrnPath, \"/mergeAllH5.sh\" );\n"
  "            FILE *fin = fopen( nrnPath, \"r\" );\n"
  "            if( !fin ) {\n"
  "                // try the other name\n"
  "                *term = 0;\n"
  "                strcat( nrnPath, \"/merge_nrn_positions.sh\" );\n"
  "                fin = fopen( nrnPath, \"r\" );\n"
  "            }\n"
  "            free(nrnPath);\n"
  "            if( fin ) {\n"
  "                info->synapseCatalog.directFile = fin;\n"
  "                return;\n"
  "            }\n"
  "\n"
  "            // need to determine if I open multiple files per cpu or multiple cpus share a file\n"
  "            if( mpi_size > nFiles ) { // multiple cpus per file\n"
  "                int nRanksPerFile = (int) mpi_size / nFiles;\n"
  "                if( mpi_size % nFiles != 0 )\n"
  "                    nRanksPerFile++;\n"
  "\n"
  "                //fprintf( stderr, \"nRanksPerFile %d = %d/%d\\n\", nRanksPerFile, mpi_size, nFiles );\n"
  "\n"
  "                if( nRanksPerFile * nFiles > mpi_size ) { // no files left for this rank\n"
  "                    info->file_ = -1;\n"
  "                    return;\n"
  "                }\n"
  "\n"
  "                int fileIndex = (int) mpi_rank / nRanksPerFile;  //this should be truncated\n"
  "                int startRank = fileIndex * nRanksPerFile;\n"
  "\n"
  "                //sprintf( nameoffile, \"%s.%d\", gargstr(1), fileIndex );\n"
  "                //fprintf( stderr, \"I should open file %s\\n\", nameoffile );\n"
  "\n"
  "                openFile( info, nameoffile, fileIndex, nRanksPerFile, startRank, mpi_rank );\n"
  "\n"
  "            } else {\n"
  "                // one or more files per cpu - any file opened should load all the data.\n"
  "                int nFilesPerRank = nFiles / mpi_size;\n"
  "                //fprintf( stderr, \"nFilesPerRank %d = %d/%d\\n\", nFilesPerRank, nFiles, mpi_size );\n"
  "\n"
  "                if( nFiles % mpi_size != 0 ) {\n"
  "                    nFilesPerRank++;\n"
  "                }\n"
  "                int startFile = mpi_rank * nFilesPerRank;\n"
  "                if( startFile+nFilesPerRank > nFiles ) {\n"
  "                    nFilesPerRank = nFiles-startFile;\n"
  "                    if( nFilesPerRank <= 0 ) {\n"
  "                        info->file_ = -1;\n"
  "                        return;\n"
  "                    }\n"
  "                }\n"
  "\n"
  "                int fileIndex=0;\n"
  "                for( fileIndex=0; fileIndex<nFilesPerRank; fileIndex++ ) {\n"
  "                    //sprintf( nameoffile, \"%s.%d\", gargstr(1), startFile+fileIndex );\n"
  "                    openFile( info, nameoffile, startFile+fileIndex, 1, 0, 0 );\n"
  "                }\n"
  "            }\n"
  "        }\n"
  "    }\n"
  "#endif  // DISABLE_HDF5\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "DESTRUCTOR {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST; Info* info = *ip;\n"
  "    if(info->file_>=0)\n"
  "    {\n"
  "        if( info->acc_tpl1 != -1 ) {\n"
  "            if( nrnmpi_myid == 0 ) { fprintf( stderr, \"terminating parallel h5 access\\n\" ); }\n"
  "            H5Pclose(info->acc_tpl1);\n"
  "        }\n"
  "        //printf(\"Trying to close\\n\");\n"
  "        H5Fclose(info->file_);\n"
  "        //printf(\"Close\\n\");\n"
  "        info->file_ = -1;\n"
  "    }\n"
  "    if(info->datamatrix_ != NULL)\n"
  "    {\n"
  "        free(info->datamatrix_);\n"
  "        info->datamatrix_ = NULL;\n"
  "    }\n"
  "    if( info->datavector_ != NULL )\n"
  "    {\n"
  "        free( info->datavector_ );\n"
  "        info->datavector_ = NULL;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION redirect() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "#ifndef DISABLE_MPI\n"
  "    FILE *fout;\n"
  "    char fname[128];\n"
  "\n"
  "    int mpi_size, mpi_rank;\n"
  "    //fprintf( stderr, \"rank %d\\n\", getpid() );\n"
  "    //sleep(20);\n"
  "\n"
  "\n"
  "    // get MPI info\n"
  "    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);\n"
  "    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);\n"
  "\n"
  "    if( mpi_rank != 0 ) {\n"
  "        sprintf( fname, \"NodeFiles/%d.%dnode.out\", mpi_rank, mpi_size );\n"
  "        fout = freopen( fname, \"w\", stdout );\n"
  "        if( !fout ) {\n"
  "            fprintf( stderr, \"failed to redirect.  Terminating\\n\" );\n"
  "            exit(0);\n"
  "        }\n"
  "\n"
  "        sprintf( fname, \"NodeFiles/%d.%dnode.err\", mpi_rank, mpi_size );\n"
  "        fout = freopen( fname, \"w\", stderr );\n"
  "        setbuf( fout, NULL );\n"
  "    }\n"
  "#endif  // DISABLE_MPI\n"
  "#endif  // DISABLE_HDF5\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "FUNCTION checkVersion() {\n"
  "VERBATIM {\n"
  "    int versionNumber = 0;\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    int mpi_size=1, mpi_rank=0;\n"
  "\n"
  "#ifndef DISABLE_MPI\n"
  "    // get MPI info\n"
  "    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);\n"
  "    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);\n"
  "#endif\n"
  "\n"
  "    if( mpi_rank == 0 )\n"
  "    {\n"
  "        if( H5Lexists(info->file_, \"info\", H5P_DEFAULT) == 0) {\n"
  "            versionNumber = 0;\n"
  "        } else {\n"
  "            hid_t dataset_id = H5Dopen( info->file_, \"info\" );\n"
  "            hid_t attr_id = H5Aopen_name( dataset_id, \"version\" );\n"
  "            H5Aread( attr_id, H5T_NATIVE_INT, &versionNumber );\n"
  "            H5Aclose(attr_id);\n"
  "            H5Dclose(dataset_id);\n"
  "        }\n"
  "    }\n"
  "\n"
  "#ifndef DISABLE_MPI\n"
  "    MPI_Bcast( &versionNumber, 1, MPI_INT, 0, MPI_COMM_WORLD );\n"
  "#endif\n"
  "\n"
  "#endif  // DISABLE_HDF5\n"
  "    return versionNumber;\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "FUNCTION loadData() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "\n"
  "    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))\n"
  "    {\n"
  "        if( ifarg(2) ) {\n"
  "            if( *getarg(2) == 1 ) { //load vector\n"
  "                info->mode = LONG_VECTOR;\n"
  "                return loadDataVector( info, gargstr(1) );\n"
  "            }\n"
  "        }\n"
  "\n"
  "        info->mode = FLOAT_MATRIX;\n"
  "        return loadDataMatrix( info, gargstr(1) );\n"
  "    }\n"
  "    else if( ifarg(1) )\n"
  "    {\n"
  "        int gid = *getarg(1);\n"
  "        int gidIndex=0;\n"
  "\n"
  "        for( gidIndex=0; gidIndex<info->confirmedCells.count; gidIndex++ ) {\n"
  "            if( info->confirmedCells.gids[gidIndex] == gid ) {\n"
  "                openFile( info, info->synapseCatalog.rootName, info->confirmedCells.fileIDs[gidIndex], 0, 0, 0 );\n"
  "\n"
  "                char cellname[256];\n"
  "                sprintf( cellname, \"a%d\", gid );\n"
  "\n"
  "                info->mode = FLOAT_MATRIX;\n"
  "                return loadDataMatrix( info, cellname );\n"
  "            }\n"
  "        }\n"
  "\n"
  "        //if we reach here, did not find data\n"
  "        if( info->verboseLevel > 0 )\n"
  "            fprintf( stderr, \"Warning: failed to find data for gid %d\\n\", gid );\n"
  "    }\n"
  "\n"
  "    return -1;\n"
  "#endif  // DISABLE_HDF5\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION getNoOfColumns(){ : string cellname\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    //printf(\"(Inside number of Col)Number of Col %s\\n\",gargstr(1));\n"
  "    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))\n"
  "    {\n"
  "        char name[256];\n"
  "        strncpy(name,gargstr(1),256);\n"
  "        if(strncmp(info->name_group,name,256) == 0)\n"
  "        {\n"
  "            //printf(\"Returning :%d\\n\",(int)info->rowsize_);\n"
  "            int res = (int) info->columnsize_;\n"
  "            //printf(\"Res :%d\\n\",res);\n"
  "            return res;\n"
  "        }\n"
  "        //printf(\"NumberofCol Error on the name of last loaded data: trying to access:%s loaded:%s\\n\",name,info->name_group);\n"
  "        return 0;\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        return 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION numberofrows() { : string cellname\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    //printf(\"(Inside number of rows)Number of rows %s\\n\",gargstr(1));\n"
  "    if(info->file_>=0 && ifarg(1) && hoc_is_str_arg(1))\n"
  "    {\n"
  "        char name[256];\n"
  "        strncpy(name,gargstr(1),256);\n"
  "        if(strncmp(info->name_group,name,256) == 0)\n"
  "        {\n"
  "            //printf(\"Returning :%d\\n\",(int)info->rowsize_);\n"
  "            int res = (int) info->rowsize_;\n"
  "            //printf(\"Res :%d\\n\",res);\n"
  "            return res;\n"
  "        }\n"
  "        //printf(\"Numberofrows Error on the name of last loaded data: trying to access:%s loaded:%s\\n\",name,info->name_group);\n"
  "        return 0;\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        fprintf(stderr, \"general error: bad file handle, missing arg?\");\n"
  "        return 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION getData() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && ifarg(3))\n"
  "    {\n"
  "        char name[256];\n"
  "        strncpy(name,gargstr(1),256);\n"
  "        if(strncmp(info->name_group,name,256) == 0)\n"
  "        {\n"
  "            hsize_t row,column;\n"
  "            row = (hsize_t) *getarg(2);\n"
  "            column = (hsize_t) *getarg(3);\n"
  "            if(row<0 || row >=info->rowsize_ || column < 0 || column>=info->columnsize_)\n"
  "            {\n"
  "                fprintf(stderr, \"ERROR: trying to access to a row and column erroneus on %s, size: %lld,%lld accessing to %lld,%lld\\n\",\n"
  "                        name, info->rowsize_, info->columnsize_, row, column);\n"
  "                return 0;\n"
  "            }\n"
  "\n"
  "            if( info->mode == FLOAT_MATRIX ) {\n"
  "                return info->datamatrix_[row*info->columnsize_ + column];\n"
  "            } else if( info->mode == LONG_VECTOR ) {\n"
  "                return (double) info->datavector_[row];\n"
  "            } else {\n"
  "                fprintf( stderr, \"unexpected mode: %d\\n\", info->mode );\n"
  "            }\n"
  "        }\n"
  "        fprintf(stderr, \"(Getting data)Error on the name of last loaded data: access:%s loaded:%s\\n\",name,info->name_group);\n"
  "        return 0;\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        fprintf( stderr, \"ERROR:Error on number of rows of %s\\n\", gargstr(1) );\n"
  "        return 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "Retrieve a integer value  from an hdf5 dataset\n"
  "Note that this function doesn't apply as many checks as other functions.\n"
  "e.g. The row is assumed to be within the dataset; this code is expected to be refactored ( -JGK, Jul 6 2017)\n"
  "@param dataset name\n"
  "@param row\n"
  "@return read integer\n"
  "ENDCOMMENT\n"
  "FUNCTION getDataInt() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    int value = -1;\n"
  "\n"
  "    _lgetDataInt = 0;\n"
  "    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )\n"
  "    {\n"
  "        // Use HDF5 interface to get the requested string item from the dataset\n"
  "        if( loadDataInt( info, gargstr(1), *getarg(2), &value ) == 0 ) {\n"
  "            _lgetDataInt = value;\n"
  "        }\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "Load a dataset so that the dimensions can be accessed\n"
  "Note that this function doesn't apply as many checks as other functions.\n"
  "@param dataset name\n"
  "ENDCOMMENT\n"
  "PROCEDURE getDimensions() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "\n"
  "    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) ) {\n"
  "        loadDimensions( info, gargstr(1) );\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "Retrieve a single string from an hdf5 dataset and store in the provided hoc strdef\n"
  "Note that this function doesn't apply as many checks as other functions.\n"
  "e.g. The row is assumed to be within the dataset; this code is expected to be refactored ( -JGK, Jul 6 2017)\n"
  "@param dataset name\n"
  "@param row\n"
  "@param destination strdef from hoc\n"
  "ENDCOMMENT\n"
  "PROCEDURE getDataString() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "\n"
  "    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && ifarg(3) )\n"
  "    {\n"
  "        // Use HDF5 interface to get the requested string item from the dataset\n"
  "        loadDataString( info, gargstr(1), *getarg(2), hoc_pgargstr(3) );\n"
  "    }\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION getColumnDataRange() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    void* pdVec = NULL;\n"
  "    double* pd  = NULL;\n"
  "    int i = 0;\n"
  "    int nStart, nEnd, count;\n"
  "    if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )\n"
  "    {\n"
  "        char name[256];\n"
  "        strncpy(name,gargstr(1),256);\n"
  "        if(strncmp(info->name_group,name,256) == 0)\n"
  "        {\n"
  "            hsize_t column;\n"
  "            column  = (hsize_t) *getarg(2);\n"
  "            if(column<0 || column >=info->columnsize_ )\n"
  "            {\n"
  "                fprintf(stderr, \"ERROR: trying to access to a column erroneus on %s, size: %lld,%lld accessing to column %lld\\n \",name,info->rowsize_,info->columnsize_,column);\n"
  "                return 0;\n"
  "            }\n"
  "            pdVec = vector_arg(3);\n"
  "            nStart = (int)*getarg(4);\n"
  "            nEnd  = (int)*getarg(5);\n"
  "            vector_resize(pdVec, nEnd-nStart+1);\n"
  "            pd = vector_vec(pdVec);\n"
  "            count =0;\n"
  "            for( i=nStart; i<=nEnd; i++){\n"
  "                pd[count] = info->datamatrix_[i*info->columnsize_ + column];\n"
  "                count = count +1;\n"
  "                //printf(\"\\n Filling [%f]\", pd[i]);\n"
  "            }\n"
  "            //float res = info->datamatrix_[row*info->columnsize_ + column];\n"
  "            return 1;\n"
  "        }\n"
  "        fprintf(stderr, \"(Getting data)Error on the name of last loaded data: access:%s loaded:%s\\n\",name,info->name_group);\n"
  "        return 0;\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        //printf(\"ERROR:Error on number of rows of \\n\");\n"
  "        return 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * Load all the data from a single column of active dataset into a NEURON Vector object\n"
  " *\n"
  " * @param dataset name - used to confirm that the active dataset matches what is requested\n"
  " * @param column index\n"
  " * @param Vector object to fill - resized as needed to hold the available data\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION getColumnData() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    void* pdVec = NULL;\n"
  "    double* pd  = NULL;\n"
  "    int i = 0;\n"
  "    if(info->file_>=0&& ifarg(1) && hoc_is_str_arg(1) && ifarg(2) )\n"
  "    {\n"
  "        char name[256];\n"
  "        strncpy(name,gargstr(1),256);\n"
  "        if(strncmp(info->name_group,name,256) == 0)\n"
  "        {\n"
  "            hsize_t column;\n"
  "            column  = (hsize_t) *getarg(2);\n"
  "            if(column<0 || column >=info->columnsize_ )\n"
  "            {\n"
  "                fprintf(stderr, \"ERROR: trying to access to a column erroneus on %s, size: %lld,%lld accessing to column %lld\\n \",name,info->rowsize_,info->columnsize_,column);\n"
  "                return 0;\n"
  "            }\n"
  "            pdVec = vector_arg(3);\n"
  "            vector_resize(pdVec, (int) info->rowsize_);\n"
  "            pd = vector_vec(pdVec);\n"
  "            for( i=0; i<info->rowsize_; i++){\n"
  "                pd[i] = info->datamatrix_[i*info->columnsize_ + column];\n"
  "                //printf(\"\\n Filling [%f]\", pd[i]);\n"
  "            }\n"
  "            //float res = info->datamatrix_[row*info->columnsize_ + column];\n"
  "            return 1;\n"
  "        }\n"
  "        fprintf(stderr, \"(Getting data)Error on the name of last loaded data: access:%s loaded:%s\\n\",name,info->name_group);\n"
  "        return 0;\n"
  "    }\n"
  "    else\n"
  "    {\n"
  "        //printf(\"ERROR:Error on number of rows of \\n\");\n"
  "        return 0;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * Retrieve the value for an attribute of the active dataset.  Expected to contain only one value of double type\n"
  " *\n"
  " * @param dataset name\n"
  " * @param attribute name\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION getAttributeValue() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    if( info->file_ >= 0 && ifarg(1) && hoc_is_str_arg(1) && ifarg(2) && hoc_is_str_arg(2) )\n"
  "    {\n"
  "        if( H5Lexists(info->file_, gargstr(1), H5P_DEFAULT) == 0)\n"
  "        {\n"
  "            fprintf( stderr, \"Error: no dataset with name %s available.\\n\", gargstr(1) );\n"
  "            return 0;\n"
  "        }\n"
  "        hid_t dataset_id = H5Dopen( info->file_, gargstr(1) );\n"
  "\n"
  "        double soughtValue;\n"
  "        hid_t attr_id = H5Aopen_name( dataset_id, gargstr(2) );\n"
  "        if( attr_id < 0 ) {\n"
  "            fprintf( stderr, \"Error: failed to open attribute %s\\n\", gargstr(2) );\n"
  "            return 0;\n"
  "        }\n"
  "        H5Aread( attr_id, H5T_NATIVE_DOUBLE, &soughtValue );\n"
  "        H5Dclose(dataset_id);\n"
  "\n"
  "        return soughtValue;\n"
  "    }\n"
  "\n"
  "    return 0;\n"
  "#endif\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "FUNCTION closeFile() {\n"
  "VERBATIM {\n"
  "#ifndef DISABLE_HDF5\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "    if(info->file_ >=0)\n"
  "    {\n"
  "        H5Fclose(info->file_);\n"
  "        //printf(\"Close\\n\");\n"
  "        info->file_ = -1;\n"
  "    }\n"
  "    if(info->datamatrix_ != NULL)\n"
  "    {\n"
  "        free(info->datamatrix_);\n"
  "        info->datamatrix_ = NULL;\n"
  "    }\n"
  "#endif\n"
  "}\n"
  "ENDVERBATIM\n"
  "}\n"
  "\n"
  "\n"
  "\n"
  "COMMENT\n"
  "/**\n"
  " * This function will have each cpu learn from the other cpus which nrn.h5 file contains the data it needs.  It can then load\n"
  " * the data as needed using the older functions.  Hopefully this will be better since it avoids loading data that is not needed and then\n"
  " * transmitting it across the network.  My concern is that there will still be some contention on the various nrn.h5 files with multiple cpus\n"
  " * accessing it at once, but we will see how that unfolds.\n"
  " *\n"
  " * @param gidvec hoc vector containing list of gids on local cpu\n"
  " */\n"
  "ENDCOMMENT\n"
  "FUNCTION exchangeSynapseLocations() {\n"
  "VERBATIM\n"
  "#ifndef DISABLE_HDF5\n"
  "#ifndef DISABLE_MPI\n"
  "    INFOCAST;\n"
  "    Info* info = *ip;\n"
  "\n"
  "    void* vv = vector_arg(1);\n"
  "    int gidCount = vector_capacity(vv);\n"
  "    double *gidList = vector_vec(vv);\n"
  "\n"
  "    if( info->synapseCatalog.directFile != NULL ) {\n"
  "        // the file generated by circuit building with gid to file id exists, so use that to determine mapping instead\n"
  "        readDirectMapping( info, gidCount, gidList );\n"
  "        return 0;\n"
  "    }\n"
  "\n"
  "    int mpi_size, mpi_rank;\n"
  "\n"
  "    MPI_Comm_size (MPI_COMM_WORLD, &mpi_size);\n"
  "    MPI_Comm_rank (MPI_COMM_WORLD, &mpi_rank);\n"
  "\n"
  "    // used to store the number of gids found per cpu\n"
  "    int *foundCountsAcrossCPUs = (int*) malloc( sizeof(int)*mpi_size );\n"
  "    int *foundDispls = (int*) malloc( sizeof(int)*mpi_size );\n"
  "\n"
  "    int bufferSize;\n"
  "\n"
  "    // have every cpu allocate a buffer capable of holding the data for the cpu with the most cells\n"
  "    MPI_Allreduce( &gidCount, &bufferSize, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD );\n"
  "    double* gidsRequested = (double*) malloc ( sizeof(double)*bufferSize );\n"
  "    int* gidsFound = (int*) malloc( sizeof(int)*bufferSize );\n"
  "    int* fileIDsFound = (int*) malloc( sizeof(int)*bufferSize );\n"
  "\n"
  "    double *tempRequest;  //used to hold the gidsRequested buffer when this cpu is broadcasting its gidList\n"
  "\n"
  "    // each cpu in turn will bcast its local gids.  It should then get back the file indices where the data can be found.\n"
  "    int activeRank, requestCount;\n"
  "    for( activeRank=0; activeRank<mpi_size; activeRank++ ) {\n"
  "        if( activeRank == mpi_rank ) {\n"
  "            requestCount = gidCount;\n"
  "            tempRequest = gidsRequested;\n"
  "            gidsRequested = gidList;\n"
  "        }\n"
  "\n"
  "        MPI_Bcast( &requestCount, 1, MPI_INT, activeRank, MPI_COMM_WORLD );\n"
  "        MPI_Bcast( gidsRequested, requestCount, MPI_DOUBLE, activeRank, MPI_COMM_WORLD );\n"
  "\n"
  "        // each cpu will check if the requested gids exist in its list\n"
  "        int nFiles = 0;\n"
  "\n"
  "        // TODO: linear searches at the moment.  Maybe a more efficient ln(n) search.  Although, I would prefer to implement that\n"
  "        //  with access to STL or the like data structures.\n"
  "        int fileIndex, gidIndex, requestIndex;\n"
  "        for( fileIndex=0; fileIndex < info->synapseCatalog.nFiles; fileIndex++ ) {\n"
  "            for( gidIndex=0; gidIndex < info->synapseCatalog.availablegidCount[fileIndex]; gidIndex++ ) {\n"
  "                for( requestIndex=0; requestIndex < requestCount; requestIndex++ ) {\n"
  "                    if( info->synapseCatalog.availablegids[fileIndex][gidIndex] == gidsRequested[requestIndex] ) {\n"
  "                        gidsFound[nFiles] = gidsRequested[requestIndex];\n"
  "                        fileIDsFound[nFiles++] = info->synapseCatalog.fileIDs[fileIndex];\n"
  "                    }\n"
  "                }\n"
  "            }\n"
  "        }\n"
  "\n"
  "        MPI_Gather( &nFiles, 1, MPI_INT, foundCountsAcrossCPUs, 1, MPI_INT, activeRank, MPI_COMM_WORLD );\n"
  "\n"
  "        if( activeRank == mpi_rank ) {\n"
  "            info->confirmedCells.count = 0;\n"
  "\n"
  "            int nodeIndex;\n"
  "            for( nodeIndex=0; nodeIndex<mpi_size; nodeIndex++ ) {\n"
  "                foundDispls[nodeIndex] = info->confirmedCells.count;\n"
  "                info->confirmedCells.count += foundCountsAcrossCPUs[nodeIndex];\n"
  "            }\n"
  "            info->confirmedCells.gids = (int*) malloc ( sizeof(int)*info->confirmedCells.count );\n"
  "            info->confirmedCells.fileIDs = (int*) malloc ( sizeof(int)*info->confirmedCells.count );\n"
  "        }\n"
  "\n"
  "        MPI_Gatherv( gidsFound, nFiles, MPI_INT, info->confirmedCells.gids, foundCountsAcrossCPUs, foundDispls, MPI_INT, activeRank, MPI_COMM_WORLD );\n"
  "        MPI_Gatherv( fileIDsFound, nFiles, MPI_INT, info->confirmedCells.fileIDs, foundCountsAcrossCPUs, foundDispls, MPI_INT, activeRank, MPI_COMM_WORLD );\n"
  "\n"
  "        // put back the original gid request buffer so as to not destroy this cpu's gidList\n"
  "        if( activeRank == mpi_rank ) {\n"
  "            gidsRequested = tempRequest;\n"
  "        }\n"
  "\n"
  "    }\n"
  "\n"
  "    free(gidsRequested);\n"
  "    free(gidsFound);\n"
  "    free(fileIDsFound);\n"
  "    free(foundCountsAcrossCPUs);\n"
  "    free(foundDispls);\n"
  "#endif  // DISABLE_MPI\n"
  "#endif  // DISABLE_HDF5\n"
  "ENDVERBATIM\n"
  "}\n"
  ;
#endif
