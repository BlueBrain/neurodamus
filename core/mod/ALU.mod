COMMENT
If the local variable step method is used then the only variables that should
be added are variables of the cell in which this ALU has been instantiated.
ENDCOMMENT

NEURON {
    THREADSAFE
    POINT_PROCESS ALU
    BBCOREPOINTER ptr
    RANGE Dt
    RANGE output
}

PARAMETER {
    Dt = .1 (ms)
    output = 0
}

ASSIGNED {
    ptr
}

INITIAL {
    net_send(0, 1)
}

VERBATIM

#ifndef CORENEURON_BUILD
#if defined(NRN_VERSION_GTEQ)
#if NRN_VERSION_GTEQ(9,0,0)
#define NRN_VERSION_GTEQ_9_0_0
#endif
#endif
#ifndef NRN_VERSION_GTEQ_8_2_0
extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern int ifarg(int iarg);
extern void nrn_register_recalc_ptr_callback(void (*f)());
extern Point_process* ob2pntproc(Object*);
extern double* nrn_recalc_ptr(double*);
#endif

#ifdef NRN_MECHANISM_DATA_IS_SOA
using handle_to_double = decltype(hoc_hgetarg<double>(42));
#else
typedef double* handle_to_double;
#endif
typedef struct {
    //! list of pointers to hoc variables
    handle_to_double* ptrs_;

    /*! list of scalars to apply to corresponding variables; useful for making units of variables
     * from different sources consistent (e.g. i current sources may be distributed, mA/cm^2, or point processes, nA)
     */
    double * scalars_;

    //! number of elements stored in the vectors
    int np_;

    //! number of slots allocated to the vectors
    int psize_;

    //! function pointer to execute when net_receive is triggered
#ifdef NRN_MECHANISM_DATA_IS_SOA
    int (*process)(_internalthreadargsproto_);
#else
    int (*process)(_threadargsproto_);
#endif
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

#define dp double*

#ifndef NRN_MECHANISM_DATA_IS_SOA
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
    sym = hoc_lookup("ALU");
    #ifndef NRN_VERSION_GTEQ_8_2_0
    instances = sym->u.template->olist;
    #else
    instances = sym->u.ctemplate->olist;
    #endif
    ITERATE(q, instances) {
        Info* InfoPtr;
        Point_process* pnt;
        Object* o = OBJ(q);
        /*printf("callback for %s\n", hoc_object_name(o));*/
        pnt = ob2pntproc(o);
        Datum* _ppvar = pnt->_prop->dparam;
        INFOCAST;
        InfoPtr = *ip;
        for (i=0; i < InfoPtr->np_; ++i)
            InfoPtr->ptrs_[i] =  nrn_recalc_ptr(InfoPtr->ptrs_[i]);
    }
}
#endif
#endif
ENDVERBATIM

NET_RECEIVE(w) {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    info->process(_threadargs_);
#endif
}
ENDVERBATIM
    net_send(Dt - 1e-5, 1)
}

CONSTRUCTOR {
VERBATIM {
#ifndef CORENEURON_BUILD
#ifndef NRN_MECHANISM_DATA_IS_SOA
    static int first = 1;
    if (first) {
        first = 0;
        nrn_register_recalc_ptr_callback(recalc_ptr_callback);
    }
#endif

    INFOCAST;
    Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
    info->psize_ = 10;
#ifdef NRN_VERSION_GTEQ_9_0_0
    info->ptrs_ = new handle_to_double[info->psize_]; hoc_malchk();
#else
    info->ptrs_ = (handle_to_double*)hoc_Ecalloc(info->psize_, sizeof(handle_to_double)); hoc_malchk();
#endif
    info->scalars_ = (double*)hoc_Ecalloc(info->psize_, sizeof(double)); hoc_malchk();
    info->np_ = 0;
    *ip = info;

    if (ifarg(2)) {
        Dt = *getarg(2);
    }

    //default operation is average
    info->process = &average;
#endif
}
ENDVERBATIM
}

DESTRUCTOR {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
#ifdef NRN_VERSION_GTEQ_9_0_0
    delete[] info->ptrs_;
#else
    free(info->ptrs_);
#endif
    free(info);
#endif
}
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
    #if defined(NRN_VERSION_GTEQ_9_0_0)
    net_send(_tqitem, (double*)0, _ppvar[1].get<Point_process*>(), etime, 1.0);
    #else
    net_send(_tqitem, (double*)0, (Point_process*)_ppvar[1]._pvoid, etime, 1.0);
    #endif    
#endif
ENDVERBATIM
}


COMMENT
/*!
 * Include another variable in the arithmetic operation
 * @param variable pointers
 * @param scalar (optional, 1 by default)
 */
ENDCOMMENT
PROCEDURE addvar() { : double* pd
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    if (info->np_ >= info->psize_) {
        info->psize_ += 10;
#ifdef NRN_VERSION_GTEQ_9_0_0
        auto old_ptrs = info->ptrs_;
        info->ptrs_ = new handle_to_double[info->psize_]; hoc_malchk();
        std::copy(old_ptrs, old_ptrs+info->np_, info->ptrs_);
        delete[] old_ptrs;
#else
        info->ptrs_ = (handle_to_double*)hoc_Erealloc(info->ptrs_, info->psize_*sizeof(handle_to_double)); hoc_malchk();
#endif
        info->scalars_ = (double*) hoc_Erealloc(info->scalars_, info->psize_*sizeof(double)); hoc_malchk();
    }
#ifdef NRN_MECHANISM_DATA_IS_SOA
    handle_to_double var = hoc_hgetarg<double>(1);
#else
    handle_to_double var = hoc_pgetarg(1);
#endif
    info->ptrs_[info->np_] = var;
    if( ifarg(2)) {
        info->scalars_[info->np_] = *getarg(2);
    } else {
        info->scalars_[info->np_] = 1;
    }

    ++info->np_;
    //printf("I have %d values.. (new = %g * %g)\n", info->np_, *(info->ptrs_[info->np_-1]), info->scalars_[info->np_-1] );
#endif
}
ENDVERBATIM
}

COMMENT
/*!
 * Ignore the ptr and instead just report the constant value.  This is a hack to allow reporting of the
 * area of a section.  A better solution should be created
 */
ENDCOMMENT
PROCEDURE constant() {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    if( info->np_ > 0 ) {
        output = info->scalars_[0];
    } else {
        output = 0;
    }
#endif
}
ENDVERBATIM
}


COMMENT
/*!
 * Take an average of all the variables assigned to this ALU object
 */
ENDCOMMENT
PROCEDURE average() {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST;
    Info* info = *ip;
    int i;
    double n = 0;
    for (i=0; i < info->np_; ++i) {
      //  printf("%f", (*info->ptrs_[i] * info->scalars_[i]) );
        n += (*info->ptrs_[i] * info->scalars_[i]);
    }
    //printf("\n");
//    output = n/info->np_;
    if (info->np_ > 0)
      output = n/info->np_;
    else output = 0;
#endif
}
ENDVERBATIM
}

COMMENT
/*!
 * Take a summation of all the variables assigned to this ALU object
 */
ENDCOMMENT
PROCEDURE summation() {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST; Info* info = *ip;
    int i;
    double n = 0;
    for (i=0; i < info->np_; ++i) {
        //printf("%f = %f * %f\n", (*info->ptrs_[i] * info->scalars_[i]), *info->ptrs_[i], info->scalars_[i] );
        n += (*info->ptrs_[i] * info->scalars_[i]);
    }

    output = n;
#endif
}
ENDVERBATIM
}

COMMENT
/*!
 * Set the operation performed when NET_RECEIVE block executes
 *
 * @param opname The name of the function to be executed
 */
ENDCOMMENT
PROCEDURE setop() {
VERBATIM {
#ifndef CORENEURON_BUILD
    INFOCAST; Info* info = *ip;

    char *opname = NULL;
    if (!hoc_is_str_arg(1)) {
        exit(0);
    }

    opname = gargstr(1);
    if( strcmp( opname, "summation" ) == 0 ) {
        info->process = &summation;
    } else if ( strcmp( opname, "average" ) == 0 ) {
        info->process = &average;
    } else if ( strcmp( opname, "constant" ) == 0 ) {
        info->process = &constant;
    } else {
        fprintf( stderr, "Error: unknown operation '%s' for ALU object.  Terminating.\n", opname );
        exit(0);
    }
#endif
}
ENDVERBATIM
}

VERBATIM
/** not executed in coreneuron and hence need empty stubs only */
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
}
ENDVERBATIM
