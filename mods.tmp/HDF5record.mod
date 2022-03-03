COMMENT
/**
 * If the local variable step method is used then the only variables that should
 * be added are variables of the cell in which this FileRecord
 * has been instantiated.
 */
ENDCOMMENT

NEURON {
    POINT_PROCESS HDF5Record
    POINTER pntr
    RANGE mpirank : rank of processor
    RANGE Dt
    RANGE tstart
    RANGE tstop
    RANGE rpts
}

PARAMETER {
    mpirank = 0
    Dt = .1 (ms)
    tstart = 0 (ms)
    tstop  = 0 (ms)
    rpts = 0
}

ASSIGNED {
    pntr
}

INITIAL {
    writeMeta()
    consolidateTiming()
    net_send(tstart, 1)
}

NET_RECEIVE(w) {
    recdata()
    if (t<tstop) {
        net_send(Dt, 1)
    }
}

VERBATIM

#include <stdlib.h>
#include <math.h>

#ifndef DISABLE_HDF5
#undef pntr
#define H5_USE_16_API 1
#undef dt
#include "hdf5.h"
#define dt nrn_threads->_dt

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern char* gargstr(int iarg);
extern int hoc_is_str_arg(int iarg);
extern int nrnmpi_numprocs;
extern int nrnmpi_myid;
extern int ifarg(int iarg);
extern double chkarg(int iarg, double low, double high);

typedef struct {
    void* nextReport_;
    int handle_;
    char neuronName_[256];
    char rptName_[256];
    char path_[512];
    char fn_[256];
    int tstep_;
    int tsteps_;
    double tstart_;
    double tstop_;
    double Dt_;
    double** ptrs_; /* list of pointers to hoc variables */
    float* buf_;
    float* map_;
    int np_;
    int nm_;
    int tp_; /* temporary indicator of passed variable pointers */
    int mp_; /* temporary indicator of passed variable pointers */

    /* hdf5 version */
    hid_t file_;
    hid_t neuron_;
    hid_t rpt_;
    hid_t dataspace_;
    hid_t mem_space_;
    hid_t file_space_;
    hid_t data_;
    hid_t mapping_;
//    hid_t mapping_space_;
//    hid_t map_mem_space_;
//    hid_t map_file_space_;
    int groupCreated_;

} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_pntr))

#define dp double*
extern void nrn_register_recalc_ptr_callback(void (*f)());
extern Point_process* ob2pntproc(Object*);
extern double* nrn_recalc_ptr(double*);

static void recalcptr(Info* info, int cnt, double** old_vp, double* new_v) {
    int i;
    /*printf("recalcptr np_=%d %s\n", info->np_, info->path_);*/
}

static void recalc_ptr_callback() {
    Symbol* sym;
    int i;
    hoc_List* instances;
    hoc_Item* q;
    /*printf("ASCIIrecord.mod recalc_ptr_callback\n");*/
    /* hoc has a list of the ASCIIRecord instances */
    sym = hoc_lookup("HDF5Record");
    instances = sym->u.template->olist;
    ITERATE(q, instances) {
        Info* InfoPtr;
        Point_process* pnt;
        Object* o = OBJ(q);
        /*printf("callback for %s\n", hoc_object_name(o));*/
        pnt = ob2pntproc(o);
        _ppvar = pnt->_prop->dparam;
        INFOCAST;

        for (InfoPtr = *ip; InfoPtr != 0; InfoPtr = (Info*) InfoPtr->nextReport_)
            for (i=0; i < InfoPtr->np_; ++i)
                InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);
    }
}

#endif  // ifndef DISABLE_HDF5
ENDVERBATIM


CONSTRUCTOR { : double - loc of point process, int mpirank, string path, string filename
VERBATIM
#ifndef DISABLE_HDF5
    static int first = 1;
    if (first) {
        first = 0;
        nrn_register_recalc_ptr_callback(recalc_ptr_callback);
    }

    if (ifarg(2)) {
        mpirank = floor(*getarg(2));
    }

    if (ifarg(3) && hoc_is_str_arg(3)) {
        INFOCAST;
        Info* info = 0;

        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
        info->nextReport_ = 0;
        info->neuronName_[0]= 0;
        info->rptName_[0]= 0;
        info->path_[0]=0;
        info->handle_ = -1;
        info->neuron_ = 0;
        info->tstart_ = 0;
        info->tstop_ = 0;
        info->Dt_ = 0;
        info->rpt_ = 0;
        info->ptrs_ = 0;
        info->np_ = 0;
        info->nm_ = 0;
        info->tp_ = 0;
        info->mp_ = 0;
        info->tstep_ = 0;
        info->tsteps_ = 0;
        info->groupCreated_ = 0;
        info->data_ = 0;
        info->mapping_ = 0;
        info->map_ =0;

        *ip = info;
        sprintf((*ip)->path_, "%s", gargstr(3));
        sprintf((*ip)->fn_, "%s", gargstr(4));
    }
#else
    if (ifarg(2)) {
        fprintf(stderr, "%s\n", "HDF5 is Disabled, HDF5 reports are not available");
        exit(-1);
    }
#endif
ENDVERBATIM
}


DESTRUCTOR {
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    /* need to close datasets etc */
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->data_) {
            H5Sclose(info->file_space_);
            H5Sclose(info->mem_space_);
            H5Dclose(info->data_);
            H5Dclose(info->mapping_);
        }
        H5Fclose(info->file_);
    }
#endif
ENDVERBATIM
}


COMMENT
/**
 * Resume the event delivery loop for NEURON restore. Call from Hoc only (there's param)
 *
 * @param t The initial time
 */
ENDCOMMENT
PROCEDURE restartEvent() {
VERBATIM
#ifndef CORENEURON_BUILD
    const double etime = *getarg(1);
    net_send(_tqitem, (double*)0, _ppvar[1]._pvoid, etime, 1.0);
#endif
ENDVERBATIM
}


FUNCTION printInfo() {
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* ttt = *ip;
    for (ttt = *ip; ttt != 0; ttt = (Info*) ttt->nextReport_) {
        printf("Info-Structure Debugging (%s->%s)\n", ttt->rptName_, ttt->neuronName_);
        printf("========================\n");
        printf("nextReport_= \t\t%p\n", (void*)ttt->nextReport_);
        printf("handle_ = \t\t%d\n", ttt->handle_);
        printf("neuronName = \t\t%s\n", ttt->neuronName_);
        printf("rptName =\t\t%s\n", ttt->rptName_);
        printf("path_=\t\t%s\n", ttt->path_);
        printf("fn_ =\t\t%s\n",ttt->fn_);
        printf("tstep_ =\t\t%d\n",ttt->tstep_);
        printf("tsteps_=\t\t%d\n",ttt->tsteps_);
        printf("tstart_=\t\t%g\n",ttt->tstart_);
        printf("tstop_ =\t\t%g\n",ttt->tstop_);
        printf("Dt_=\t\t%g\n", ttt->Dt_);
        printf("ptrs_=\t\t%p\n",  (void*) ttt->ptrs_); /* list of pointers to hoc variables */
        printf("buf_=\t\t%p\n",(void*)ttt->buf_);
        printf("map_=\t\t%p\n", (void*)ttt->map_);
        printf("np_=\t\t%d\n", ttt->np_);
        printf("nm_=\t\t%d\n", ttt->nm_);
        printf("tp_=\t\t%d\n", ttt->tp_); /* temporary indicator of passed variable pointers */
        printf("mp_=\t\t%d\n", ttt->mp_); /* temporary indicator of passed variable pointers */

        /* hdf5 version */
        printf("file_=\t\t%lld\n", ttt->file_);
        printf("neuron_=\t\t%lld\n", ttt->neuron_);
        printf("rpt_=\t\t%lld\n", ttt->rpt_);
        printf("dataspace_=\t\t%lld\n", ttt->dataspace_);
        printf("mem_space_=\t\t%lld\n", ttt->mem_space_);
        printf("file_space_=\t\t%lld\n", ttt->file_space_);
        printf("data_=\t\t%lld\n", ttt->data_);
        printf("mapping_=\t\t%lld\n", ttt->mapping_);
        printf("groupCreated_=\t\t%d\n", ttt->groupCreated_);
    }
#endif
ENDVERBATIM
}


FUNCTION newReport() { : string neuronname, string setname, double vars, double tstart, double tstop, double dt, string unit
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST;
    Info* iPtr;
    Info* info;
    for (iPtr = *ip; iPtr->nextReport_ != 0; iPtr = (Info*) iPtr->nextReport_) {}
    int newRpt = 0;
    int trial = 0;
    int fileOpen = 0;
    char fn[1024];

    if (iPtr->handle_ == -1) {
        if (hoc_is_str_arg(1)) sprintf(iPtr->neuronName_, "%s", gargstr(1));
        else sprintf(iPtr->neuronName_, "neuron");

        if (hoc_is_str_arg(2)) sprintf(iPtr->rptName_, "%s", gargstr(2));
        else sprintf(iPtr->rptName_, "report");

        sprintf(fn, "%s/%s.h5", iPtr->path_, iPtr->fn_);
        // printf("the filename is: %s\n", fn);
        hid_t plist = H5Pcreate(H5P_FILE_CREATE);
            H5Pset_fapl_stdio(plist);
        // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
        iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);
        // plist = H5Pcreate(H5P_DATASET_XFER);
        // H5Pset_buffer(plist, 2097152, 0, 0);

        while ((iPtr->file_ < 0) && (trial < 20)) {
            // info->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
            iPtr->file_ = H5Fcreate(fn, H5F_ACC_TRUNC, plist, H5P_DEFAULT);
            trial += 1;
            // printf("trial %d\n", trial);
        }
        if (iPtr->file_>=0) fileOpen = 1;
        // plist = H5Pcreate(H5P_DATASET_XFER);
        // H5Pset_buffer(plist, 16777216, 0, 0);
        iPtr->handle_ = 0;
    }

    // there already is a report --> need to create a new info struct
    else {
        newRpt = 1;

        Info* info = 0;
        info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
        info->handle_ = 0;
        info->nextReport_ = 0;
        info->neuronName_[0]= 0;
        info->rptName_[0]= 0;
        info->path_[0]=0;
        info->neuron_ = 0;
        info->tstart_ = 0;
        info->tstop_ = 0;
        info->Dt_ = 0;
        info->rpt_ = 0;
        info->ptrs_ = 0;
        info->np_ = 0;
        info->nm_ = 0;
        info->tp_ = 0;
        info->mp_ = 0;
        info->tstep_ = 0;
        info->tsteps_ = 0;
        info->map_ = 0;
        info->groupCreated_ = 1;
        info->data_ = 0;
        info->mapping_ = 0;

        if (hoc_is_str_arg(1)) sprintf(info->neuronName_, "%s", gargstr(1));
        else sprintf(info->neuronName_, "neuron");

        if (hoc_is_str_arg(2)) sprintf(info->rptName_, "%s", gargstr(2));
        else sprintf(info->rptName_, "report");

        sprintf(info->fn_, "%s", (*ip)->fn_);
        sprintf(info->path_, "%s", (*ip)->path_);

        info->file_ = (*ip)->file_;
        iPtr=info;
        fileOpen = 1;
    }
    if (!fileOpen) {
        fprintf(stderr, "Rank %.0f: file creation failed!", mpirank);
        return 0;
    }

    char tmp[256];
    char unitStr[5];

    if (ifarg(3)) {
        iPtr->np_   = (int) *getarg(3);
        iPtr->ptrs_ = (double**)hoc_Ecalloc(iPtr->np_, sizeof(double*)); hoc_malchk();
        iPtr->buf_  = (float*)hoc_Ecalloc(iPtr->np_, sizeof(float)); hoc_malchk();
    }

    if (ifarg(4) && ifarg(5) && ifarg(6)) {
        iPtr->tstart_   = *getarg(4);
        iPtr->tstop_    = *getarg(5);
        iPtr->Dt_       = *getarg(6);
        // printf("tstart = %g\n", iPtr->tstart_);
        // printf("tstop = %g\n", iPtr->tstop_);
        // printf("Dt = %g\n", iPtr->Dt_);
        iPtr->tsteps_   = (int) (((iPtr->tstop_-iPtr->tstart_)/iPtr->Dt_)+.5);
        // printf("steps = %d\n", info->tsteps_);
        // iPtr->tsteps_ += 1;
        // printf("steps = %d\n", iPtr->tsteps_);
    }

    if (hoc_is_str_arg(7)) {
        sprintf(unitStr, "%s", gargstr(7));
    } else {
        sprintf(unitStr, "xx");
    }

    tstart = iPtr->tstart_;
    tstop  = iPtr->tstop_;
    Dt = iPtr->Dt_;

    /*****************************************************/
    /* hdf5                                              */
    /*****************************************************/
    // neuron name
    sprintf(tmp, "/%s", iPtr->neuronName_);

    if (iPtr->groupCreated_ ==0) {
        // printf("create group: %s\n", tmp);
        iPtr->neuron_ = H5Gcreate(iPtr->file_, tmp, 0);
    }

    // report name
    sprintf(tmp, "/%s/%s", iPtr->neuronName_, iPtr->rptName_);
    // printf("create group: %s\n", tmp);
    iPtr->rpt_ = H5Gcreate(iPtr->file_, tmp, 0);

    // printf("info->np_=%d\n", info->np_);

    // create data set
    hsize_t dims[2]; dims[0] = iPtr->tsteps_; dims[1] = iPtr->np_;
    iPtr->dataspace_ = H5Screate_simple(2, dims, NULL);
    sprintf(tmp, "/%s/%s/data", iPtr->neuronName_, iPtr->rptName_);
    iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_FLOAT, iPtr->dataspace_, H5P_DEFAULT);
    // iPtr->data_ = H5Dcreate(iPtr->file_, tmp, H5T_NATIVE_DOUBLE, iPtr->dataspace_, H5P_DEFAULT);

    // select hyperslab for writing each time step separately into dataset
    hsize_t off[2]; off[0] = 0; off[1] = 0;
    hsize_t size[2]; size[0] = 1; size[1] = iPtr->np_;
    hsize_t start[2]; start[0] = 0; start[1] = 0;
    iPtr->file_space_ = H5Dget_space(iPtr->data_);
    iPtr->mem_space_ = H5Screate_simple(2, size, NULL);
    H5Sselect_hyperslab(iPtr->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);

    // write attributes
    hid_t atype, attr;

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "rank", H5T_NATIVE_INT, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_INT, &mpirank);
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "tstart", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstart_));
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "tstop", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->tstop_));
    H5Aclose(attr);

    // attribute
    atype = H5Screate(H5S_SCALAR);
    attr  = H5Acreate(iPtr->data_, "Dt", H5T_NATIVE_DOUBLE, atype, H5P_DEFAULT);
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &(iPtr->Dt_));
    H5Aclose(attr);

    // attribute
    hid_t astring;
    atype  = H5Screate(H5S_SCALAR);
    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 5);
    attr = H5Acreate(iPtr->data_, "dunit", astring, atype, H5P_DEFAULT);
    H5Awrite(attr, astring, unitStr);
    H5Aclose(attr);

    // attribute
    atype  = H5Screate(H5S_SCALAR);
    astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 2);
    attr = H5Acreate(iPtr->data_, "tunit", astring, atype, H5P_DEFAULT);
    H5Awrite(attr, astring, "ms");
    H5Aclose(attr);

    // if (!newRpt) *ip = info;
    if (newRpt == 1) {
        Info* tPtr; int hd = 1;
        for (tPtr = *ip; tPtr->nextReport_ != 0; tPtr = (Info*) tPtr->nextReport_, hd++) {}
        tPtr->nextReport_ = iPtr;
        iPtr->handle_ = hd;
    }
    rpts += 1;

    return iPtr->handle_;
#endif
ENDVERBATIM
}

FUNCTION newMapping() { : double rptHd, string mapping
VERBATIM
#ifndef DISABLE_HDF5
//printf("newMapping\n");
    INFOCAST; Info* iPtr = 0; Info* info = 0;
    hsize_t dims[2];
    char tmp[256];
    hid_t atype, attr, astring;
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    if (hoc_is_str_arg(2)) {
        if (strncmp(gargstr(2), "point", 5) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_*3, sizeof(float)); hoc_malchk();
            dims[0]=3; dims[1]=info->np_;
        }
        else if (strncmp(gargstr(2), "compartment3D", 13) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_*4, sizeof(float)); hoc_malchk();
            dims[0]=4; dims[1]=info->np_;
        }
        else if (strncmp(gargstr(2), "compartment", 11) == 0) {
            info->map_  = (float*)hoc_Ecalloc(info->np_, sizeof(float)); hoc_malchk();
            dims[0]=1; dims[1]=info->np_;
        }
        info->nm_ = dims[0]*dims[1];
    }

    if(info->file_>=0) {
        // create mapping data set
        hid_t map = H5Screate_simple(2, dims, NULL);
        sprintf(tmp, "/%s/%s/mapping", info->neuronName_, info->rptName_);
        info->mapping_= H5Dcreate(info->file_, tmp, H5T_NATIVE_FLOAT, map, H5P_DEFAULT);

        // hsize_t size[2]; size[0] = 1; size[1] = dim[1]*dim[0];
        // info->map_mem_space_ = H5Screate_simple(2, size, NULL);
        // H5Sselect_hyperslab(info->mem_space_, H5S_SELECT_SET, start, NULL, size, NULL);

        if (strncmp(gargstr(2), "point", 5) == 0) {
            // attribute
            atype  = H5Screate(H5S_SCALAR);
            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);
            attr = H5Acreate(info->mapping_, "type", astring, atype, H5P_DEFAULT);
            H5Awrite(attr, astring, "point");
            H5Aclose(attr);
        }
        else if (strncmp(gargstr(2), "compartment", 11) == 0) {
            int sec, soma, axon, basal, apic;
            sec = soma = axon = basal = apic = 0;

            if (ifarg(3)) {
                sec = (int) *getarg(3);
            }
            if (ifarg(4)) {
                soma = (int) *getarg(4);
            }
            if (ifarg(5)) {
                axon = (int) *getarg(5);
            }
            if (ifarg(6)) {
                basal = (int) *getarg(6);
            }
            if (ifarg(7)) {
                apic = (int) *getarg(7);
            }

            // attribute
            atype  = H5Screate(H5S_SCALAR);
            astring = H5Tcopy(H5T_C_S1); H5Tset_size(astring, 15);
            attr = H5Acreate(info->mapping_, "type", astring, atype, H5P_DEFAULT);
            H5Awrite(attr, astring, gargstr(2));
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "sections", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &sec);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "soma", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &soma);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "axon", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &axon);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "basal", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &basal);
            H5Aclose(attr);

            // attribute
            atype = H5Screate(H5S_SCALAR);
            attr  = H5Acreate(info->mapping_, "apic", H5T_NATIVE_INT, atype, H5P_DEFAULT);
            H5Awrite(attr, H5T_NATIVE_INT, &apic);
            H5Aclose(attr);

        }

    }
#endif
ENDVERBATIM
}


PROCEDURE addvar() { : int rptHD, double* pd
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = 0; Info* iPtr = 0;
    //printf("addVar\n");
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    if (info->tp_ < info->np_) {
        info->ptrs_[info->tp_] = hoc_pgetarg(2);
        ++info->tp_;
    }
#endif
ENDVERBATIM
}


PROCEDURE addmapping() { : int rptHD, double var1, double var2, double var3
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = 0; Info* iPtr = 0;
    //printf("addMapping\n");
    if (ifarg(1)) {
        for (iPtr = *ip; iPtr!= 0 && iPtr->handle_ != (int) *getarg(1); iPtr = (Info*) iPtr->nextReport_) {}
        if (iPtr == 0) printf("ERROR: given handle does not correspond to report!\n");
        else info=iPtr;
    }

    // printf("getarg(2) = %g\n", *getarg(2));
    if (info->mp_ < info->np_) {
        // printf("info->mp_ = %d\n", info->mp_);
        if (ifarg(2)) {
            info->map_[info->mp_] = (float) *getarg(2);
            // printf("info->map = %g\n", info->map_[info->mp_]);
        }
        if (ifarg(3)) {
            info->map_[info->mp_+info->np_] = (float) *getarg(3);
        }
        if (ifarg(4)) {
            info->map_[info->mp_+info->np_*2] = (float) *getarg(4);
        }
        if (ifarg(5)) {
            info->map_[info->mp_+info->np_*3] = (float) *getarg(5);
        }
        ++info->mp_;
    }
#endif
ENDVERBATIM
}


PROCEDURE recdata() {
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if ((t >= info->tstart_) && (t < info->tstop_) && (info->tstep_ < info->tsteps_)) {

            /*****************************************************/
            /* HDF5                                              */
            /*****************************************************/

            if ((info->file_>=0) && (info->data_)) {
                hsize_t off[2] = {info->tstep_, 0};
                hsize_t size[2] = {1, info->np_};

                H5Sselect_hyperslab(info->file_space_, H5S_SELECT_SET, off, NULL, size, NULL);

                float* tt = info->buf_;
                int i;
                for(i=0; i< info->tp_; i++,tt++) {
                    *tt = (float)(*info->ptrs_[i]);
                }
                H5Dwrite(info->data_, H5T_NATIVE_FLOAT, info->mem_space_, info->file_space_, H5P_DEFAULT, info->buf_);
            }

            ++info->tstep_;
        }
    }
#endif
ENDVERBATIM
}


PROCEDURE writeMeta() {
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    char tmp[256];
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->map_) {
            /*****************************************************/
            /* HDF5                                              */
            /*****************************************************/
            if (info->file_ >= 0) {
                if (info->mapping_)
                    H5Dwrite(info->mapping_, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, info->map_);
            }
        }
    }
#endif
ENDVERBATIM
}


COMMENT
/**
 * currently, consolidateTiming() has a simple logic:
 *  1. go through all reports and get minimum start time and maximum stop time
 *  2. check whether all reports have same Dt
 *  3. check whether the start and stop times are consistent with common Dt
 */
ENDCOMMENT
PROCEDURE consolidateTiming() {
VERBATIM
#ifndef DISABLE_HDF5
    INFOCAST; Info* info = *ip;
    //printf("consolidateTiming()\n");
    double tmin = tstart; // values of last report!
    double tmax = tstop; // values of last report!
    double myeps=1e-10;
    double commonDt = Dt;
    //printf("tmin=%g\n", tmin);
    //printf("tmax=%g\n", tmax);
    //printf("Dt=%g\n", Dt);
    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        if (info->tstart_ < tmin) tmin = info->tstart_;
        if (info->tstop_ > tmax) tmax = info->tstop_;
        if (info->Dt_ != Dt) {
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Dt is not the same throughout reports! Setting Dt to %g\n", Dt);
            info->Dt_ = Dt;
        }
    }
    //printf("tmin=%g\n", tmin);
    //printf("tmax=%g\n", tmax);
    //printf("Dt=%g\n", Dt);

    for (info = *ip; info != 0; info = (Info*) info->nextReport_) {
        int steps2start = (int)((info->tstart_-tmin)/Dt+.5);
        double dsteps2start = (info->tstart_-tmin)/Dt;
        if (fabs(dsteps2start - (double)(steps2start)) > myeps) {
            info->tstart_ = tmin + steps2start*Dt;
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting start time to %g\n", info->tstart_);
        }
        int steps2stop = (int)((info->tstop_-tmin)/Dt+.5);
        double dsteps2stop = (info->tstop_-tmin)/Dt;
        if (fabs(dsteps2stop - (double)(steps2stop)) > myeps) {
            info->tstop_ = tmin + steps2stop*Dt;
            if (mpirank == 0) printf("[ASCIIrecord] Warning: Adjusting reporting stop time to %g\n", info->tstop_);
        }
    }

    tstart = tmin;
    tstop = tmax;
#endif
ENDVERBATIM
}
