COMMENT
If the local variable step method is used then the only variables that should
be added are variables of the cell in which this ALU has been instantiated.
ENDCOMMENT

NEURON {
	POINT_PROCESS ALU
	POINTER ptr
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

extern double* hoc_pgetarg(int iarg);
extern double* getarg(int iarg);
extern int ifarg(int iarg);

typedef struct {
    //! list of pointers to hoc variables
	double** ptrs_;
    
    /*! list of scalars to apply to corresponding variables; useful for making units of variables
     * from different sources consistent (e.g. i current sources may be distributed, mA/cm^2, or point processes, nA)
     */
    double * scalars_;
    
    //! number of elements stored in the vectors
	int np_;
    
    //! number of slots allocated to the vectors
	int psize_;
    
    //! function pointer to execute when net_receive is triggered
    int (*process)(void);
} Info;

#define INFOCAST Info** ip = (Info**)(&(_p_ptr))

ENDVERBATIM

NET_RECEIVE(w) {
VERBATIM { INFOCAST; Info* info = *ip;
	info->process();
}
ENDVERBATIM
	net_send(Dt, 1)
}

CONSTRUCTOR {
VERBATIM {
	INFOCAST;
	Info* info = (Info*)hoc_Emalloc(sizeof(Info)); hoc_malchk();
	info->psize_ = 10;
	info->ptrs_ = (double**)hoc_Ecalloc(info->psize_, sizeof(double*)); hoc_malchk();
    info->scalars_ = (double*)hoc_Ecalloc(info->psize_, sizeof(double)); hoc_malchk();
	info->np_ = 0;
	*ip = info;
	
    if (ifarg(2)) {
         Dt = *getarg(2);
    }
    
    //default operation is average
    info->process = &average;
}
ENDVERBATIM
}

DESTRUCTOR {
VERBATIM {
	INFOCAST; Info* info = *ip;
	free(info->ptrs_);
	free(info);
}
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
VERBATIM { INFOCAST; Info* info = *ip;
	if (info->np_ >= info->psize_) {
		info->psize_ += 10;
		info->ptrs_ = (double**) hoc_Erealloc(info->ptrs_, info->psize_*sizeof(double*)); hoc_malchk();
        info->scalars_ = (double*) hoc_Erealloc(info->scalars_, info->psize_*sizeof(double)); hoc_malchk();
	}
    
	info->ptrs_[info->np_] = hoc_pgetarg(1);
    if( ifarg(2)) {
        info->scalars_[info->np_] = *getarg(2);
    } else {
        info->scalars_[info->np_] = 1;
    }

	++info->np_;
    //printf("I have %d values.. (new = %g * %g)\n", info->np_, *(info->ptrs_[info->np_-1]), info->scalars_[info->np_-1] );
}
ENDVERBATIM
}

COMMENT
/*!
 * Take an average of all the variables assigned to this ALU object
 */
ENDCOMMENT
PROCEDURE average() {
VERBATIM { INFOCAST; Info* info = *ip;
	int i;
	double n = 0;
	for (i=0; i < info->np_; ++i) {
      //  printf("%f", (*info->ptrs_[i] * info->scalars_[i]) );
		n += (*info->ptrs_[i] * info->scalars_[i]);
	}
    //printf("\n");
//	output = n/info->np_;
	if (info->np_ > 0) 
	  output = n/info->np_;
	else output = 0;
}
ENDVERBATIM
}

COMMENT
/*!
 * Take a summation of all the variables assigned to this ALU object
 */
ENDCOMMENT
PROCEDURE summation() {
VERBATIM { INFOCAST; Info* info = *ip;
	int i;
	double n = 0;
	for (i=0; i < info->np_; ++i) {
        //printf("%f = %f * %f\n", (*info->ptrs_[i] * info->scalars_[i]), *info->ptrs_[i], info->scalars_[i] );
		n += (*info->ptrs_[i] * info->scalars_[i]);
	}
    
    output = n;
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
VERBATIM { INFOCAST; Info* info = *ip;
	
    char *opname = NULL;
    if (!hoc_is_str_arg(1)) {
        exit(0);
    }
    
    opname = gargstr(1);
    if( strcmp( opname, "summation" ) == 0 ) {
        info->process = &summation;
    } else if ( strcmp( opname, "average" ) == 0 ) {
        info->process = &average;
    } else {
        fprintf( stderr, "Error: unknown operation '%s' for ALU object.  Terminating.\n", opname );
        exit(0);
    }
}
ENDVERBATIM
}
